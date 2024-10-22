#encoding:utf-8

import sqlite3
from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import re
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def extraer_jornadas():
    f = urllib.request.urlopen("http://resultados.as.com/resultados/futbol/primera/2023_2024/calendario/")
    s = BeautifulSoup(f,"lxml")
    
    l = s.find_all("div", class_= ["cont-modulo","resultados"])
    return l


def imprimir_lista(cursor):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    jornada=0
    for row in cursor:
        if row[0] != jornada:
            jornada=row[0]
            lb.insert(END,"\n")
            s = 'JORNADA '+ str(jornada)
            lb.insert(END,s)
            lb.insert(END,"-----------------------------------------------------")
        s = "     " + row[1] +' '+ str(row[3]) +'-'+ str(row[4]) +' '+  row[2]
        lb.insert(END,s)
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)
 
def almacenar_bd():
    conn = sqlite3.connect('as.db')
    conn.text_factory = str  # para evitar problemas con el conjunto de caracteres que maneja la BD
    conn.execute("DROP TABLE IF EXISTS JORNADAS") 
    conn.execute('''CREATE TABLE JORNADAS
       (JORNADA       INTEGER NOT NULL,
       LOCAL          TEXT    NOT NULL,
       VISITANTE      TEXT    NOT NULL,
       GOLES_L        INTEGER    NOT NULL,
       GOLES_V        INTEGER NOT NULL,
       LINK           TEXT);''')
    l = extraer_jornadas()
    for i in l:
        jornada = int(re.compile('\d+').search(i['id']).group(0))
        partidos = i.find_all("tr",id=True)
        for p in partidos:
            equipos= p.find_all("span",class_="nombre-equipo")
            local = equipos[0].string.strip()
            visitante = equipos[1].string.strip()
            resultado_enlace = p.find("a",class_="resultado")
            goles=re.compile('(\d+).*(\d+)').search(resultado_enlace.string.strip())
            goles_l=goles.group(1)
            goles_v=goles.group(2)
            link = resultado_enlace['href']
                
            conn.execute("""INSERT INTO JORNADAS VALUES (?,?,?,?,?,?)""",(jornada,local,visitante,goles_l,goles_v,link))
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM JORNADAS")
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def listar_bd():
    conn = sqlite3.connect('as.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM JORNADAS ORDER BY JORNADA")
    imprimir_lista(cursor)
    conn.close()
    

def buscar_jornada():
    def listar_busqueda(event):
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        s =  int(en.get())
        cursor = conn.execute("""SELECT * FROM JORNADAS WHERE JORNADA = ?""",(s,)) 
        imprimir_lista(cursor)       
        conn.close()
    
    conn = sqlite3.connect('as.db')
    conn.text_factory = str
    cursor= conn.execute("""SELECT DISTINCT JORNADA FROM JORNADAS""")
    valores=[i[0] for i in cursor]
    conn.close()
    
    v = Toplevel()
    lb = Label(v, text="Seleccione la jornada: ")
    lb.pack(side = LEFT)
    en = Spinbox(v,values=valores,state="readonly")
    en.bind("<Return>", listar_busqueda)
    en.pack(side = LEFT)


def estadistica_jornada():
    def listar_estadistica(event):
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        s =  int(en.get())
        cursor = conn.execute("""SELECT SUM(GOLES_L)+SUM(GOLES_V) FROM JORNADAS WHERE JORNADA = ?""",(s,)) 
        total_goles = cursor.fetchone()[0]
        cursor = conn.execute("""SELECT GOLES_L,GOLES_V FROM JORNADAS WHERE JORNADA = ?""",(s,))
        empates=0
        locales=0
        visitantes=0
        for g in cursor:
            if g[0] == g[1]:
                empates +=1 
            elif g[0] > g[1]:
                locales +=1
            else:
                visitantes +=1          
        conn.close()
        
        s = "TOTAL GOLES JORNADA : " + str(total_goles)+ "\n\n" + "EMPATES : " + str(empates) + "\n" + "VICTORIAS LOCALES : " + str(locales) + "\n" + "VICTORIAS VISITANTES : " + str(visitantes)
        v = Toplevel()
        lb = Label(v, text=s) 
        lb.pack()
        
    conn = sqlite3.connect('as.db')
    conn.text_factory = str
    cursor= conn.execute("""SELECT DISTINCT JORNADA FROM JORNADAS""")
    valores=[i[0] for i in cursor]
    conn.close()
    
    v = Toplevel()
    lb = Label(v, text="Seleccione la jornada: ")
    lb.pack(side = LEFT)  
    en = Spinbox(v, values=valores, state="readonly" )
    en.bind("<Return>", listar_estadistica)
    en.pack(side = LEFT)
    


   
def buscar_goles():
    
    def et_span_no_class(tag):
        # funcion para cpmprobar si una etiqueta es span y no tiene atributo class
        return tag.name=="span" and not tag.has_attr('class')
    
    def mostrar_equipo_l():
        #actualiza la lista de los equipos que juegan como local en la jornada seleccionada
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        cursor= conn.execute("""SELECT LOCAL FROM JORNADAS WHERE JORNADA=? """,(int(en_j.get()),))
        en_l.config(values=[i[0] for i in cursor])
        conn.close()
        
    def mostrar_equipo_v():
        #actualiza el equipo que juega como visitante en la jornada y equipo local seleccionados
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        cursor = conn.execute("""SELECT VISITANTE FROM JORNADAS WHERE JORNADA=? AND LOCAL LIKE ?""",(int(en_j.get()),en_l.get()))
        en_v.config(textvariable=vis.set(cursor.fetchone()[0]))
        conn.close
        
    def cambiar_jornada():
        #se invoca cuando cambia la jornada
        mostrar_equipo_l()
        mostrar_equipo_v()
            
    def listar_busqueda():
        conn = sqlite3.connect('as.db')
        conn.text_factory = str
        cursor = conn.execute("""SELECT LINK,LOCAL,VISITANTE FROM JORNADAS WHERE JORNADA=? AND LOCAL LIKE ? AND VISITANTE LIKE ?""",(int(en_j.get()),en_l.get(),en_v.get()))
        partido = cursor.fetchone()
        enlace = partido[0]
        conn.close()
        f = urllib.request.urlopen(enlace)
        so = BeautifulSoup(f,"lxml")
        #buscamos los goles del equipo local
        l = so.find("div", class_="is-local").find("div", class_="scr-hdr__scorers").find_all(et_span_no_class)
        s=""
        for g in l:
            s = s + g.string.strip()
        #buscamos los goles del equipo visitante
        l = so.find("div", class_="is-visitor").find("div", class_="scr-hdr__scorers").find_all(et_span_no_class)
        s1=""
        for g in l:
            s1 = s1 + g.string.strip()
        
        goles= partido[1] + " : " + s + "\n" + partido[2] + " : " + s1
                      
        v = Toplevel()
        lb = Label(v, text=goles) 
        lb.pack()
    
    conn = sqlite3.connect('as.db')
    conn.text_factory = str
    #lista de jornadas para la spinbox de seleccion de jornada
    cursor= conn.execute("""SELECT DISTINCT JORNADA FROM JORNADAS""")
    valores_j=[int(i[0]) for i in cursor]
    #lista de los equipos que juegan como local en la jornada seleccionada
    cursor= conn.execute("""SELECT LOCAL FROM JORNADAS WHERE JORNADA=?""",(int(valores_j[0]),))
    valores_l=[i[0] for i in cursor]
    conn.close()
    
    v = Toplevel()
    lb_j = Label(v, text="Seleccione jornada: ")
    lb_j.pack(side = LEFT)
    en_j = Spinbox(v,values=valores_j,command=cambiar_jornada,state="readonly")
    en_j.pack(side = LEFT)
    lb_l = Label(v, text="Seleccione equipo local: ")
    lb_l.pack(side = LEFT)
    en_l = Spinbox(v,values=valores_l,command=mostrar_equipo_v,state="readonly")
    en_l.pack(side = LEFT)
    lb_v = Label(v, text="Equipo visitante: ")
    lb_v.pack(side = LEFT)
    vis=StringVar() #variable para actualizar el equipo visitante 
    en_v = Entry(v,textvariable=vis,state=DISABLED)
    en_v.pack(side = LEFT)
    mostrar_equipo_v() #funcion para mostrar el equipo visitante en funcion de la jornada y el local
    buscar = Button(v, text="Buscar goles", command=listar_busqueda)
    buscar.pack(side=BOTTOM)


    
def ventana_principal():
    top = Tk()
    almacenar = Button(top, text="Almacenar Resultados", command = almacenar_bd)
    almacenar.pack(side = TOP)
    listar = Button(top, text="Listar Jornadas", command = listar_bd)
    listar.pack(side = TOP)
    Buscar = Button(top, text="Buscar Jornada", command = buscar_jornada)
    Buscar.pack(side = TOP)
    Buscar = Button(top, text="EstadÃ­sticas Jornada", command = estadistica_jornada)
    Buscar.pack(side = TOP)
    Buscar = Button(top, text="Buscar Goles", command = buscar_goles)
    Buscar.pack(side = TOP)
    top.mainloop()
    

if __name__ == "__main__":
    ventana_principal()


