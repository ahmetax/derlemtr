# -*- coding: utf-8 -*-
#Author: Ahmet Aksoy
#Tarih: 09.03.2016
"""
Bu programda elimizdeki .txt dosyalarında kullanılan karakterler
kullanım frekanslarına göre gruplanacak.
Böylece Türkçedeki harf ve işaretleri kullanım sıklığını da
görmüş olacağız.
"""
import os
import time, datetime

def damga():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')

def txt_dosyabul(klasor):
    liste = []
    #klasördeki .txt uzantılı ve ismi zzz_ ile başlamayan dosyaları bul
    for dir, dirs, files in os.walk(klasor):
        for dosya in files:
            if dosya.endswith(".txt"):
                liste.append(dosya)

    return klasor, liste

if __name__ == '__main__':
    klasorler =["D:/aaa-kaynaklar","D:/aaa-kaynaklar2","D:/aaa-kaynaklar3"]
    #klasorler =["D:/aaa-kaynaklar"]
    logfile = open("harfler_istatistik.txt","w",encoding="utf-8")
    basla = time.perf_counter()

    dosyasay =0
    harfler = {'a': 1}
    for txt_klasor in klasorler:
        klasor, dosyalar = txt_dosyabul(txt_klasor)
        for d in dosyalar:
            dosyasay +=1
            #if dosyasay > 10: break
            print("{} {:06d} {}".format(damga(),dosyasay,d))
            print("{} {:06d} {}".format(damga(),dosyasay,d), file=logfile)
            try:
                with open(klasor+"/"+d,encoding="utf-8") as dosya:
                    for text in dosya:
                        for i in range(len(text)):
                            c= text[i]
                            if c in harfler.keys():
                                harfler[c] +=1
                            else:
                                harfler[c] =1

            except Exception as e:
                print(e)
                dosyasay -= 1

    say=1
    gentop =0
    sd = sorted(harfler.items(), key=lambda x:x[1], reverse=True)

    for c,n in sd:
        print("{:4d}  {} {:>6d} {:>10,}\n".format(say,c,ord(c),n))
        print("{:4d}  {} {:>6d} {:>10,}\n".format(say,c,ord(c),n), file = logfile)
        say += 1
        gentop+=n

    print("Harf sayısı = {}    Toplam harf sayısı= {:>16,}\n".format(say,gentop))
    print("Harf sayısı = {}    Toplam harf sayısı= {:>16,}\n".format(say,gentop),file=logfile)

    print("{} Toplam çalışma süresi = {} saniye".format(damga(),time.perf_counter()-basla))
    print("{} Toplam çalışma süresi = {} saniye".format(damga(),time.perf_counter()-basla),file=logfile)
    logfile.flush()
    logfile.close
