import bz2
import xml.sax
import re
import os
from datetime import datetime

# Gemini ile birlikte hazırlandı

# --- Sabitler ---
INPUT_FILE = '/home/axax/Downloads/trwiki-latest-pages-articles.xml.bz2'
OUTPUT_FILE = 'tr_corpus_wiki.txt'

# Wikipedia içindeki bazı etiketleri ve kısımları temizlemek için regex
# 1. Wiki bağlantıları ve şablonları: {{...}} ve [[Dosya:...]] gibi
RE_WIKI_CLEAN = re.compile(r'\{\{.*?\}\}|\[\[Dosya:.*?\]\]|\[\[Kategori:.*?\]\]', re.DOTALL)
# 2. HTML etiketleri (varsa): <ref>...</ref> ve <div> gibi
RE_HTML_CLEAN = re.compile(r'<.*?>', re.DOTALL)
# 3. Birden fazla boşluğu tek boşluğa indirgeme
RE_SPACES = re.compile(r'\s+')
# 4. Başlıkları temizleme (== Başlık ==)
RE_HEADERS = re.compile(r'==.*?==')


class WikiTextHandler(xml.sax.ContentHandler):
    """
    XML içeriğini işlemek için özel SAX işleyici sınıfı.
    Sadece <text> etiketleri içindeki içeriği yakalar ve temizler.
    """
    def __init__(self, output_handle):
        self.in_title = False
        self.in_text = False
        self.current_text = []
        self.page_count = 0
        self.output_handle = output_handle

    def startElement(self, name, attrs):
        if name == 'title':
            self.in_title = True
            self.current_text = []
        elif name == 'text':
            self.in_text = True
            self.current_text = []

    def characters(self, content):
        if self.in_title or self.in_text:
            self.current_text.append(content)

    def endElement(self, name):
        if name == 'title':
            self.in_title = False
        
        elif name == 'text':
            if self.in_text:
                # Metni birleştir
                content = "".join(self.current_text)
                
                # Sadece makale içeriği (<text> içeriği) için temizleme yap
                content = self._clean_wiki_content(content)
                
                # Dosyaya yaz (her makale arasına bir boşluk bırakılabilir)
                self.output_handle.write(content + '\n\n')
                
                self.page_count += 1
                if self.page_count % 10000 == 0:
                    print(f"-> {self.page_count} makale işlendi...")
            
            self.in_text = False
            self.current_text = []

    def _clean_wiki_content(self, text):
        """Wikipedia metnini temizleme adımları."""
        text = RE_WIKI_CLEAN.sub('', text)  # Wiki etiketlerini temizle
        text = RE_HEADERS.sub('', text)      # Başlıkları temizle
        text = RE_HTML_CLEAN.sub('', text)   # HTML etiketlerini temizle
        text = text.replace("'", '')        # Tek tırnakları temizle
        text = RE_SPACES.sub(' ', text)      # Birden fazla boşluğu tek boşluğa indirge
        return text.strip()


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"HATA: Giriş dosyası '{INPUT_FILE}' bulunamadı.")
        print("Lütfen dosyanın betik ile aynı klasörde olduğundan emin olun.")
        return

    start_time = datetime.now()
    print(f"Başlangıç: {start_time.strftime('%H:%M:%S')}")
    print(f"Giriş dosyası: {INPUT_FILE}")
    print(f"Çıkış dosyası: {OUTPUT_FILE}\n")

    try:
        # 1. BZ2 sıkıştırmasını açma
        bz2_file = bz2.BZ2File(INPUT_FILE, 'r')
        
        # 2. Çıkış dosyasını açma
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as output_handle:
            
            # 3. SAX ayrıştırıcısını oluşturma ve çalıştırma
            parser = xml.sax.make_parser()
            parser.setContentHandler(WikiTextHandler(output_handle))
            
            # XML ayrıştırmasını bz2 dosya akışı üzerinden yapma
            parser.parse(bz2_file)
            
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n--- İşlem Tamamlandı ---")
            print(f"Toplam {parser.getContentHandler().page_count} makale işlendi.")
            print(f"Süre: {duration}")
            print(f"Temiz metin dosyası '{OUTPUT_FILE}' oluşturuldu.")
            
    except Exception as e:
        print(f"\nKRİTİK HATA: {e}")
        print("XML ayrıştırması sırasında bir sorun oluştu.")

if __name__ == "__main__":
    main()
