# -*- coding: utf-8 -*-
#turkcemi.py
#2016-02-08
#author = Ahmet Aksoy
#Son güncelleme = 2016-03-01
#Python 3.5.1 ile test edildi
import time, sys

"""
Amaç: Bir metni okuyup sözcüklerine ayırmak
sonra da bu sözcüklerin ne kadarının dertop.txt
dosyasında yer aldığını belirlemek
"""
BHARF = "ÇĞİIÖŞÜ"
KHARF = "çğiıöşü"
BHARFX = "Iİ"
KHARFX = "ıi"
AYRACLAR = ",\.;«»!?-:/\*+_=\"<>()'[]|º#&%"

#Dikkat! dertop listesinde uzatma/inceltme işaretli sözcükler yok
#Bütün sözcükler küçük harf
encok = []
with open("./veri/encok.txt",encoding="utf-8") as fin:
    for soz in fin:
        encok.append(soz.strip())
print("encok boyu = "+str(len(encok)))

def ayraclari_kaldir(string):
    ystring=''
    for i in range(len(string)):
        if string[i] not in AYRACLAR+" ":
            ystring += string[i]
    return ystring

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
        else:
            s+=harf
    return s


def parcala(metin):
    sozcukler = []
    sat0 = ''
    for sat in metin.split():
        sat0 += sat.strip()
        if sat[-1]=='-':    #Satır sonunda tire varsa
            sat0 =sat0[:-1]+' '     # - yerine boşluk 10.02.2016
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

    return sozcukler

def turkcemi(metin,fout=None,printet=True):
    #metni sözcüklerine ayır
    liste = parcala(metin)
    say = len(liste)
    print("Sozcuk sayısı = ",say)
    if say <1:
        print("Liste boş.")
        print("Liste boş.",file=fout,flush=True)
        return False
    var = 0
    yok = 0
    for soz in liste:
        #if len(soz)<2: continue
        soz2 = inceltme_yok(kucukHarfYap(soz))
        if soz2  in encok:
            var += 1
            if var % 1000 ==0:
                print(var,end=' ',flush=True)
        else:
            yok += 1

    oran = 100*var/say
    if printet==True:
        print("Toplam= {} Bulunan= {} Bulunma Oranı= % {}".format(say,var,oran))
        if fout != None:
            print("Toplam= {} Bulunan= {} Bulunma Oranı= % {}".format(say,var,oran),file=fout,flush=True)
    if oran >= 20: return True
    return False

if __name__ == "__main__":
    #kucukHaryYap fonksiyonunun Türkçe karakterler için doğru çalıştığından emin olalım
    assert kucukHarfYap("ÇĞIİÖŞÜ")=="çğıiöşü"

    metin = """
    Bu bir Türkçe şarkı metnidir.
    Semavi dinler ne durumda?
    Cengaverler ne yapmışlar?
    Yoksa cengâver mi demeliydi?
    Peki paşalar ne demiş bu işe?
    Bu köşe yaz köşesi, o köşe kış köşesi, ortasında su şişesi.
    Çekoslavakyalılaştıramadıklarımızdan mısınız?
    Avustralyalılaştıramadıklarımızdan mısınız?
    İstanbul, Eskişehir, Ankara tren güzergahında...
    ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ
    """
    basla = time.perf_counter()

    #fad = "D:/aaa-kaynaklar/alice.txt"
    #fad = "D:/aaa-kaynaklar/Başkasının Karısı.txt"
    fad = "D:/aaa-kaynaklar/calikusu.txt"
    #fad = "D:/aaa-english/python3programs.txt"

    metin = ""
    try:
        fin = open(fad, encoding="utf-8")
        metin = fin.read()
    except UnicodeDecodeError:
        fin = open(fad, encoding="cp1254")
        metin = fin.read()
    except Exception as e:
        print(e)
        sys.exit()
    finally:
        fin.close()
    metin=""
    turkcemi(metin)
    print("Toplam çalışma süresi = {} saniye".format(time.perf_counter()-basla))
