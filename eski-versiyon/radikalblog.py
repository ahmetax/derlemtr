# -*- coding: utf-8 -*-
#radikalblog.py
#2016-03-13
#author = Ahmet Aksoy
#Son güncelleme = 2016-03-28
#Python 3.5.1 ile test edildi
from urllib.parse import urlparse
from  turlib import *
import turkcemi
from derlem import *
import re
import time, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

xharfler= {'ÅŸ':'ş','ÄŸ':'ğ','â€™':"'",'Ä±':'ı','Ã¶':'ö','Ã¼':'ü','Ã§':'ç','Â':' ',
           'Ä°':'İ','Ã‡':'Ç','Ã–':'Ö','Åž':'Ş','Äž':'Ğ','Ãœ':'Ü','â€¦':'...',
           'â€œ':'“','â€':'”','Ã¢':'â','â€':'‘',
           'ð':'ğ','ý':'ı','þ':'ş','Ý':'İ','Þ':'Ş','Ð':'Ğ'}

#zharfler = {'ð':'ğ','ý':'ı','þ':'ş','Ý':'İ'}

base_url = "http://blog.radikal.com.tr/"
modname = "radikalblog_py"

sayfasay =0
sayfasay0 = 0
baslama = int(time.time())

global outfilename
#outfilename = "temp/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
#outfile = open(outfilename,"a",encoding="utf-8")

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
        """
        profile = webdriver.FirefoxProfile()
        profile.native_events_enabled = True
        useragent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"
        profile.set_preference("general.useragent.override",useragent)
        driver = webdriver.Firefox(firefox_profile=profile)
        """
        #driver =webdriver.Firefox()
        driver =webdriver.Chrome("C:/webdrivers/chromedriver.exe")
        driver.wait = WebDriverWait(driver, 10)
    except Exception as e:
        print("get_driver Exception: "+str(e),flush=True)
        #print("get_driver Exception: "+str(e),file=outfile, flush=True)
        turkcemi.mesajyaz("get_driver Exception: "+str(e))
        driver = None
    return driver

def sayfa_oku(b,basla):
    #global sayfasay
    basla = time.perf_counter()
    sayfa = sayfaOku(b)
    if sayfa == None:
        print("{} Sayfa okunamadı: {}".format(modname,b))
        #print("{} Sayfa okunamadı: {}".format(modname,b),file=outfile, flush=True)
        turkcemi.mesajyaz("{} Sayfa okunamadı: {}".format(modname,b))
        return

    #TODO: link açıklamaları kalkmayacak
    #sayfadan tüm linkleri kaldır
    #for tag in sayfa.findAll('a', href=True):
    #    tag.extract()

    #paragraflar = sayfa.find_all('div',attrs={'itemprop' : 'articleBody'})
    paragraflar = sayfa.find_all('div',attrs={'class' : 'text-area'})
    if len(paragraflar)==0:
        print("Bu sayfada makale bulunmamaktadır.")
        #print("Bu sayfada makale bulunmamaktadır.",file=outfile, flush=True)
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
        print(parag)
        #print(parag,file=outfile,flush=True)
        try:
            turkcemi.mesajyaz(parag)
        except:
            pass
        if (turkcemi.turkcemi(parag)==True) and (len(parag)>=400):
            print("Bu metin Türkçedir")
            #print("Bu metin Türkçedir", file=outfile, flush=True)
            turkcemi.mesajyaz("Bu metin Türkçedir")
            print("{} {:06d} {} {}".format(damgatar(),sayfasay,modname,b), flush=True)
            #print("{} {:06d} {} {}".format(damgatar(),sayfasay,modname,b),file=outfile, flush=True)
            turkcemi.mesajyaz("{} {:06d} {} {}".format(damgatar(),sayfasay,modname,b))
            txttest = TXTDerlemTRText(parag)
            print("{} {} Toplam çalışma süresi = {} saniye".format(damgatar(),modname,time.perf_counter()-basla),flush=True)
            #print("{} {} Toplam çalışma süresi = {} saniye".format(damgatar(),modname,time.perf_counter()-basla),file=outfile,flush=True)
            turkcemi.mesajyaz("{} {} Toplam çalışma süresi = {} saniye".format(damgatar(),modname,time.perf_counter()-basla))
        else:
            print(modname+" Bu metin Türkçe değildir veya yeterli sayıda geçerli Türkçe sözcük barındırmamaktadır.")
            #print(modname+" Bu metin Türkçe değildir veya yeterli sayıda geçerli Türkçe sözcük barındırmamaktadır.",file=outfile,flush=True)
            turkcemi.mesajyaz(modname+" Bu metin Türkçe değildir veya yeterli sayıda geçerli Türkçe sözcük barındırmamaktadır.")

def kategori_kaydet(driver):
    driver.get(base_url)
    element = driver.find_element_by_class_name('jspPane')
    fk=open("global_kategori.txt","w",encoding="utf-8")
    lkategori = element.find_elements_by_xpath("//li/a[@href]")
    for kategori in lkategori:
        b = kategori.get_attribute('href')
        if base_url in b:
            fk.write(b)
    fk.close()
    return

def kategori_oku():
    kategorilistesi=[]
    fk=open("global_kategori.txt","r",encoding="utf-8")
    liste = fk.readlines()
    for kat in liste:
        kategorilistesi.append(kat.strip())
    fk.close()
    return kategorilistesi

def kategori_sayfa(driver,kategori):
    global sayfasay0
    global sayfasay
    sayfasay=1
    basla = time.perf_counter()
    driver.get(kategori)
    print("(kategori_sayfa()): Kategori: {} Sayfasay: {}".format(kategori,sayfasay))
    #print("Kategori: {} Sayfasay: {}".format(kategori,sayfasay),file=outfile,flush=True)
    turkcemi.mesajyaz("(kategori_sayfa()): Kategori: {} Sayfasay: {}".format(kategori,sayfasay))
    eskisayfano=''
    timeout=0
    while True:
        # sayfanın yüklenmesini bekle
        next=None
        try:
            next = driver.wait.until(EC.presence_of_element_located(
                (By.ID,"MainContent_Pager1_lnkNext")
            ))
            logo = driver.wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME,"logo")
            ))
            sayfano = driver.find_element_by_class_name("aspNetDisabled").text
            if next != None:
                if sayfano == eskisayfano:
                    sonsayfa=True
                else:
                    eskisayfano=sayfano
                    sonsayfa=False
                    print("{} SayfaNo ={}".format(damgatar(),sayfano))
                    #print("{} SayfaNo ={}".format(damgatar(),sayfano),file=outfile,flush=True)
                    turkcemi.mesajyaz("{} SayfaNo ={}".format(damgatar(),sayfano))
                timeout=0

        except TimeoutException:
            print("Kategori_sayfa() timeout1")
            #print("Kategori_sayfa() timeout1",file=outfile,flush=True)
            turkcemi.mesajyaz("Kategori_sayfa() timeout1")
            timeout +=1
            if timeout <5: continue

        # Tüm yazı linklerini al
        #print("Burada sayfadaki yazı linkleri bulunacak")
        # linkleri okut ve işleme sok
        #print("Yazı linklerine bağlanıp yazı okunacak")
        sayfasay += 1
        if sayfasay < sayfasay0:
            next.click()
            continue
        linkler = driver.find_elements_by_xpath("//h5/a[@href]")
        for a in linkler:
            try:
                b = a.get_attribute('href')
            except Exception as e:
                print("{} {} Exception -1: {}".format(damgatar(),modname,e))
                #print("{} {} Exception -1: {}".format(damgatar(),modname,e),file=outfile,flush=True)
                turkcemi.mesajyaz("{} {} Exception -1: {}".format(damgatar(),modname,e))
                continue
            print("\n{} {} {} {:05d} {}".format(damgatar(), modname, gecen_sure(baslama), sayfasay, b))
            #print("\n{} {} {} {:05d} {}".format(damgatar(), modname, gecen_sure(baslama), sayfasay, b),file=outfile,flush=True)
            turkcemi.mesajyaz("\n{} {} {} {:05d} {}".format(damgatar(), modname, gecen_sure(baslama), sayfasay, b))
            sayfa = sayfa_oku(b,basla)
            if sayfa != None:
                print(sayfa.text)

        # next yoksa döngüden çık
        if next == None: break
        if sonsayfa == True: break
        next.click()

def main():
    global sayfasay0
    global outfile
    ilk_kategori=""
    try:
        driver = get_driver()
        if driver != None:
            #kategori_kaydet(driver)
            kategorilistesi=kategori_oku()
            for kategori in kategorilistesi:
                #if outfile: outfile.close()
                turkcemi.outfilename = "temp/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
                #outfile = open(outfilename,"a",encoding="utf-8")
                #LOGFILE = "loglar/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
                #logging.basicConfig(filename=outfilename, level=logging.INFO)
                sayfasay = 1        #Yeni kategori için başlangıç sayfano
                print("\n{} Kategori: {} Sayfasay: {}".format(damgatar(),kategori,sayfasay),flush=True)
                #print("\n{} Kategori: {} Sayfasay: {}".format(damgatar(),kategori,sayfasay),file=outfile,flush=True)
                turkcemi.mesajyaz("\n{} Kategori: {} Sayfasay: {}".format(damgatar(),kategori,sayfasay))
                kategori_sayfa(driver,kategori)
    finally:
        if driver==None:
            print("Driver açılamadı!")
            #print("Driver açılamadı!",file=outfile,flush=True)
            turkcemi.mesajyaz("Driver açılamadı!")
        # manuel kapat
        # driver.quit()

    #outfile.close()

if __name__ == "__main__":
    gensozluk_oku()
    #LOGFILE = "loglar/derlemlog"+"{}.txt".format(datetime.datetime.now().strftime("%Y%m%d"))
    #LOGFILE = "loglar/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
    #logging.basicConfig(filename=LOGFILE, level=logging.INFO)
    """
    turkcemi.outfilename= "loglar/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+modname+".txt"
    turkcemi.logyaz("deneme")
    turkcemi.logyaz("bu iş tamam")
    """
    main()

    """
    b="http://blog.radikal.com.tr/aile/can-disarida-olsa-o-yazardibu-yazi-onun-bir-sevgilisi-olmali-insanin-125042"
    basla= time.perf_counter()
    sayfa_oku(b,basla)
    """
