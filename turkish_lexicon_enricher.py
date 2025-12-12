#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Sözlük Zenginleştirici – FINAL VERSION
- Paralel işlem (3 thread)
- attempted + failed veritabanında
- pending & progress takibi
- kullanıcı dostu menü
- güvenli rate limiting
- Grok tarafından optimize edildi
"""

import sqlite3
import time
import requests
import random
import os
import logging
from typing import Optional, Dict, Tuple, Set
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Lock

Total_success = 0
Total_skipped = 0
Total_count = 0

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
    """Türkçe sözlük verilerini TDK + Wiktionary ile zenginleştirir."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.session = self._create_session()
        self.lock = Lock()  # Rate limiting için
        self.user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0'
        ]
        self._ensure_db_schema()

    def _ensure_db_schema(self):
        """Gerekli kolonları ekler."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(sozluk)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'attempted' not in columns:
                cursor.execute("ALTER TABLE sozluk ADD COLUMN attempted INTEGER DEFAULT 0")
                logger.info("✓ 'attempted' kolonu eklendi")
            
            if 'failed' not in columns:
                cursor.execute("ALTER TABLE sozluk ADD COLUMN failed INTEGER DEFAULT 0")
                logger.info("✓ 'failed' kolonu eklendi")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Schema kontrol hatası: {e}")

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
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.9'
        }

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
            logger.debug(f"TDK API hatası ({word}): {e}")
        return None

    def fetch_from_wiktionary_api(self, word: str) -> Optional[Dict]:
        try:
            with self.lock:
                time.sleep(random.uniform(0.6, 1.2))
            url = "https://tr.wiktionary.org/w/api.php"
            params = {
                'action': 'parse', 'page': word, 'format': 'json',
                'prop': 'wikitext', 'formatversion': 2
            }
            response = self.session.get(url, params=params, headers=self._get_headers(), timeout=8)
            if response.status_code == 200:
                data = response.json()
                return {'wikitext': data['parse']['wikitext']} if 'parse' in data else None
        except Exception as e:
            logger.debug(f"Wiktionary API hatası ({word}): {e}")
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

    def enrich_word(self, word_id: int, word: str, current_anlam: str, current_koken: str) -> Dict:
        result = {
            'id': word_id, 'anlam': current_anlam, 'koken': current_koken,
            'kaynak': None, 'kaynak_guncellendi': False, 'skipped': False
        }

        # İşleme alındı → attempted=1
        self.update_word(word_id, attempted=1)

        # Daha önce başarısız → atla
        if self.is_word_failed(word_id):
            result['skipped'] = True
            return result

        if current_anlam and current_koken:
            return result

        # TDK
        tdk_data = self.fetch_from_tdk_api(word)
        if tdk_data:
            anlam, koken = self.parse_tdk_data(tdk_data)
            if anlam and not current_anlam:
                result['anlam'] = anlam
                result['kaynak_guncellendi'] = True
            if koken and not current_koken:
                result['koken'] = koken
                result['kaynak_guncellendi'] = True
            if result['kaynak_guncellendi']:
                result['kaynak'] = 'TDK'
                logger.info(f"TDK: {word}")
                return result

        # Wiktionary
        wiki_data = self.fetch_from_wiktionary_api(word)
        if wiki_data:
            anlam, koken = self.parse_wiktionary_data(wiki_data)
            if anlam and not current_anlam:
                result['anlam'] = anlam
                result['kaynak_guncellendi'] = True
            if koken and not current_koken:
                result['koken'] = koken
                result['kaynak_guncellendi'] = True
            if result['kaynak_guncellendi']:
                result['kaynak'] = 'Wiktionary'
                logger.info(f"Wiktionary: {word}")
                return result

        # Hiçbir şey bulunamadı → failed=1
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

    def get_empty_words(self, limit: Optional[int] = None) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = """
            SELECT id, kok, anlam, koken 
            FROM sozluk 
            WHERE ((anlam IS NULL OR anlam = '') OR (koken IS NULL OR koken = ''))
              AND (attempted = 0 OR attempted IS NULL)
              AND (failed = 0 OR failed IS NULL)
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
            updates, params = [], []
            if anlam is not None:
                updates.append("anlam = ?")
                params.append(anlam)
            if koken is not None:
                updates.append("koken = ?")
                params.append(koken)
            if kaynak is not None:
                updates.append("kaynak = ?")
                params.append(kaynak)
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
            logger.error(f"DB güncelleme hatası (ID: {word_id}): {e}")
            return False

    def process_batch(self, batch_size: int = 50, max_workers: int = 3):
        global Total_success, Total_skipped, Total_count
        words = self.get_empty_words(limit=batch_size)
        if not words:
            logger.info("İşlenecek kelime kalmadı!")
            return

        logger.info(f"{len(words)} kelime işleniyor (paralel: {max_workers})...")
        success_count = skipped_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_word = {
                executor.submit(self.enrich_word, wid, w, ca, ck): (wid, w)
                for wid, w, ca, ck in words
            }
            for future in as_completed(future_to_word):
                wid, w = future_to_word[future]
                try:
                    result = future.result()
                    if result['skipped']:
                        skipped_count += 1
                        continue
                    if result['kaynak_guncellendi']:
                        self.update_word(wid, result['anlam'], result['koken'], result['kaynak'])
                        success_count += 1
                except Exception as e:
                    logger.error(f"Thread hatası ({w}): {e}")

        Total_success += success_count
        Total_skipped += skipped_count
        Total_count += len(words)
        logger.info(f"Tamamlandı: {success_count} güncellendi, {skipped_count} atlandı")
        logger.info(f"Success: {Total_success} Skipped: {Total_skipped} Total: {Total_count}")

    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        stats = {}

        cursor.execute("SELECT COUNT(*) FROM sozluk")
        stats['toplam'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE anlam IS NOT NULL AND anlam != ''")
        stats['anlam_dolu'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE koken IS NOT NULL AND koken != ''")
        stats['koken_dolu'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE (anlam IS NULL OR anlam = '') OR (koken IS NULL OR koken = '')")
        stats['eksik'] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM sozluk 
            WHERE ((anlam IS NULL OR anlam = '') OR (koken IS NULL OR koken = ''))
              AND (attempted = 0 OR attempted IS NULL)
              AND (failed = 0 OR failed IS NULL)
        """)
        stats['pending'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sozluk WHERE failed = 1")
        stats['failed_count'] = cursor.fetchone()[0]

        conn.close()
        return stats

    def reset_attempted(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE sozluk SET attempted = 0")
            conn.commit()
            conn.close()
            logger.info("Attempted sıfırlandı")
        except Exception as e:
            logger.error(f"Attempted sıfırlanamadı: {e}")

    def clear_failed(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE sozluk SET failed = 0 WHERE failed = 1")
            conn.commit()
            conn.close()
            logger.info("Başarısızlar temizlendi")
        except Exception as e:
            logger.error(f"Başarısızlar temizlenemedi: {e}")


def main():
    global Total_success, Total_skipped, Total_count
    DB_PATH = "lexicon.db"
    enricher = TurkishDictionaryEnricher(DB_PATH)


    while True:
        stats = enricher.get_statistics()
        logger.info("=" * 60)
        logger.info("VERİTABANI İSTATİSTİKLERİ")
        logger.info("=" * 60)
        logger.info(f"Toplam: {stats['toplam']}")
        logger.info(f"Anlam dolu: {stats['anlam_dolu']} (%{stats['anlam_dolu']*100/stats['toplam']:.1f})")
        logger.info(f"Köken dolu: {stats['koken_dolu']} (%{stats['koken_dolu']*100/stats['toplam']:.1f})")
        logger.info(f"Eksik: {stats['eksik']} | Pending: {stats['pending']} | Başarısız: {stats['failed_count']}")
        logger.info("=" * 60)

        print("\n[ENTER] Başla | [C] Başarısızları Temizle | [R] Attempted Sıfırla | [CR] İkisi | [Q] Çık")
        choice = input("Seçim: ").strip().upper()

        if choice == 'Q':
            break
        if 'C' in choice:
            enricher.clear_failed()
        if 'R' in choice:
            enricher.reset_attempted()
        if choice in ('', 'C', 'R', 'CR'):
            if choice == '':  # ENTER → başla
                Total_count = stats['toplam']-stats['pending']-stats['failed_count']-stats['eksik']
                try:
                    while True:
                        enricher.process_batch(batch_size=50, max_workers=3)
                        stats = enricher.get_statistics()
                        if stats['pending'] == 0:
                            logger.info("TÜM KELİMELER İŞLENDİ!")
                            break
                        time.sleep(3)
                except KeyboardInterrupt:
                    logger.info("\nİşlem durduruldu.")
            else:
                continue  # Menüye dön


if __name__ == "__main__":
    main()
