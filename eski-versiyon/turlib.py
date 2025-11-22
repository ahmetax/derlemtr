# -*- coding: utf-8 -*-
"""
Bu dosyada çeşitli fonksiyonlar bulunacak
"""
import requests
from bs4 import BeautifulSoup
import re
import datetime, time
from urllib.parse import urlparse
from turkcemi import ayraclari_kaldir, kucukHarfYap, inceltme_yok

alfabe_kh = "abcçdefgğhıijklmnoöprsştuüvyz"
alfabe_bh = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"

#Ayraçları, inceltme işaretlerini kaldır ve küçük harfe çevir
def hepsi_turkceye(kelime):
    sozcuk = ayraclari_kaldir(kelime)
    sozcuk = kucukHarfYap(sozcuk)
    sozcuk = inceltme_yok(sozcuk)
    return sozcuk

#Ayraçları kaldırdıktan sonra kalanların hepsi Türkçe karakter mi?
def hepsi_turkce(kelime):
    sozcuk = hepsi_turkceye(kelime)
    for c in sozcuk:
        if c not in alfabe_kh:
            return False
    return True

#damga() fonksiyonu log satırlarının zamanını vurgulamak için kullanılıyor
def damgatar():
    return datetime.datetime.now().strftime('%Y%m%d-%H:%M:%S.%f')

def gecen_sure(baslangic):
    now = int(time.time())
    delta = now-baslangic
    d=divmod(delta,86400)
    h=divmod(d[1],3600)
    m=divmod(h[1],60)
    s=m[1]
    return "{}:{:02d}:{:02d}:{:02d}".format(d[0],h[0],m[0],s)

def get_base_url(url):
    o =urlparse(url)
    base_url=''
    if o.scheme > '':
        base_url += o.scheme+"://"
    base_url += o.netloc
    return base_url

#url-path ilk parçasını döndürür
def get_path1(url):
    o =urlparse(url)
    path=o.path
    if path.count('/')>1:
        s = path.split('/')
        path = s[1]
    return path

def linkleriAl(sayfa_url):
    linkler=[]
    base_url = get_base_url(sayfa_url)
    if base_url == "":
        return linkler
    soup = sayfaOku(sayfa_url)
    try:
        for link in soup.findAll('a'):
            if 'href' in link.attrs:
                adres = link.attrs['href']
                if (base_url in adres) and (adres not in linkler):
                    path = get_path1(adres)
                    linkler.append(base_url+"/"+path)
    except Exception as e:
        fout2 = open("outfile.txt","a",encoding="utf-8")
        print(e,file=fout2, flush=True)
        fout2.close()
        pass
    return linkler

def sayfaOku(sayfa_url):
    try:
        r = requests.get(sayfa_url)
    except Exception as e:
        print(e)
        print(sayfa_url)
        return None
    try:
        soup = BeautifulSoup(r.content,"lxml")
    except:
        soup = BeautifulSoup(r.content,"html.parser")

    #print(soup.prettify())
    return soup

def turkcemi():
    True

if __name__ == "__main__":
    url ="http://www.gamet.com.tr/gelecege-donus/"
    print(get_path1(url))
    print(gecen_sure(int(time.time())-86400))
    print(hepsi_turkceye("Bu Türkçe bir cümledir."))
    print(hepsi_turkce("Bu Türkçe bir cümledir."))
    print(hepsi_turkceye("Şemsi Paşa Yalısındaki yalıçapkını"))