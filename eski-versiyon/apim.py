from flask_api import FlaskAPI
import random

app = FlaskAPI(__name__)

kelimeler =[]
with open('static/kelimeler.txt',encoding='utf-8') as fd:
    for kelime in fd:
        kelimeler.append(kelime.strip())

def get_random_kelime(say):
    if say is None: n = 1
    else: n = say
    if n<1: n = 1
    elif n>10: n = 10

    sayilar = []
    for m in range(n):
        sayilar.append(random.randrange(len(kelimeler)))

    kelimelist=[]
    for m in range(n):
        kelimelist.append(kelimeler[sayilar[m]])
    return kelimelist
        
def kelime_yolla():
    return {
	'sayı': 0,
        'text': get_random_kelime(1)[0]
    }

@app.route("/", methods=['GET'])
def bos_kelime_listesi():
    liste = {'0':'Lütfen doğru parametre girin'}
    return liste

@app.route("/<int:key>/", methods=['GET'])
def kelime_listesi(key):
    kelimelist = get_random_kelime(key)
    liste = {}
    for i in range(len(kelimelist)):
        liste[i]=kelimelist[i]
    return liste

@app.route("/kelime/", methods=['GET'])
def tek_kelime():
    return kelime_yolla()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=11713,debug=True)

