# -*- coding: utf-8 -*-
#hurriyet.py
#2016-03-13
#author = Ahmet Aksoy
#Son güncelleme = 2016-04-01
#Python 3.5.1 ile test edildi
from selenium import webdriver
from urllib.parse import urlparse
import turlib
import turkcemi
import derlem
import re
import time, datetime

xharfler= {'ÅŸ':'ş','ÄŸ':'ğ','â€™':"'",'Ä±':'ı','Ã¶':'ö','Ã¼':'ü','Ã§':'ç','Â':' ',
           'Ä°':'İ','Ã‡':'Ç','Ã–':'Ö','Åž':'Ş','Äž':'Ğ','Ãœ':'Ü','â€¦':'...',
           'â€œ':'“','â€':'”','Ã¢':'â','â€':'‘',
           'ð':'ğ','ý':'ı','þ':'ş','Ý':'İ','Þ':'Ş','Ð':'Ğ'}

adresler = "http://www.hurriyet.com.tr/index/?p=250"
modname = "hurriyet_py"

global outfilename

habersay =0
baslama = int(time.time())


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

def sayfa_oku(b,basla):
    sayfa = turlib.sayfaOku(b)
    if sayfa == None:
        turkcemi.mesajyaz("{} Sayfa okunamadı: {}".format(modname,b))
        return

    #TODO: link açıklamaları kalkmayacak
    #sayfadan tüm linkleri kaldır
    #for tag in sayfa.findAll('a', href=True):
    #    tag.extract()

    paragraflar = sayfa.find_all('div',attrs={'itemprop' : 'articleBody'})
    if len(paragraflar)==0:
        turkcemi.mesajyaz("Bu sayfada makale bulunmamaktadır.")
        return
    for pr in paragraflar:
        #script bölümlerini temizle
        #[s.extract() for s in pr('script')]

        #http:// ile başlayan ardışık karakterleri sil
        #re.sub('(http.*)\s',' ',pr.text)

        #Başlık ile metin arasında boşluk karakteri olsun
        parag = " ".join(pr.findAll(text=True))
        #Farklı karakterler varsa düzelt
        for i in xharfler.keys():
            parag=re.sub(i,xharfler[i],parag)
        #Başlık ile normal yazı arasına boşluk eklenmesi lazım
        turkcemi.mesajyaz(parag)
        if (turkcemi.turkcemi(parag) == True) and (len(parag)>=400):
            turkcemi.mesajyaz("Bu metin Türkçedir")
            turkcemi.mesajyaz("{} {:06d} {} {}".format(turlib.damgatar(),habersay,modname,b))
            txttest = derlem.TXTDerlemTRText(parag)
            turkcemi.mesajyaz("{} {} Toplam çalışma süresi = {} saniye".format(turlib.damgatar(),modname,time.perf_counter()-basla))
        else:
            turkcemi.mesajyaz(modname+" Bu metin Türkçe değildir veya yeterli sayıda geçerli Türkçe sözcük barındırmamaktadır.")

def load_arsiv_page(driver,adres):
    global habersay
    basla = time.perf_counter()
    if adres[-1]=='/': adres = adres[:-1]
    base_url = get_base_url(adres)
    driver.get(adres)
    elements = driver.find_elements_by_xpath("//h3/a[@href]")
    for a in elements:
        try:
            b = a.get_attribute('href')
        except Exception as e:
            turkcemi.mesajyaz("{} Exception -1: {}".format(modname,e))
            continue
        if b is None: continue
        if len(b)==0: continue
        if b[-1]=='/': b = b[:-1]
        if b == base_url: continue
        if not b.startswith(base_url): continue
        if b == adres: continue
        if b == base_url+"/index": continue
        habersay += 1
        turkcemi.mesajyaz("\n{} {} {} {:05d} {}".format(turlib.damgatar(), modname, turlib.gecen_sure(baslama), habersay, b))
        #link başka bir siteye ait olmasın
        if base_url in b:
            sayfa_oku(b,basla)
        else:
             turkcemi.mesajyaz(modname+" Link başka siteye aittir: {}".format(b))

def main():
    sene = 2014
    if str(sene) not in derlem.GENSOZLUK_DOSYA_ADI:
        print("derlem.py dosyasında GENSOZLUK_DOSYA_ADI Yılı hatalı. Düzeltin.")
        return
    driver = get_driver()    
    pagestart = 0
    pageend=2810
    if driver != None:
        turkcemi.outfilename = "temp/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
        for pageno in range(pagestart,pageend):
            if pageno%10 ==0:
                turkcemi.outfilename = "temp/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
            adres = "http://www.hurriyet.com.tr/index/?p="+"{}&d={}".format(pageno,sene)
            turkcemi.mesajyaz("*"*50)
            turkcemi.mesajyaz("\n{} SayfaNo:{:06d} {}".format(turlib.damgatar(), pageno,adres))
            load_arsiv_page(driver,adres)
        driver.quit()


if __name__ == "__main__":
    derlem.gensozluk_oku()
    main()
    """
    b = "http://www.hurriyet.com.tr/basbakan-davutoglundan-onemli-aciklamalar-40067609"
    basla = time.perf_counter()
    sayfa_oku(b,basla)
    """
