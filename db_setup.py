import sqlite3

DATABASE_NAME = 'lexicon.db'

def create_tables():
    """SQLite veritabanı tablolarını oluşturur."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # 1. Sözlük Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sozluk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kok TEXT NOT NULL,
            detay TEXT, -- büyük-küçük harf duyarlı
            tip TEXT, -- isim, fiil, ozel_isim, terim, vb.
            koken TEXT, -- Turkce, Arapca, Farsca, Ingilizce, vb.
            kaynak TEXT, -- TDK, Wiktionary, Manuel, vb.
            kullanim TEXT, -- güncel, eskimiş, ağız, argo, vb
            anlam TEXT,
            aciklama TEXT,
            attempted INTEGER DEFAULT 0, 
            failed INTEGER DEFAULT 0,
            onay INTEGER DEFAULT 0,
            dil TEXT,
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
            onay INTEGER DEFAULT 0,
            hata INTEGER DEFAULT 0,
            tip TEXT,	-- from analiz
            detay TEXT,	-- from analiz
            skor INTEGER DEFAULT 0,	-- frequency from related docs
            dil TEXT,
            CHECK (LENGTH(kelime) > 0)
        );
    ''')
    
# 3. Kaynaklar Tablosu (Eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kaynaklar (
            id INTEGER PRIMARY KEY,
            adres TEXT NOT NULL UNIQUE, -- URL veya Dosya Yolu
            ad TEXT,
            checksum TEXT, 
            kayit_tarihi DATETIME
        );
    ''')

    # 4. Kelime-Kaynak İlişki Tablosu (Eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kelime_kaynak (
            kelime_id INTEGER,
            kaynak_id INTEGER,
            FOREIGN KEY (kelime_id) REFERENCES kelimeler(id),
            FOREIGN KEY (kaynak_id) REFERENCES kaynaklar(id),
            UNIQUE (kelime_id, kaynak_id)
        );
    ''')

    # 5. Endeksler (executescript ile toplu ve güvenli oluşturma)
    cursor.executescript('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_kaynaklar_adres ON kaynaklar (adres);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_detay ON kelimeler (detay);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_hata ON kelimeler (hata);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_kelime ON kelimeler(kelime);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_kok ON kelimeler (kok);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_lemma ON kelimeler (lemma);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_onay ON kelimeler (onay);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_skor ON kelimeler (skor);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_tip ON kelimeler (tip);
        CREATE INDEX IF NOT EXISTS idx_kelimeler_dil ON kelimeler (dil);
        CREATE INDEX IF NOT EXISTS idx_kk_kaynak_id ON kelime_kaynak (kaynak_id);
        CREATE INDEX IF NOT EXISTS idx_kk_kelime_id ON kelime_kaynak (kelime_id);
        CREATE INDEX IF NOT EXISTS idx_sozluk_kok ON sozluk(kok);
        CREATE INDEX IF NOT EXISTS idx_sozluk_detay ON sozluk(detay);
        CREATE INDEX IF NOT EXISTS idx_sozluk_tip ON sozluk(tip);
        CREATE INDEX IF NOT EXISTS idx_sozluk_dil ON sozluk(dil);
        CREATE INDEX IF NOT EXISTS idx_sozluk_onay ON sozluk(onay);
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"'{DATABASE_NAME}' veritabanı, tablolar ve endeksler başarıyla hazırlandı.")

if __name__ == '__main__':
    create_tables()
