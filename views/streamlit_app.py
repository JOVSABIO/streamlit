import streamlit as st
import pandas as pd
import requests
from io import StringIO
import folium
from streamlit_folium import st_folium

# Configuración básica
st.set_page_config(page_title="Mapa Accidentes Medellín", layout="wide")
st.title("🗺️ Mapa de Accidentes Medellín")

# Función para cargar datos
def cargar_datos(link):
    try:
        # Extraer ID del enlace
        if 'id=' in link:
            file_id = link.split('id=')[1].split('&')[0]
        else:
            file_id = link.split('/d/')[1].split('/')[0]
        
        url = f'https://drive.google.com/uc?id={file_id}&export=download'
        response = requests.get(url)
        df = pd.read_csv(StringIO(response.text))
        return df
    except:
        return None

# Sidebar simple
with st.sidebar:
    st.header("📁 Cargar Datos")
    
    # REEMPLAZA ESTE ID CON EL TUYO
    enlace = st.text_input(
        "Enlace de Google Drive:",
        value='https://drive.google.com/uc?id=1R5JxWJZK_OvFYdGmE2mG3wUhFRb7StdD&export=download'
    )
    
    if st.button("Cargar Datos y Mostrar Mapa"):
        if enlace:
            with st.spinner("Cargando..."):
                datos = cargar_datos(enlace)
                if datos is not None:
                    st.session_state.datos = datos
                    st.success("✅ Datos cargados")
                else:
                    st.error("❌ Error al cargar")

# Si no hay datos, mostrar instrucción simple
if 'datos' not in st.session_state:
    st.info("👈 Ingresa el enlace de Google Drive y haz clic en 'Cargar Datos'")
    st.stop()

# Procesar datos simples
datos = st.session_state.datos
puntos = []

for i, fila in datos.iterrows():
    try:
        if 'LOCATION' in datos.columns:
            loc = str(fila['LOCATION']).strip('[]')
            lon, lat = map(float, loc.split(','))
            puntos.append({'lat': lat, 'lon': lon})
    except:
        continue

# Crear mapa simple
if puntos:
    st.success(f"📍 {len(puntos)} accidentes cargados")
    
    # Mapa centrado en Medellín
    mapa = folium.Map(location=[6.2442, -75.5812], zoom_start=12)
    
    # Agregar marcadores
    for punto in puntos:
        folium.Marker(
            [punto['lat'], punto['lon']],
            icon=folium.Icon(color='red', icon='car')
        ).add_to(mapa)
    
    # Mostrar mapa
    st_folium(mapa, width=1200, height=600)
    
    # Mostrar tabla simple
    st.subheader("📋 Datos (primeras 10 filas)")
    st.dataframe(datos.head(10))
    
else:
    st.error("No se encontraron coordenadas válidas en el archivo")
