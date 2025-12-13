"""
aktalib.py file will contain functions to be used
to operate AKTA project.
"""
import time, datetime

BHARFX = "Iİ"
KHARFX = "ıi"
import time

def show_time(message, t1, t0=None):
    """
    Show total elapsed at the end of a process
    t1: start time
    t2: finishing time
    """
    now = datetime.datetime.now()
    t2 = time.time()
    fark = round(t2-t1, 4)
    h = int(fark//3600)
    m = int((fark-h*3600)//60)
    s = round(fark-h*3600-m*60, 4)
    
    print(f"{message}: {fark} secs ->  {h}h {m}m {s}s ({now.strftime('%H:%M:%S')})")
    if t0:
        fark = round(t2-t0, 4)
        h = int(fark//3600)
        m = int((fark-h*3600)//60)
        s = round(fark-h*3600-m*60, 4)        
        print(f"Total time: {fark} secs ->  {h}h {m}m {s}s")
    return t2 - t1

def show_time_old(message, t1, t0=None):
    """
    Show total elapsed at the end of a process
    t1: start time
    t2: finishing time
    """
    t2 = time.time()
    fark = round(t2-t1,4)
    h = int(fark//3600)
    m = int((fark-h*3600)//60)
    s = round(fark-h*3600-m*60,4)
    # print(f"{message}: {round(t2-t1,4)} secs")
    print(f"{message}: {round(t2-t1,4)} secs ->  {h}h {m}m {s}s")
    if t0:
        fark = round(t2-t0,4)
        h = int(fark//3600)
        m = int((fark-h*3600)//60)
        s = round(fark-h*3600-m*60,4)        
        print(f"Total time: {round(t2-t0,4)} secs ->  {h}h {m}m {s}s")
    return t2


def trklower(text):
    for j in range(len(BHARFX)):
        text = text.replace(BHARFX[j], KHARFX[j])
    text = text.lower()
    return text

def extract_turkish_body(text):
    # find "*** START OF TURKISH PART ***"
    start = text.find("*** START OF TURKISH PART ***\n") + 30
    # find "*** END OF TURKISH PART ***"
    end = text.find("*** END OF TURKISH PART ***\n") -1
    trtext = text[start:end]
    return trtext

def get_lines(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # UTF-8 ile açılamazsa, farklı bir kodlama deneyin
        with open(filename, 'r', encoding='iso-8859-1') as file:
            lines = file.readlines()

    return lines
    
def get_text(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            text = file.read()
    except UnicodeDecodeError:
        # UTF-8 ile açılamazsa, farklı bir kodlama deneyin
        with open(filename, 'r', encoding='iso-8859-1') as file:
            text = file.read()

    return text
    


if __name__ == "__main__":
    filename = "aktadata/30006.txt"
    with open(filename, 'r') as f:
        content = f.read()
        trtext = extract_turkish_body(content)
        print(trtext[:200])
        print("")
        print(trtext[-200:])

