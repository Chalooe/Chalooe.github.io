import streamlit as st
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
import requests as rq
import json
#
# --- Cabecera ---
col1, col2 = st.columns([1, 4])  # proporción ancho de columnas
with col1:
    st.image(
        "https://tr.rbxcdn.com/180DAY-f783c31a43c5367156b46c524642f8ac/256/256/Image/Webp/noFilter",
        width=100
    )

with col2:
    st.title("Dashboard Lectoworld")
    st.subheader("Bienvenido al sistema de monitoreo")
#
#nombre = st.text_input("Cual es tu nombre?")
#st.write(f"Hola, {nombre}!")
#
##xd
#opcion = st.selectbox("Elige tu equipo:", {"1. xd", "2. xd", "3. xd"})
#st.write(f"Elegiste, {opcion}!")
#
#funciones
def obtener_datos_api(nombre_archivo):
    """
    Llama a la API Lambda para obtener los datos de un archivo JSON en S3.
    Parámetros:
        nombre_archivo (str): Nombre del archivo en S3 (sin extensión .json)
    Retorna:
        list: Lista de registros contenidos en el JSON, o lista vacía si no hay datos.
    """
    url = "https://ki5ndjdhu74cn532ahazohft3m0kygti.lambda-url.us-east-2.on.aws/"
    params = {"nombreArchivo": nombre_archivo}

    try:
        r = rq.get(url, params=params)
        if r.status_code == 200:
            return r.json().get("archivos", [])
        else:
            print(f"Error {r.status_code}: {r.text}")
            return []
    except Exception as e:
        print(f"Error al llamar a la API: {e}")
        return []

#
#
jugadores = obtener_datos_api("Jugadores")
df_jugadores = pd.DataFrame(jugadores[0]["contenido"])
#
# Crear un diccionario {id: nombre}
mapa_jugadoresN = dict(zip(df_jugadores["id"].astype(str), df_jugadores["nombre"]))
mapa_jugadoresU = dict(zip(df_jugadores["id"].astype(str), df_jugadores["userName"]))
#
#graficas
actividadUsuario = obtener_datos_api("ActividadUsuario")
if actividadUsuario:
    df = pd.DataFrame(actividadUsuario[0]["contenido"])
    #st.dataframe(df)

    # Convertir 'fecha' a datetime y extraer solo el día
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['dia'] = df['fecha'].dt.date

    # --- Gráfico 1: Intentos por día ---
    df_dia = df.groupby('dia').size().reset_index(name='intentos')
    st.subheader("Intentos por día")
    st.dataframe(df_dia)
    st.line_chart(df_dia.set_index('dia')['intentos'])

    # --- Gráfico 2: Intentos por playerId ---
    df_player = df.groupby('playerId').size().reset_index(name='intentos')
    
    # Reemplazar playerId por nombre de jugador usando el diccionario
    df_player["Jugador"] = df_player["playerId"].astype(str).map(mapa_jugadoresN)

    st.subheader("Intentos por jugador")
    st.dataframe(df_player[["Jugador", "intentos"]])
    st.bar_chart(df_player.set_index("Jugador")["intentos"])
else:
    st.warning("No se encontraron datos.")


#
inventarios = obtener_datos_api("Inventario")
#
if inventarios:
    st.subheader("Inventario Jugador")
    # Unir inventarios
    dfs = []
    for inv in inventarios:
        df_temp = pd.DataFrame(inv["contenido"])
        df_temp["identificador"] = inv["id"]  # agregar id como fila
        # Buscar el nombre del jugador en el diccionario
        df_temp["nombre_jugador"] = mapa_jugadoresN.get(str(inv["id"]), "Desconocido")
        df_temp["userName_jugador"] = mapa_jugadoresU.get(str(inv["id"]), "Desconocido")
        dfs.append(df_temp)

        df_inv = pd.concat(dfs, ignore_index=True)
        
        # Mantener ambas columnas en el DataFrame
        df_inv["Usuario"] = df_inv["userName_jugador"]
        df_inv["Nombre"] = df_inv["nombre_jugador"]

        # Pivotear con múltiples índices
        tabla = df_inv.pivot_table(
            index=["identificador", "Usuario", "Nombre"],  # filas = inventario + usuario + nombre
            columns="nombre",                              # ítems del inventario
            values="cantidad",                             # cantidades
            fill_value=0
        ).reset_index()

    st.dataframe(tabla)