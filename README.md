# DerlemTr - Birim Test Paketi (Unit Test Suite)

[DerlemTr](https://github.com/ahmetax/derlemtr) projesinin veri ön işleme modülleri için özel olarak hazırlanmış, Türkçe sözlük oluşturma sürecinde güvenilirliği sağlayan otomatik bir test paketi.

## 📌 Genel Bakış

Bu fork, temel veri ön işleme betiklerini doğrulamak amacıyla `pytest` kullanan otomatik bir birim testi (unit test) mimarisi sunar. Dosya işlemlerini izole eder ve diske devasa dosyalar yazmadan işlevsel sınırları (boundary conditions) test eder.

Test paketi özellikle şunları hedefler:

* **`kelime_toplayici.py`:** Metin normalizasyonunu, Türkçe karakterlerin korunmasını ve boşluk/noktalama işaretleri filtrelemesini doğrular.
  * **Uygulanan Testler (TC-B06 - TC-B08):** Siyah kutu (Black-Box / EP) test teknikleri kullanılarak geçerli küçük harf girişleri, büyük/küçük harf ve tire karışımları (örn. "TüRkÇe-Dil" -> "türkçe-dil") ile geçersiz karakter/sayı barındıran karmaşık metinlerin (örn. " Selam123!@# ") doğru şekilde temizlendiği senaryoları kapsar.

* **`splitter.py`:** Dosya G/Ç (I/O) işlemlerini yakalamak için `unittest.mock` kullanarak veri seti bölme mantığını, parçalama (chunking) matematiğini ve kalan yakalama (remainder catch) mekaniklerini doğrular.
  * **Yapısal Testler (TC-W01 - TC-W02):** Beyaz kutu temel yol testi (White-Box Basis Path) ile standart eşit parçalama döngüsü ve matematiksel bölümden kalanın son dosyaya aktarıldığı (remainder catch) algoritmalar test edilir.
  * **İşlevsel Sınır Testleri (TC-B01 - TC-B05):** Sınır değer analizi (BVA) ve eşdeğerlik bölümleri (EP) kullanılarak; boş dosyalar, `ZeroDivisionError` (sıfıra bölme) fırlatma durumları, hedeflenen parça sayısından daha az satır içeren küçük dosyalar ve tek parça (min chunks) oluşturma gibi uç (edge) senaryolar doğrulanır.
## 🛠️ Ortam ve Bağımlılıklar

| Bileşen | Versiyon / Detay |
|---|---|
| **Dil** | Python 3.12+ |
| **Çerçeve (Framework)** | pytest 9.0.3 |
| **Gerekli Paketler** | `pytest`, `python-docx`, `ebooklib`, `beautifulsoup4`, `PyPDF2`, `tqdm` |

## 🚀 Kurulum Talimatları

**1. Depoyu klonlayın ve dizine gidin:**

```bash
git clone https://github.com/Aya-cyber6/derlemtr.git
cd derlemtr
```

**2. Sanal ortam oluşturun ve etkinleştirin:**

Windows (PowerShell):

```powershell
python -m venv venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

Mac/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

**3. Bağımlılıkları yükleyin:**

```bash
pip install pytest python-docx ebooklib beautifulsoup4 PyPDF2 tqdm
```

## 🧪 Testleri Çalıştırma

Sanal ortam aktif hale geldikten ve bağımlılıklar yüklendikten sonra, tüm test paketini ana dizinden (root directory) çalıştırabilirsiniz:

```bash
pytest -v
```

Bu komut, her iki modüldeki toplam **10 yapısal ve işlevsel test senaryosunu** yürütecek ve başarılı olan testlerin detaylı (verbose) bir çıktısını terminalde gösterecektir.
