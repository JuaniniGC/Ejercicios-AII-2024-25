from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import re

# lineas para evitar error SSL
import os, ssl


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

base_url = "https://www.xvideos.com"
pages = 5

def cargar():
    respuesta = messagebox.askyesno(
        title="Cargar",
        message="¿Desea cargar los datos? Esta operación puede ser lenta.",
        icon="question",
    )
    if respuesta:
        store_bd()

def extract_data():
    lista=[]
    for p in range(0,pages):
        if (p == 0):
            url= base_url
        else:
            url = base_url + "/new/" + str(p)
        html = urllib.request.urlopen(url)
        soup = BeautifulSoup(html,"lxml")      
        lista = []
        tables = soup.find_all("div", class_= "thumb-inside")
        for table in tables:
            enlace_div = table.a["href"].strip()
            enlace_local = base_url + enlace_div
            print (enlace_local)
            html_local = urllib.request.urlopen(enlace_local)
            soup_local = BeautifulSoup(html_local,"lxml")
            titulo = soup_local.find("h2", class_="page-title")[0].re
            print (titulo)

    return lista


def store_bd():
    conn = sqlite3.connect('videos.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS VIDEOS")
    conn.execute(
        """CREATE TABLE VIDEOS
                 (NOMBRE                   	TEXT NOT NULL,
                 DURACION                  	INTEGER,
                 CANAL                  		TEXT,
                 VISUALIZACIONES           	INTEGER,
                 ETIQUETAS          				TEXT,
                 VOTOS_POSITIVOS            INTEGER,
                 VOTOS_NEGATIVOS      			INTEGER,
                 COMENTARIOS                INTEGER);"""
    )

    for i in extract_data():
        print("-------------------")

    conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM VIDEOS")
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()

def ventana_principal():
    # Crear la ventana principal
    ventana = Tk()
    ventana.title("Xvideos")
    ventana.geometry("300x210")

    # Crear los 5 botones y asignarles las funciones correspondientes
    boton1 = Button(ventana, text="Almacenar Resultados", command=cargar)
    boton1.pack(pady=5)

    # Iniciar el bucle de la ventana
    ventana.mainloop()

if __name__ == "__main__":
    ventana_principal()