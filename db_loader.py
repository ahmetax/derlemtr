# db_loader.py
# İşlev: Sadece 'analysis_results.tsv' dosyasındaki Zemberek analiz sonuçlarını
# 'lexicon.db' veritabanındaki 'kelimeler' tablosuna aktarır. (PRAGMA Optimizasyonları ile)

import sqlite3
import csv
import os
import sys
import time

# --- KONFİGÜRASYON ---
DATABASE_NAME = 'lexicon.db'
TSV_INPUT_FILE = 'analysis_results.tsv'
BATCH_SIZE = 50000 # Tek seferde veritabanına yazılacak maksimum satır sayısı

def setup_database(db_path: str):
    """SQLite veritabanı tablolarını (sadece kelimeler tablosunu) oluşturur/günceller."""
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
            CHECK (LENGTH(kelime) > 0)
        );
    """
    try:
        with sqlite3.connect(db_path) as conn:
            conn.cursor().executescript(script)
        print("-> Veritabanı yapısı başarıyla oluşturuldu/güncellendi.")
    except sqlite3.Error as e:
        print(f"Veritabanı kurulum hatası: {e}")
        sys.exit(1)

def import_tsv_to_db(db_path: str, tsv_path: str):
    """TSV dosyasındaki verileri toplu (BATCH) olarak veritabanına yükler."""
    
    if not os.path.exists(tsv_path):
        print(f"\nHATA: TSV dosyası ({tsv_path}) bulunamadı.")
        return 0
    
    print(f"\n-> '{tsv_path}' dosyasından veritabanına toplu yükleme başlatılıyor...")
    start_time = time.time()
    total_imported = 0
    batch_count = 0
    
    sql = "INSERT OR IGNORE INTO kelimeler (kelime, lemma, kok, ekler, analiz, yontem) VALUES (?, ?, ?, ?, ?, ?)"
    
    try:
        # 1. Veritabanı bağlantısını aç ve PRAGMA ayarlarını uygula (Sizin keşfettiğiniz kritik adım)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # YÜKSEK PERFORMANS AYARLARI
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = OFF") 
            # YÜKSEK PERFORMANS AYARLARI SONU
            
            current_batch = []
            
            # 2. TSV dosyasını satır satır oku
            with open(tsv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                
                for row in reader:
                    # Satır 6 sütun içermelidir: kelime, lemma, kök, ekler, analiz, yöntem
                    if len(row) != 6:
                         # Hatalı satırı atla
                         continue
                         
                    current_batch.append(row)
                    
                    if len(current_batch) >= BATCH_SIZE:
                        # Batch büyüklüğüne ulaştık: Veritabanına yaz
                        cursor.executemany(sql, current_batch)
                        conn.commit()
                        
                        total_imported += len(current_batch)
                        batch_count += 1
                        print(f"-> Batch {batch_count}: {total_imported} satır yüklendi. ({time.time() - start_time:.2f} sn)")
                        current_batch = []
            
            # 3. Kalan veriyi yükle (Son batch)
            if current_batch:
                cursor.executemany(sql, current_batch)
                conn.commit()
                total_imported += len(current_batch)
                batch_count += 1
                print(f"-> Batch {batch_count} (Son): {total_imported} satır yüklendi. ({time.time() - start_time:.2f} sn)")

        end_time = time.time()
        print(f"\n-> Veritabanına toplam {total_imported} satır başarıyla eklendi/güncellendi.")
        print(f"-> İşlem süresi: {end_time - start_time:.2f} saniye.")
        
        return total_imported

    except sqlite3.Error as e:
        print(f"\nKRİTİK VERİTABANI HATASI: {e}")
        print("Hata, toplu yükleme sırasında oluştu.")
        sys.exit(1)
    except Exception as e:
        print(f"\nGenel Aktarım Hatası: {e}")
        sys.exit(1)

# --- ANA FONKSİYON ---

def main():
    print("--- Türkçe Leksikon Veritabanı Aktarıcı (TSV -> SQLite Batching) ---")
    
    # 1. Veritabanı yapısını hazırla
    setup_database(DATABASE_NAME)

    # 2. Aktarımı başlat
    import_tsv_to_db(DATABASE_NAME, TSV_INPUT_FILE)

    print("\n🎉 AKTARIM İŞLEMİ TAMAMLANDI!")

if __name__ == "__main__":
    import time
    main()
