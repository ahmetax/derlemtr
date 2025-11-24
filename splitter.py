# splitter.py
INPUT_FILE = 'tr_lexicon.txt'
NUM_CHUNKS = 9

def split_file():
    print(f"'{INPUT_FILE}' dosyası okunuyor...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        words = f.readlines()

    total_words = len(words)
    chunk_size = total_words // NUM_CHUNKS
    
    print(f"Toplam {total_words} kelime, her parça yaklaşık {chunk_size} kelime.")

    for i in range(NUM_CHUNKS):
        start = i * chunk_size
        # Son parçaya kalan tüm kelimeleri ekle
        end = (i + 1) * chunk_size if i < NUM_CHUNKS - 1 else total_words
        
        output_file = f"chunk_{i+1}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.writelines(words[start:end])
        
        print(f"Dosya {output_file} oluşturuldu ({end - start} kelime).")

if __name__ == '__main__':
    split_file()

# Çalıştır: python splitter.py
