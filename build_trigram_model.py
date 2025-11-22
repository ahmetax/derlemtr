import collections
import os

# Sadece Türkçe ve temel Latin harfleri
ALFABE = set('abcçdefgğhıijklmnoöprsştuüvyz')

def build_trigram_model(file_path: str, model_output: str = 'trigram_model.txt'):
    """tr_corpus.txt dosyasından 3-gram frekans modelini oluşturur ve kaydeder."""
    trigrams = collections.defaultdict(int)
    total_trigrams = 0

    if not os.path.exists(file_path):
        print(f"HATA: Corpus dosyası bulunamadı: {file_path}")
        return

    print(f"'{file_path}' dosyasından 3-gram frekansları hesaplanıyor...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Sadece harfleri küçük harfe çevir
                text = "".join(filter(str.isalpha, line.lower()))
                
                # Her kelimenin başına ve sonuna boşluk eklenerek 3-gramlar daha doğru hesaplanır
                # Ancak burada sadece harf dizilimlerini inceliyoruz, bu da işimizi görecektir.
                
                # Kelime uzunluğu en az 3 olmalıdır
                if len(text) < 3:
                    continue

                for i in range(len(text) - 2):
                    trigram = text[i:i+3]
                    trigrams[trigram] += 1
                    total_trigrams += 1
                    
        # Modeli kaydetme
        with open(model_output, 'w', encoding='utf-8') as out_f:
            for trigram, count in trigrams.items():
                # Frekansı log-olasılık olarak kaydetmek daha iyidir, ancak 
                # basitlik için şimdilik sadece sayıyı kaydedelim.
                out_f.write(f"{trigram}\t{count}\n")
        
        print(f"3-Gram modeli '{model_output}' dosyasına kaydedildi.")
        print(f"Toplam benzersiz 3-gram: {len(trigrams):,}")
        
    except Exception as e:
        print(f"HATA: 3-Gram modeli oluşturulurken bir hata oluştu: {e}")

def build_trigram_model_filtered(file_path: str, model_output: str = 'trigram_model.txt'):
    """tr_corpus.txt dosyasından 3-gram frekans modelini oluşturur ve kaydeder."""

    trigrams = collections.defaultdict(int)
    total_trigrams = 0

    if not os.path.exists(file_path):
        print(f"HATA: Corpus dosyası bulunamadı: {file_path}")
        return

    print(f"'{file_path}' dosyasından 3-gram frekansları hesaplanıyor...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_lower = line.lower()
                # SADECE Türkçe alfabedeki harfleri koru. Diğer her şeyi at.
                # DİKKAT: İngilizce 'a', 'b', 'c' gibi harfleri korumak için ALFABE setini buna göre genişletmeniz gerekir.
                # En güvenlisi: 'a'dan 'z'ye kadar olan tüm harfleri ve Türkçe harfleri al.
                text = "".join(char for char in line_lower if char in ALFABE)
               
                # Her kelimenin başına ve sonuna boşluk eklenerek 3-gramlar daha doğru hesaplanır
                # Ancak burada sadece harf dizilimlerini inceliyoruz, bu da işimizi görecektir.
                
                # Kelime uzunluğu en az 3 olmalıdır
                if len(text) < 3:
                    continue

                for i in range(len(text) - 2):
                    trigram = text[i:i+3]
                    trigrams[trigram] += 1
                    total_trigrams += 1
                    
        # Modeli kaydetme
        with open(model_output, 'w', encoding='utf-8') as out_f:
            for trigram, count in trigrams.items():
                # Frekansı log-olasılık olarak kaydetmek daha iyidir, ancak 
                # basitlik için şimdilik sadece sayıyı kaydedelim.
                out_f.write(f"{trigram}\t{count}\n")
        
        print(f"3-Gram modeli '{model_output}' dosyasına kaydedildi.")
        print(f"Toplam benzersiz 3-gram: {len(trigrams):,}")
        
    except Exception as e:
        print(f"HATA: 3-Gram modeli oluşturulurken bir hata oluştu: {e}")


# Çalıştırma:
# build_trigram_model('tr_corpus_wiki.txt')
if __name__ == "__main__":
    build_trigram_model_filtered('tr_corpus_wiki.txt')

