from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import json
from typing import List, Dict, Any

# Geocoding servisini başlat
geolocator = Nominatim(user_agent="yeradi_adres_sorgulama_v2")

def dosyadan_yer_adlarini_oku(dosya_yolu: str) -> List[str]:
    """Dosyadan yer adlarını (her satırda bir ad) okur ve temizler."""
    yer_adlari = []
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            for line in f:
                temiz_ad = line.strip()
                if temiz_ad:
                    yer_adlari.append(temiz_ad)
    except FileNotFoundError:
        print(f"❌ Hata: '{dosya_yolu}' dosyası bulunamadı.")
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        
    return list(set(yer_adlari)) # Tekrarlayanları baştan temizle

def onbellek_yukle_ve_kaydet(cikti_dosyasi: str) -> Dict[str, Any]:
    """Çıktı dosyasını okur, önbelleğe yükler ve güncelleyen bir fonksiyon döndürür."""
    try:
        with open(cikti_dosyasi, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"✅ Önbellek yüklendi: '{cikti_dosyasi}' dosyasında {len(cache)} kayıt bulundu.")
    except FileNotFoundError:
        cache = {}
        print(f"✅ Yeni çıktı dosyası oluşturuluyor: '{cikti_dosyasi}'")
    except json.JSONDecodeError:
        print("⚠️ Hata: Çıktı dosyası bozuk. Yeniden başlatılıyor (Mevcut dosyanın yedeğini alın).")
        cache = {}
    
    def onbellege_yaz(yeni_veri: Dict[str, Any]):
        """Bellekteki tüm veriyi dosyaya atomik olarak yazar."""
        cache.update(yeni_veri)
        
        # Geçici dosyaya yazma ve yeniden adlandırma (veri kaybını önler)
        temp_file = cikti_dosyasi + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=4, ensure_ascii=False)
            import os
            os.replace(temp_file, cikti_dosyasi)
        except Exception as e:
            print(f"❌ KAYDETME HATASI: {e}")

    return cache, onbellege_yaz

def coğrafi_kodlama_islemi(yer_adlari: List[str], cache: Dict[str, Any], kaydet_fonksiyonu):
    """Sadece önbellekte olmayan yer adları için sorgulama yapar."""
    
    sorgulanacaklar = [ad for ad in yer_adlari if ad not in cache]
    toplam_sorgu = len(sorgulanacaklar)
    
    print(f"\n✅ Toplam {len(yer_adlari)} benzersiz yer adı bulundu.")
    print(f"⭐ Önbellekte {len(cache)} kayıt var. {toplam_sorgu} yeni sorgu yapılacak.")
    
    sayac = 0

    for yer_adi in sorgulanacaklar:
        sayac += 1
        print(f"   ({sayac}/{toplam_sorgu}) Sorgulanıyor: {yer_adi}...", end=" ")
        
        konum_bilgisi = {
            "tam_adres_aciklamasi": None,
            "ilce_il_ulke": None,
            "hata": None
        }

        try:
            # Sorguyu Türkiye ile sınırlandırma ve detaylı adres isteme
            konum = geolocator.geocode(yer_adi, timeout=10, country_codes='tr')
            
            if konum:
                konum_bilgisi["tam_adres_aciklamasi"] = konum.address
                
                address_parts = konum.raw.get('address', {})
                
                # İdari hiyerarşi anahtarlarını kontrol etme
                ilce = address_parts.get('suburb') or address_parts.get('town') or address_parts.get('county')
                il = address_parts.get('city') or address_parts.get('state') or address_parts.get('province')
                ulke = address_parts.get('country')
                
                hata_kontrol = [p for p in [ilce, il, ulke] if p]
                
                if hata_kontrol:
                     konum_bilgisi["ilce_il_ulke"] = ", ".join(hata_kontrol)
                     print(f"✅ Bulundu ({konum_bilgisi['ilce_il_ulke']})")
                else:
                    # Ayrıştırma başarılı değilse, genel adresi kullan.
                    konum_bilgisi["ilce_il_ulke"] = konum.address
                    print(f"✅ Bulundu (Sadece tam adres mevcut): {konum_bilgisi['ilce_il_ulke']}")
                
                konum_bilgisi["hata"] = None # Başarılı sorguda hata yok

            else:
                konum_bilgisi["hata"] = "Konum bulunamadı"
                print("❌ Bulunamadı")

        except GeocoderTimedOut:
            konum_bilgisi["hata"] = "Sorgu zaman aşımına uğradı"
            print("❌ Zaman Aşımı")
        except GeocoderServiceError as e:
            konum_bilgisi["hata"] = f"Servis hatası: {e}"
            print("❌ Servis Hatası")
        except Exception as e:
            konum_bilgisi["hata"] = f"Beklenmedik hata: {e}"
            print("❌ Genel Hata")

        # Önbelleğe ekle ve hemen dosyaya kaydet
        kaydet_fonksiyonu({yer_adi: konum_bilgisi})
        
        # Nominatim kuralına uyum için 1 saniye bekleme
        time.sleep(1) 

    print("\n🎉 Tüm sorgulama ve kaydetme işlemleri tamamlandı.")


if __name__ == "__main__":
    girdi_dosyasi = "sozlukler/zemberek_tr/locations-tr.dict"
    cikti_dosyasi = "cografi_adres_sozluk.json"

    # 1. Yer adlarını dosyadan oku ve benzersizleştir
    yer_adlari_listesi = dosyadan_yer_adlarini_oku(girdi_dosyasi)
    
    if not yer_adlari_listesi:
        print("İşlem sonlandırıldı. Okunacak yer adı bulunamadı.")
    else:
        # 2. Önbelleği yükle ve kaydetme fonksiyonunu al
        coğrafi_sozluk, kaydet_func = onbellek_yukle_ve_kaydet(cikti_dosyasi)

        # 3. Coğrafi kodlama işlemini başlat
        coğrafi_kodlama_islemi(yer_adlari_listesi, coğrafi_sozluk, kaydet_func)