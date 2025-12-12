# data_loader.py
# Amaç: Yüksek Performanslı ve Hata Toleranslı Zemberek Yükleyici.
# Çözüm: Multiprocessing Pool ile analiz ve sonuçları TSV dosyasına kaydetme.
# analysis_results.tsv dosyasını oluşturur.
# kelimeler tablosuna hata kolonu eklendi
# Gemini (Verimli SQLite Veri Yükleme Stratejisi)

import os
import glob
import sqlite3
import sys
import csv
from typing import List, Tuple
from multiprocessing import Pool, cpu_count, current_process

# Zemberek/Jpype kütüphaneleri
try:
    from jpype import startJVM, getDefaultJVMPath, JClass, JString, shutdownJVM
except ImportError:
    print("HATA: jpype1 kütüphanesi kurulu değil. Lütfen kontrol edin.")
    sys.exit(1)

# --- GLOBAL KONFİGÜRASYONLAR ---
morphology = None
TurkishMorphology = None
ZEMBEREK_PATH = os.path.abspath('zemberek-full.jar')
TSV_OUTPUT_FILE = 'analysis_results.tsv'

# --- ZEMBEREK İŞÇİ FONKSİYONLARI ---

def zemberek_pool_worker_init():
    """
    Bu fonksiyon, her işçi süreci (worker) başladığında YALNIZCA BİR KEZ çalışır.
    JVM'yi başlatır ve Zemberek'i belleğe yükler (Tek seferlik maliyet).
    """
    global morphology, TurkishMorphology
    
    try:
        # Her işçiye daha az RAM veriyoruz (32GB RAM için 2GB yeterli)
        startJVM(getDefaultJVMPath(), '-ea', f'-Djava.class.path={ZEMBEREK_PATH}', '-Xmx2g') 
        TurkishMorphology = JClass('zemberek.morphology.TurkishMorphology')
        morphology = TurkishMorphology.createWithDefaults()
        # print(f"-> İşçi {current_process().pid}: Zemberek Hazır.") # Gürültüyü azaltmak için kapatıldı
    except Exception as e:
        print(f"-> İşçi {current_process().pid}: JVM/Zemberek Başlatma Hatası: {e}", file=sys.stderr)
        sys.exit(1)

def format_morphemes(analysis):
    """Ekleri (iyor-um) formatında çıkarır."""
    morpheme_data_list = analysis.getMorphemeDataList()
    if morpheme_data_list.size() <= 1: 
        return ""
    surface_forms = [str(morpheme_data_list.get(i).surface) for i in range(1, morpheme_data_list.size())]
    return f"({'-'.join(surface_forms)})"

def analyze_single_word(word: str) -> Tuple:
    """
    Her kelimeyi analiz eder (İşçi Pool'u tarafından tekrar tekrar kullanılır).
    """
    global morphology
    
    if morphology is None:
        return (word, "", "", "", "HATA: JVM başlatılamadı", "zemberek_hata")

    try:
        j_word = JString(word)
        analysis = morphology.analyze(j_word) 
        results = analysis.getAnalysisResults()
        
        if results.isEmpty():
            return (word, word, "", "", "", "zemberek")
        
        best_result = results.get(0)
        
        lemma = str(best_result.getLemmas()[0])
        kok = str(best_result.getStems()[0])
        ekler = format_morphemes(best_result)
        analiz_tam = str(best_result.formatLong())
        yontem = "zemberek"
        
        # TSV'ye yazılacak format: kelime, lemma, kok, ekler, analiz, yontem
        return (word, lemma, kok, ekler, analiz_tam, yontem)

    except Exception as e:
        # Analiz sırasında takılma/çökme yaşanırsa, hata yakalanır ve atlanır.
        return (word, word, "", "", f"HATA: Analiz Hatası ({e})", "zemberek_hata")

# --- VERİTABANI YÖNETİMİ ---

class DBManager:
    def __init__(self, db_path: str = 'lexicon.db'):
        self.db_path = db_path
        self.tsv_path = TSV_OUTPUT_FILE

    def setup_database(self):
        """SQLite veritabanı tablolarını oluşturur/günceller."""
        print(f"-> Veritabanı {self.db_path} ve tablolar oluşturuluyor/güncelleniyor...")
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
                CHECK (LENGTH(kelime) > 0)
            );
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().executescript(script)
            print("-> Veritabanı sozluk tablosu başarıyla oluşturuldu/kontrol edildi.")
        except sqlite3.Error as e:
            print(f"Veritabanı kurulum hatası: {e}")

    def import_tsv_to_db(self):
        """TSV dosyasındaki verileri toplu olarak veritabanına yükler.
        Ancak bu metodu bu betikte kullanmayacağız."""
        if not os.path.exists(self.tsv_path):
            print(f"UYARI: TSV dosyası ({self.tsv_path}) bulunamadı. Veritabanına aktarılacak bir şey yok.")
            return 0
        
        print(f"\n-> '{self.tsv_path}' dosyasından veritabanına toplu yükleme başlatılıyor...")
        total_imported = 0
        
        # Kelime, lemma, kök, ekler, analiz, yöntem
        sql = "INSERT OR IGNORE INTO kelimeler (kelime, lemma, kok, ekler, analiz, yontem) VALUES (?, ?, ?, ?, ?, ?)"
        
        try:
            with open(self.tsv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                data = list(reader) # Tüm veriyi belleğe al

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(sql, data)
                conn.commit()
                total_imported = cursor.rowcount # rows imported
            
            print(f"-> Veritabanına {total_imported} satır başarıyla eklendi/güncellendi.")
            return total_imported

        except sqlite3.Error as e:
            print(f"Veritabanı aktarım hatası: {e}")
            raise
        except Exception as e:
            print(f"TSV okuma/aktarma hatası: {e}")
            raise


# --- ANA İŞ AKIŞI ---

def process_chunk_and_load(chunk_file: str, num_processes: int, batch_size: int = 5000):
    
    # 1. Kelimeleri Oku
    with open(chunk_file, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
        
    total_words = len(words)
    print(f"\n--- 📂 {chunk_file} işleniyor. Toplam {total_words} kelime bulundu. ---")
    
    print(f"-> {num_processes} adet paralel Zemberek işçisi (worker) başlatılıyor. (Bu birkaç saniye sürecek)...")
    
    total_processed = 0
    
    # TSV dosyasına veriyi yazmak için aç
    # 'a': append modu. Eğer program çökerse, yeniden başlarken kaldığı yerden devam edebilir.
    with open(TSV_OUTPUT_FILE, 'a', encoding='utf-8', newline='') as tsvfile:
        tsv_writer = csv.writer(tsvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)

        # 2. Pool'u Başlat (JVM'ler bu aşamada yüklenir)
        with Pool(processes=num_processes, initializer=zemberek_pool_worker_init) as pool:
            
            # 3. Kelimeleri batch'ler halinde pool'a gönder ve sonuçları TSV'ye yaz
            
            for i in range(0, total_words, batch_size):
                word_batch = words[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                # Paralel Analiz: pool.map ile tüm batch'i gönder
                # Eğer bir worker kilitlenirse, pool.map tüm sonuçları bekler.
                # Bu yüzden Zemberek kilitlenmelerini analyze_single_word içinde yakaladık.
                analyzed_data = pool.map(analyze_single_word, word_batch)
                
                # 4. TSV Dosyasına Yazma (Ana süreç)
                tsv_writer.writerows(analyzed_data)
                
                total_processed += len(analyzed_data)
                
                # İlerleme Takibi
                print(f"[{chunk_file}] İlerleme: {total_processed} kelime işlendi. Batch {batch_num} TSV'ye yazıldı.") 
                
    print(f"--- ✅ {chunk_file} işlenmesi tamamlandı. Toplam {total_processed} kelime analiz edildi. ---")

def main():
    print("--- Türkçe Leksikon Veritabanı Yükleyici (Optimal TSV Yöntemi) ---")
    
    # Kullanılabilir CPU çekirdek sayınızın bir kısmı kullanılır (32GB RAM için 6 uygun bir başlangıçtır)
    num_processes = min(cpu_count(), 6) 
    print(f"Sistem CPU Sayısı: {cpu_count()}. Kullanılan İşçi Sayısı: {num_processes}.")
    
    db_manager = DBManager(db_path='lexicon.db')
    db_manager.setup_database() 

    # 1. Analiz ve TSV Dosyasına Yazma
    chunk_files = sorted(glob.glob('chunk_*.txt'))
    
    if not chunk_files:
        print("HATA: 'chunk_?.txt' formatında dosya bulunamadı.")
        return

    for chunk_file in chunk_files:
        process_chunk_and_load(chunk_file, num_processes, batch_size=5000)

    # 2. Analiz tamamlandıktan sonra TSV'den veritabanına yükleme işlemini db_loader.py ile yapacağız.
    # total_imported = db_manager.import_tsv_to_db()

    print(f"\n\n🎉 TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI!")
    # print(f"   Analiz edilen toplam kelime: {total_imported}")


if __name__ == "__main__":
    main()
