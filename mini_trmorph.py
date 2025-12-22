# Gemini (Verimli SQLite Veri Yükleme Stratejisi)
# kelimeler tablosuna hata kolonu eklendi
# mini_trmorph.py

import sqlite3
import subprocess
import os
import sys
import re
import time
from typing import List, Tuple, Optional

# --- KONFİGÜRASYON ---
# Tr-Morph'un derlenmiş Foma makinesinin yolu
# Projenizi klonladığınız yerde 'trmorph.fst' dosyasının bulunduğundan emin olun.
TRMORPH_FST_PATH = os.path.abspath('./trmorph.fst') 
FLOOKUP_EXEC_PATH = 'flookup' # 'flookup' komutunun sistem PATH'inde olduğunu varsayıyoruz
USE_HYPHEN = False # Görsel okunabilirlik için '-' ekler
DATABASE_NAME = 'lexicon.db'
# INPUT_FILE = 'yeni_adaylar.txt'
MAX_RECORDS = 100000
COMMIT_BATCH_SIZE = 1000

def parse_trmorph_analysis(analysis_line: str) -> Optional[Tuple[str, str, str]]:
    """
    Tr-Morph'un tek bir analiz satırını kök ve tam analiz stringine ayırır.
    """
    
    # Kelime ve analiz kısmını ayırmak için \t kullan
    parts = analysis_line.split('\t')
    if len(parts) < 2:
        return None
    
    # Analiz stringi (örn: oku<V><cv:ye><Adv><0><N><dim><N><0><V><cpl:past><1s>)
    morph_string = parts[1].strip()

    # YENİ KONTROL: Eğer analiz tanınmadıysa (+?) kontrolü
    if morph_string == '+?':
        return None # Bu kelimeyi analiz edemediğimizi belirtmek için None döndür

    # Kökü çıkarmak için ilk morfolojik etiketi bul
    # Desen: Kökü, ardından gelen ilk açılı etiketi bulur.
    match = re.match(r'(.+?)<[A-Za-z]+?:?.*?>', morph_string)
    
    if match:
        root = match.group(1)
    else:
        # Eğer morfolojik etiket yoksa (örn: bilgisayar<N> gibi)
        root = morph_string.split('<')[0] 
        
    ekler = "" 
    analiz = morph_string
    
    return (root, ekler, analiz)

def extract_surface_morphemes(word: str, root: str) -> str:
    """
    Kök ve kelime arasındaki farkı kullanarak eklerin yüzey formunu tahmin eder
    ve görsel okunabilirlik için aralarına '-' ekler. 
    
    ⚠️ ÖNEMLİ NOT: Bu kesimler linguistik olarak doğru olmayabilir, sadece görsel amaçlıdır.
    """
    
    # 1. Kökün yüzey uzunluğunu tahmin etme (Basit string farkı)
    root_len = len(root)
    
    # Eğer kelime, kök ile başlıyorsa (en basit durum)
    # if word.startswith(root):
    #     surface_root = root
    # else:
    #     # Yumuşama/Düşme vb. durumlarını göz ardı ederek, basitçe kelimenin başında kök uzunluğu kadarını alırız.
    #     surface_root = word[:root_len] 
    
    # 2. Eklerin yüzey formu (Örn: 'okuyacaktım' ve 'oku' -> 'yacaktım')
    surface_affixes = word[len(root):]
    
    if not surface_affixes:
        return ""

    # 3. GÖRSEL OKUNABİLİRLİK İÇİN HİFENLEME
    # Morfem sınırlarını bilmediğimiz için 4 karakterde bir ayıracağız.
    # Bu, Zemberek'in yaptığına benzer bir görünüm sağlar ancak doğru morfem kesimini garanti etmez.
    
    max_chunk_size = 4 # Ekleri 4 karakterlik parçalara böl
    chunks = []
    i = 0
    while i < len(surface_affixes):
        chunk = surface_affixes[i:i + max_chunk_size]
        chunks.append(chunk)
        i += max_chunk_size
    if USE_HYPHEN:
        return "(" + "-".join(chunks) + ")"
    else:
        return "(" + "".join(chunks) + ")"

def ensure_kelimeler_table_exists():
    """'kelimeler' tablosunu db_loader.py şemasına göre oluşturur (Yoksa)."""
    script = """
        CREATE TABLE IF NOT EXISTS kelimeler (
            id INTEGER PRIMARY KEY,
            kelime TEXT NOT NULL UNIQUE,
            lemma TEXT,
            kok TEXT,
            ekler TEXT,
            analiz TEXT,
            yontem TEXT,
            aciklama TEXT,
            onay INTEGER DEFAULT 0,
            hata INTEGER DEFAULT 0,
            tip TEXT,
            detay TEXT,
            skor INTEGER DEFAULT 0,        
            CHECK (LENGTH(kelime) > 0)
        );
    """
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            conn.cursor().executescript(script)
        # print("-> 'kelimeler' tablosu hazır.")
    except sqlite3.Error as e:
        print(f"HATA: Veritabanı kurulum hatası: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_word_with_trmorph(word: str) -> Optional[Tuple]:
    """
    Verilen kelimeyi Foma (flookup) aracılığıyla analiz eder ve sonuçları döndürür.
    Dönüş formatı: (kelime, lemma, kok, ekler, analiz, yontem)
    """
    # print(f"Kelime: {word}")
    word = word.strip().lower()
    
    try:
        # 1. Komutu hazırla ve çalıştır
        # Komut: echo "kelime" | flookup trmorph.fst
        command = [FLOOKUP_EXEC_PATH, TRMORPH_FST_PATH] 
        
        process = subprocess.run(
            command,
            input=word, # HATA DÜZELTİLDİ: Artık bytes değil, string (word) gönderiliyor.
            capture_output=True,
            text=True,
            encoding='utf-8', # ÖNEMLİ: Türkçe karakterler için açık UTF-8 ayarı
            timeout=10, 
            check=False 
        )
        
        output = process.stdout.strip()
        output_lines = [line for line in output.split('\n') if line.strip()]
        
        if not output_lines:
            return None # Çıktı yok
        
        # 2. En iyi sonucu (ilk satırı) al
        best_line = output_lines[0]
        
        if best_line.endswith('\t?'):
            # Tr-Morph kelimeyi tanımadı
            return None 

        # 3. Analizi Ayrıştır
        parsed_data = parse_trmorph_analysis(best_line)
        
        if not parsed_data:
            return None 

        root, _, analiz = parsed_data # İkinci alan (eski ekler) artık kullanılmıyor.

        # analiz'in başına "[{root}:{tip}] " ekle
        ss = analiz.split('>')
        if len(ss) > 1:
            sss = ss[0].split('<')
            if len(sss) > 1:
                tip = sss[1]
                if tip=='N':
                    tip = 'Noun'
                elif tip=='V':
                    tip = 'Verb'
                elif tip=='Ij':
                    tip = 'Interj'
                elif tip == 'Adj':
                    tip = 'Adj'
                elif tip == 'Adv':
                    tip = 'Adv'
                elif tip == 'Det':
                    tip = 'Det'
                elif tip == 'Num':
                    tip = 'Num'
                elif tip == 'Onom':
                    tip = 'Onom'
                elif tip == 'Postp':
                    tip = 'Postp'
                elif tip == 'Prn':
                    tip = 'Pron'
                elif tip.startswith('Ij:'):
                    tip = 'Interj,'+tip[3:]
                elif tip.startswith('N:'):
                    tip = 'Noun,'+tip[2:]
                elif tip.startswith('V:'):
                    tip = 'Verb,'+tip[3:]
                elif tip.startswith('Det:'):
                    tip = 'Det,'+tip[4:]
                elif tip.startswith('Num:'):
                    tip = 'Num,'+tip[4:]
                elif tip.startswith('Onom:'):
                    tip = 'Onom,'+tip[5:]
                elif tip.startswith('Postp:'):
                    tip = 'Postp,'+tip[6:]
                elif tip.startswith('Prn:'):
                    tip = 'Prn,'+tip[4:]

                analiz = f"[{sss[0]}:{tip}] {analiz}"
                 
        # YENİ: Yüzey eklerini tahmin et
        ekler = extract_surface_morphemes(word, root) # <-- Yeni fonksiyon çağrıldı

        # kelime, lemma, kok, ekler, analiz, yontem, onay, hata
        # Lemma'yı kök olarak varsayalım
        return (word, root, root, ekler, analiz, "trmorph", 2, 0)	# onay=2, hata=0
        
    except FileNotFoundError:
        print(f"KRİTİK HATA: 'flookup' veya '{TRMORPH_FST_PATH}' yolu bulunamadı.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UYARI: Tr-Morph analizinde hata ({word}): {e}", file=sys.stderr)
        return (word, "", "", "", f"HATA: Tr-Morph İşlem Hatası ({type(e).__name__})", "trmorph_hata")

def main():
    print("--- TRmorph Mini Analiz ve Doğrudan Veritabanı Yükleyici ---")
    start_time = time.time()
    
    conn = None # Bağlantıyı try bloğu dışında tanımla
    try:
        # 1. Veritabanı Bağlantısı ve Kurulumu
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()    
        ensure_kelimeler_table_exists() # Tabloyu kontrol et

        # Performans ayarları
        cursor.execute("PRAGMA journal_mode = WAL") 
        cursor.execute("PRAGMA synchronous = OFF") 

        # 2. Kelime Adaylarını Çekme
        SQL = f"SELECT kelime FROM kelimeler WHERE (onay = 0) AND (hata=0) AND ((analiz = '') OR (analiz IS NULL)) LIMIT {MAX_RECORDS}"
        candidate_words = cursor.execute(SQL).fetchall()
        total_candidates = len(candidate_words)
        print(f"-> '{DATABASE_NAME}' tablosundan {total_candidates} adet kelime adayı okundu.")

        # 3. Analiz, Toplu Veri Toplama ve Periyodik Commit
        print("-> TRmorph analizleri başlıyor ve veriler toplanıyor...")
        
        success_batch = [] # Başarılı analizler için geçici batch
        fail_batch = []    # Başarısız kelimeler için geçici batch
        global_success_count = 0
        global_failed_count = 0

        # SQL Sorguları (Periyodik kullanım için tanımlanır)
        sql_upsert = """
        INSERT INTO kelimeler (kelime, lemma, kok, ekler, analiz, yontem, onay, hata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?) -- 8 adet Soru İşareti
        ON CONFLICT(kelime) DO UPDATE SET
            lemma = excluded.lemma,
            kok = excluded.kok,
            ekler = excluded.ekler,
            analiz = excluded.analiz,
            yontem = excluded.yontem,
            onay = excluded.onay, -- excluded.onay = 2 değerini alacak
            hata = excluded.hata;
        """
        sql_fail_update = """
        UPDATE kelimeler 
        SET hata = 2, 
            aciklama = 'TRmorph tarafından analiz edilemedi'
        WHERE kelime = ?;
        """

        for i, word in enumerate(candidate_words):
            word_str = word[0]
            result_tuple = analyze_word_with_trmorph(word_str)
            
            if result_tuple:
                success_batch.append(result_tuple)
                global_success_count += 1
            else:
                fail_batch.append((word_str,))
                global_failed_count += 1
            
            
            # --- COMMIT KONTROL NOKTASI ---
            if (i + 1) % COMMIT_BATCH_SIZE == 0:
                print(f"   İlerleme: {i + 1}/{total_candidates} kelime analiz edildi. Veritabanına yazılıyor...")
                
                # 4. Geçici Batch'leri Veritabanına Yaz ve Commit Et
                if success_batch:
                    cursor.executemany(sql_upsert, success_batch)
                    success_batch = [] # Batch'i temizle
                
                if fail_batch:
                    cursor.executemany(sql_fail_update, fail_batch)
                    fail_batch = [] # Batch'i temizle
                    
                conn.commit() # KRİTİK: Bu noktada veriler kalıcı hale gelir.
                print(f"   ✅ {i + 1} kayda kadar başarıyla kaydedildi.")


        # 5. Kalan Kayıtları Yaz (Son Batch)
        if success_batch or fail_batch:
            print("\n-> Kalan son batch veritabanına yazılıyor...")
            if success_batch:
                cursor.executemany(sql_upsert, success_batch)
            if fail_batch:
                cursor.executemany(sql_fail_update, fail_batch)
            conn.commit() # KRİTİK: Son kayıtları kaydet
            print("✅ Son batch başarıyla kaydedildi.")

        
        print(f"\n-> Analiz tamamlandı. Başarılı analiz sayısı: {global_success_count}")
        print(f"-> Başarısız (Tekrar Denenmeyecek) kayıt sayısı: {global_failed_count}")


    except sqlite3.Error as e:
        print(f"HATA: Veritabanı işlemi sırasında sorun oluştu: {e}", file=sys.stderr)
    except Exception as e:
        print(f"HATA: Genel işlem sırasında sorun oluştu: {e}", file=sys.stderr)
        
    finally:
        if conn:
            conn.close()

    end_time = time.time()
    print(f"--- ✅ İŞLEM TAMAMLANDI! Toplam süre: {end_time - start_time:.2f} saniye. ---")

if __name__ == '__main__':
    main()
