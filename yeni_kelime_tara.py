# 

import os
import sqlite3
import re
import multiprocessing as mp
from typing import List, Set, Dict, Tuple
from tqdm import tqdm # İlerleme çubuğu için
import itertools # İlerlemeyi daha iyi yönetmek için
import math
import time
from aktalib import show_time

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

KESIN_TURKCE_CIKTI = 'yeni_kesin_turkce_adaylari.txt'
OLASI_TURKCE_CIKTI = 'yeni_olasi_turkce_adaylari.txt'

SESLI_HARFLER = set('aâeıiîoöuü')
TURKISH_CHARS = set('çğıöşü')
FOREIGN_CHARS = set('qwx')
# ... (Diğer sabitler)

# --- 3-GRAM FİLTRELEME İÇİN GEREKLİLER ---
VALID_CHARS = set('abcçdefgğhıijklmnoöprsştuüvyz')
TR_MODEL = {}
TOTAL_TRIGRAM_COUNT = 0
TRGRAM_ALT_ESIK = -11.0 # DENEME EŞİĞİ: Bu değeri ayarlamamız gerekebilir.

def get_files_from_folder(folder_path: str, extensions: Tuple[str] = ('.txt', '.doc', '.pdf')) -> List[str]:
    """Bir klasördeki (alt klasörler dahil) metin dosyalarını bulur."""
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(extensions):
                file_paths.append(os.path.join(root, file))
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

def check_word_candidate(word: str) -> Tuple[str, str]:
    """
    Bir kelimenin Türkçe olma olasılığını kontrol eder ve sınıflandırır.
    Zemberek, Ardışık Ünlü ve 3-Gram filtresi uygular.
    """
    word = word.strip().lower()
    if len(word) < 4:
        return word, 'YOK'

    ot_ratio, oy_ratio = calculate_ratios(word)
    
    # 1. Yabancı Harf Kontrolü
    if oy_ratio > OY_UST_ESIK:
        return word, 'YOK'

    # 2. Morfolojik Analiz (KESİN Aday Kontrolü)
    is_zemberek_approved = False
    
    if GLOBAL_MORPHOLOGY:
        try:
            # Sadece bir kere analiz yap
            analysis = GLOBAL_MORPHOLOGY.analyze(word)
            
            # API Kontrolü: Doğru sonuç listesi alanını bul
            results_list = None
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
            pass
    
    # KESİN Filtreleme Uygulama: Zemberek + Ardışık Ünlü + 3-Gram
    if is_zemberek_approved:
        
        # **FİLTRE 1: ARDIŞIK ÜNLÜ KONTROLÜ**
        if check_consecutive_vowels(word, max_vowels=2):
            # aaada, aaadır gibi kelimeler buraya düşer.
            return word, 'OLASI' # Manuel kontrole düşür
            
        # **FİLTRE 2: 3-GRAM KONTROLÜ**
        # Ardışık Ünlü filtresi ana işi yaptığı için, 3-Gram filtresini çok düşük puanlıları elemek için kullanıyoruz (-11.0).
        trigram_score = calculate_trigram_score(word)
        
        if trigram_score > TRGRAM_ALT_ESIK:
            # Hem Zemberek hem 3-Gram onayladı (ve Ünlü Kuralı Başarılı)
            return word, 'KESIN'
        else:
            # Zemberek onayladı ama anlamsız (çok düşük 3-Gram puanı, örn: öşüçği)
            return word, 'OLASI' # Manuel kontrole düşür.

    # 3. Harf Oranları Kontrolü (Geleneksel OLASI Kontrolü)
    if ot_ratio >= OT_ALT_ESIK or oy_ratio < 0.001:
        # Zemberek onaylayamadı, ancak harf kurallarına uyuyor.
        return word, 'OLASI'

    return word, 'YOK'

def metin_dosyasindan_kelime_ayikla(file_path: str, lexicon: Set[str], pool: mp.Pool) -> Dict[str, Set[str]]:
    """Metin dosyasından kelimeleri ayıklar, havuza gönderir ve sonuçları toplar."""
    
    WORD_REGEX = re.compile(r'[a-zçğıöşü]+')
    words_to_check = []
    
    # 1. Tüm kelimeleri hızlıca oku ve filtrele (ana süreçte)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc=f"Dosya Okuma: {os.path.basename(file_path)}"):
                line = line.lower()
                words = WORD_REGEX.findall(line)
                
                for word in words:
                    if word not in lexicon and len(word) >= 4:
                        words_to_check.append(word)
                        
    except FileNotFoundError:
        print(f"\nUyarı: Dosya bulunamadı: {file_path}")
        return {'KESIN': set(), 'OLASI': set()}

    # Sadece benzersiz kelimeleri kontrol et (iş yükünü azaltır)
    unique_words = list(set(words_to_check))
    print(f"Kontrol edilecek benzersiz kelime sayısı: {len(unique_words):,}")

    # 2. Kelime kontrolünü çoklu işlem havuzuna gönder
    candidates = {'KESIN': set(), 'OLASI': set()}
    
    # tqdm ile ilerleme takibi
    results = pool.imap(check_word_candidate, unique_words)
    
    # Sonuçları işleme
    for word, result_type in tqdm(results, total=len(unique_words), desc="Kelime Kontrolü"):
        if result_type == 'KESIN':
            candidates['KESIN'].add(word)
        elif result_type == 'OLASI':
            candidates['OLASI'].add(word)

    return candidates

# --- Dosya Yazma ve Main Fonksiyonları (Optimize Edildi) ---

def dosyaya_yaz_optimizeli(candidates: Dict[str, Set[str]]):
    """Bulunan adayları dosyaya yazar (Var olanı silip yeniden yazar)."""
    
    # Var olan çıktıları sil (tekrar yazmayı önlemek için)
    if os.path.exists(KESIN_TURKCE_CIKTI): os.remove(KESIN_TURKCE_CIKTI)
    if os.path.exists(OLASI_TURKCE_CIKTI): os.remove(OLASI_TURKCE_CIKTI)

    # Kesin adayları yaz
    try:
        with open(KESIN_TURKCE_CIKTI, 'w', encoding='utf-8', errors='ignore') as f:
            print(f"'{len(candidates['KESIN']):,}' kesin adayı yazılıyor...")
            f.write('\n'.join(sorted(candidates['KESIN'])) + '\n')
    except Exception as e:
        print(f"UYARI: {KESIN_TURKCE_CIKTI} dosyası işlenirken beklenmedik hata oluştu: {e}")
        return {'KESIN': set(), 'OLASI': set()}
    
    try:
        # Olası adayları yaz
        with open(OLASI_TURKCE_CIKTI, 'w', encoding='utf-8', errors='ignore') as f:
            print(f"'{len(candidates['OLASI']):,}' olası adayı yazılıyor...")
            f.write('\n'.join(sorted(candidates['OLASI'])) + '\n')
    except Exception as e:
        print(f"UYARI: {OLASI_TURKCE_CIKTI} dosyası işlenirken beklenmedik hata oluştu: {e}")
        return {'KESIN': set(), 'OLASI': set()}

def main(target: str, mode: str):
    """Ana program akışını yönetir."""
    t0 = time.time()    # Başlangıç zamanı
    
    # ... (Lexicon yükleme kısmı aynı kalır)
    # 1. Mevcut tr_lexicon.txt içeriğini yükle
    lexicon = set()
    try:
        with open('tr_lexicon.txt', 'r', encoding='utf-8') as f:
            lexicon.update(line.strip().lower() for line in f if line.strip())
        print(f"'{len(lexicon)}' kelime mevcut lexikon'dan yüklendi.")
    except FileNotFoundError:
        print("tr_lexicon.txt dosyası bulunamadı. Boş bir lexicon ile devam ediliyor.")
    
    all_files_to_process = []
    if mode == 'path':
        all_files_to_process = [target]
    elif mode == 'folder':
        all_files_to_process = get_files_from_folder(target)
    else:
        print("Geçersiz mod belirlendi. (path veya folder olmalı)")
        return
    
    load_trigram_model()
    
    # 2. Multiprocessing Havuzunu Başlat
    cpu_count = mp.cpu_count()
    print(f"Kullanılabilir CPU çekirdek sayısı: {cpu_count}")
    # Zemberek'in başlatılması (her alt süreçte)
    with mp.Pool(processes=cpu_count - 1 or 1, initializer=init_morphology) as pool:
        
        final_candidates = {'KESIN': set(), 'OLASI': set()}
        
        print(f"Toplam {len(all_files_to_process)} dosya işlenecek...")
        
        for file_path in all_files_to_process:
            print(f"\n-> İŞLENİYOR: {file_path}")
            new_candidates = metin_dosyasindan_kelime_ayikla(file_path, lexicon, pool)
            
            # Ana bellekte adayları birleştir
            final_candidates['KESIN'].update(new_candidates['KESIN'])
            final_candidates['OLASI'].update(new_candidates['OLASI'])
            
            # Burası aralıklı yazma noktasıdır (Dosya bazında yazma)
            # İsteğe bağlı: Her dosya bittiğinde çıktıyı yazmak güvenilirliği artırır.
            dosyaya_yaz_optimizeli(final_candidates)


    # 3. Sonuçları Dosyalara Kaydet (Son durumda yazma)
    # Bu zaten döngünün içinde yapıldı. Sadece özet verelim.
    print("\n--- İşlem Özeti ---")
    print(f"Yeni KESİN Türkçe Adayı (Morfolojik onaylı): {len(final_candidates['KESIN']):,} kelime.")
    print(f"Yeni OLASI Türkçe Adayı (Kural uyumlu): {len(final_candidates['OLASI']):,} kelime.")
    print(f"Sonuçlar '{KESIN_TURKCE_CIKTI}' ve '{OLASI_TURKCE_CIKTI}' dosyalarında mevcuttur.")
    # print(f"Toplam zaman: {time.time() - t0:.2f} saniye.")
    show_time("Toplam çalışma süresi", t0, t0)

if __name__ == "__main__":
    # Tekrar deneme amaçlı kullanım:
    main('tr_corpus_wiki.txt', 'path')
    # main('kaynak_metnler/', 'folder') 
