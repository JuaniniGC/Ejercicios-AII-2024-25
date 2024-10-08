# encoding:utf-8

import re
from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
from datetime import datetime

# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",
                                    message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_bd()


def almacenar_bd():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS JUEGO")
    conn.execute('''CREATE TABLE JUEGO
       (TITULO            TEXT NOT NULL,
        PORCENTAJE_VOTOS_POSITIVOS    INTEGER        ,
        PRECIO      INTEGER,
        TEMATICAS            TEXT,          
        COMPLEJIDAD         TEXT);''')

    #PAG1
    f = urllib.request.urlopen("https://zacatrus.es/juegos-de-mesa.html")
    #PAG2
    f2 = urllib.request.urlopen("https://zacatrus.es/juegos-de-mesa.html?p=2")

    s = BeautifulSoup(f, "lxml")
    s2 = BeautifulSoup(f2, "lxml")

    lista_link_juegos = [link.get("href") for link in s.find_all("a", class_="product-item-link")]
    lista_link_juegos.extend(link.get("href") for link in s2.find_all("a", class_="product-item-link"))
    lista_link_juegos = list(filter(lambda x:x != None, lista_link_juegos))
    for link_juego in lista_link_juegos:
        f = urllib.request.urlopen(link_juego)
        s = BeautifulSoup(f, "lxml")
        titulo = s.find("span", itemprop="name").text.strip()
        porcentaje_votos_positivos = s.find("div", class_="rating-result")
        if porcentaje_votos_positivos is not None:
            porcentaje_votos_positivos = int(porcentaje_votos_positivos.get("title").replace("%",""))
        else:
            porcentaje_votos_positivos = 0
        precio = re.compile('\d+,\d+').search(s.find("span", class_="price").string.strip()).group()
        precio = float(precio.replace(',','.'))
        if precio is not None:
            precio = float(precio)
        else:
            precio = 0.00
        print(precio)
        tematicas = s.find("div",attrs={"data-th":"TemÃ¡tica"})
        if tematicas:
            tematicas = tematicas.string.strip()
        else:
            tematicas = "Desconocida"
        complejidad = s.find("div",attrs={"data-th":"Complejidad"})
        if complejidad:
            complejidad = complejidad.string.strip()
        else:
            complejidad = "Desconocida"
        print(complejidad)
        conn.execute(
            """INSERT INTO JUEGO (TITULO, PORCENTAJE_VOTOS_POSITIVOS, PRECIO, TEMATICAS, COMPLEJIDAD) VALUES (?,?,?,?,?)""",
            (titulo, porcentaje_votos_positivos, precio, tematicas, complejidad))

    conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM JUEGO")
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()      
        
        
        
def listar_juegos():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT * FROM JUEGO")
    listar(cursor)     
    conn.close

def listar_mejores_juegos():
    conn = sqlite3.connect('juegos.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT * FROM JUEGO WHERE  PORCENTAJE_VOTOS_POSITIVOS > 90 ORDER BY  PORCENTAJE_VOTOS_POSITIVOS DESC")
    listar(cursor)     
    conn.close

def listar(cursor):      
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        s = 'JUEGO: ' + row[0]
        lb.insert(END, s)
        lb.insert(END, "------------------------------------------------------------------------")
        s = "     PORCENTAJE DE VOTOS POSITIVOS: " + str(row[1]) + ' | PRECIO: ' + str(row[2])+ ' | TEMATICA: ' + row[3] + ' | COMPLEJIDAD: ' + row[4]
        lb.insert(END, s)
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

        
        
        
def ventana_principal():
    raiz = Tk()

    menu = Menu(raiz)

    raiz.geometry("800x400")
    raiz.title("Juegos de mesa")

    # DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command = cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    # LISTAR
    menulistar = Menu(menu, tearoff=0) 
    menulistar.add_command(label="Juegos", command = listar_juegos)
    menulistar.add_command(label="Mejores Juegos", command = listar_mejores_juegos)
    menu.add_cascade(label="Listar", menu=menulistar)

    # BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Juegos por temática")
    menubuscar.add_command(label="Juegos por complejidad")
    menu.add_cascade(label="Buscar", menu=menubuscar)

    # Configurar el menú
    raiz.config(menu=menu)

    # Ejecutar la ventana principal
    raiz.mainloop()


if __name__ == "__main__":
    ventana_principal()
