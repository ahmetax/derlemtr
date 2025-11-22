# kelime_toplayici.py
import os
import re
import sys
from pathlib import Path

# Gerekli kütüphaneler için pip ile kurulum:
# pip install python-docx ebooklib beautifulsoup4 PyPDF2 tqdm
# Grok ile hazırlandı

try:
    from docx import Document
    from ebooklib import epub
    from bs4 import BeautifulSoup
    import PyPDF2
    from tqdm import tqdm
except ImportError as e:
    print("Eksik kütüphane:", e)
    print("Lütfen kur: pip install python-docx ebooklib beautifulsoup4 PyPDF2 tqdm")
    sys.exit(1)

# Çıktı dosyası
OUTPUT_FILE = Path("kelimeler.txt")
OUTPUT_FILE.touch(exist_ok=True)  # Dosya yoksa oluştur

# Mevcut kelimeleri yükle (tekrar yazmamak için)
existing_words = set()
if OUTPUT_FILE.stat().st_size > 0:
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                existing_words.add(word)

print(f"{len(existing_words):,} kelime zaten mevcut.")

# Türkçe kelime kontrolü için basit regex
# En az 2 harf, sadece harf ve Türkçe karakterler (ü,ğ,ş,ı,ö,ç)
WORD_PATTERN = re.compile(r"\b[a-zA-ZçÇğĞıİöÖşŞüÜ]{2,}\b")

def temizle_kelime(kelime: str) -> str:
    kelime = kelime.lower()
    # Sadece harfleri bırak, - ile birleşik kelimelere izin ver (örneğin: "yarı-automatic")
    kelime = re.sub(r"[^a-zçğıöşü-]", "", kelime)
    return kelime

def dosya_oku_ve_kelimeleri_ekle(dosya_yolu: Path):
    ext = dosya_yolu.suffix.lower()
    metin = ""

    try:
        if ext == ".pdf":
            with open(dosya_yolu, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    metin += page.extract_text() or ""

        elif ext in {".txt", ".csv", ".tsv", ".md"}:
            with open(dosya_yolu, "r", encoding="utf-8", errors="ignore") as f:
                metin = f.read()

        elif ext == ".docx":
            doc = Document(str(dosya_yolu))
            metin = "\n".join([para.text for para in doc.paragraphs])

        elif ext == ".epub":
            book = epub.read_epub(str(dosya_yolu))
            for item in book.get_items_of_type(epub.ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), "html.parser")
                metin += soup.get_text()

        else:
            print(f"Desteklenmeyen dosya tipi: {dosya_yolu}")
            return

        # Kelimeleri bul ve temizle
        bulunanlar = WORD_PATTERN.findall(metin)
        temizlenenler = {temizle_kelime(k) for k in bulunanlar if len(temizle_kelime(k)) >= 2}

        yeni_kelimeler = temizlenenler - existing_words
        existing_words.update(yeni_kelimeler)

        print(f"{dosya_yolu.name}: {len(yeni_kelimeler):,} yeni kelime eklendi.")

    except Exception as e:
        print(f"Hata {dosya_yolu}: {e}")

def main():
    klasor = Path("kaynak_metnler")
    if not klasor.exists():
        klasor.mkdir()
        print(f"'{klasor}' klasörü oluşturuldu. Lütfen metin dosyalarınızı buraya koyun.")
        return

    desteklenen_uzantilar = {".txt", ".pdf", ".csv", ".tsv", ".docx", ".epub", ".md"}
    dosyalar = [p for p in klasor.rglob("*") if p.suffix.lower() in desteklenen_uzantilar and p.is_file()]

    if not dosyalar:
        print("kaynak_metnler/ klasöründe desteklenen dosya bulunamadı.")
        return

    print(f"{len(dosyalar)} dosya işleniyor...\n")
    for dosya in tqdm(dosyalar, desc="İşleniyor"):
        dosya_oku_ve_kelimeleri_ekle(dosya)

    # Dosya boyut kontrolü (GitHub önerisi: <50 MB)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for kelime in sorted(existing_words):
            f.write(kelime + "\n")

    boyut_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"\nİşlem tamamlandı! Toplam {len(existing_words):,} benzersiz kelime.")
    print(f"kelimeler.txt boyutu: {boyut_mb:.2f} MB")

    if boyut_mb > 50:
        print("UYARI: Dosya 50 MB'ı geçti. GitHub'a yüklemek için Git LFS önerilir.")
        print("   Kurulum: git lfs install && git lfs track \"kelimeler.txt\"")

if __name__ == "__main__":
    main()