# -*- coding: utf-8 -*-
#sozluk_temizle.py
#2016-03-12
#author = Ahmet Aksoy
#Son güncelleme = 2016-03-12
#Python 3.5.1 ile test edildi
"""
Bu program, gensozluk.txt dosyasını tarayarak
geçersiz olanları xgensozluk.txt ve geçerli olanları
ygensozluk.txt dosyasına kaydediyor
"""

alfabe_kh = "abcçdefgğhıijklmnoöprsştuüvyz"

gensozluk = dict()
def gensozluk_oku():
    try:
        with open("eski-gensozluk.txt",encoding="utf-8") as f:
            for line in f:
                l = line.split()
                gensozluk[l[1].strip()] = int(l[0].strip())
    except:
        pass

def sozluk_kaydet(fad,sozluk):
    fout = open(fad, "w", encoding="utf-8")
    sd = sorted(sozluk.items(), key=lambda x:x[1], reverse=True)
    for saz in sd:
        s = "{:08d} {}\n".format(int(saz[1]), saz[0])
        fout.write(s)
    fout.close()


if __name__ == "__main__":
    gensozluk_oku()
    qgensozluk = dict()     #qwx geçen sözcükler
    xgensozluk = dict()     #diğer hatalı sözcükler
    ygensozluk = dict()     #sadece Türkçe karakter içeren sözcükler
    for key in gensozluk.keys():
        qsay=0
        xsay=0
        for c in key:
            if c not in alfabe_kh:
                if c in "qwx": qsay += 1
                else: xsay += 1

        if xsay>0:
            print("çöp: ", key)
            xgensozluk[key]=gensozluk[key]
        elif qsay>0:
            print("qwx: ", key)
            qgensozluk[key]=gensozluk[key]
        else:
            ygensozluk[key]=gensozluk[key]

    sozluk_kaydet("xgensozluk.txt",xgensozluk)
    sozluk_kaydet("qgensozluk.txt",qgensozluk)
    sozluk_kaydet("ygensozluk.txt",ygensozluk)