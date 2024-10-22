from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import re

import os
import ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

PAGINAS = 4
# datos de cada receta: título, fecha de publicación, categorías, ingredientes, valoración y número de votos


def extraer_recetas():
    lista = []

    for p in range(1, PAGINAS+1):
        url = "https://www.javirecetas.com/receta/recetas-faciles-cocina-facil/page/" + \
            str(p)
        f = urllib.request.urlopen(url)
        s = BeautifulSoup(f, "lxml")
        lista_urls = s.find_all("p", class_="sigueLeyendo")
        for url_receta in lista_urls:
            f_receta = urllib.request.urlopen(url_receta.a["href"])
            s_receta = BeautifulSoup(f_receta, "lxml")
            titulo = s_receta.find("div", class_="titulo").h1.a["title"]
            fecha = s_receta.find("span", class_="postDate").text
            categorias = s_receta.find("span", class_="categoriasReceta").find_all(
                "a")  # puede q haya q loopear
            lista_categorias = []
            for cat in categorias:
                lista_categorias.append(cat.text)
            ingredientes = s_receta.find("span", class_="ingredientesReceta").find_all(
                "a")  # puede q haya q loopear
            lista_ingredientes = []
            for ing in ingredientes:
                lista_ingredientes.append(ing.text)
            valoracion = s_receta.find(
                "div", class_="post-ratings").text.split(":")[1].split("-")[0].strip()
            num_votos = s_receta.find(
                "div", class_="post-ratings").text.split("-")[1].split(":")[1].replace(")", "").strip()
            receta = [titulo, fecha, lista_categorias,
                      lista_ingredientes, valoracion, num_votos]
            lista.append(receta)
    return lista


def almacenar_bd():
    conn = sqlite3.connect('recetas.db')
    # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS RECETAS")
    conn.execute('''CREATE TABLE RECETAS
       (TITULO        TEXT    NOT NULL,
       FECHA_DE_PUBLICACION          TEXT    ,
       CATEGORIAS         TEXT    ,
        INGREDIENTES        TEXT    ,
        VALORACION        INT    ,
       NUMERO_DE_VOTOS     INT);''')
    conn.execute("DROP TABLE IF EXISTS INGREDIENTES")
    conn.execute('''CREATE TABLE INGREDIENTES
       (NOMBRE            TEXT NOT NULL);''')
    conn.execute("DROP TABLE IF EXISTS CATEGORIAS")
    conn.execute('''CREATE TABLE CATEGORIAS
       (NOMBRE            TEXT NOT NULL);''')

    # METER DATOS DE SCRAPING
    lista_recetas = extraer_recetas()
    for receta in lista_recetas:
        categorias_str = ""
        for cat in receta[2]:
            categorias_str += cat + ","
        categorias_str = categorias_str[:-1]
        ingredientes_str = ""
        for ing in receta[3]:
            ingredientes_str += ing + ","
        ingredientes_str = ingredientes_str[:-1]
        # Convertir la fecha al formato YYYYMMDD
        fecha = receta[1]
        fecha_formateada = fecha.split(" - ")[2] + fecha.split(" - ")[1] + fecha.split(" - ")[0]
        
        receta_def = [receta[0], fecha_formateada, categorias_str,
                  ingredientes_str, receta[4], receta[5]]
        conn.execute("INSERT INTO RECETAS (TITULO,FECHA_DE_PUBLICACION,CATEGORIAS,INGREDIENTES,VALORACION,NUMERO_DE_VOTOS) \
              VALUES (?,?,?,?,?,?)", receta_def)
        for cat in receta[2]:
            conn.execute("INSERT INTO CATEGORIAS (NOMBRE) VALUES (?)", [cat])
        for ing in receta[3]:
            conn.execute("INSERT INTO INGREDIENTES (NOMBRE) VALUES (?)", [ing])

    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM RECETAS")
    cursor1 = conn.execute("SELECT COUNT(*) FROM INGREDIENTES")
    cursor2 = conn.execute("SELECT COUNT(*) FROM CATEGORIAS")
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) +
                        " recetas, " + str(cursor1.fetchone()
                                           [0]) + " ingredientes y "
                        + str(cursor2.fetchone()[0]) + " categorias")
    conn.close()


def imprimir_lista(cursor):
    v = Toplevel()
    v.title("RECETAS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END, row[0])
        #quiero que la fecha de publicacion se muestre en formato dd/mm/yyyy
        lb.insert(END, "    Fecha de publicacion: " + row[1][6:8] + "/" + row[1][4:6] + "/" + row[1][0:4])
        lb.insert(END, "    Categorias: " + row[2])
        lb.insert(END, "    Ingredientes: " + row[3])
        lb.insert(END, "    Valoración: " + str(row[4]))
        lb.insert(END, "    Número de votos: " + str(row[5]))
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)


def listar_ordenadas_votos():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute(
        "SELECT * FROM RECETAS ORDER BY NUMERO_DE_VOTOS DESC")
    imprimir_lista(cursor)
    conn.close()


def listar_top_3_recetas_por_valoracion():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute(
        "SELECT * FROM RECETAS ORDER BY VALORACION DESC LIMIT 3")
    imprimir_lista(cursor)
    conn.close()


def buscar_por_categoria():
    def listar(event):
        conn = sqlite3.connect('recetas.db')
        conn.text_factory = str
        cursor = conn.execute(
            "SELECT * FROM RECETAS where CATEGORIAS LIKE '%" + str(categoria.get()) + "%'")
        conn.close
        imprimir_lista(cursor)

    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT NOMBRE FROM CATEGORIAS")

    categorias = [c[0] for c in cursor]

    v = Toplevel()
    label = Label(v, text="Seleccione la categoria: ")
    label.pack(side=LEFT)
    categoria = Spinbox(v, width=30, values=categorias)
    categoria.bind("<Return>", listar)
    categoria.pack(side=LEFT)

    conn.close()


def buscar_por_ingredientes():
    def listar(event):
        conn = sqlite3.connect('recetas.db')
        conn.text_factory = str
        cursor = conn.execute(
            "SELECT * FROM RECETAS where INGREDIENTES LIKE '%" + str(ingrediente.get()) + "%'")
        conn.close
        imprimir_lista(cursor)

    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT NOMBRE FROM INGREDIENTES")

    ingredientes = [u[0] for u in cursor]

    v = Toplevel()
    label = Label(v, text="Seleccione el ingrediente: ")
    label.pack(side=LEFT)
    ingrediente = Spinbox(v, width=30, values=ingredientes)
    ingrediente.bind("<Return>", listar)
    ingrediente.pack(side=LEFT)

    conn.close()

def parse_fecha_entry(fecha_entry):
    #fecha entry = dd/mm/yyyy
    lista_fecha = fecha_entry.split("/")
    fecha_parseada= lista_fecha[2].strip()+lista_fecha[1].strip()+lista_fecha[0].strip()
    return fecha_parseada

def buscar_por_fecha_y_categoria():
    def listar_por_fecha_categoria():
        conn = sqlite3.connect('recetas.db')
        conn.text_factory = str
        fecha_parseada = parse_fecha_entry(entry.get())
        cursor = conn.execute("SELECT TITULO, FECHA_DE_PUBLICACION, CATEGORIAS FROM RECETAS WHERE FECHA_DE_PUBLICACION < '" +
                              fecha_parseada+ "' AND CATEGORIAS LIKE '%" + str(categoria.get()) + "%'")
        imprimir_busqueda_fecha_categoria(cursor)
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT NOMBRE FROM CATEGORIAS")
    categorias = [i[0] for i in cursor]
    v = Toplevel()
    label = Label(v, text="Introduzca la fecha: ")
    label.pack(side=LEFT)
    entry = Entry(v)
    print(entry.get())
    entry.pack(side=LEFT)
    label = Label(v, text="Seleccione la categoría: ")
    label.pack(side=LEFT)
    categoria = Spinbox(v, width=30, values=categorias)
    categoria.pack(side=LEFT)
    boton = Button(v, text="Buscar", command=listar_por_fecha_categoria)
    boton.pack(side=LEFT)
    conn.close()
    return 0


def imprimir_busqueda_fecha_categoria(cursor):
    v = Toplevel()
    v.title("RECETAS")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END, row[0])
        lb.insert(END, "    Fecha de publicacion: " + row[1][6:8] + "/" + row[1][4:6] + "/" + row[1][0:4])
        lb.insert(END, "    Categorias: " + row[2])
        lb.insert(END, "\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)


def ventana_principal():
    root = Tk()
    root.geometry("300x150")

    menubar = Menu(root)

    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=almacenar_bd)
    datosmenu.add_separator()
    datosmenu.add_command(label="Salir", command=root.quit)

    menubar.add_cascade(label="Datos", menu=datosmenu)

    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Todas ordenadas por votos",
                           command=listar_ordenadas_votos)
    buscarmenu.add_command(label="Mejor valoradas",
                           command=listar_top_3_recetas_por_valoracion)

    menubar.add_cascade(label="Listar", menu=buscarmenu)

    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Recetas por categoría",
                           command=buscar_por_categoria)
    buscarmenu.add_command(label="Recetas por ingrediente",
                           command=buscar_por_ingredientes)
    buscarmenu.add_command(
        label="Recetas por fecha y categoría", command=buscar_por_fecha_y_categoria)
    menubar.add_cascade(label="Buscar", menu=buscarmenu)

    root.config(menu=menubar)
    root.mainloop()


if __name__ == "__main__":
    ventana_principal()
