# Gemini ile geliştirilen yeni_kelime_tara.py betiğinden yararlanıldı

import os
import sqlite3
import re
import multiprocessing as mp
from typing import List, Set, Dict, Tuple
from tqdm import tqdm # İlerleme çubuğu için
import itertools # İlerlemeyi daha iyi yönetmek için
import math
from tr_core.io_utils import extract_turkish_body, get_files_from_folder

# Zemberek importu ve başlatılması
# DİKKAT: Zemberek'in her alt süreçte (child process) yeniden başlatılması gerekir.
try:
    from zemberek import TurkishMorphology
    
    # Global değişkenler, multiprocessing'de her süreç için kopyalanır.
    GLOBAL_MORPHOLOGY = None

    def init_morphology():
        """Her alt süreç için Zemberek'i başlatır."""
        global GLOBAL_MORPHOLOGY
        if GLOBAL_MORPHOLOGY is None:
            # Sadece bir kere başlat
            GLOBAL_MORPHOLOGY = TurkishMorphology.create_with_defaults()
            # print(f"Zemberek başlatıldı (PID: {os.getpid()})")
except ImportError:
    print("Zemberek kütüphanesi bulunamadı. Morfolojik analiz devre dışı.")
    GLOBAL_MORPHOLOGY = None
    def init_morphology():
        pass


# --- Yapılandırma ve Eşik Değerleri (Aynı Kalıyor) ---
OT_ALT_ESIK = 0.0616  
OY_UST_ESIK = 0.01044  
INPUT_FOLDER = '/home/axax/github/akta/duzyazilar001/project_gutenberg/'
DB_PATH = 'file_index.db'
KESIN_TURKCE_CIKTI = 'akta_kesin_turkce_adaylari.txt'

SESLI_HARFLER = set('aâeıiîoöuü')
TURKISH_CHARS = set('çğıöşü')
FOREIGN_CHARS = set('qwx')
# ... (Diğer sabitler)

# --- 3-GRAM FİLTRELEME İÇİN GEREKLİLER ---
VALID_CHARS = set('abcçdefgğhıijklmnoöprsştuüvyz')
TR_MODEL = {}
TOTAL_TRIGRAM_COUNT = 0
TRGRAM_ALT_ESIK = -11.0 # DENEME EŞİĞİ: Bu değeri ayarlamamız gerekebilir.

def get_files_from_db(db_path: str) -> List[str]:
    """SQLite veritabanından dosya yollarını alır."""
    file_paths = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # files tablosunun 'path' veya 'file_path' gibi bir sütun içerdiğini varsayıyoruz
        cursor.execute("SELECT path FROM files") 
        file_paths = [row[0] for row in cursor.fetchall()]
        conn.close()
    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")
    except Exception as e:
        print(f"Genel hata: {e}")
    return file_paths


# --- Yeni Ardışık Ünlü Kontrol Fonksiyonu ---
def check_consecutive_vowels(word: str, max_vowels: int = 2) -> bool:
    """
    Kelimenin max_vowels'tan fazla ardışık ünlü içerip içermediğini kontrol eder.
    Dönüş: True ise kurala aykırıdır (yani KÖTÜ), False ise uygundur (İYİ).
    """
    word_lower = word.lower()
    consecutive_count = 0
    
    for char in word_lower:
        if char in SESLI_HARFLER:
            consecutive_count += 1
            if consecutive_count > max_vowels:
                return True  # Üçüncü (ve daha fazlası) ardışık ünlü bulundu.
        else:
            consecutive_count = 0
            
    return False

def load_trigram_model(model_path: str = 'trigram_model.txt'):
    """trigram_model.txt dosyasını RAM'e yükler."""
    global TR_MODEL, TOTAL_TRIGRAM_COUNT
    
    if TR_MODEL: return
        
    try:
        total_count = 0
        with open(model_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    trigram = parts[0]
                    # Modeliniz temiz olduğu için yabancı filtreleme yapmaya gerek yok.
                    TR_MODEL[trigram] = int(parts[1])
                    total_count += int(parts[1])
        
        TOTAL_TRIGRAM_COUNT = total_count
        print(f"3-Gram modeli yüklendi. Benzersiz 3-gram: {len(TR_MODEL):,}. Toplam frekans: {TOTAL_TRIGRAM_COUNT:,}")
        
    except FileNotFoundError:
        print(f"HATA: 3-Gram modeli bulunamadı: {model_path}. Puanlama devre dışı.")

def analyze_trigram_scores(test_words: List[str]):
    """
    Verilen kelimelerin 3-Gram puanlarını hesaplar ve dağılımı gösterir.
    """
    if not TR_MODEL:
        print("HATA: 3-Gram modeli yüklü değil. Analiz yapılamaz.")
        return

    scores = {}
    
    # Kelimeleri üç gruba ayırıyoruz:
    # 1. İyi Türkçe (Örn: kitaplık, abacı)
    # 2. Anlamsız (Örn: aaada, aaadır)
    # 3. Yabancı (Örn: gimbal, parkinson)
    
    # Test kelimelerini kontrol.txt'ten alabilirsiniz.
    
    print("\n--- 3-GRAM PUAN ANALİZİ ---")
    for word in test_words:
        score = calculate_trigram_score(word)
        scores[word] = score
        print(f"{word:<20}: {score:>.4f}")

    # Puanları sırala ve ortalama değeri bul
    all_scores = list(scores.values())
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    print("-" * 30)
    print(f"Puan Ortalaması: {avg_score:>.4f}")
    print(f"Minimum Puan: {min(all_scores):>.4f}")
    print(f"Maksimum Puan: {max(all_scores):>.4f}")
    
    return scores

def calculate_trigram_score(word: str) -> float:
    """Kelimenin 3-Gram Log-Olasılık Puanını hesaplar."""
    if not TR_MODEL: return 1.0 
        
    word_lower = word.lower()
    
    trigrams_in_word = []
    # Kelimeyi sadece geçerli harflerle filtrele
    filtered_word = "".join(char for char in word_lower if char in VALID_CHARS)

    if len(filtered_word) < 3:
        return -float('inf') # Çok kısa veya filtrelemeden sonra anlamsız kalanları ele
        
    for i in range(len(filtered_word) - 2):
        trigrams_in_word.append(filtered_word[i:i+3])

    log_prob_sum = 0.0
    # Add-One Smoothing (yumuşatma): Modelde olmayan 3-gramlar için bile bir olasılık atarız.
    V = len(TR_MODEL) # Benzersiz 3-gram sayısı
    
    for trigram in trigrams_in_word:
        count = TR_MODEL.get(trigram, 0)
        
        # Add-One Smoothing ile olasılık hesapla: (count + 1) / (Toplam + V)
        probability = (count + 1) / (TOTAL_TRIGRAM_COUNT + V)
        log_prob_sum += math.log(probability)

    # Ortalama Log-Olasılık
    return log_prob_sum / len(trigrams_in_word)

# --- Multiprocessing İçin Kelime Kontrol Fonksiyonu ---

def calculate_ratios(word: str) -> Tuple[float, float]:
    """Türkçe ve Yabancı harf oranlarını hesaplar (Aynı)."""
    # ... (Önceki koddan calculate_ratios fonksiyonunu buraya kopyalayın)
    word_lower = word.lower()
    only_letters = "".join(filter(str.isalpha, word_lower))
    total_letter_count = len(only_letters)
    
    if total_letter_count == 0:
        return 0.0, 0.0

    turkce_char_count = sum(only_letters.count(c) for c in TURKISH_CHARS)
    foreign_char_count = sum(only_letters.count(c) for c in FOREIGN_CHARS)
    
    return turkce_char_count / total_letter_count, foreign_char_count / total_letter_count


def check_word_candidate(word: str) -> bool: # Sadece bool döndürüyor (True: KESİN, False: YOK/OLASI)
    """
    Bir kelimenin Türkçe olma olasılığını kontrol eder. Sadece Zemberek Onaylı (KESİN) ise True döndürür.
    OLASI sonuçlar (Zemberek'ten geçmeyenler) bu fonksiyonda False döner.
    """
    word = word.strip().lower()
    if len(word) < 4:
        return False

    ot_ratio, oy_ratio = calculate_ratios(word)
    
    # 1. Yabancı Harf Kontrolü
    if oy_ratio > OY_UST_ESIK:
        return False

    # 2. Morfolojik Analiz (KESİN Aday Kontrolü)
    is_zemberek_approved = False
    
    if GLOBAL_MORPHOLOGY:
        try:
            analysis = GLOBAL_MORPHOLOGY.analyze(word)
            results_list = []
            
            # API Kontrolü: Doğru sonuç listesi alanını bul (Zemberek API uyumluluğu için)
            if hasattr(analysis, 'getAnalysisResults'):
                results_list = analysis.getAnalysisResults()
            elif hasattr(analysis, 'results'):
                results_list = analysis.results
            elif hasattr(analysis, 'get_results'):
                 results_list = analysis.get_results()
            elif hasattr(analysis, 'analysis_results'):
                 results_list = analysis.analysis_results
                 
            # Kesin Kontrol: Analiz sonuçları listesi boş değilse Morfolojik Onay başarılıdır.
            if results_list and len(results_list) > 0:
                is_zemberek_approved = True
                
        except Exception:
            # Analiz sırasında hata oluşursa (Type Error vb.), onay başarısızdır.
            is_zemberek_approved = False
    
    # KESİN Filtreleme Uygulama: Zemberek + Ardışık Ünlü + 3-Gram
    if is_zemberek_approved:
        
        # FİLTRE 1: ARDIŞIK ÜNLÜ KONTROLÜ
        if check_consecutive_vowels(word, max_vowels=2):
            return False # Kuralı ihlal etti, elendi.
            
        # FİLTRE 2: 3-GRAM KONTROLÜ
        trigram_score = calculate_trigram_score(word)
        
        if trigram_score > TRGRAM_ALT_ESIK:
            return True # KESİN ONAYLANDI
        else:
            return False # 3-Gram puanı çok düşük, elendi.

    # 3. Zemberek onaylamazsa veya kural dışı kalırsa (Eski OLASI adayı olsa bile)
    return False # Artık OLASI sonuçları istemediğiniz için her zaman False


def metin_dosyasindan_kelime_ayikla(file_path: str, lexicon: Set[str], pool: mp.Pool) -> Set[str]:
    """
    Tek bir metin dosyasından kelimeleri ayıklar ve kontrol eder.
    Sadece 'KESİN' Türkçe adaylarını içeren bir set döndürür.
    """
    WORD_REGEX = re.compile(r'[a-zçğıöşü]+')
    words_to_check = []
    
    # 1. Tüm kelimeleri hızlıca oku ve filtrele (ana süreçte)
    try:
        # errors='ignore' kullanmaya devam ediyoruz, ek güvenlik sağlar
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in tqdm(f, desc=f"Dosya Okuma: {os.path.basename(file_path)}"):
                line = line.lower()
                words = WORD_REGEX.findall(line)
                
                for word in words:
                    # Yeni kelimeleri sadece mevcut lexicon'da yoksa ve en az 4 harfse kontrol et
                    if word not in lexicon and len(word) >= 4:
                        words_to_check.append(word)
                        
    except Exception as e:
        print(f"UYARI: {file_path} dosyası okuma/ayrıştırma hatası: {e}")
        return set() # Hata durumunda boş küme döndür

    # Sadece benzersiz kelimeleri kontrol et (iş yükünü azaltır)
    unique_words = list(set(words_to_check))
    print(f"Kontrol edilecek benzersiz kelime sayısı: {len(unique_words):,}")

    # 2. Kelime kontrolünü çoklu işlem havuzuna gönder
    kesin_adaylar = set()
    
    # tqdm ile ilerleme takibi
    results = pool.map(check_word_candidate, unique_words)
    
    # Sonuçları topla: Sadece KESİN olarak True dönenleri al
    for word, is_kesin in zip(unique_words, results):
        if is_kesin:
            kesin_adaylar.add(word)

    # OLASI sonuçları artık toplamadığımız için burayı sadeleştiriyoruz.
    print(f"Yeni KESİN Aday (Dosya): {len(kesin_adaylar):,}")
    
    return kesin_adaylar # Sadece KESİN setini döndür

# --- Dosya Yazma ve Main Fonksiyonları (Optimize Edildi) ---

def dosyaya_yaz_optimizeli(candidates: Dict[str, Set[str]]):
    """Bulunan adayları dosyaya yazar (Var olanı silip yeniden yazar)."""
    
    # Var olan çıktıları sil (tekrar yazmayı önlemek için)
    # if os.path.exists(KESIN_TURKCE_CIKTI): os.remove(KESIN_TURKCE_CIKTI)
    # if os.path.exists(OLASI_TURKCE_CIKTI): os.remove(OLASI_TURKCE_CIKTI)

    # Kesin adayları yaz
    try:
        with open(KESIN_TURKCE_CIKTI, 'a', encoding='utf-8', errors='ignore') as f:
            print(f"'{len(candidates['KESIN']):,}' kesin adayı yazılıyor...")
            f.write('\n'.join(sorted(candidates['KESIN'])) + '\n')
    except Exception as e:
        print(f"UYARI: {KESIN_TURKCE_CIKTI} dosyası işlenirken beklenmedik hata oluştu: {e}")
        return {'KESIN': set(), 'OLASI': set()}

def sonuclari_kaydet(candidates: Set[str], file_path: str):
    """
    Tüm işlem bittikten sonra KESİN adayları tek seferde dosyaya yazar.
    """
    print(f"\nSonuçlar {file_path} dosyasına yazılıyor...")
    
    # Dosya yazma modunda ('w') açılır, çünkü tüm kelimeler zaten set içinde tekil (unique) olarak toplandı.
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # Alfabetik sıraya göre yazmak okumayı kolaylaştırır.
            sorted_candidates = sorted(list(candidates))
            f.write('\n'.join(sorted_candidates))
            
        print(f"[BAŞARILI] Toplam {len(candidates):,} KESİN aday kaydedildi.")
        
    except Exception as e:
        print(f"HATA: Sonuçlar dosyaya yazılırken bir sorun oluştu: {e}")


def main(target: str, mode: str):
    
    # --- YENİ SABİT: ARALIKLI KAYIT İÇİN EŞİK ---
    SAVE_INTERVAL = 1000 # Kaç dosyada bir kayıt yapılacağı
    
    # 1. Mevcut Lexicon içeriğini yükle (TR_LEXICON ve KESİN ADAYLARI birleştirildi)
    lexicon = set()
    previously_saved_candidates = set() # YENİ: Önceden kaydedilenleri buraya alacağız

    # 1a. Ana Sözlük (tr_lexicon.txt)
    try:
        # Lütfen buradaki yolu kendi tr_lexicon.txt dosyanızın yoluna göre düzeltin.
        TR_LEXICON_PATH = '/home/axax/Videos/yapayzeka/GUNLUK_HABERLER/YWRITER/tr_lexicon.txt'
        with open(TR_LEXICON_PATH, 'r', encoding='utf-8') as f:
            lexicon.update(line.strip().lower() for line in f if line.strip())
        print(f"'{len(lexicon):,}' kelime mevcut tr_lexicon.txt'ten yüklendi.")
    except FileNotFoundError:
        print("tr_lexicon.txt dosyası bulunamadı. Boş bir sözlük ile devam ediliyor.")
        
    # 1b. Önceki Kesin Adaylar (kesin_turkce_adaylari.txt)
    try:
        with open(KESIN_TURKCE_CIKTI, 'r', encoding='utf-8') as f:
            previously_saved_candidates.update(line.strip().lower() for line in f if line.strip())
            
        # Önceden kaydedilmiş adayları hem filtreleme sözlüğüne (lexicon)
        lexicon.update(previously_saved_candidates)
        # hem de merkezi toplama setine (final_candidates) eklenmek üzere tutuyoruz.
        print(f"'{len(previously_saved_candidates):,}' kelime kesin adaylar dosyasından YENİDEN yüklendi.")
    except FileNotFoundError:
        print("kesin_turkce_adaylari.txt bulunamadı. Sıfırdan başlanıyor.")
        
    print(f"TOPLAM KONTROL SÖZLÜĞÜ BOYUTU: {len(lexicon):,} kelime.")
    
    # ... (Geri kalan Dosya listeleme, Trigram yükleme lojiği aynı kalır) ...
    all_files_to_process = []
    # ... (get_files_from_folder ve diğer modları buraya yerleştirin)
    if mode == 'path':
        all_files_to_process = [target]
    elif mode == 'db':
        all_files_to_process = get_files_from_db(DB_PATH)
    elif mode == 'folder':
        all_files_to_process = get_files_from_folder(target)
    else:
        print("Geçersiz mod belirlendi. (path, db, folder olmalı)")
        return
    
    load_trigram_model()

    # 2. Multiprocessing Havuzunu Başlat
    cpu_count = mp.cpu_count()
    print(f"Kullanılan Çekirdek Sayısı (Pool Size): {cpu_count}")

    with mp.Pool(processes=cpu_count - 1 or 1, initializer=init_morphology) as pool:
        
        final_candidates = previously_saved_candidates.copy()
        
        total_files = len(all_files_to_process)
        print(f"Toplam {total_files:,} dosya işlenecek...")
        
        # Dosya numarası i ile döngü
        for i, file_path in enumerate(all_files_to_process, 1):
            print(f"\n[{i}/{total_files}] -> İŞLENİYOR: {os.path.basename(file_path)}")
            
            # metin_dosyasindan_kelime_ayikla artık sadece KESİN kelimeler setini döndürür
            new_candidates = metin_dosyasindan_kelime_ayikla(file_path, lexicon, pool)
            
            # Ana bellekte adayları merkezi küme ile birleştir (Tekillik garanti altında)
            final_candidates.update(new_candidates)
            
            # --- ARALIKLI KAYDETME KONTROLÜ ---
            if i % SAVE_INTERVAL == 0:
                print(f"\n<<< {i:,} DOSYA TAMAMLANDI: ARALIKLI KAYIT BAŞLIYOR >>>")
                # Var olan set'i 'w' (yazma) moduyla kaydet, böylece dosya güncel ve tekil kalır.
                sonuclari_kaydet(final_candidates, KESIN_TURKCE_CIKTI)
                print("<<< ARALIKLI KAYIT BİTTİ >>>")

        print("\n--- İşlem Tamamlandı ---")
        
    # 3. Sonuçları Dosyalara Kaydet (Döngü bittikten sonra son kez yazma)
    print("\nSON KAYIT İŞLEMİ BAŞLIYOR...")
    sonuclari_kaydet(final_candidates, KESIN_TURKCE_CIKTI)

    print("\n--- Nihai Özet ---")
    print(f"İşlenen Toplam Dosya Sayısı: {total_files:,}")
    print(f"Bulunan KESİN Türkçe Adayı: {len(final_candidates):,} kelime.")
    print("İyi çalışmalar!")

if __name__ == "__main__":
    # Tekrar deneme amaçlı kullanım:
    # main(INPUT_FOLDER+'271.txt', 'path')
    main(INPUT_FOLDER, 'folder') 
    # main('/home/axax/kaynaklar/aaa-kaynaklar/', 'db') 

