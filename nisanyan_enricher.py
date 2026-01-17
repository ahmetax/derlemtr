#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Sözlük Zenginleştirici - NİŞANYAN + TEMİZ KAPANMA
- .wal ve .shm kalıntısı KALMAZ
- atexit ile otomatik temizlik
- WAL → normal mod geçişi
"""

import sqlite3
import time
import requests
import random
import os
import logging
import re
import atexit
from typing import Optional, Dict, Tuple
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Lock

# Brotli
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    print("Uyarı: brotli yok → pip install brotli")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sozluk_enrichment.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TurkishDictionaryEnricher:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"\nLEXICON.DB BULUNAMADI!\nDosya burada olmalı:\n  {self.db_path}\n")
        
        if os.path.getsize(self.db_path) == 0:
            raise ValueError(f"\nLEXICON.DB BOŞ!\nBu dosya yanlış. Doğru dosyayı buraya taşıyın:\n  {self.db_path}\n")
        
        logger.info(f"Veritabanı yüklendi: {self.db_path} ({os.path.getsize(self.db_path):,} bayt)")

        self.session = self._create_session()
        self.lock = Lock()
        self.user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0'
        ]
        self._ensure_db_schema()

        # Otomatik temiz kapatma
        atexit.register(self._cleanup_on_exit)

    def _ensure_db_schema(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sozluk)")
            columns = [col[1] for col in cursor.fetchall()]

            for col, sql in [
                ('attempted', "ALTER TABLE sozluk ADD COLUMN attempted INTEGER DEFAULT 0"),
                ('failed', "ALTER TABLE sozluk ADD COLUMN failed INTEGER DEFAULT 0"),
                ('kaynak', "ALTER TABLE sozluk ADD COLUMN kaynak TEXT")
            ]:
                if col not in columns:
                    cursor.execute(sql)
                    logger.info(f"'{col}' kolonu eklendi")

            # WAL modunu kontrol et ve ayarla
            cursor.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
            if mode != 'wal':
                cursor.execute("PRAGMA journal_mode = WAL")
                logger.info("WAL modu etkinleştirildi (performans için)")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Schema hatası: {e}")

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    # ==================== TDK ====================
    def fetch_from_tdk_api(self, word: str) -> Optional[Dict]:
        try:
            with self.lock:
                time.sleep(random.uniform(0.2, 0.5))
            url = f"https://sozluk.gov.tr/gts?ara={quote(word)}"
            response = self.session.get(url, headers=self._get_headers(), timeout=6)
            if response.status_code == 200:
                data = response.json()
                return data[0] if data and isinstance(data, list) and len(data) > 0 else None
        except Exception as e:
            logger.debug(f"TDK hatası ({word}): {e}")
        return None

    def parse_tdk_data(self, tdk_data: Dict) -> Tuple[Optional[str], Optional[str]]:
        anlam = koken = None
        try:
            if 'anlamlarListe' in tdk_data:
                anlamlar = [f"{i}. {a['anlam']}" for i, a in enumerate(tdk_data['anlamlarListe'], 1) if 'anlam' in a]
                anlam = " | ".join(anlamlar) if anlamlar else None
            if 'lisan' in tdk_data and tdk_data['lisan']:
                koken = tdk_data['lisan']
            elif 'kokenleri' in tdk_data:
                koken = ', '.join(tdk_data['kokenleri'])
        except Exception as e:
            logger.debug(f"TDK parse hatası: {e}")
        return anlam, koken

    # ==================== WIKTIONARY ====================
    def fetch_from_wiktionary_api(self, word: str) -> Optional[Dict]:
        try:
            with self.lock:
                time.sleep(random.uniform(0.6, 1.2))
            url = "https://tr.wiktionary.org/w/api.php"
            params = {'action': 'parse', 'page': word, 'format': 'json', 'prop': 'wikitext', 'formatversion': 2}
            response = self.session.get(url, params=params, headers=self._get_headers(), timeout=8)
            if response.status_code == 200:
                data = response.json()
                return {'wikitext': data['parse']['wikitext']} if 'parse' in data else None
        except Exception as e:
            logger.debug(f"Wiktionary hatası ({word}): {e}")
        return None

    def parse_wiktionary_data(self, wiki_data: Dict) -> Tuple[Optional[str], Optional[str]]:
        anlam = koken = None
        try:
            lines = wiki_data.get('wikitext', '').split('\n')
            for i, line in enumerate(lines):
                if 'köken' in line.lower() or 'etimoloji' in line.lower():
                    if i + 1 < len(lines):
                        koken = lines[i + 1].strip('*# ').strip()
                if line.strip().startswith('#') and not line.strip().startswith('##'):
                    clean = line.strip('#* ').strip()
                    if clean and len(clean) > 3:
                        anlam = (anlam + " | " if anlam else "") + clean
        except Exception as e:
            logger.debug(f"Wiktionary parse hatası: {e}")
        return anlam, koken

    # ==================== NİŞANYAN ====================
    def fetch_from_nisanyan(self, word: str) -> Optional[Dict]:
        try:
            with self.lock:
                time.sleep(random.uniform(1.0, 2.0))
            url = f"https://www.nisanyansozluk.com/?k={quote(word)}"
            response = self.session.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                html = self._decompress_response(response)
                return {'html': html}
        except Exception as e:
            logger.debug(f"Nişanyan fetch hatası ({word}): {e}")
        return None

    def _decompress_response(self, response) -> str:
        encoding = response.headers.get('Content-Encoding', '')
        content = response.content
        try:
            if encoding == 'br' and BROTLI_AVAILABLE:
                return brotli.decompress(content).decode('utf-8')
            elif encoding == 'gzip':
                import gzip
                from io import BytesIO
                with gzip.GzipFile(fileobj=BytesIO(content)) as f:
                    return f.read().decode('utf-8')
            else:
                return content.decode('utf-8')
        except Exception as e:
            logger.debug(f"Decompression hatası: {e}")
            return content.decode('utf-8', errors='ignore')

    def parse_nisanyan_data(self, data: Dict) -> Tuple[Optional[str], Optional[str]]:
        anlam = koken = None
        try:
            html = data.get('html', '')
            pattern = r'\{[^}]*name:"([^"]+)"[^}]*note:"([^"]+)"[^}]*\}'
            matches = re.findall(pattern, html)
            if matches:
                _, note = matches[0]
                note = note.replace('\\u003C', '<').replace('\\u003E', '>').replace('\\"', '"').replace('\\n', ' ')
                note = re.sub(r'%[bi]', '', note)
                note = re.sub(r'\s+', ' ', note).strip()
                if len(note) > 20:
                    koken = note[:1000]
                    first = note.split('.')[0]
                    if 20 < len(first) < 300:
                        anlam = first
        except Exception as e:
            logger.debug(f"Nişanyan parse hatası: {e}")
        return anlam, koken

    # ==================== ZENGİNLEŞTİRME ====================
    def enrich_word(self, word_id: int, word: str, current_anlam: str, current_koken: str, mode: str = 'full') -> Dict:
        result = {
            'id': word_id, 'anlam': current_anlam, 'koken': current_koken,
            'kaynak': None, 'kaynak_guncellendi': False, 'skipped': False
        }

        self.update_word(word_id, attempted=1)
        if self.is_word_failed(word_id):
            result['skipped'] = True
            return result
        if current_anlam and current_koken:
            return result

        sources = [
            ('TDK', self.fetch_from_tdk_api, self.parse_tdk_data),
            ('Wiktionary', self.fetch_from_wiktionary_api, self.parse_wiktionary_data),
            ('Nişanyan', self.fetch_from_nisanyan, self.parse_nisanyan_data)
        ]

        if mode == 'nisanyan':
            sources = [('Nişanyan', self.fetch_from_nisanyan, self.parse_nisanyan_data)]

        for src_name, fetch_fn, parse_fn in sources:
            data = fetch_fn(word)
            if not data:
                continue
            anlam, koken = parse_fn(data)
            updated = False
            if anlam and not current_anlam:
                result['anlam'] = anlam
                updated = True
            if koken and not current_koken:
                result['koken'] = koken
                updated = True
            if updated:
                result['kaynak_guncellendi'] = True
                result['kaynak'] = src_name
                logger.info(f"{src_name}: {word}")
                return result

        self.update_word(word_id, failed=1)
        logger.debug(f"Veri bulunamadı: {word}")
        return result

    def is_word_failed(self, word_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT failed FROM sozluk WHERE id = ?", (word_id,))
            row = cursor.fetchone()
            conn.close()
            return row and row[0] == 1
        except:
            return False

    def get_empty_words(self, limit: Optional[int] = None, mode: str = 'full') -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if mode == 'koken':
            query = """
                SELECT id, kok, anlam, koken FROM sozluk 
                WHERE (koken IS NULL OR koken = '')
                  AND (attempted = 0 OR attempted IS NULL)
                  AND (failed = 0 OR failed IS NULL)
                  AND (onay=0)
                ORDER BY id
            """
        else:
            query = """
                SELECT id, kok, anlam, koken FROM sozluk 
                WHERE ((anlam IS NULL OR anlam = '') OR (koken IS NULL OR koken = ''))
                  AND (attempted = 0 OR attempted IS NULL)
                  AND (failed = 0 OR failed IS NULL)
                  AND (onay=0)
                ORDER BY id
            """
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        words = cursor.fetchall()
        conn.close()
        return words

    def update_word(self, word_id: int, anlam: Optional[str] = None, koken: Optional[str] = None,
                    kaynak: Optional[str] = None, attempted: Optional[int] = None,
                    failed: Optional[int] = None) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT kaynak FROM sozluk WHERE id = ?", (word_id,))
            current_kaynak = cursor.fetchone()
            current_kaynak = current_kaynak[0] if current_kaynak and current_kaynak[0] else None

            updates, params = [], []

            if anlam is not None:
                updates.append("anlam = ?")
                params.append(anlam)
            if koken is not None:
                updates.append("koken = ?")
                params.append(koken)
            if kaynak is not None:
                new_kaynak = kaynak
                if current_kaynak:
                    existing = {k.strip() for k in current_kaynak.split(',')}
                    if kaynak not in existing:
                        new_kaynak = f"{current_kaynak}, {kaynak}"
                updates.append("kaynak = ?")
                params.append(new_kaynak)
                updates.append("onay = ?")
                params.append(1)
            if attempted is not None:
                updates.append("attempted = ?")
                params.append(attempted)
            if failed is not None:
                updates.append("failed = ?")
                params.append(failed)

            if updates:
                params.append(word_id)
                query = f"UPDATE sozluk SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()

            conn.close()
            return True
        except Exception as e:
            logger.error(f"DB hatası (ID: {word_id}): {e}")
            return False

    def process_batch(self, batch_size: int = 50, max_workers: int = 3, mode: str = 'full'):
        query_mode = 'koken' if mode == 'nisanyan' else 'full'
        words = self.get_empty_words(limit=batch_size, mode=query_mode)
        if not words:
            logger.info("İşlenecek kelime kalmadı!")
            return

        logger.info(f"{len(words)} kelime işleniyor (mod: {mode})...")
        success = skipped = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.enrich_word, wid, w, ca, ck, mode): (wid, w)
                for wid, w, ca, ck in words
            }
            for future in as_completed(futures):
                wid, w = futures[future]
                try:
                    res = future.result()
                    if res['skipped']:
                        skipped += 1
                        continue
                    if res['kaynak_guncellendi']:
                        self.update_word(wid, res['anlam'], res['koken'], res['kaynak'])
                        success += 1
                except Exception as e:
                    logger.error(f"Thread hatası ({w}): {e}")

        logger.info(f"Tamamlandı: {success} güncellendi, {skipped} atlandı")

    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stats = {}

        cursor.execute("SELECT COUNT(*) FROM sozluk"); stats['toplam'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE anlam IS NOT NULL AND anlam != ''"); stats['anlam_dolu'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE koken IS NOT NULL AND koken != ''"); stats['koken_dolu'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE (anlam IS NULL OR anlam = '') OR (koken IS NULL OR koken = '')"); stats['eksik'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE (koken IS NULL OR koken = '') AND (attempted = 0 OR attempted IS NULL) AND (failed = 0 OR failed IS NULL)"); stats['koken_pending'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE ((anlam IS NULL OR anlam = '') OR (koken IS NULL OR koken = '')) AND (attempted = 0 OR attempted IS NULL) AND (failed = 0 OR failed IS NULL)"); stats['pending'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE failed = 1"); stats['failed_count'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE onay = 0"); stats['unapproved'] = cursor.fetchone()[0]

        cursor.execute("SELECT kaynak, COUNT(*) FROM sozluk WHERE kaynak IS NOT NULL AND kaynak != '' GROUP BY kaynak ORDER BY 2 DESC")
        stats['kaynak_dagilim'] = {k: c for k, c in cursor.fetchall()}

        conn.close()
        return stats

    def reset_attempted(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE sozluk SET attempted = 0")
            conn.commit()
            conn.close()
            logger.info("Attempted sıfırlandı")
        except Exception as e:
            logger.error(f"Attempted sıfırlanamadı: {e}")

    def clear_failed(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE sozluk SET failed = 0 WHERE failed = 1")
            conn.commit()
            conn.close()
            logger.info("Başarısızlar temizlendi")
        except Exception as e:
            logger.error(f"Başarısızlar temizlenemedi: {e}")

    def _cleanup_on_exit(self):
        """Uygulama kapanırken WAL modunu kapatır → .wal/.shm silinir."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode = DELETE")  # WAL → normal mod
            conn.commit()
            conn.close()
            logger.info("Veritabanı temiz kapatıldı. WAL dosyaları temizlendi.")
        except Exception as e:
            logger.warning(f"Temiz kapatma başarısız: {e}")


def main():
    DB_PATH = "lexicon.db"
    full_path = os.path.abspath(DB_PATH)

    print("\n" + "="*70)
    print("LEXICON.DB KONTROLÜ")
    print("="*70)
    print(f"Aranan dosya: {full_path}")

    if not os.path.exists(full_path):
        print("HATA: lexicon.db bu klasörde YOK!")
        print("Lütfen lexicon.db dosyasını bu klasöre taşıyın.")
        return

    size = os.path.getsize(full_path)
    if size == 0:
        print("HATA: lexicon.db BOŞ! Yanlış dosya olabilir.")
        return

    print(f"VERİTABANI BULUNDU: {size:,} bayt")
    print("="*70 + "\n")

    try:
        enricher = TurkishDictionaryEnricher(full_path)
    except Exception as e:
        print(e)
        return

    try:
        while True:
            stats = enricher.get_statistics()
            logger.info("=" * 70)
            logger.info("İSTATİSTİKLER")
            logger.info("=" * 70)
            logger.info(f"Toplam: {stats['toplam']}")
            logger.info(f"Anlam: {stats['anlam_dolu']} (%{stats['anlam_dolu']*100/stats['toplam']:.1f})")
            logger.info(f"Köken: {stats['koken_dolu']} (%{stats['koken_dolu']*100/stats['toplam']:.1f})")
            logger.info(f"Eksik: {stats['eksik']} | Pending: {stats['pending']} | Köken Pending: {stats['koken_pending']}")
            logger.info(f"Başarısız: {stats['failed_count']}")
            logger.info(f"Onaysız: {stats['unapproved']}")
            if stats['kaynak_dagilim']:
                logger.info("Kaynak Dağılımı:")
                for k, c in stats['kaynak_dagilim'].items():
                    logger.info(f"  {k}: {c}")
            logger.info("=" * 70)

            print("\n" + "=" * 70)
            print("MENÜ")
            print("=" * 70)
            print("[1] FULL Tarama (TDK → Wiktionary → Nişanyan)")
            print("[2] SADECE Nişanyan (köken eksik)")
            print("[C] Başarısızları Temizle")
            print("[R] Attempted Sıfırla")
            print("[CR] İkisi")
            print("[Q] Çıkış")
            print("=" * 70)
            
            choice = input("Seçim: ").strip().upper()

            if choice == 'Q':
                break
            if 'C' in choice:
                enricher.clear_failed()
            if 'R' in choice:
                enricher.reset_attempted()
            if choice in ('1', '2'):
                mode = 'full' if choice == '1' else 'nisanyan'
                workers = 2 if mode == 'nisanyan' else 3
                total_count=0
                while True:
                    enricher.process_batch(batch_size=50, max_workers=workers, mode=mode)
                    total_count+=50
                    print(f"process_batch tamamlandı- Toplam: {total_count:,}")
                    stats = enricher.get_statistics()
                    if stats['failed_count'] == 0:
                        break
                    key = 'koken_pending' if mode == 'nisanyan' else 'pending'
                    if stats[key] == 0:
                        logger.info("TÜM KELİMELER İŞLENDİ!")
                        break
                    time.sleep(3)
    except KeyboardInterrupt:
        logger.info("\nKullanıcı durdurdu. Temiz kapanış bekleniyor...")
    finally:
        # atexit zaten çalışacak, ama log için
        pass


if __name__ == "__main__":
    main()
