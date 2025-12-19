# DerlemTr

## DerlemTr projesinin yeniden canlandırılması

🇹🇷 Yeniden Başlatıldı! (Kasım 2025) - Project Re-started! (November 2025)

Bu yeni çalışmada, geçerliliği denetlenmiş sözcüklerin yer aldığı bir dosyayı doğrudan paylaşmak yerine, böyle bir listeyi oluşturmanın yöntemlerini tüm aşamalarıyla birlikte paylaşacağız.

Eski deponun orijinal içeriğini, eski-versiyon klasöründe bulabilirsiniz.


<p align="center">
  <img src="https://github.com/ahmetax/derlemtr/blob/master/images/gemini_generated_image.jpg" alt="Derlemtr Proje Tanıtım Infografiği" width="70%">
</p>

# A VERIFIED TURKISH WORDLIST

In this project, we're creating a list of words that are still commonly used in current Turkish. I won't share my existing 2 million-word list here. Github has strict file size restrictions. It's certainly possible to bypass this, but I don't think it's very user-friendly. So, instead of providing you with a ready-made list, I'll share tools that will allow you to create a Turkish vocabulary similar to the one I have.

It would be a good idea to create a simple "word collector" as a starting code.

To speed up the coding process, I'm using Claude, Gemini, and Grok as coding consultants. Our primary coding language will be Python. We'll use SQLite as our database manager. The latest version of the Zemberek library (zemberek-full-0.17.1.jar) will be the core of our word analysis.

## TODO LIST
1. Word Collector (Completed)
2. Word Collector from Wikipedia (Completed)
3. Creating the database and tables (Completed)
4. Downloading the updated zemberek-full.jar file (Completed)
5. Obtaining yeni_kesin_turkce_adaylari.txt from tr_corpus_wiki.txt (Completed)
6. Creating lexicon.db database (Completed)
7. Preparing collected words to be imported into the database (Completed)
8. Cloning of the AKTA Project and scanning of Turkish documents (Completed)
9. Adding the sozluk (dictionary) table to the lexicon.db database (Completed)
10. Adding the roots from the kelimeler (words) table to the dictionary table (Completed)
11. Adding the Turkish geographical place names to the dictionary table (Completed)
12. Filling in the meaning, origin, and source columns using TDK and Wiktionary resources.
13. Filling in the meaning, origin, and source columns using TDK, Wiktionary, and Nisanyan resources.

## Using the Word Collector

1. Clone this repo:
```bash
git clone https://github.com/ahmetax/derlemtr.git
cd derlemtr
```
I recommend using a virtual environment: (The following codes are for Ubuntu 24.04. Adapt them to your own system.)
```bash
python3.12 -m venv e312
source e312/bin/activate
```

2. Install the required libraries:
```bash
pip install python-docx ebooklib beautifulsoup4 PyPDF2 tqdm
```
or
```bash
pip install -r requirements.txt
```

3. Create a folder to place the source text:
```bash
mkdir kaynak_metnler
```

4. Copy the desired Turkish text files into the kaynak_metnler folder.

5. Run the word collector:
```bash
python kelime_toplayici.py
```

With each run, newly found words are added alphabetically to the kelimeler.txt file.

## Data transfer from Wikipedia and conversion into isolated and verified words

Download the file https://dumps.wikimedia.org/trwiki/latest/trwiki-latest-pages-articles.xml.bz2. (Approximately 1 GB)

Copy this file to your working folder or provide the full address in wiki_xml2txt.py.

Run the wiki_xml2txt.py script. (This may take a while. Approximately 1,580,000 articles will be processed.)
```bash
python wiki_xml2txt.py
```
You should now have a file named tr_corpus_wiki.txt. It is approximately 2 GB in size. The information in this file is of no direct use to us. Therefore, we will extract word candidates from the corpus file using the yeni_kelime_tara.py script. This script requires the zemberek-full.jar file.

### Downloading the Zemberek jar file
The Zemberek project is located at https://github.com/ahmetaa/zemberek-nlp. A Google Drive address is provided for the distribution files: https://drive.google.com/#folders/0B9TrB39LQKZWSjNKdVcwWUxxUm8. From the Drive homepage, navigate to the distributions folder and download version 0.17.1. The downloaded file should be named something like 0.17.1-20251119T073639Z-1-001.zip. Unzip this zip file. Go to the folder named 0.17.1 within the resulting folder. Copy the zemberek-full.jar file from there to your working folder.

### Collecting new words
```bash
python yeni_kelime_tara.py
```
You can add the words in the file yeni_kesin_turkce_adaylari.txt to your list. We will examine these words more thoroughly later.

Note: If you want to rebuild the trigram_model.txt file:

You can use the command:
```bash
python build_trigram_model.py
```

### Creating Database and the Tables (lexicon.db - sozluk, kelimeler)

   ```bash
   python db_setup.py
   ```

### Preparing the data to be loaded into the words table 

The words in the file yeni_turkce_adaylari.txt are copied to tr_lexicon.txt. 
If the number of words in the tr_lexicon.txt file is more than 300 thousand, 
It should be splitted into chunk files with splitter.py.

### Chunk the tr_lexicon.txt file 

```bash 
python splitter.py 
``` 

It splits the tr_lexicon.txt file into chunk_1.txt, chunk_2.txt, etc. 
The number of chunks is defined by NUM_CHUNKS. 
The number of words contained in each Chunk must be approximately 300 thousand words. 
Determine the NUM_CHUNKS value accordingly.


### Creation of analysis_results.tsv file from the chunk files 

```bash 
python data_loader.py 
``` 

Using chunk_*.txt (singular words) files, it creates the analysis_results.tsv() file. 
Uses jpype1 and zemberek-full.jar. 
The purpose of this script is to integrate file operations and database operations
to ease multiprocessing processes by separating them from each other.


### Uploading the analysis_results.tsv file to the database 

```bash 
python db_loader.py 
``` 

You can view previously generated data using the analysis_results.tsv file. 
transfers it to the words table.

### mini_loader.py for small word additions 

```bash 
python mini_loader.py 
``` 

Analyzing the words in the yeni_adaylar.txt file with Zemberek, 
saves the results in the kelşmeler (words) table. 
This script is a small sized version of the integrated data_loader.py and db_loader.py scripts. 
Useful when using small datasets.


## Cloning the AKTA Project

Clone the project at https://github.com/ahmetax/akta to your computer.

Update the INPUT_FOLDER variable in the akta_tara.py file to the project's location on your computer and run the akta_tara.py script. (This process will take hours.)
The output file will be saved as akta_kesin_turkce_adaylari.txt.
You can add the contents of this file to your master list (tr_lexicon.txt) to be imported into the database.

   ```bash
   git clone https://github.com/ahmetax/akta.git

   python akta_tara.py
   ```

## Adding Geographic Location Names to the Dictionary

### geocoding_adres.py
We obtain location names from zemberek sources.
If you have a more comprehensive list, you can use that as well.
Input: sozlukler/zemberek_tr/locations-tr.dict
Output: cografi_adres_sozluk.json

```bash
python geocoding_adres.py
```

### geo_bulk_aktarim.py
Information scanned through the Geocoding API and saved in the cografi_adres.json file is transferred to the database in bulk using this script.
Input: cografi_adres_sozluk.json

```bash
python geo_bulk_aktarim.py
```


# DENETLENMİŞ TÜRKÇE SÖZCÜK DAĞARCIĞI

Bu projede, güncel Türkçede geçerli olan ve genellikle hala kullanılan sözcüklerin bir listesini oluşturuyoruz.
Elimdeki 2 milyonluk listeyi burada paylaşmayacağım. 
Github, dosya boyutu konusunda katı kısıtlamalara sahip.
Bunu aşmak da mümkün elbette, ama, pek kullanıcı dostu değil bana göre.
O yüzden size hazır bir liste sunmak yerine, sizinle, benim elimdeki gibi bir Türkçe Sözcük Dağarcığını elde etmenizi sağlayacak araçlar paylaşacağım. 

Başlangıç kodu olarak basit bir "kelime toplayıcı" hazırlamak iyi olacak.

Kod çalışmalarını hızlandırmak amacıyla Claude, Gemini ve Grok'u kodlama danışmanı olarak kullanıyorum.
Ana kodlama dilimiz Python olacak.
Veritabanı yöneticisi olarak SQLite kullanacağız.
Kelime analizlerimizin çekirdeğinde Zemberek kütüphanesinin son sürümü (zemberek-full-0.17.1.jar) bulunacak.

## YAPILACAKLAR LİSTESİ

1. Kelime Toplayıcı (Tamamlandı)
2. Wikipedia'dan kelime toplayıcı (Tamamlandı)
3. Veritabanı ve tabloları oluşturma (Tamamlandı)
4. Güncel zemberek-full.jar dosyasının indirilmesi (Tamamlandı)
5. tr_corpus_wiki.txt dosyasından yeni_kesin_turkce_adaylari.txt dosyasının elde edilmesi (Tamamlandı)
6. tr_lexicon.db veritabanının oluşturulması (Tamamlandı)
7. Toplanan kelimelerin veritabanına aktarılmak üzere hazırlanması (Tamamlandı)
8. AKTA Projesinin klonlanması ve Türkçe belgelerin taranması (Tamamlandı)
9. lexicon.db veritabanına sozluk tablosunun eklenmesi (Tamamlandı)
10. kelimeler tablosundaki kelime köklerinin sozluk tablosuna eklenmei (Tamamlandı)
11. Coğrafik yer adlarının sozluk tablosuna eklenmesi (Tamamlandı)
12. TDK ve Wiktionary kaynaklarını kullanarak anlam, koken ve kaynak kolonlarının doldurulması
13. TDK, Wiktionary ve Nisanyan kaynaklarını kullanarak anlam, koken ve kaynak kolonlarının doldurulması


## Kelime Toplayıcı Kullanımı

1. Bu repoyu klonla:
   ```bash
   git clone https://github.com/ahmetax/derlemtr.git
   cd derlemtr
   ```
   Sanal ortam kullanmanızı öneririm: (Aşağıdaki kodlar Ubuntu 24.04 içindir. Kendi sisteminize göre uyarlayın.)
   ```bash
   python3.12 -m venv e312
   source e312/bin/activate
   ```
2. Gerekli kütüphaneleri kurun:
   ```bash
   pip install python-docx ebooklib beautifulsoup4 PyPDF2 tqdm
   ```
   veya
   ```bash
   pip install -r requirements.txt
   ``` 
3. Kaynak metinleri içine koyacağınız bir klasör açın:
   ```bash
   mkdir kaynak_metnler
   ```
4. kaynak_metnler klasörünün içine istediğiniz Türkçe metin dosyalarını kopyalayın.

5. Kelime toplayıcıyı çalıştırın:
   ```bash
   python kelime_toplayici.py
   ```
   Her çalıştırmada yeni bulunan kelimeler alfabetik olarak kelimeler.txt dosyasına eklenir.
   

## Wikipedia'dan veri aktarımı ve ayrık ve denetlenmiş kelimelere dönüştürme

https://dumps.wikimedia.org/trwiki/latest/trwiki-latest-pages-articles.xml.bz2
dosyasını indirin. (Yaklaşık 1 GB)

Bu dosyayı çalışma klasörünüze kopyalayın veya wiki_xml2txt.py dosyasında tam adresini verin.

wiki_xml2txt.py betiğini çalıştırın. (Bu işlem biraz uzun sürebilir. Yaklaşık 1,580,000 makale işlenecek.)

   ```bash
   python wiki_xml2txt.py
   ```
Şimdi elinizde tr_corpus_wiki.txt isimli bir dosya olmalı. Boyutu 2GB civarındadır. 
Bu dosyanın içindeki bilgiler doğrudan işimize yaramaz. 
O yüzden yeni_kelime_tara.py betiği aracılığıyla corpus dosyasından kelime adaylarını çıkaracağız.
Bu betik, zemberek-full.jar dosyasına ihtiyaç duyar.

### Zemberek jar dosyasının indirilmesi

Zemberek projesi  https://github.com/ahmetaa/zemberek-nlp adresinde bulunur.
Dağıtım dosyaları içinse bir Google-drive adresi verilmiştir:
https://drive.google.com/#folders/0B9TrB39LQKZWSjNKdVcwWUxxUm8
Bağlandığınız drive ana sayfasından distributions klasörüne geçin ve 0.17.1 sürümünü indirin.
İnecek dosyanın adı 0.17.1-20251119T073639Z-1-001.zip benzeri olmalıdır.
Bu zip dosyasını açın. 
Elde edeceğiniz klasörün altındaki 0.17.1 isimli klasöre girin.
Buradaki zemberek-full.jar dosyasını çalışma klasörünüze kopyalayın.

### Yeni kelimelerin çıkarılması

   ```bash
   python yeni_kelime_tara.py
   ```
yeni_kesin_turkce_adaylari.txt dosyasındaki kelimeleri listenize ekleyebilirsiniz.
Bu kelimeleri daha sonra daha ayrıntılı bir denetimden geçireceğiz.

Not: trigram_model.txt dosyasını yeniden oluşturmak isterseniz:

   ```bash
   python build_trigram_model.py
   ```
betiğini kullanabilirsiniz.

### Veritabanı ve tabloların oluşturulması (lexicon.db - sozluk, kelimeler)

   ```bash
   python db_setup.py
   ```

### Verilerin kelimeler tablosuna yüklenmek üzere hazırlanması

   yeni_turkce_adaylari.txt dosyasındaki kelimeler tr_lexicon.txt isimli 
   dosyaya kaydedilir.
   tr_lexicon.txt dosyasındaki kelime sayısı 300 binden fazlaysa, 
   splitter.py ile chunk dosyalarına bölünmelidir.

### tr_lexicon.txt dosyasının parçalara (chunk) ayrılması

   ```bash
   python splitter.py
   ```
   tr_lexicon.txt dosyasını chunk_1.txt, chunk_2.txt, vb parçalara ayırır.
   Chunk (parça) sayısı NUM_CHUNKS ile tanımlanır.
   Her bir Chunk'ın içerdiği kelime sayısı yaklaşık 300 bin kelime
   civarında olmalıdır. NUM_CHUNKS değerini ona göre belirleyin.	


### Chunk dosyalarından analysis_results.tsv dosyasının oluşturulması

   ```bash
   python data_loader.py
   ```

   chunk_*.txt (tekil kelimeler)  dosyalarını kullanarak 
   analysis_results.tsv () dosyasını oluşturur.
   jpype1 ve zemberek-full.jar kullanır.
   Bu betiğin amacı, zemberek işlemleri ile veritabanı işlemlerini
   birbirinden ayırarak multiprocessing süreçlerini rahatlatmaktır.


### analysis_results.tsv dosyasının veritabanına yüklenmesi

   ```bash
   python db_loader.py
   ```

   analysis_results.tsv dosyasını kullanarak önceden üretilmiş verileri
   kelimeler tablosuna aktarır.

### Küçük çaplı kelime eklemeleri için mini_loader.py

   ```bash
   python mini_loader.py
   ```

   yeni_adaylar.txt dosyasında yer alan kelimeleri Zemberek ile analiz edip,
   sonuçları kelimeler tablosuna kaydeder.
   Bu betik, data_loader.py ve db_loader.py betiklerinin küçük boyutlu ve
   entegre edilmiş halidir. Küçük verisetleri kullanırken işe yarar.

   
## AKTA Projesinin klonlanması   

https://github.com/ahmetax/akta adresindeki projeyi bilgisayarınıza klonlayın.
akta_tara.py dosyasındaki INPUT_FOLDER değişkenini, projenin bilgisayarınızdaki konumuna 
uygun olarak güncelleyin ve akta_tara.py betiğini çalıştırın. (İşlemler, saatler boyu sürecektir.)
Çıktı dosyası, akta_kesin_turkce_adaylari.txt olarak kaydedilir.
Bu dosyanın içeriğini veritabanına aktarılmak üzere ana listenize (tr_lexicon.txt) ekleyebilirsiniz.

   ```bash
   git clone https://github.com/ahmetax/akta.git
   
   python akta_tara.py
   ```
   
## sozluk Tablosuna Kelimelerin Eklenmesi

lexicon.db veritabanında bulunan kelimeler tablosunu kullanarak 
kökleri gruplar ve sozluk tablosuna aktarır.
Temiz bir başlangıç yapmak için eski sozluk tablosunu siler (DROP), 
yeniden oluşturur ve kelimeler tablosundaki kökleri, tip ve detay bilgisini 
analiz alanından doğru şekilde aktarır.
DİKKATLİ BİR ŞEKİLDE KULLANILMASI GEREKİR! 
BAZI ÖNEMLİ BİLGİLERİ KAYBEDEBİLİRSİNİZ!

   ```bash
   python sozluk_initializer.py
   ```

## Coğrafik Yer Adlarının Sözlüğe Eklenmesi

### geocoding_adres.py
Yer adlarını zemberek kaynaklarından elde ediyoruz.
Elinizde daha zengin bir liste varsa, onu da kullanabilirsiniz.
	Girdi: sozlukler/zemberek_tr/locations-tr.dict
	Çıktı: cografi_adres_sozluk.json
	
   ```bash
   python geocoding_adres.py
   ```	

### geo_bulk_aktarim.py
Geocoding API'si üzerinden taranan ve cografi_adres.json
dosyasına kaydedilen bilgiler, toplu işlemlerle veritabanına
bu betik sayesinde aktarılmaktadır.
    Girdi: cografi_adres_sozluk.json
	
   ```bash
   python geo_bulk_aktarim.py
   ```	



