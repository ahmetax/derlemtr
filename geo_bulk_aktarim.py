import sqlite3
import json
from typing import List, Dict, Any

# ⚠️ Değişkenleri Kendi Dosya Yollarınızla Ayarlayın
SQLITE_DB_YOLU = "lexicon.db"  # Veritabanı dosyanızın yolu
JSON_DOSYA_YOLU = "cografi_adres_sozluk.json" # Oluşturulan JSON dosyanızın yolu

def turkce_kucult(metin: str) -> str:
    """Türkçe karakterleri koruyarak metni küçük harfe çevirir."""
    # Türkçe harf dönüşümleri (Önce büyük harf/noktasız harfleri dönüştür)
    metin = metin.replace("İ", "i")
    metin = metin.replace("I", "ı")

    # Geri kalan Türkçe karakterleri küçük harfe çevirme
    metin = metin.replace("Ç", "ç")
    metin = metin.replace("Ö", "ö")
    metin = metin.replace("Ş", "ş")
    metin = metin.replace("Ü", "ü")
    metin = metin.replace("Ğ", "ğ")

    # Son olarak, standart küçük harf çevrimini yap
    metin = metin.lower()

    return metin

def json_verilerini_islem_ve_aktar_bulk():
    """JSON dosyasını okur, veritabanını kontrol eder, verileri bellekte toplar ve toplu (BULK) aktarım yapar."""
    
    # 1. Veriyi Oku ve Yükle
    try:
        with open(JSON_DOSYA_YOLU, 'r', encoding='utf-8') as f:
            cografi_sozluk = json.load(f)
    except Exception as e:
        print(f"❌ Hata: JSON dosyası okunamadı veya formatı bozuk: {e}")
        return

    print(f"✅ JSON'dan {len(cografi_sozluk)} kayıt yüklendi.")
    
    conn = None
    try:
        # 2. Veritabanı Bağlantısı ve WAL Modu
        conn = sqlite3.connect(SQLITE_DB_YOLU)
        cursor = conn.cursor()
        
        # WAL modu, okuma/yazma çakışmalarını azaltarak performansı artırır.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous = OFF") 
        print("✅ SQLite bağlantısı WAL modunda yapılandırıldı.")

        # 3. Mevcut Veritabanı Durumunu Belleğe Çekme (Hızlı Kontrol İçin)
        cursor.execute("SELECT detay, anlam FROM sozluk")
        db_kayitlari = {row[0]: row[1] for row in cursor.fetchall()}

        # 4. Bellekte Toplu İşlem Listelerini Hazırlama
        insert_list = []  # Yeni eklenecek kayıtlar için
        update_list = []  # Güncellenecek kayıtlar için (anlamı boş olanlar)
        
        yeni_eklenen_sayisi = 0
        guncellenecek_sayisi = 0
        atlanan_sayisi = 0

        print(f"🔄 {len(cografi_sozluk)} kayıt işleniyor...")

        for lokasyon_adi, veri in cografi_sozluk.items():
            
            # 4.1. Hata Kontrolü
            anlam_degeri = veri.get("ilce_il_ulke")
            if veri.get("hata") == "Konum bulunamadı" or not anlam_degeri:
                atlanan_sayisi += 1
                continue
            
            # 4.2. Durum Kontrolü ve Listeye Ekleme
            if lokasyon_adi in db_kayitlari:
                
                # Kayıt var, anlam kolonu dolu mu?
                if db_kayitlari[lokasyon_adi] and db_kayitlari[lokasyon_adi].strip():
                    # Anlam dolu, atla (Zaten işlenmiş)
                    atlanan_sayisi += 1
                else:
                    # Kayıt var ama anlam boş (GÜNCELLEME listesine ekle)
                    # Parametre sırası: (anlam, kaynak, detay)
                    update_list.append((anlam_degeri, "Geocoding", lokasyon_adi))
                    guncellenecek_sayisi += 1
            else:
                # Kayıt yok (YENİ EKLEME listesine ekle)
                kok_degeri = turkce_kucult(lokasyon_adi)
                # Parametre sırası: (kok, detay, tip, kaynak, anlam, attempted)
                insert_list.append((kok_degeri, lokasyon_adi, "Noun,Prop", "Geocoding", anlam_degeri, 1))
                yeni_eklenen_sayisi += 1

        print(f"✅ Bellekte toplandı: {yeni_eklenen_sayisi} ekleme, {guncellenecek_sayisi} güncelleme.")

        # 5. Toplu (BULK) Veritabanı İşlemleri
        
        # 5.1. Toplu Ekleme (INSERT)
        if insert_list:
            print("⏳ Toplu Ekleme yapılıyor...")
            cursor.executemany("""
                INSERT INTO sozluk (kok, detay, tip, kaynak, anlam, attempted)
                VALUES (?, ?, ?, ?, ?, ?)
            """, insert_list)

        # 5.2. Toplu Güncelleme (UPDATE)
        if update_list:
            print("⏳ Toplu Güncelleme yapılıyor...")
            cursor.executemany("""
                UPDATE sozluk SET anlam = ?, kaynak = ?, attempted = 1
                WHERE detay = ?
            """, update_list)

        # 6. Tek Bir Kez Kaydetme (COMMIT)
        conn.commit()
        
        print("\n--- İŞLEM ÖZETİ ---")
        print(f"⭐ Yeni Eklenen Kayıt Sayısı: {yeni_eklenen_sayisi}")
        print(f"⭐ Güncellenen Kayıt Sayısı: {guncellenecek_sayisi}")
        print(f"✖️ Atlanan Kayıt Sayısı: {atlanan_sayisi}")
        print(f"🎉 Tüm veri {SQLITE_DB_YOLU} veritabanına tek bir işlemle aktarıldı!")

    except sqlite3.Error as e:
        print(f"❌ KRİTİK VERİTABANI HATASI: Toplu işlem başarısız oldu: {e}")
        if conn:
            conn.rollback() # Hata durumunda hiçbir değişiklik yapılmaz
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    json_verilerini_islem_ve_aktar_bulk()