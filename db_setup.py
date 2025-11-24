import sqlite3

DATABASE_NAME = 'lexicon.db'

def create_tables():
    """SQLite veritabanı tablolarını oluşturur."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # 1. Sözlük Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sozluk (
            id INTEGER PRIMARY KEY,
            kok TEXT NOT NULL,
            detay TEXT, -- büyük-küçük harf duyarlı
            tip TEXT, -- isim, fiil, ozel_isim, terim, vb.
            koken TEXT, -- Turkce, Arapca, Farsca, Ingilizce, vb.
            kaynak TEXT, -- TDK, Wiktionary, Manuel, vb.
            anlam TEXT,
            aciklama TEXT,
            attempted INTEGER DEFAULT 0, 
            failed INTEGER DEFAULT 0,
            onay INTEGER DEFAULT 0,
            UNIQUE(kok, tip, koken) -- Tekrarlayan kök girişlerini engellemek için (tamamen aynı ise)
        );
    ''')

    # 2. Kelimeler Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kelimeler (
            id INTEGER PRIMARY KEY,
            kelime TEXT NOT NULL UNIQUE,
            lemma TEXT,
            kok TEXT,
            ekler TEXT,
            analiz TEXT,
            yontem TEXT, -- zemberek, manuel, baska_arac, vb.
            aciklama TEXT,
            onay INTEGER DEFAULT 0
        );
    ''')
    
    conn.commit()
    conn.close()
    print(f"'{DATABASE_NAME}' veritabanı ve tablolar başarıyla oluşturuldu/güncellendi.")

if __name__ == '__main__':
    create_tables()
