#encoding:utf-8

import csv
from tkinter import *
from tkinter import messagebox
import sqlite3
import urllib.request
import os.path
import re



dataBase = "vinos.db"

def abrir_url(url,file):
    try:
        if os.path.exists(file):
            recarga = input("La página ya ha sido cargada. Desea recargarla (s/n)?")
            if recarga == "s":
                urllib.request.urlretrieve(url,file)
                print("Página recargada")
        else:
            urllib.request.urlretrieve(url,file)
            print("Página cargada")
        return file
    except:
        print  ("Error al conectarse a la página")
        return None
    
def extraer_lista(file):
    f = open (file, "r",encoding='utf-8')
    s = f.read()
    lista_vinos = re.findall(r'<div class="list large">.*?</div>', s)
    nombre = re.findall(r'<h2 class="title heading">(.*)</h2>', s)
    print (nombre)
    return 0
    
def ventana_principal():
    raiz = Tk()
    raiz.title("Gestion de Vinos")
    raiz.geometry("400x400")

    menu = Menu(raiz)

    raiz.config(menu=menu)

    raiz.mainloop()

if __name__ == "__main__":
    url = "https://www.vinissimus.com/es/vinos/tinto/?cursor=0"
    file = "Beatifulsoup/vinos.html"
    abrir_url(url,file)
    extraer_lista(file)
    ventana_principal()
