import subprocess
import os
import sys
import re
from typing import Optional, Tuple # <-- BU SATIRI EKLEYİN VEYA KONTROL EDİN

# --- KONFİGÜRASYON ---
# Tr-Morph'un derlenmiş Foma makinesinin yolu
# Projenizi klonladığınız yerde 'trmorph.fst' dosyasının bulunduğundan emin olun.
TRMORPH_FST_PATH = os.path.abspath('./trmorph.fst') 
FLOOKUP_EXEC_PATH = 'flookup' # 'flookup' komutunun sistem PATH'inde olduğunu varsayıyoruz
USE_HYPHEN = False # Görsel okunabilirlik için '-' ekler

def get_mastar_eki(root):
    """Kökün son ünlüsüne göre 'mak' veya 'mek' döner."""
    kalin_unluler = 'aıou'
    ince_unluler = 'eiöü'
    
    # Kökü sondan başa tarayarak ilk bulduğumuz ünlüyü baz alıyoruz
    for char in reversed(root.lower()):
        if char in kalin_unluler:
            return "mak"
        if char in ince_unluler:
            return "mek"
    return "mak" # Ünlü bulunamazsa varsayılan

# --- ANALİZ FONKSİYONU ---

def parse_trmorph_analysis(analysis_line: str) -> Optional[Tuple[str, str, str]]:
    """
    Tr-Morph'un tek bir analiz satırını kök ve tam analiz stringine ayırır.
    """
    
    # Kelime ve analiz kısmını ayırmak için \t kullan
    parts = analysis_line.split('\t')
    if len(parts) < 2 or parts[1].strip() == '+?':
        return None        
    
    # Analiz stringi (örn: oku<V><cv:ye><Adv><0><N><dim><N><0><V><cpl:past><1s>)
    morph_string = parts[1].strip()
    # print(f"morph_string: {morph_string}")
    
    # Kökü çıkarmak için ilk morfolojik etiketi bul
    # Desen: Kökü, ardından gelen ilk açılı etiketi bulur.
    # match = re.match(r'(.+?)<[A-Za-z]+?:?.*?>', morph_string)
    match = re.match(r'.+?<([A-Za-z]+?)>', morph_string)
    # print(f"match: {match}")
    tip = match.group(1) if match else "Unknown"
    # print(f"tip: {tip}")
    
    # Tip dönüşümlerini burada yapabiliriz
    tag_map = {'N': 'Noun', 'V': 'Verb', 'Adj': 'Adj', 'Adv': 'Adv', 'Ij': 'Interj'}
    tip_full = tag_map.get(tip, tip)
    # print(f"tip_full: {tip_full}")

    # Kökü bul
    root_match = re.match(r'(.+?)<', morph_string)
    root = root_match.group(1) if root_match else morph_string.split('<')[0]

    return (root, tip_full, morph_string) # (root, tip, analiz)


def extract_surface_morphemes_old(word: str, root: str) -> str:
    """
    Kök ve kelime arasındaki farkı kullanarak eklerin yüzey formunu tahmin eder.
    
    Args:
        word (str): Orijinal kelime (örn: 'okuyacaktım')
        root (str): Morfolojik kök (örn: 'oku')
        
    Returns:
        str: Eklerin yüzey formu (örn: '(yacak-tı-m)')
    """
    
    # Kök ve Kelime Uzunluğu Kontrolü
    if len(root) > len(word):
        return "(HATA: Kök kelimeden uzun)"

    # Tr-Morph kökü, orijinal kelimenin başında yer almak zorunda değildir (ünlü düşmesi/türevi olabilir)
    
    # 1. Kökün Yüzey Formunu Tahmin Etme:
    #   Tr-Morph kökünü kullanarak kelimenin başlangıcında kök yüzey formunu bulmaya çalışalım.
    #   Örn: "gözlemciliklerindendi" -> Kök: "gözlem"
    
    root_len = len(root)
    
    # Eğer kelime, kök ile başlıyorsa (en basit durum)
    if word.startswith(root):
        surface_root = root
    else:
        # Yumuşama/Düşme kontrolü: 
        # İlk başta eşleşmeyen ama muhtemel yüzey formu
        surface_root = word[:root_len] 
        
        # Eğer kök tam olarak kelimenin başında değilse (örn: 'git' -> 'gid') 
        # burada kök yüzey formunun uzunluğunu doğru ayarlamamız gerekir.
        # Basitçe, Zemberek gibi yapalım: Yüzey kökü kelimenin en başında varsayalım.
        
    # 2. Eklerin Yüzey Formunu Çıkarma
    # Kelimenin geri kalan kısmı eklerin yüzey formudur.
    surface_affixes = word[len(surface_root):]
    
    # 3. Yüzey Eklerini, Tr-Morph etiketleriyle eşleştirmek çok karmaşıktır.
    # Bu yüzden sadece yüzey ekini '-' ile ayırılmış olarak döndürelim (Zemberek stilinde).
    
    # Geçici çözüm: Yüzey eklerini tek bir string olarak döndürmek
    
    # NOT: Türkçe'de eklerin yüzey formu, her zaman kök uzunluğundan hemen sonra başlamaz
    # (örn: "o" -> "onun"). Bu, basit bir string manipülasyonu ile çözülebilecek bir sorun değildir.
    # Ancak Foma çıktısını yorumlamak için, eklerin *tam* yüzeyini alabiliriz.
    
    return f"({surface_affixes})" if surface_affixes else ""

def extract_surface_morphemes(word: str, root: str) -> str:
    """
    Kök ve kelime arasındaki farkı kullanarak eklerin yüzey formunu tahmin eder
    ve görsel okunabilirlik için aralarına '-' ekler. 
    
    ⚠️ ÖNEMLİ NOT: Bu kesimler linguistik olarak doğru olmayabilir, sadece görsel amaçlıdır.
    """
    
    # 1. Kökün yüzey uzunluğunu tahmin etme (Basit string farkı)
    root_len = len(root)
    
    # Eğer kelime, kök ile başlıyorsa (en basit durum)
    if word.startswith(root):
        surface_root = root
    else:
        # Yumuşama/Düşme vb. durumlarını göz ardı ederek, basitçe kelimenin başında kök uzunluğu kadarını alırız.
        surface_root = word[:root_len] 
    
    # 2. Eklerin yüzey formu (Örn: 'okuyacaktım' ve 'oku' -> 'yacaktım')
    surface_affixes = word[len(surface_root):]
    
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

def analyze_word_with_trmorph(word: str) -> Optional[Tuple]:
    """
    Verilen kelimeyi Foma (flookup) aracılığıyla analiz eder ve sonuçları döndürür.
    Dönüş formatı: (kelime, lemma, kok, ekler, analiz, yontem, tip, detay)
    """
    
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

        root, tip, analiz_tam = parsed_data # İkinci alan (eski ekler) artık kullanılmıyor.
        
        # YENİ: Yüzey eklerini tahmin et
        ekler = extract_surface_morphemes(word, root) # <-- Yeni fonksiyon çağrıldı

        # kelime, lemma, kok, ekler, analiz, yontem
        # Lemma'yı kök olarak varsayalım
        detay = root	# Şimdilik bu şekilde. Verb olunca mak/mek eklenecek
        if tip == 'Verb':
            mastar = get_mastar_eki(root)
            detay = f"{root}{mastar}" 
        return (word, root, root, ekler, analiz_tam, "trmorph", tip, detay)
        
    except FileNotFoundError:
        print(f"KRİTİK HATA: 'flookup' veya '{TRMORPH_FST_PATH}' yolu bulunamadı.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UYARI: Tr-Morph analizinde hata ({word}): {e}", file=sys.stderr)
        return (word, "", "", "", f"HATA: Tr-Morph İşlem Hatası ({type(e).__name__})", "trmorph_hata","","")

# --- KULLANIM ÖRNEĞİ (Test) ---

def interactive_mode():
    """Kullanıcıdan girdi alarak sürekli analiz yapan ana döngü."""
    
    while True:
        user_input = input("❓ Analiz edilecek kelime(ler)i girin (Çıkmak için 'EXIT'):\n> ").strip().lower()
        
        if user_input == "exit":
            break
        
        if not user_input:
            continue
            
        words_to_analyze = [w.strip() for w in user_input.split() if w.strip()]
        
        for word in words_to_analyze:
            print("... Analiz yapılıyor, lütfen bekleyin...")
            # Analizi gerçekleştir
            result_tuple = analyze_word_with_trmorph(word)
            # results = analyze_batch(words_to_analyze)
            if result_tuple:
                # Başarılı: Tuple'ı güvenle aç (unpack)
                kelime, lemma, kok, ekler, analiz_tam, yontem, tip, detay = result_tuple
                
                print(f"  Kök\t\t: {kok}")
                print(f"  Lemma\t\t: {lemma}")
                print(f"  Ekler\t\t: {ekler}")
                print(f"  Analiz\t: {analiz_tam}")
                print(f"  Yöntem\t: {yontem}")
                print(f"  Tip\t\t: {tip}")
                print(f"  Detay\t\t: {detay}")
            else:
                # Başarısız: None sonucu işlenir
                print("  Sonuç: Tanınmadı")            
            # Sonuçları ekrana bas ve LOG dosyasına kaydet
            # print_and_log_results(results, LOG_FILE_NAME)


if __name__ == "__main__":
    
    print("==============================================")
    print("      TRmorph İnteraktif Kelime Analiz       ")
    print("      (Sonuçlar LOG dosyasına kaydediliyor)   ")
    print("==============================================")
    
    # İnteraktif modu başlat
    interactive_mode()
    
    print("Uygulama başarıyla kapatıldı.")
