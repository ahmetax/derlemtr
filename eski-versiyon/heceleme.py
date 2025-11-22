# -*- coding: utf-8 -*-
#Yazar: Ahmet Aksoy
#Tarih: 19.04.2016
"""
Bu betikte kullanılan algoritma T. Hürsel Kendir'in 25.3.1982 tarihli tezinde sunulmuştur.
Algoritmanın geliştirilmesinde Güney Gönenç ve Ersin Töreci'nin çalışmaları referans
alınmıştır.
Algoritma ile ilgili ayrıntılara http://gurmezin.com/turkce-hecelemede-6-temel-kural/
adresinden ulaşabilirsiniz.
"""
import sys

SESLILER ="aeıioöuüAEIİOÖUÜ"

def sesliSay(kelime):
    say = 0; harita =''
    for i in range(len(kelime)):
        if kelime[i] in SESLILER:
            say += 1
            harita += '0'
        else: harita += '.'
        i += 1
    return say, harita

#kelime içindeki sesli harfleri sayarak hece sayısını saptar
def hecele(kelime, detayli):
    n,harita = sesliSay(kelime)
    if detayli: print("Hece (sesli) sayısı = {} Harita = {} ({})".format(n, harita, kelime))
    #Haritaya göre parçala
    heceler = ''
    i=0
    l= len(harita)
    while i < l-1:
        if harita[i]=='0':
            #a
            if harita[i+1]=='0':   #peşpeşe iki karakter de sesli
                #iki sesliyi ayır
                heceler += harita[i]+'-'
                i+=1
            #b
            elif i<l-2 and harita[i+1]=='.' and harita[i+2]=='0':
                #ilk sesliden sonra böl
                heceler += harita[i]+'-'
                i+=1
            #c
            elif i<l-3 and harita[i+1]=='.' and harita[i+2]=='.' and harita[i+3]=='0':
                #iki sessiz arasından böl
                heceler += harita[i:i+2]+'-'
                i+=2
            #d
            elif i<l-4 and harita[i+1]=='.' and harita[i+2]=='.' and harita[i+3]=='.' and harita[i+4]=='0':
                if kelime[i+3]=='r':
                    #birinci sessizden sonra böl
                    heceler += harita[i:i+2]+'-'
                    i+=2
                else:
                    #ikinci sessizden sonra böl
                    heceler += harita[i:i+3]+'-'
                    i+=3
            #e
            elif i<l-5 and harita[i+1]=='.' and harita[i+2]=='.' and harita[i+3]=='.' and harita[i+4]=='.'\
                    and harita[i+5]=='0':
                if kelime[i+3]=='r':
                    #üçüncü sessizden sonra böl
                    heceler += harita[i:i+4]+'-'
                    i+=4
                else:
                    #ikinci sessizden sonra böl
                    heceler += harita[i:i+3]+'-'
                    i+=3
            #f
            elif i<l-6 and harita[i+1]=='.' and harita[i+2]=='.' and harita[i+3]=='.' and harita[i+4]=='.'\
                    and harita[i+5]=='.' and harita[i+6]=='0':
                #ikinci sessizden sonra böl
                heceler += harita[i:i+3]+'-'
                i+=4

            else:
                heceler+=harita[i]
                i+=1
        else:
            heceler+=harita[i]
            i+=1
    heceler+=harita[-1]
    oz,yab,yok = ozturkce(heceler)

    return heceler, n, oz,yab,yok

def ozturkce(heceler):
    ozturkcehece =['0','.0','0.','.0.','0..','.0..']
    yabancihece = ['..0','..0.','...0','...0.','..0..','.0...','...0..','..0...']
    liste = heceler.split('-')
    oz = yab = yok = 0
    for hece in liste:
        if hece in ozturkcehece: oz+=1
        elif hece in yabancihece: yab +=1
        else: yok +=1

    return oz, yab, yok

def kelimeOku():
    kelimeler = []

    with open("/home/ax/PycharmProjects/trderlemx/gensozlukler/gensozluk-kit-rad-hur.txt",encoding="utf-8") as fin:
        for soz in fin:
            kelime=soz.split(' ')[1].strip()
            if len(kelime)>10:
                kelimeler.append(kelime)
    return kelimeler

def ana():
    kelimeler =['pıtırcık',"kraliçe","kontrol","strateji","stronsiyum","trençkot","kontrbas",
                "sprinkler","sfenks","ıstranca","endüstriyel","samsunspor","bursaspor"]
    #kelimeler =["endüstriyel","bursaspor"]
    #fout = open("yabanci_kokenli.txt","w", encoding="utf-8")
    fout=sys.stdout
    #kelimeler = kelimeOku()
    kelimesay =0
    for kelime in kelimeler:
        s,n,oz,yab,yok = hecele(kelime, False)
        #print(s)
        j=0; ss = '';tiresay=0
        for i in range(len(s)):
            if s[i]=='-':
                ss+='-'
                tiresay+=1
            else:
                ss+=kelime[j]
                j+=1
        #print(ss)
        if tiresay!=n-1:
            print(ss+"  ****** Hece sayısında tutarsızlık var! ******")
        else:
            if yok+yab==0:
                oztr = ''   #'Öztürkçe'
            elif yok>0:
                oztr = 'Belirsiz'
            else:
                oztr = 'Yabancı kökenli'
                #print("{} {}".format(ss,oztr),file=fout,flush=True)
            print("{} {} {} {} {}".format(ss,oz,yab,yok,oztr))

        kelimesay+=1
        #if kelimesay>10000: break

    fout.close()

if __name__ == "__main__":
    ana()