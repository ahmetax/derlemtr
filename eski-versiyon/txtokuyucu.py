# -*- coding: utf-8 -*-
#txtokuyucu.py
#2016-02-06
#author = Ahmet Aksoy
#Son güncelleme = 2016-02-07
#Python 3.5.1 ile test edildi
import os
import time
from operator import itemgetter
from collections import OrderedDict

DATA_KLASOR = "D:/aaa-kaynaklar"
BHARF = "ÇĞİIÖŞÜ"
KHARF = "çğiıöşü"
#Sadece I ve İ harfleri küçük harfe dönüşürken sorun yaratıyor.
#Bu yüzden sadec I ve İ harflerini kontrol etmek yeterli olacak
BHARFX = "Iİ"
KHARFX = "ıi"

AYRACLAR = ",\.;«»!?-:/\*+_=\"<>()'[]|º#&%"

#Asıl bilgiler bu sozlukte yer alacak sozcuk:frekans
anaSozluk = dict()

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


def txt_dosyabul(klasor):
    liste = []
    #klasördeki .txt uzantılı ve ismi zzz_ ile başlamayan dosyaları bul
    for dir, dirs, files in os.walk(klasor):
        for dosya in files:
            if dosya.endswith(".txt"):
                if not dosya.startswith("zzz_"):
                    #liste.append(os.path.join(root,dosya))
                    liste.append(dosya)

    return klasor, liste

def txt_dosyaOku(klasor, dosya):
    eski=klasor+"/"+dosya
    yeni=klasor+"/zzz_"+dosya
    sozcukler = []
    with open(eski) as fdosya:
        sat0 = ''
        for sat in fdosya:

            sat0 += sat.strip()
            if sat[-1]=='-':    #Satır sonunda tire varsa
                sat0 =sat0[:-1]
                continue
            else:
                #AYRACLAR içindeki karakterler de aslında sözcükleri ayırıyor
                for a in AYRACLAR:
                    sat0 = sat0.replace(a,' ')

                kelimeler = sat0.split()    #boşluklara göre parçala
                for kelime in kelimeler:
                    if kelime.isalpha():
                        sozcukler.append(kelime)
                    elif kelime.isalnum():
                        pass
                    elif kelime.isdigit():
                        pass
                    else:
                        k = kelime.strip(AYRACLAR)
                        sozcukler.append(k)
                sat0=''

    print(eski)
    #os.rename(eski,yeni)
    return sozcukler

def is_tek_tire_var(sozcuk):
    var = 0
    for say in range(len(sozcuk)):
        if sozcuk[say] == "-":
            if say==0 or say == len(sozcuk)-1:
                return False
            var +=1

    if var==1:
        return True
    else:
        return False

def is_tirnak_icinde(sozcuk):
    if sozcuk[0]=="'" or sozcuk[-1]== "'":
        return True
    elif sozcuk[0]=='"' or sozcuk[-1]== '"':
        return True
    else:
        return False

def is_tek_tirnak_alpha(sozcuk):
    if is_tirnak_icinde(sozcuk):
        return False
    var = 0
    say0=-1
    for say in range(len(sozcuk)):
        if sozcuk[say] == "'":
            if say==0 or say == len(sozcuk)-1:
                return False
            if say0<0:
                say0 = say
            var +=1

    if var==1:
        s1 = sozcuk[:say0]
        s2 = sozcuk[say0+1:]
        if s1.isalpha() and s2.isalpha():
            return True
        else:
            return False
    else:
        return False

def alfabetik(sozluk):
    ys = OrderedDict(sorted(sozluk.items(),key=itemgetter(0)))
    return ys

def frekansa_gore(sozluk):
    ys = OrderedDict(sorted(sozluk.items(),key=itemgetter(1)))
    return ys


if __name__ == "__main__":
    #kucukHaryYap fonksiyonunun Türkçe karakterler için doğru çalıştığından emin olalım
    assert kucukHarfYap("ÇĞIİÖŞÜ")=="çğıiöşü"
    basla = time.perf_counter()
    hatalar = []
    sozcuksay=0

    klasor, dosyalar = txt_dosyabul(DATA_KLASOR)
    for dosya in dosyalar:
        #print(dosya)
        sozcukler = txt_dosyaOku(klasor,dosya)
        for sozcuk in sozcukler:
            #TODO: yanlış sözcükler ayıklanacak
            if sozcuk == '' or sozcuk.isdigit() or sozcuk.isdecimal():
                continue
            #TODO: apostrof kullanıldıysa sözcük ve ekini ayırmak doğru olur mu?
            #TODO: isalpha kontrolü yap - tırnak varsa sorun olacak
            if is_tek_tirnak_alpha(sozcuk):
                pass
            elif is_tek_tire_var(sozcuk):
                pass
            elif sozcuk.isalpha():
                pass
            else:
                hatalar.append(sozcuk)
                continue

            #TODO: hepsini küçük harf yapsak mı?
            sozcuk = kucukHarfYap(sozcuk)
            print(sozcuk )
            if sozcuk in anaSozluk:
                anaSozluk[sozcuk] +=1
            else:
                anaSozluk[sozcuk] = 1
            sozcuksay +=1

    print("*"*50)
    print(hatalar)
    print("Toplam Sözcük = {}  Hatalı Sözcük = {} Oran = % {}".format(sozcuksay,
                                                                    len(hatalar),
                                                                    100*len(hatalar)/sozcuksay))
    print("Toplam çalışma süresi = {} saniye".format(time.perf_counter()-basla))
    print("Ayrık sözcük sayısı = {}".format(len(anaSozluk)))

    #alfabetik sıralama yapalım
    ays= alfabetik(anaSozluk)
    fout=open("sozler.txt","w")

    #frekansa göre sıralama yapalım
    #ays= frekansa_gore(anaSozluk)
    #fout=open("frekans.txt","w")

    i = 1
    #for sozcuk,frekans in anaSozluk.items():
    for sozcuk,frekans in ays.items():
        #print("{>:6d} {<30:}:{>:6d}".format(i, sozcuk,frekans))
        print("{}:{}".format(sozcuk,frekans),file=fout)
        i+=1
    fout.close()

    fout = open("hatalar.txt","w")
    for hata in hatalar:
        print("{}".format(hata),file=fout)
    fout.close()
