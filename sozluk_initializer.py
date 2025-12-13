import sqlite3
import pandas as pd
import sys
import os

# --- KONFİGÜRASYON ---
DATABASE_NAME = 'lexicon.db' 

# --- YARDIMCI FONKSİYONLAR ---

def ensure_sozluk_table_exists_and_is_up_to_date(cursor):
    """
    'sozluk' tablosunu yoksa oluşturur ve eksik olan yeni kolonları (detay, attempted, failed, onay) ekler.
    Mevcut veriyi korur.
    """
    print("-> 'sozluk' tablosunun varlığı kontrol ediliyor ve güncelleniyor...")
    
    # 1. Sözlük Tablosunu Oluşturma (Yoksa)
    # UNIQUE(kok, tip) kısıtlaması, aynı kökün aynı tipte (örneğin iki kez fiil) eklenmesini engeller.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sozluk (
            id INTEGER PRIMARY KEY,
            kok TEXT NOT NULL,
            detay TEXT, -- Yeni/Doğru alan: Orijinal (Şapkalı) kök bilgisi
            tip TEXT,   -- isim, fiil, Adj, Noun, vb.
            koken TEXT, 
            kaynak TEXT, 
            kullanim TEXT, 
            anlam TEXT,
            aciklama TEXT,
            attempted INTEGER DEFAULT 0, 
            failed INTEGER DEFAULT 0,
            onay INTEGER DEFAULT 0,
            UNIQUE(kok, tip) 
        );
    ''')
    
    # 2. Mevcut Tablolara Eksik Kolonları Ekleme (ALTER TABLE)
    new_columns = [
        ('detay', 'TEXT'),
        ('attempted', 'INTEGER DEFAULT 0'),
        ('failed', 'INTEGER DEFAULT 0'),
        ('onay', 'INTEGER DEFAULT 0'),
        # Tip alanları güncel olduğu için tekrar eklemeye gerek yok
    ]

    # Yeni kolonları eklemek için kontrol ve ALTER TABLE komutları
    for col_name, col_type in new_columns:
        try:
            # Kolonun varlığını kontrol etme
            cursor.execute(f"SELECT {col_name} FROM sozluk LIMIT 1")
        except sqlite3.OperationalError:
            # Kolon yoksa ekle
            cursor.execute(f"ALTER TABLE sozluk ADD COLUMN {col_name} {col_type}")
            print(f"-> 'sozluk' tablosuna '{col_name}' kolonu eklendi.")

    print("-> 'sozluk' tablosu hazırdır.")


def insert_missing_roots_with_analysis():
    """
    'kelimeler' tablosundaki Zemberek analizini ayrıştırarak 
    'sozluk' tablosuna yeni, benzersiz kök/tip kayıtlarını güvenli bir şekilde ekler.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Tablonun varlığını ve güncelliğini sağla
    ensure_sozluk_table_exists_and_is_up_to_date(cursor)
    
    print("-> 'kelimeler' tablosundaki Zemberek analizleri ayrıştırılıyor ve yeni kökler ekleniyor...")
    
    sql_query = """
    INSERT OR IGNORE INTO sozluk (kok, detay, tip, kaynak)
    SELECT 
        -- 'kok' alanı (Normalized Root): Aksanları kaldırılmış, küçük harfli ve yalın hali.
        REPLACE(REPLACE(REPLACE(
            LOWER(
                SUBSTR(T1.analiz, 2, INSTR(T1.analiz, ':') - 2)
            ),
            'â', 'a'
        ), 'î', 'i'), 'û', 'u') AS yalin_kok,
        
        -- 'detay' alanı (Original Root): Orijinal kök bilgisi (büyük/küçük harf duyarlı, şapkalı)
        SUBSTR(
            T1.analiz, 
            2,
            INSTR(T1.analiz, ':') - 2 
        ) AS detay,
        
        -- Kök Tipini Belirleme: '[kok:tip]' kısmından 'tip' değerini çıkarır.
        SUBSTR(
            T1.analiz, 
            INSTR(T1.analiz, ':') + 1, 
            INSTR(T1.analiz, ']') - (INSTR(T1.analiz, ':') + 1)
        ) AS tip,
        
        yontem AS kaynak
    FROM kelimeler T1
    WHERE T1.analiz IS NOT NULL AND T1.analiz LIKE '[%:%]%'
    GROUP BY 
        yalin_kok, 
        tip;
    """

    try:
        cursor.execute(sql_query)
        rows_affected = cursor.rowcount
        conn.commit()
        
        print(f"✅ Başarıyla eklenen yeni kök/tip kaydı sayısı: {rows_affected}")
        
    except sqlite3.Error as e:
        print(f"Hata: Yeni kökler eklenirken sorun oluştu: {e}", file=sys.stderr)
        
    finally:
        conn.close()


def main():
    print("--- Sözlük Tablosu Güvenli Başlatma/Güncelleme ---")
    
    insert_missing_roots_with_analysis()
    
    print("--- İşlem Tamamlandı. ---")


if __name__ == '__main__':
    main()
