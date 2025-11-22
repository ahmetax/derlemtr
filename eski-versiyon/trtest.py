# -*- coding: utf-8 -*-
#trtest.py
#2016-10-18
#author = Ahmet Aksoy
#Son güncelleme = 2016-10-18
#Python 3.5.2 ile test edildi
"""
Türkçe karakterlerle ilgili görsel sorun yaratan bazı karakterler
düzeltilecek
"""

BHARFX = "Iİ"
KHARFX = "ıi"

AYRACLAR = ",\.;«»!?-:/\*+_=\"<>()'[]|º#&%“’”‘…–´—•`˜·"

xharfler= {'ÅŸ':'ş','ÄŸ':'ğ','â€™':"'",'Ä±':'ı','Ã¶':'ö','Ã¼':'ü','Ã§':'ç','Â':' ',
           'Ä°':'İ','Ã‡':'Ç','Ã–':'Ö','Åž':'Ş','Äž':'Ğ','Ãœ':'Ü','â€¦':'...',
           'â€œ':'“','â€':'”','Ã¢':'â','â€':'‘','':'â','$':'',
           'ă':'ç','a':'\'','‘':'\'','’':'\'','”':'"','“':'"',
           'Äą':'ı','Ĺ':'ş','Ăś':'ö','Ăź':'ü','Ă§':'ç','Ä':'ğ','ă':'ö','Ă':'Ü','Ĺ':'Ş','Ă':'Ö',
           'ð':'ğ','ý':'ı','þ':'ş','Ý':'İ','Þ':'Ş','Ð':'Ğ',"‘™":"'","‘¦":"...","�":""}


def karakter_duzelt(s):
    s = bytes_duzelt(s)
    for i in xharfler.keys():
        x = xharfler[i]
        #s=re.sub(i,x,s)
        s = s.replace(i,x)
    return s

bss= {b"\x61\xc2\x80\xc2\x9c":'\"',
           b"\xc4\x83\xc2\x87":'ç',
           b"\xc3\xa4\xc2\x9e":'ğ',
           b"\x61\xc2\x80\xc2\x98":'\'',
           b"\x61\xc2\x80\xc2\x99":'\'',
           b"\x61\xc2\x80\xc2\x9D":'\"',
      b"\xc2\x96":'û'
      }

# bytes_duzelt() fonksiyonu beklediğim değişikliği yapamıyor.
# i.decode() metodu bytes'ı doğru şekilde decode edemiyor.
# Farklı bir yöntem bulmak gerekiyor.
def bytes_duzelt(s):
    s0=s
    for i in bss.keys():
        x = bss[i]
        y = i.decode()
        s = s.replace(y,x)
    if s!= s0:
        print("{} -> {}".format(s0,s))
    return s

def kucukHarfYap(sozcuk):
    ss = ''
    for i in range(len(sozcuk)):
        ok = False
        for j in range(len(BHARFX)):
            if sozcuk[i]== BHARFX[j]:
                ss += KHARFX[j]
                ok = True
                break
        if ok == False:
            ss += sozcuk[i]
    ss = ss.lower()
    return ss

def inceltme_yok(sozcuk):
    s=""
    for harf in sozcuk:
        if harf=='â' or harf=='Â':
            s += 'a'
        elif harf == 'ê' or harf=='Ê':
            s += 'e'
        elif harf == 'û' or harf=='Û':
            s += 'u'
        elif harf == 'î' or harf=='Î':
            s += 'i'
        else:
            s+=harf
    return s

def escape_tire(s):
    tireler={" 'da ":"\'da "," 'de ":"\'de "," 'ın ":"\'ın "," 'in ":"\'in "," 'un ":"\'un "," 'ün ":"\'ün "}
    for tire in tireler.keys():
        s = s.replace(tire,tireler[tire])

    return s

def kelimelere_ayir(haber):
    # karakterleri düzelt
    haber = karakter_duzelt(haber)
    sozcukler = []
    # Noktalamalar
    for ayrac in AYRACLAR:
        haber = haber.replace(ayrac, " ")
    for kelime in haber.split():
        if kelime.isalpha():
            sozcukler.append(kelime)
        elif kelime.isalnum() or kelime.isdigit():
            pass
        else:
            k = kelime.strip(AYRACLAR)
            sozcukler.append(k)
    # Dikkat' Gerekirse burada tek tırnak ile bölünen Özel_isim'ek tek bir sözcük haline dönüştürülebilir.
    # Sözcükleri bir dict içinde topla
    sozluk={}
    for sozcuk in sozcukler:
        sozcuk = inceltme_yok(kucukHarfYap(sozcuk))
        if sozcuk in sozluk.keys():
            sozluk[sozcuk] +=1
        else:
            sozluk[sozcuk] =1
    return(sozluk)


def metin_cozumle(haber):
    sozluk = kelimelere_ayir(haber)
    for s in sozluk.keys():
        print(s)

if __name__ == "__main__":
    f = open("test.txt","r",encoding="utf-8")
    haber = f.read()
    f.close()
    metin_cozumle(haber)
