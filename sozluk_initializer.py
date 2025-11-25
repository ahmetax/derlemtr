# sozluk_initializer.py - Sıfırdan Temizleme ve Detay Çekme Düzeltmesi

import sqlite3
import sys

DATABASE_NAME = 'lexicon.db'

def initialize_sozluk_table_from_scratch():
    """
    sozluk tablosunu siler (DROP), yeniden oluşturur ve kelimeler tablosundaki 
    kökleri, tip ve detay bilgisini analiz alanından doğru şekilde aktarır.
    """
    
    print(f"-> '{DATABASE_NAME}' veritabanı kullanılıyor...")
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # 1. Sözlük Tablosunu SİLME (Sıfırdan Başlangıç)
        print("-> 'sozluk' tablosu siliniyor (Temiz başlangıç)...")
        cursor.execute("DROP TABLE IF EXISTS sozluk;")
        
        # 2. Yeni Sözlük Tablosunu Oluşturma (Detay kolonu dahil)
        print("-> Yeni ve doğru şemayla 'sozluk' tablosu oluşturuluyor...")
        cursor.execute('''
            CREATE TABLE sozluk (
                id INTEGER PRIMARY KEY,
                kok TEXT NOT NULL,
                detay TEXT, -- Yeni/Doğru alan: Büyüklük/Küçüklük, İnceltme işaretleri vb. içerir
                tip TEXT, -- isim, fiil, Adj, Noun, vb.
                koken TEXT, 
                kaynak TEXT, 
                kullanim TEXT, 
                anlam TEXT,
                aciklama TEXT,
                attempted INTEGER DEFAULT 0, 
                failed INTEGER DEFAULT 0,
                onay INTEGER DEFAULT 0,
                UNIQUE(kok, tip, koken) -- Tekrarlayan kök girişlerini engeller
            );
        ''')
        
        # 3. kelimeler tablosundaki Kökleri sozluk tablosuna aktarma
        print("-> 'kelimeler' tablosundaki benzersiz kökler 'sozluk' tablosuna aktarılıyor (Aksansız ve Yalın Kök Formu)...")

        # Yeni ve düzeltilmiş SQL Sorgusu: detay alanını T1.analiz'den çekiyor ve kok'u normalleştiriyor.
        sql_query = """
        INSERT OR IGNORE INTO sozluk (kok, detay, tip, kaynak)
        SELECT 
            -- 'kok' alanı: LOWER() ve ardışık REPLACE'ler ile aksanları kaldırılmış, küçük harfli ve yalın hali.
            REPLACE(REPLACE(REPLACE(
                LOWER(
                    -- Analiz alanından orijinal kökü çıkar
                    SUBSTR(T1.analiz, 2, INSTR(T1.analiz, ':') - 2)
                ),
                'â', 'a'
            ), 'î', 'i'), 'û', 'u') AS yalın_kok,
            
            -- 'detay' alanı: Orijinal (büyük/küçük harf duyarlı, şapkalı) kök bilgisi, analiz alanından çekildi
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
            
            'Zemberek' AS kaynak
        FROM kelimeler T1
        GROUP BY 
            SUBSTR(T1.analiz, 2, INSTR(T1.analiz, ':') - 2), -- Detay köke göre gruplandı
            tip; 
        """

        cursor.execute(sql_query)
        imported_count = conn.total_changes
        conn.commit()
        
        print(f"-> 'sozluk' tablosuna {imported_count} adet benzersiz kök başarıyla aktarıldı (Detay analizin içinden çekildi).")

    except sqlite3.Error as e:
        print(f"KRİTİK HATA: Veritabanı işlemi sırasında bir hata oluştu: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    initialize_sozluk_table_from_scratch()
