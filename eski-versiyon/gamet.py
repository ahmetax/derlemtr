# -*- coding: utf-8 -*-
#gamet.py
#2016-03-07
#author = Ahmet Aksoy
#Son güncelleme = 2016-03-12
#Python 3.5.1 ile test edildi
from selenium import webdriver
from urllib.parse import urlparse
import turlib
import turkcemi
from derlem import *
import re
import time, datetime
"""
adresler = [
    "http://webmaster.gamet.com.tr/arsiv/",
    "http://www.gamet.com.tr/arsiv-2/"
]
"""
adresler = [
    "http://www.gamet.com.tr/arsiv-2/"
]

sayfasay =0
baslama = int(time.time())

outfilename = "temp/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+"-metin.txt"
outfile = open(outfilename,"a",encoding="utf-8")

def get_base_url(url):
    o =urlparse(url)
    base_url=''
    if o.scheme > '':
        base_url += o.scheme+"://"
    base_url += o.netloc
    return base_url

#Varsayılan driver olarak Firefox kullanılacak
def get_driver():
    try:
        driver = webdriver.Firefox()
    except:
        driver = None
    return driver

def load_arsiv_page(driver,adres):
    global sayfasay
    basla = time.perf_counter()
    if adres[-1]=='/': adres = adres[:-1]
    base_url = get_base_url(adres)
    driver.get(adres)
    elements = driver.find_elements_by_xpath("//li/a[@href]")
    for a in elements:
        try:
            b = a.get_attribute('href')
        except Exception as e:
            print("gamet.py Exception -1: {}".format(e))
            print("gamet.py Exception -1: {}".format(e),file=outfile, flush=True)
            continue

        if b[-1]=='/': b = b[:-1]
        if b == base_url: continue
        if not b.startswith(base_url): continue
        if b == adres: continue
        sayfasay += 1
        print("{} gamet.py-2 {} {:05d} {}".format(turlib.damga(), turlib.gecen_sure(baslama), sayfasay, b))
        #link başka bir siteye ait olmasın
        if base_url in b:
            sayfa = turlib.sayfaOku(b)
            if sayfa == None:
                print("gamet.py Sayfa okunamadı: {}".format(b))
                print("gamet.py Sayfa okunamadı: {}".format(b),file=outfile, flush=True)
                continue
            #sayfadan tüm linkleri kaldır
            for tag in sayfa.findAll('a', href=True):
                tag.extract()

            paragraflar = sayfa.find_all('div',attrs={'class' : 'entry-content'})
            if len(paragraflar)== 0:
                paragraflar = sayfa.find_all('div',attrs={'class' : 'entry fix'})
            if len(paragraflar)==0:
                print("Bu sayfada makale bulunmamaktadır.")
                print("Bu sayfada makale bulunmamaktadır.",file=outfile, flush=True)
                continue
            for p in paragraflar:
                #script bölümlerini temizle
                [s.extract() for s in p('script')]
                #div - class=sharedaddy bölümünü temizle
                for div in p.findAll('div', attrs={'class':'sharedaddy'}):
                    div.extract()
                #http:// ile başlayan ardışık karakterleri sil
                re.sub('(http.*)\s','',p.text)
                print(p.text)
                print(p.text,file=outfile,flush=True)
                if (turkcemi.turkcemi(p.text, fout=outfile) == True) and (len(p.text)>=1000):
                    print("Bu metin Türkçedir")
                    print("Bu metin Türkçedir", file=outfile, flush=True)
                    print("{} {:06d} {} {}".format(damga(), sayfasay,'gamet.py-1',b), flush=True)
                    print("{} {:06d} {} {}".format(damga(),sayfasay,'gamet.py',b),file=outfile, flush=True)
                    txttest = TXTDerlemTRText(p.text)
                    print("{} gamet.py Toplam çalışma süresi = {} saniye".format(damga(),time.perf_counter()-basla),flush=True)
                    print("{} gamet.py Toplam çalışma süresi = {} saniye".format(damga(),time.perf_counter()-basla),file=logfile,flush=True)
                else:
                    print("gamet.py Bu metin Türkçe değildir veya yeterli sayıda geçerli Türkçe sözcük barındırmamaktadır.")
                    print("gamet.py Bu metin Türkçe değildir veya yeterli sayıda geçerli Türkçe sözcük barındırmamaktadır.",file=logfile,flush=True)
        else:
             print("gamet.py Link başka siteye aittir: {}".format(b))
             print("gamet.py Link başka siteye aittir: {}".format(b),file=logfile,flush=True)

def main():
    driver = get_driver()
    if driver != None:
        for adres in adresler:
            load_arsiv_page(driver,adres)
    outfile.close()

if __name__ == "__main__":
    logfile = logfile_ac()
    gensozluk_oku()
    main()
