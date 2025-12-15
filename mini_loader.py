# Gemini (Verimli SQLite Veri Yükleme Stratejisi)
# mini_loader.py

import sqlite3
import os
import sys
import time
from typing import List, Tuple, Optional

# Zemberek ve Jpype kütüphaneleri
try:
    from jpype import startJVM, getDefaultJVMPath, JClass, JString, shutdownJVM
except ImportError:
    print("HATA: jpype1 kütüphanesi kurulu değil. Lütfen kontrol edin.", file=sys.stderr)
    sys.exit(1)

# --- KONFİGÜRASYON ---
DATABASE_NAME = 'lexicon.db'
INPUT_FILE = 'yeni_adaylar.txt'
ZEMBEREK_PATH = os.path.abspath('zemberek-full.jar')

# Global Zemberek nesneleri (Sequential işlem için)
morphology = None
TurkishMorphology = None

# --- ZEMBEREK VE JVM AYARLARI ---

def setup_jvm_and_zemberek():
    """JVM'yi başlatır ve Zemberek'i belleğe yükler."""
    global morphology, TurkishMorphology
    
    if not os.path.exists(ZEMBEREK_PATH):
        print(f"HATA: Zemberek JAR dosyası bulunamadı: {ZEMBEREK_PATH}", file=sys.stderr)
        sys.exit(1)
        
    try:
        print("-> JVM Başlatılıyor...")
        # Küçük veri seti için daha düşük Xmx ayarı kullanılabilir
        startJVM(getDefaultJVMPath(), '-ea', f'-Djava.class.path={ZEMBEREK_PATH}', '-Xmx2g')
        
        TurkishMorphology = JClass('zemberek.morphology.TurkishMorphology')
        morphology = TurkishMorphology.createWithDefaults()
        print("-> Zemberek TurkishMorphology yüklendi.")
        return True
    except Exception as e:
        print(f"KRİTİK HATA: JVM başlatılırken veya Zemberek yüklenirken bir sorun oluştu: {e}", file=sys.stderr)
        return False

# --- YARDIMCI FONKSİYONLAR ---

def format_morphemes(analysis):
    """Analizden eklerin yüzey formlarını (surface forms) birleştirir (data_loader.py'den alınmıştır)."""
    morpheme_data_list = analysis.getMorphemeDataList()
    if morpheme_data_list.size() <= 1:
        return ""
    
    # Kök hariç morpheme'lerin yüzey formlarını al ve birleştir
    surface_forms = [str(morpheme_data_list.get(i).surface) for i in range(1, morpheme_data_list.size())]
    return f"({'-'.join(surface_forms)})"

def analyze_word(word: str) -> Optional[Tuple]:
    """Verilen kelimeyi analiz eder ve veritabanına yazılacak formata dönüştürür."""
    global morphology
    if morphology is None:
        return None

    try:
        j_word = JString(word.strip())
        analysis = morphology.analyze(j_word)
        results = analysis.getAnalysisResults()
        
        # Analiz sonucu yoksa, None döndür
        if results.isEmpty():
             return None

        # En iyi sonucu al (Zemberek genellikle ilk sonucu en olası kabul eder)
        best_result = results.get(0)
        
        # Analiz bileşenlerini çek
        kelime = word.strip()
        lemma = str(best_result.getLemmas()[0])
        kok = str(best_result.getStems()[0])
        ekler = format_morphemes(best_result)
        analiz = str(best_result.formatLong()) # Tam Zemberek analiz formatı
        yontem = 'zemberek'
        detay = analiz.split(' ')[0].strip()
        detaylar = detay.split(':')
        detay = detaylar[0].strip()[1:]
        tip = detaylar[1].strip()[:-1]
         
        # kelime, lemma, kok, ekler, analiz, yontem, tip, detay (kelimeler tablosunun ilk 6 kolonu + 2)
        return (kelime, lemma, kok, ekler, analiz, yontem, tip, detay)

    except Exception as e:
        # Analiz sırasında JVM hatası/çökmesi oluşursa (nadir)
        print(f"UYARI: '{word}' kelimesi analiz edilirken hata oluştu: {type(e).__name__}", file=sys.stderr)
        return None

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

# --- ANA AKIŞ ---

def main():
    print("--- Zemberek Mini Analiz ve Doğrudan Veritabanı Yükleyici ---")
    start_time = time.time()
    
    # 1. JVM ve Zemberek Kurulumu
    if not setup_jvm_and_zemberek():
        return
        
    # 2. Kelime Adaylarını Oku
    if not os.path.exists(INPUT_FILE):
        print(f"HATA: Giriş dosyası '{INPUT_FILE}' bulunamadı.", file=sys.stderr)
        return
        
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            # Boşlukları temizle ve sadece dolu satırları al
            candidate_words = {line.strip() for line in f if line.strip()}
        
        total_candidates = len(candidate_words)
        print(f"-> '{INPUT_FILE}' dosyasından {total_candidates} adet benzersiz kelime adayı okundu.")
        
    except Exception as e:
        print(f"HATA: Giriş dosyası okunurken sorun oluştu: {e}", file=sys.stderr)
        return

    # 3. Veritabanı Kurulumu
    ensure_kelimeler_table_exists()

    # 4. Analiz ve Toplu Veri Toplama
    print("-> Zemberek analizleri başlıyor ve veriler toplanıyor...")
    analysis_data_for_db = []
    
    for i, word in enumerate(candidate_words):
        result = analyze_word(word)
        if result:
            analysis_data_for_db.append(result)
            
        if (i + 1) % 5000 == 0:
            print(f"   İlerleme: {i + 1}/{total_candidates} kelime analiz edildi...")
            
    success_count = len(analysis_data_for_db)
    print(f"-> Analiz tamamlandı. Başarılı analiz sayısı: {success_count}")


    # 5. Veritabanına Doğrudan Toplu Yazma (UPSERT)
    if not analysis_data_for_db:
        print("-> Veritabanına yazılacak analiz sonucu yok.")
        return

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # db_loader.py'den alınan performans ayarları
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = OFF") 

        # YENİ UPSERT SORGUSU (ON CONFLICT):
        # Eğer 'kelime' kolonu çakışırsa (yani kelime zaten varsa), 
        # o kaydın 'lemma', 'kok', 'ekler', 'analiz' ve 'yontem' kolonları GÜNCELLENİR.
        sql_upsert = """
        INSERT INTO kelimeler (kelime, lemma, kok, ekler, analiz, yontem, tip, detay)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(kelime) DO UPDATE SET
            lemma = excluded.lemma,
            kok = excluded.kok,
            ekler = excluded.ekler,
            analiz = excluded.analiz,
            yontem = excluded.yontem,
            tip = excluded.tip,
            detay = excluded.detay;
        """
        
        cursor.executemany(sql_upsert, analysis_data_for_db)
        # rows_affected, hem eklenen hem de güncellenen satır sayısını içerir.
        rows_affected = cursor.rowcount
        conn.commit()
        
        # Eklenen ve güncellenen satır sayısını ayrıştırmak zordur, bu yüzden toplam etkiyi raporlayalım.
        print(f"\n✅ Başarıyla veritabanına eklenen/güncellenen toplam kayıt sayısı: {rows_affected}")
        
    except sqlite3.Error as e:
        print(f"HATA: Veritabanına yazma sırasında sorun oluştu: {e}", file=sys.stderr)
        
    finally:
        if conn:
            conn.close()

    end_time = time.time()
    print(f"--- ✅ İŞLEM TAMAMLANDI! Toplam süre: {end_time - start_time:.2f} saniye. ---")


if __name__ == '__main__':
    main()
    
    # İşlem bittiğinde JVM'yi kapat
    try:
        shutdownJVM()
        # print("-> JVM başarıyla kapatıldı.") # Zaten main içinde yazdırıldığı için burada kapatıldı
    except Exception as e:
        print(f"UYARI: JVM kapatılırken sorun oluştu: {e}", file=sys.stderr)
