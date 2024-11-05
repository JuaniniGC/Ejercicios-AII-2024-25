#encoding:utf-8

from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
import re, shutil
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, NUMERIC, KEYWORD, ID, DATETIME
from whoosh.qparser import QueryParser, MultifieldParser


PAGINAS = 3  # nÃºmero de pÃ¡ginas

# lineas para evitar error SSL
import os, ssl

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",
                                    message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_datos()


def extraer_peliculas():
    lista = []

    for p in range(1, PAGINAS + 1):
        url = "https://www.elseptimoarte.net/estrenos/2024/"+ str(p) + "/"
        f = urllib.request.urlopen(url)
        s = BeautifulSoup(f, "lxml")

        lista_link_peliculas = s.find("ul", class_="elements").find_all("li")

        for link_pelicula in lista_link_peliculas:
            f = urllib.request.urlopen("https://www.elseptimoarte.net/" + link_pelicula.a['href'])
            s = BeautifulSoup(f, "lxml")
            datos = s.find("main", class_="informativo").find("section", class_="highlight").div.dl
            titulo_original = datos.find("dt", string="Título original").find_next_sibling("dd").string.strip()
            titulo = datos.find("dt", string="Título").find_next_sibling("dd").string.strip()
            estreno_españa = datetime.strptime(datos.find("dt", string="Estreno en España").find_next_sibling("dd").string.strip(),
                '%d/%m/%Y')
            pais = "".join(datos.find("dt", string="País").find_next_sibling("dd").stripped_strings)
            generos_director = s.find("div", id="datos_pelicula")
            generos = "".join(generos_director.find("p", class_="categorias").stripped_strings)
            director = "".join(generos_director.find("p", class_="director").stripped_strings)
            sinopsis = s.find("div", class_="description")
            if sinopsis.find("p"):
                sinopsis = "".join(sinopsis.p.stripped_strings)
            else:
                sinopsis = "".join(sinopsis)
            url_pag_detalle = link_pelicula

            lista.append((titulo_original, titulo, estreno_España, pais, generos, director, sinopsis, url_pag_detalle))

    return lista


def imprimir_lista(cursor):
    v = Toplevel()
    v.title("PELÍCULAS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END, row['titulo'])
        lb.insert(END, "    Título original: " + str(row['titulo_original']) + " â‚¬")
        lb.insert(END, "    Estreno en España: " + row['estreno_españa'])
        lb.insert(END, "    País: " + row['pais'])
        lb.insert(END, "    Géneros: " + row['generos'])
        lb.insert(END, "    Director: " + row['director'])
        lb.insert(END, "    Sinopsis: " + row['sinopsis'])
        lb.insert(END, "    Url página detalle: " + row['url_pag_detalle'])

        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

def almacenar_datos():
    # define el esquema de la información
    schem = Schema(titulo_original=TEXT(stored=True, phrase=False), titulo=TEXT(stored=True, phrase=False),
                   estreno_españa=DATETIME(stored=True), pais=TEXT(stored=True, phrase=False),
                   generos=KEYWORD(stored=True, commas=True), director=KEYWORD(stored=True, commas=True),
                   sinopsis=KEYWORD(stored=True, commas=True), url_pag_detalle=TEXT(stored=True))

    # eliminamos el directorio del Índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")

    # creamos el Índice
    ix = create_in("Index", schema=schem)
    # creamos un writer para poder aÃ±adir documentos al indice
    writer = ix.writer()
    i = 0
    lista = extraer_peliculas()
    for j in lista:
        # aÃ±ade cada juego de la lista al Índice
        #lista.append((titulo_original, titulo, estreno_españa, pais, generos, director, sinopsis, url_pag_detalle))

        writer.add_document(titulo_original=str(j[0]), titulo=str(j[1]), estreno_españa=str(j[2]), pais=str(j[3]),
                            director=str(j[4]), sinopsis=str(j[5]), url_pag_detalle=str(j[6]))
        i += 1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado " + str(i) + " películas")

def imprimir_lista_titulo(results):
    ventana_resultados = Toplevel()
    ventana_resultados.title("Resultados de la Búsqueda")

    for hit in results:
        titulo = hit.get("titulo", "Título no disponible")
        titulo_original = hit.get("titulo_original", "Título original no disponible")
        director = hit.get("director", "Director no disponible")
        
        texto = f"Título: {titulo}\nTítulo Original: {titulo_original}\nDirector: {director}\n{'-'*40}\n"
        etiqueta = Label(ventana_resultados, text=texto, justify=LEFT)
        etiqueta.pack(anchor='w')


def buscar_por_titulo():
    def mostrar_lista(event):
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = MultifieldParser(["titulo", "sinopsis"], ix.schema)
            query = query.parse('"'+str(en.get())+'"')  
            results = searcher.search(query,limit=10) #solo devuelve los 10 primeros
            imprimir_lista_titulo(results)
    
    v = Toplevel()
    v.title("Busqueda por Titulo o Sinopsis")
    l = Label(v, text="Introduzca la frase o palabra a buscar:")
    l.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def imprimir_lista_genero(results):
    ventana_resultados = Toplevel()
    ventana_resultados.title("Resultados de la Búsqueda")

    for hit in results:
        titulo = hit.get("titulo", "Título no disponible")
        titulo_original = hit.get("titulo_original", "Título original no disponible")
        pais = hit.get("pais", "Pais no disponible")
        
        texto = f"Título: {titulo}\nTítulo Original: {titulo_original}\nPais: {pais}\n{'-'*40}\n"
        etiqueta = Label(ventana_resultados, text=texto, justify=LEFT)
        etiqueta.pack(anchor='w')


def buscar_por_genero():
    def mostrar_lista(event):
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            query = QueryParser("genero", ix.schema).parse('"'+str(en.get())+'"')
            results = searcher.search(query,limit=10) #solo devuelve los 10 primeros
            imprimir_lista_genero(results)
    
    v = Toplevel()
    v.title("Busqueda por Genero")
    l = Label(v, text="Introduzca la frase o palabra a buscar:")
    l.pack(side=LEFT)
    en = Entry(v, width=75)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)

def ventana_principal():
    raiz = Tk()

    menu = Menu(raiz)

    #DATOS
    menudatos = Menu(menu, tearoff=0)
    menudatos.add_command(label="Cargar", command=cargar)
    menudatos.add_command(label="Salir", command=raiz.quit)
    menu.add_cascade(label="Datos", menu=menudatos)

    #BUSCAR
    menubuscar = Menu(menu, tearoff=0)
    menubuscar.add_command(label="Titulo", command=buscar_por_titulo)
    menubuscar.add_command(label="Genero")
    menubuscar.add_command(label="Fecha")
    menubuscar.add_command(label="Modificar Fecha")
    menu.add_cascade(label="Buscar", menu=menubuscar)

    raiz.config(menu=menu)

    raiz.mainloop()



if __name__ == "__main__":
    ventana_principal()
