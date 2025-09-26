import streamlit as st
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
import requests as rq
import json
import datetime
import altair as alt

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
#funcion de consulta al API
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
#Obtencion de jugadores
jugadores = obtener_datos_api("Jugadores")
df_jugadores = pd.DataFrame(jugadores[0]["contenido"])
#
# Crear un diccionario {id: nombre}
mapa_jugadoresN = dict(zip(df_jugadores["idJugador"].astype(str), df_jugadores["displayName"]))
mapa_jugadoresU = dict(zip(df_jugadores["idJugador"].astype(str), df_jugadores["nombre"]))
mapa_jugadoresN["0"] = "Ningún jugador"
#
libros = obtener_datos_api("Libros")
df_libros = pd.DataFrame(libros[0]["contenido"])
#
# Crear un diccionario {id: nombre}
mapa_librosN = dict(zip(df_libros["idLibro"].astype(str), df_libros["titulo"]))

#
#cambio de vista
def mostrar_vista(opcion, nombrejugador):    
    idJugador = [k for k, v in mapa_jugadoresN.items() if v == nombrejugador][0]
    idJugador = int(idJugador)

    if opcion == "Jugadores":
        df = df_jugadores
        #        
        df_jugadores['fecha'] = pd.to_datetime(df['ultimoIngreso'])
        df_jugadores['ultimoIngreso'] = df_jugadores['fecha'].dt.date
        df_jugadores['hora'] = df_jugadores['fecha'].dt.strftime("%I %p")
        df_jugadores['hora/Minuto'] = df_jugadores['fecha'].dt.strftime("%I:%M %p")
        df_jugadores['ver'] = "https://www.roblox.com/es/users/" + df_jugadores['idJugador'].astype(str) + "/profile"
        #
        st.subheader("Detalle jugadores registrados")
        columnas = ["displayName", "nombre", "ultimoIngreso", "hora/Minuto", "ver"]  # orden personalizado

        st.dataframe(df_jugadores[columnas])

        rachas = obtener_datos_api("Racha")
        if rachas:
            df = pd.DataFrame(rachas[0]["contenido"])
            if idJugador != 0:     
                df = df[df["idJugador"] == idJugador]

            if df.empty:
                st.subheader("* El jugador (" + nombrejugador + ") no tiene datos que mostrar")
            else:
                # Convertir 'fecha' a datetime y extraer solo el día
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['dia'] = df['fecha'].dt.date
                df['hora'] = df['fecha'].dt.strftime("%I %p")
                df['hora/Minuto'] = df['fecha'].dt.strftime("%I:%M %p")
                #agregar el campo jugador
                df["Jugador"] = df["idJugador"].astype(str).map(mapa_jugadoresN)

                
                # --- Gráfico 1: Libros por día ---
                st.subheader("Racha Jugador")
                
                tabla = df.pivot_table(
                    index=["idJugador", "Jugador"],  # filas = inventario + usuario + nombre
                    columns="tipo",                              # ítems del inventario
                    values="cantidad",                             # cantidades
                    fill_value=0
                ).reset_index()

                # Pasar a formato largo (tidy data)
                tabla_long = tabla.melt(
                    id_vars="Jugador",
                    value_vars=["actual", "maxima"],
                    var_name="Tipo",
                    value_name="Valor"
                )

                # Chart con barras agrupadas y ancho fijo
                chart = (
                    alt.Chart(tabla_long)
                    .mark_bar(width=20)  # todas las barras del mismo grosor
                    .encode(
                        x=alt.X("Jugador:N", axis=alt.Axis(title="Jugador")),
                        y=alt.Y("Valor:Q", axis=alt.Axis(title="Valor")),
                        color=alt.Color("Tipo:N", legend=alt.Legend(title="Tipo")),
                        xOffset="Tipo"  # hace que se agrupen lado a lado
                    )
                )

                st.altair_chart(chart, use_container_width=True)
        else:
            st.subheader("* No hay rachas registradas")

    elif opcion == "LibrosCompletados":
        librosCompletados = obtener_datos_api("libroCompletado")
        if librosCompletados:
            df = pd.DataFrame(librosCompletados[0]["contenido"])
            if idJugador != 0:     
                df = df[df["idJugador"] == idJugador]

            if df.empty:
                st.subheader("* El jugador (" + nombrejugador + ") no tiene datos que mostrar")
            else:
                # Convertir 'fecha' a datetime y extraer solo el día
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['dia'] = df['fecha'].dt.date
                df['hora'] = df['fecha'].dt.strftime("%I %p")
                df['hora/Minuto'] = df['fecha'].dt.strftime("%I:%M %p")
                #agregar el campo jugador
                df["Jugador"] = df["idJugador"].astype(str).map(mapa_jugadoresN)
                df["Libro"] = df["idLibro"].astype(str).map(mapa_librosN)

                
                # --- Gráfico 1: Libros por día ---
                st.subheader("Libros leidos por día")
                df_dia = df.groupby("dia").size().reset_index(name="cantidad")
                st.line_chart(df_dia.set_index('dia')['cantidad'])
                
                # --- Gráfico 2: Libros por hora ---
                st.subheader("Horas con mas libros leidos")
                df_hora = df.groupby("hora").size().reset_index(name="cantidad")
                st.bar_chart(df_hora.set_index('hora')['cantidad'])
                
                # --- Lista Detalle
                st.subheader("Detalle libros leidos")
                columnas = ["Jugador", "dia", "hora/Minuto", "Libro"]  # orden personalizado
                st.dataframe(df[columnas])

        else:
            st.subheader("* No hay libros completados registrados")
    elif opcion == "Intentos":
        intentos = obtener_datos_api("Intentos")
        if intentos:
            df = pd.DataFrame(intentos[0]["contenido"])
            if idJugador != 0:     
                df = df[df["idJugador"] == idJugador]

            if df.empty:
                st.subheader("* El jugador (" + nombrejugador + ") no tiene datos que mostrar")
            else:
                # Convertir 'fecha' a datetime y extraer solo el día
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['dia'] = df['fecha'].dt.date

                # --- Gráfico 1: Intentos por día ---
                st.subheader("Intentos por día")
                df_dia = df.groupby('dia').agg(
                    intentos= ("dia","count"),
                    intentos_correctos=("estado", lambda x: (x == 1).sum()),
                    intentos_fallidos=("estado", lambda x: (x == 0).sum())
                ).reset_index()
                st.line_chart(df_dia.set_index('dia')[['intentos', 'intentos_correctos', 'intentos_fallidos']])

                # --- Gráfico 2: Intentos por idJugador ---
                st.subheader("Intentos por jugador")
                df_resumen = df.groupby("idJugador").agg(
                    intentos_correctos=("estado", lambda x: (x == 1).sum()),
                    intentos_fallidos=("estado", lambda x: (x == 0).sum())
                ).reset_index()
                df_resumen["Jugador"] = df_resumen["idJugador"].astype(str).map(mapa_jugadoresN)
                st.bar_chart(df_resumen.set_index("Jugador")[["intentos_correctos", "intentos_fallidos"]])
        else:
            st.subheader("* No hay intentos registrados")
    elif opcion == "Permanencia": 
        permanencia = obtener_datos_api("Permanencia")
        if permanencia:
            df = pd.DataFrame(permanencia[0]["contenido"])

            if idJugador != 0:     
                df = df[df["idJugador"] == idJugador]

            if df.empty:
                st.subheader("* El jugador (" + nombrejugador + ") no tiene datos que mostrar")
            else:
                # Suponiendo que tiene un DataFrame con columnas:
                # jugador, fecha, evento ("ingreso"/"salida")
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['dia'] = df['fecha'].dt.date
                df['hora'] = df['fecha'].dt.strftime("%I %p")
                df['hora/Minuto'] = df['fecha'].dt.strftime("%I:%M %p")
                df["Jugador"] = df["idJugador"].astype(str).map(mapa_jugadoresN)

                # Ordenamos por jugador y fecha
                df = df.sort_values(['Jugador', 'fecha'])

                # Creamos una columna para emparejar ingresos con salidas
                df['next_event'] = df.groupby('Jugador')['tipo'].shift(-1)
                df['next_fecha'] = df.groupby('Jugador')['fecha'].shift(-1)

                # Filtramos solo las filas que son "ingreso" y cuya siguiente fila es "salida"
                df_sesiones = df[(df['tipo'] == 'ingreso') & (df['next_event'] == 'salida')].copy()

                # Calculamos duración de la sesión en minutos (puede cambiar a segundos si desea)
                df_sesiones['duracion'] = (df_sesiones['next_fecha'] - df_sesiones['fecha']).dt.total_seconds() / 60

                # El día es el del ingreso
                df_sesiones['dia'] = df_sesiones['fecha'].dt.date

                # Promedio de duración por día
                df_resumen = (
                    df_sesiones
                    .groupby('dia')
                    .agg(
                        tiempo_total=('duracion', 'sum'),
                        tiempo_maximo=('duracion', 'max'),
                        tiempo_promedio=('duracion', 'mean'),
                        sesiones=('duracion', 'count')
                    )
                    .reset_index()
                )
                
                df_xJugador = (
                    df_sesiones
                    .groupby(['idJugador', 'Jugador'])
                    .agg(
                        tiempo_total=('duracion', 'sum'),
                        tiempo_maximo=('duracion', 'max'),
                        tiempo_promedio=('duracion', 'mean'),
                        sesiones=('duracion', 'count')
                    )
                    .reset_index()
                )

                # Mostrar en Streamlit
                st.subheader("Promedio de permanencia por dia")
                st.line_chart(df_resumen.set_index("dia")[["tiempo_maximo", "tiempo_promedio", "sesiones"]])

                # --- Lista Detalle
                st.subheader("Detalle permanencia")
                st.dataframe(df_resumen)
                st.dataframe(df_xJugador)
        else:
            st.subheader("* No hay intentos registrados")
    elif opcion == "Inventario":        
        inventarios = obtener_datos_api("Inventario")
        #
        if inventarios:
            st.subheader("Inventario Jugador")
            # Unir inventarios
            dfs = []
            for inv in inventarios:                
                if idJugador == 0 or int(inv["id"]) == idJugador:
                    df_temp = pd.DataFrame(inv["contenido"])
                    # Buscar el nombre del jugador en el diccionario
                    df_temp["idJugador"] = inv["id"]
                    df_temp["Jugador"] = mapa_jugadoresN.get(str(inv["id"]), "Desconocido")
                    dfs.append(df_temp)
                    #
                    df_inv = pd.concat(dfs, ignore_index=True)
                    #
                    # Pivotear con múltiples índices
                    tabla = df_inv.pivot_table(
                        index=["idJugador", "Jugador"],  # filas = inventario + usuario + nombre
                        columns="nombre",                              # ítems del inventario
                        values="cantidad",                             # cantidades
                        fill_value=0
                    ).reset_index()

            if not dfs:
                st.subheader("* El jugador (" + nombrejugador + ") no tiene datos que mostrar")
            else:
                st.dataframe(tabla)
    elif opcion == "Minijuegos":
        minijuegosN = {
            "OH": "Ordena la Historia",
            "PE": "Palabras Enredadas"
        }
        minijuegos = obtener_datos_api("Minijuego")
        if minijuegos:
            df = pd.DataFrame(minijuegos[0]["contenido"])
            if idJugador != 0:     
                df = df[df["idJugador"] == idJugador]

            if df.empty:
                st.subheader("* El jugador (" + nombrejugador + ") no tiene datos que mostrar")
            else:
                # Convertir 'fecha' a datetime y extraer solo el día
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['dia'] = df['fecha'].dt.date
                df["Jugador"] = df["idJugador"].astype(str).map(mapa_jugadoresN)
                df["NombreMinijuego"] = df["minijuego"].astype(str).map(minijuegosN)

                
                # Promedio de duración por día
                df_resumenDia = (
                    df
                    .groupby(['minijuego', 'NombreMinijuego', 'dia'])
                    .agg(
                        interacciones=('dia', 'count')
                    )
                    .reset_index()
                )
                df_resumenJuego = (
                    df
                    .groupby(['minijuego','NombreMinijuego'])
                    .agg(
                        interacciones=('dia', 'count')
                    )
                    .reset_index()
                )

                #
                st.subheader("Interacciones con minijuegos por Dia")
                tabla = df_resumenDia.pivot_table(
                    index=["dia"],  # filas = inventario + usuario + nombre
                    columns="minijuego",                              # ítems del inventario
                    values="interacciones",                             # cantidades
                    fill_value=0
                ).reset_index()
                # Lista de columnas que desea graficar
                cols_deseadas = ["OH", "PE"]

                # Filtrar solo las columnas que sí existen en la tabla
                cols_existentes = [c for c in cols_deseadas if c in tabla.columns]

                # Solo graficar si hay al menos una columna válida
                if cols_existentes:
                    st.line_chart(tabla.set_index("dia")[cols_existentes])
                else:
                    st.warning("No hay columnas disponibles para graficar.")

                #
                st.subheader("Interacciones con minijuegos")
                st.dataframe(df_resumenJuego)

        else:
            st.subheader("* No hay minijuegos registrados")
    else:
        return ""
#
#opciones para la lsita de jugadores
opciones = [("0", mapa_jugadoresN["0"])] + [(k, v) for k, v in mapa_jugadoresN.items() if k != "0"]
#
opcion_vista = st.selectbox("Vista:", ["Jugadores", "LibrosCompletados", "Intentos", "Permanencia", "Inventario", "Minijuegos"])
opcion_jugador = st.selectbox("Jugador:", [v for _, v in opciones])

# Selector de año
#anio = st.number_input("Año", min_value=2000, max_value=2100, value=datetime.date.today().year)
# Selector de mes
#mes = st.selectbox("Mes", list(range(1, 13)), format_func=lambda x: datetime.date(1900, x, 1).strftime('%B'))

#
mostrar_vista(opcion_vista, opcion_jugador)