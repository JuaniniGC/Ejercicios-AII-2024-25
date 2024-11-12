#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re, os, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD, ID, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from whoosh.query import Every

dirindex = "Index"

# almacena cada receta en un documento de un Índice. Usa la función extraer_peliculas() para obtener la lista de peliculas
def almacenar_datos():
    # define el esquema de la informaciÃón
    schem = Schema(titulo=TEXT(stored=True, phrase=False), comensales=NUMERIC(stored=True),
                   autor=KEYWORD(stored=True, commas=True, lowercase=True), fecha=DATETIME(stored=True),
                   caracteristicas=KEYWORD(stored=True, commas=True, lowercase=True),
                   introduccion=KEYWORD(stored=True, commas=True, lowercase=True))

    # eliminamos el directorio del Ã­ndice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")

    # creamos el Índice
    ix = create_in("Index", schema=schem)
    # creamos un writer para poder aÃ±adir documentos al indice
    writer = ix.writer()
    i = 0
    lista = extraer_recetas()
    for receta in lista:
        # añaade cada receta de la lista al índice
        writer.add_document(titulo=str(receta[0]), comensales=receta[1], autor=str(receta[2]),
                            fecha=receta[3], caracteristicas=str(receta[4]), introduccion=str(receta[5]))
        i += 1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado " + str(i) + " recetas")

def extraer_recetas():
    import locale #para activar las fechas en formato español
    locale.setlocale(locale.LC_TIME, "es_ES")
    
    lista=[]
    f = urllib.request.urlopen("https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html")
    s = BeautifulSoup(f,"lxml")
    l= s.find_all("div", class_=['resultado','link'])
    for i in l:
        titulo = i.a.string.strip()
        comensales = i.find("span",class_="comensales")
        if comensales:
            comensales = int(comensales.string.strip())
        else:
            comensales=-1
        
        f1 = urllib.request.urlopen(i.find('a')['href'])
        s1 = BeautifulSoup(f1,"lxml")
        autor = s1.find("div", class_='nombre_autor').a.string.strip()
        fecha = s1.find("div", class_='nombre_autor').find('span', class_="date_publish").string
        fecha = fecha.replace('Actualizado:','').strip()
        fecha = datetime.strptime(fecha, "%d %B %Y")
        introduccion = s1.find("div", class_="intro").text
        caracteristicas = s1.find("div", class_="properties inline")
        if caracteristicas:
            caracteristicas = caracteristicas.text.replace("Características adicionales:","")
            caracteristicas = ",".join([c.strip() for c in caracteristicas.split(",")] )     
        else:
            caracteristicas = "sin definir"
        lista.append((titulo, comensales, autor, fecha, caracteristicas,introduccion))
    return lista

# : título, número de comensales, autor, fecha de actualización, características adicionales e introducción
def listar(results):      
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in results:
        lb.insert(END,"Título: "+row['titulo']+"\n")
        lb.insert(END,"Comensales: "+str(row['comensales'])+"\n")
        lb.insert(END,"Autor: "+row['autor']+"\n")
        lb.insert(END,"Fecha: "+str(row['fecha'])+"\n")
        lb.insert(END,"Características: "+row['caracteristicas']+"\n")
        lb.insert(END,"Introducción: "+row['introduccion']+"\n")
        lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)
    
def listar_todas():
    respuesta = messagebox.askyesno("Listar", "¿Desea listar todas las recetas?")
    if respuesta:
        ix=open_dir(dirindex)
        with ix.searcher() as searcher:
            query = Every()
            results = searcher.search(query)
            listar(results)

def imprimir_lista_titulo(cursor):
    v = Toplevel()
    v.title("Recetas de Aperitivos y Tapas")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row['titulo'] + ":\n")
        lb.insert(END,"    Introduccion: "+ str(row['introduccion']))
        lb.insert(END,"------------------------------------------------------------------------\n")
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def buscar_por_titulo():
    def mostrar_lista(event):
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = MultifieldParser(["titulo", "introduccion"], ix.schema)
            query = query.parse('"'+str(en.get())+'"')  
            results = searcher.search(query,limit=10) #solo devuelve los 10 primeros
            imprimir_lista_titulo(results)
    
    v = Toplevel()
    v.title("Busqueda por Titulo o Introduccion")
    l = Label(v, text="Introduzca la frase o palabra a buscar:")
    l.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def obtener_caracteristicas():
    ix = open_dir(dirindex)
    caracteristicas_set = set()  # Usamos un set para evitar duplicados

    with ix.searcher() as searcher:
        query = Every()
        results = searcher.search(query)
        
        # Recorrer todas las recetas y recolectar las características
        for result in results:
            caracteristicas = result['caracteristicas'].split(",")
            for caracteristica in caracteristicas:
                caracteristica = caracteristica.replace("Características adicionales:","")
                caracteristicas_set.add(caracteristica.strip())

    return sorted(caracteristicas_set)

def buscar_por_caracteristicas_y_titulo():
    def mostrar_lista(event):
        ix = open_dir("Index")
        with ix.searcher() as searcher:
            # Obtener el valor del Spinbox (característica) y del Entry (título)
            caracteristica = spin.get()
            titulo = en.get()

            # Crear una consulta que combine ambas búsquedas
            parser = MultifieldParser(["caracteristicas", "titulo"], ix.schema, group=OrGroup)
            query = parser.parse(f'caracteristicas:"{caracteristica}" AND titulo:"{titulo}"')

            # Ejecutar la búsqueda
            results = searcher.search(query, limit=10)  # solo devuelve los 10 primeros
            listar(results)

    caracteristicas = obtener_caracteristicas()
    v = Toplevel()
    v.title("Búsqueda por Características y Título")

    # Etiquetas y widgets de entrada
    Label(v, text="Seleccione una característica:").pack(side=LEFT)
    spin = Spinbox(v, values=caracteristicas, width=50)
    spin.pack(side=LEFT)

    Label(v, text="Introduzca el título a buscar:").pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)  # Ejecutar búsqueda al presionar Enter
    en.pack(side=LEFT)

def ventana_principal():
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command = almacenar_datos)
    menudatos.add_command(label="Listar", command = listar_todas)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Titulo/Introduccion", command=buscar_por_titulo)
    menubuscar.add_command(label="Fecha")
    menubuscar.add_command(label="Características y Título", command=buscar_por_caracteristicas_y_titulo)
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()


if __name__ == "__main__":
    ventana_principal()