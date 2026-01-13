import bz2
import xml.sax
import mwparserfromhell
import os
from datetime import datetime

# --- Ayarlar ---
INPUT_FILE = '/home/axax/Downloads/trwiki-latest-pages-articles.xml.bz2'
OUTPUT_FILE = 'tr_corpus_wiki.txt'

class WikiTextHandler(xml.sax.ContentHandler):
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
                raw_content = "".join(self.current_text)
                
                # Yönlendirme sayfalarını (Redirect) ele
                if not raw_content.strip().startswith(('#YÖNLENDİRME', '#REDIRECT')):
                    clean_text = self._parse_with_mwparser(raw_content)
                    
                    # Sadece anlamlı uzunluktaki makaleleri al
                    if len(clean_text) > 150:
                        self.output_handle.write(clean_text + '\n\n')
                        self.page_count += 1
                
                if self.page_count % 5000 == 0:
                    print(f"-> {self.page_count} makale başarıyla ayrıştırıldı...")
            
            self.in_text = False
            self.current_text = []

    def _parse_with_mwparser(self, wiki_text):
        """mwparserfromhell kullanarak metni temizle."""
        try:
            # Metni ayrıştır (parse)
            wikicode = mwparserfromhell.parse(wiki_text)
            
            # Şablonları, tabloları ve diğer wiki kodlarını çıkarıp sadece düz metni al
            # strip_code parametreleri:
            # normalize=True (beyaz boşlukları düzenler)
            # collapse=True (gereksiz satır sonlarını birleştirir)
            clean_text = wikicode.strip_code(normalize=True, collapse=True)
            
            # Kalan ufak tefek kalıntıları temizle
            clean_text = clean_text.replace("'''", "").replace("''", "")
            return clean_text.strip()
        except Exception:
            # Çok nadiren ayrıştırma hatası olursa boş döndür
            return ""

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"HATA: {INPUT_FILE} bulunamadı.")
        return

    start_time = datetime.now()
    print(f"Başlangıç: {start_time}")

    try:
        # BZ2 dosyasını oku ve SAX ile işle
        bz2_file = bz2.BZ2File(INPUT_FILE, 'r')
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
            parser = xml.sax.make_parser()
            parser.setContentHandler(WikiTextHandler(out_f))
            parser.parse(bz2_file)
            
            duration = datetime.now() - start_time
            print(f"\n--- İşlem Tamamlandı ---")
            print(f"Süre: {duration}")
            print(f"Toplam {parser.getContentHandler().page_count} temiz makale oluşturuldu.")
            print(f"Sonuç dosyası: {OUTPUT_FILE}")
            
    except Exception as e:
        print(f"Kritik Hata: {e}")

if __name__ == "__main__":
    main()