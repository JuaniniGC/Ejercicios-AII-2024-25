# encoding:utf-8

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

url = "http://resultados.as.com/resultados/futbol/primera/2023_2024/calendario/"


def extract_data():
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('div', class_='cont-modulo resultados')
    db = sqlite3.connect('matches.db')
    cursor = db.cursor()
    match_list = []
    # cada table es una sola jornada
    jornada = 1
    for table in tables:
        matches = table.find('tbody').find_all('tr')
        for match in matches:
            row = match.find('td', class_='col-resultado finalizado')
            names_split = row.a['title'].split('-')
            local = names_split[0].strip()
            visiting = names_split[1].strip()
            visiting.replace(' en directo', '')
            goals_split = row.a.text.split('-')
            local_goals = goals_split[0].strip()
            visiting_goals = goals_split[1].strip()
            link = row.a['href']
            html = urllib.request.urlopen(link)
            soup = BeautifulSoup(html, 'lxml')
            local_spans = soup.find(
                'div', class_='is-local').find('div', class_='scr-hdr__scorers').find_all('span')
            local_scorers_list = ", ".join(
                [local_span.text for local_span in local_spans])
            visiting_spans = soup.find(
                'div', class_='is-visitor').find('div', class_='scr-hdr__scorers').find_all('span')
            visiting_scorers_list = ", ".join(
                [visiting_span.text for visiting_span in visiting_spans])
            match_list.append((jornada, local, visiting, local_goals,
                               visiting_goals, local_scorers_list, visiting_scorers_list, link))
        jornada += 1
    return match_list


def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",
                                    message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if respuesta:
        almacenar_bd()


def almacenar_bd():
    conn = sqlite3.connect('furbo.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS PARTIDOS")
    conn.execute('''CREATE TABLE PARTIDOS
       (EQUIPO_LOCAL        TEXT NOT NULL,
        EQUIPO_VISITANTE    TEXT NOT NULL,
        GOLES_LOCAL         INTEGER,
        GOLES_VISITANTE     INTEGER,          
        JORNADA             INTEGER,
        LINK                TEXT,
        GOLEADORES_LOCAL          TEXT        ,
        GOLEADORES_VISITANTE          TEXT        
        );''')

    for i in extract_data():
        conn.execute(
            "INSERT INTO PARTIDOS (JORNADA, EQUIPO_LOCAL, EQUIPO_VISITANTE, GOLES_LOCAL, GOLES_VISITANTE, GOLEADORES_LOCAL, GOLEADORES_VISITANTE, LINK) VALUES (?,?,?,?,?,?,?,?)",
            i)

    conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM PARTIDOS")
    messagebox.showinfo("Base Datos",
                        "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def listar_partidos():
    conn = sqlite3.connect('furbo.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT * FROM PARTIDOS")
    imprimir_lista(cursor)
    conn.close()


def imprimir_lista(cursor):
    v = Toplevel()
    v.title("PARTIDOS DE LA TEMPORADA 23/24")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"JORNADA" + str(row[4]) + "\n-----------------------------------------\n")
        lb.insert(END, row[0]+" "+str(row[2])+" - "+str(row[3])+" "+row[1]+"\n")
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)


def imprimir_estadisticas(total_goles, empates, victorias_local, victorias_visitante):
    v = Toplevel()
    v.title("ESTADISTICAS DE LA JORNADA")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    lb.insert(END, "Total de goles: " + str(total_goles.fetchone()[0]) + "\n")
    lb.insert(END, "Empates: " + str(empates.fetchone()[0]) + "\n")
    lb.insert(END, "Victorias locales: " + str(victorias_local.fetchone()[0]) + "\n")
    lb.insert(END, "Victorias visitantes: " + str(victorias_visitante.fetchone()[0]) + "\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)


def buscar_por_jornada():
    def listar(event):
        conn = sqlite3.connect('furbo.db')
        conn.text_factory = str
        cursor = conn.execute("SELECT * FROM PARTIDOS where JORNADA LIKE " + str(jornada.get()))
        conn.close
        imprimir_lista(cursor)

    conn = sqlite3.connect('furbo.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT JORNADA FROM PARTIDOS")

    jornadas = [i[0] for i in cursor]

    v = Toplevel()
    label = Label(v, text="Seleccione la jornada: ")
    label.pack(side=LEFT)
    jornada = Spinbox(v, width=30, values=jornadas)
    jornada.bind("<Return>", listar)
    jornada.pack(side=LEFT)

    conn.close()


def estadisticas_jornada():
    def listar(event):
        conn = sqlite3.connect('furbo.db')
        conn.text_factory = str
        total_goles = conn.execute(
            "SELECT SUM(GOLES_LOCAL + GOLES_VISITANTE) FROM PARTIDOS where JORNADA LIKE '%" + str(jornada.get()) + "%'")
        empates = conn.execute("SELECT COUNT(*) FROM PARTIDOS where JORNADA LIKE '%" + str(
            jornada.get()) + "%' AND GOLES_LOCAL = GOLES_VISITANTE")
        victorias_local = conn.execute("SELECT COUNT(*) FROM PARTIDOS where JORNADA LIKE '%" + str(
            jornada.get()) + "%' AND GOLES_LOCAL > GOLES_VISITANTE")
        victorias_visitante = conn.execute("SELECT COUNT(*) FROM PARTIDOS where JORNADA LIKE '%" + str(
            jornada.get()) + "%' AND GOLES_LOCAL < GOLES_VISITANTE")
        conn.close
        imprimir_estadisticas(total_goles, empates, victorias_local, victorias_visitante)

    conn = sqlite3.connect('furbo.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT JORNADA FROM PARTIDOS")

    jornadas = [i[0] for i in cursor]

    v = Toplevel()
    label = Label(v, text="Seleccione la jornada: ")
    label.pack(side=LEFT)
    jornada = Spinbox(v, width=30, values=jornadas)
    jornada.bind("<Return>", listar)
    jornada.pack(side=LEFT)

    conn.close()


def imprimir_goles(cursor):
    v = Toplevel()
    v.title("GOLES DE LA JORNADA")
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,"Goles del equipo local: "+row[0] + "\n")
        lb.insert(END,"Goles del equipo visitante: "+row[1] + "\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)

def buscar_goles():
    # “Buscar Goles”, que muestre una ventana que permita al usuario seleccionar un
    # número de jornada y un equipo local de esa jornada (el equipo visitante se actualiza
    # automáticamente cuando cambie la jornada o el equipo local) y muestre en otra
    # ventana los goles que se produjeron (equipo: jugador y minuto). 
    def listar(event):
            conn = sqlite3.connect('furbo.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT GOLEADORES_LOCAL, GOLEADORES_VISITANTE FROM PARTIDOS where JORNADA LIKE '%" + str(jornada.get()) + "%' AND EQUIPO_LOCAL LIKE '%" + str(equipo_local.get()) + "%'")
            imprimir_goles(cursor)
    conn = sqlite3.connect('furbo.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT JORNADA FROM PARTIDOS")
    jornadas = [i[0] for i in cursor]
    cursor = conn.execute("SELECT DISTINCT EQUIPO_LOCAL FROM PARTIDOS")
    equipos = [i[0] for i in cursor]
    v = Toplevel()
    label = Label(v,text="Seleccione la jornada: ")
    label.pack(side=LEFT)
    jornada = Spinbox(v, width= 30, values=jornadas)
    jornada.bind("<Return>", listar)
    jornada.pack(side=LEFT)
    label = Label(v,text="Seleccione el equipo local: ")
    label.pack(side=LEFT)
    equipo_local = Spinbox(v, width= 30, values=equipos)
    equipo_local.bind("<Return>", listar)
    equipo_local.pack(side=LEFT)
    conn.close()


def ventana_principal():
    # Crear la ventana principal
    ventana = Tk()
    ventana.title("Furbo")
    ventana.geometry("300x210")

    # Crear los 5 botones y asignarles las funciones correspondientes
    boton1 = Button(ventana, text="Almacenar Resultados", command=cargar)
    boton1.pack(pady=5)

    boton2 = Button(ventana, text="Listar Jornadas", command=listar_partidos)
    boton2.pack(pady=5)

    boton3 = Button(ventana, text="Buscar Jornada", command=buscar_por_jornada)
    boton3.pack(pady=5)

    boton4 = Button(ventana, text="Estadisticas Jornada", command=estadisticas_jornada)
    boton4.pack(pady=5)

    boton5 = Button(ventana, text="Buscar Goles", command=buscar_goles)
    boton5.pack(pady=5)

    # Iniciar el bucle de la ventana
    ventana.mainloop()

if __name__ == "__main__":
    ventana_principal()
