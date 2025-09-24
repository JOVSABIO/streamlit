import streamlit as st
import pandas as pd
import requests
from io import StringIO

# Configuración básica
st.set_page_config(page_title="Mapa Accidentes Medellín", layout="wide")
st.title("🗺️ Mapa de Accidentes Medellín")

# Verificar dependencias
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Error importando dependencias: {e}")
    FOLIUM_AVAILABLE = False

# Función para cargar datos
def cargar_datos(link):
    try:
        st.write("🔗 Procesando enlace...")
        
        # Extraer ID del enlace
        if 'id=' in link:
            file_id = link.split('id=')[1].split('&')[0]
        elif '/d/' in link:
            file_id = link.split('/d/')[1].split('/')[0]
        else:
            st.error("Formato de enlace no reconocido")
            return None
        
        st.write(f"📁 File ID: {file_id}")
        
        url = f'https://drive.google.com/uc?id={file_id}&export=download'
        st.write("📥 Descargando archivo...")
        
        response = requests.get(url)
        response.raise_for_status()
        
        st.write("📊 Leyendo CSV...")
        
        # Intentar diferentes encodings
        try:
            df = pd.read_csv(StringIO(response.text))
        except:
            df = pd.read_csv(StringIO(response.content.decode('latin-1')))
        
        st.write(f"✅ CSV cargado: {len(df)} filas, {len(df.columns)} columnas")
        st.write(f"📋 Columnas: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error cargando datos: {str(e)}")
        return None

# Sidebar
with st.sidebar:
    st.header("📁 Cargar Datos")
    
    # ENLACE CORRECTO - USA ESTE FORMATO
    enlace = st.text_input(
        "Enlace de Google Drive:",
        value='https://drive.google.com/uc?id=1R5JxWJZK_OvFYdGmE2mG3wUhFRb7StdD&export=download'
    )
    
    if st.button("🚀 Cargar Datos"):
        if enlace:
            datos = cargar_datos(enlace)
            if datos is not None:
                st.session_state.datos = datos
                st.session_state.datos_cargados = True
                st.success("✅ ¡Datos cargados correctamente!")
            else:
                st.session_state.datos_cargados = False
        else:
            st.warning("⚠️ Por favor ingresa un enlace")

# Mostrar estado de dependencias
if not FOLIUM_AVAILABLE:
    st.error("""
    ❌ Folium no está disponible. Por favor verifica que tu requirements.txt tenga:
    ```
    folium==0.14.0
    streamlit-folium==0.14.0
    ```
    """)

# Verificar si hay datos cargados
if 'datos_cargados' not in st.session_state or not st.session_state.datos_cargados:
    st.info("""
    👆 **Instrucciones:**
    1. Asegúrate de que tu archivo en Google Drive sea público
    2. Copia el enlace de compartir
    3. Pega el enlace en el campo de arriba
    4. Haz clic en 'Cargar Datos'
    
    **Formato correcto:** `https://drive.google.com/uc?id=TU_FILE_ID`
    """)
    st.stop()

# Procesar datos
datos = st.session_state.datos
st.success(f"📊 Datos cargados: {len(datos)} filas")

# Mostrar información del dataset
st.subheader("📋 Información del Dataset")
st.write(f"**Columnas:** {list(datos.columns)}")
st.write(f"**Primeras filas:**")
st.dataframe(datos.head(10))

# Buscar columnas de coordenadas
st.subheader("🔍 Buscando coordenadas...")

# Intentar encontrar la columna de ubicación
location_column = None
for col in datos.columns:
    if 'LOCATION' in col.upper():
        location_column = col
        break

if not location_column:
    st.error("❌ No se encontró la columna 'LOCATION' en el dataset")
    st.write("**Columnas disponibles:**", list(datos.columns))
    st.stop()

st.write(f"✅ Columna de ubicación encontrada: '{location_column}'")

# Procesar coordenadas
puntos = []
coordenadas_invalidas = 0

for i, fila in datos.iterrows():
    try:
        location_value = str(fila[location_column])
        
        # Limpiar y procesar el formato [lon, lat]
        if location_value.startswith('[') and location_value.endswith(']'):
            location_clean = location_value.strip('[]')
            partes = location_clean.split(',')
            
            if len(partes) == 2:
                lon = float(partes[0].strip())
                lat = float(partes[1].strip())
                
                # Validar que estén en Medellín
                if 6.0 <= lat <= 6.5 and -76.0 <= lon <= -75.0:
                    puntos.append({'lat': lat, 'lon': lon, 'fila': i})
                else:
                    coordenadas_invalidas += 1
            else:
                coordenadas_invalidas += 1
        else:
            coordenadas_invalidas += 1
            
    except:
        coordenadas_invalidas += 1

st.success(f"📍 {len(puntos)} coordenadas válidas encontradas")
if coordenadas_invalidas > 0:
    st.warning(f"⚠️ {coordenadas_invalidas} coordenadas inválidas omitidas")

# Crear mapa si hay puntos válidos
if puntos and FOLIUM_AVAILABLE:
    st.subheader("🗺️ Mapa de Accidentes")
    
    # Crear mapa centrado en Medellín
    mapa = folium.Map(location=[6.2442, -75.5812], zoom_start=12)
    
    # Agregar marcadores
    for punto in puntos[:1000]:  # Limitar a 1000 puntos para mejor rendimiento
        folium.Marker(
            [punto['lat'], punto['lon']],
            popup=f"Accidente {punto['fila']}",
            icon=folium.Icon(color='red', icon='car', prefix='fa')
        ).add_to(mapa)
    
    # Mostrar mapa
    st_folium(mapa, width=1200, height=600)
    
    # Mostrar estadísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total accidentes", len(puntos))
    with col2:
        st.metric("Coordenadas inválidas", coordenadas_invalidas)
    with col3:
        st.metric("Porcentaje válido", f"{(len(puntos)/(len(puntos)+coordenadas_invalidas))*100:.1f}%")
        
elif not FOLIUM_AVAILABLE:
    st.error("No se puede mostrar el mapa - Folium no está disponible")
else:
    st.error("No hay coordenadas válidas para mostrar en el mapa")

# Mostrar ejemplos de coordenadas procesadas
if puntos:
    st.subheader("📍 Ejemplos de coordenadas")
    for i, punto in enumerate(puntos[:5]):
        st.write(f"{i+1}. Lat: {punto['lat']:.6f}, Lon: {punto['lon']:.6f}")
