import streamlit as st
import pandas as pd
import requests
from io import StringIO

# Configuración de la página
st.set_page_config(
    page_title="Mapa de Accidentes Medellín",
    page_icon="🚗",
    layout="wide"
)

# Estilos CSS mejorados
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.9;
    }
    .metric-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .filter-section {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_csv_from_drive(drive_link):
    """Cargar CSV desde Google Drive"""
    try:
        # Extraer file_id del enlace
        if 'id=' in drive_link:
            file_id = drive_link.split('id=')[1].split('&')[0]
        elif '/d/' in drive_link:
            file_id = drive_link.split('/d/')[1].split('/')[0]
        else:
            return None, "Formato de enlace no válido"
        
        # Crear enlace de descarga directa
        download_url = f'https://drive.google.com/uc?id=1R5JxWJZK_OvFYdGmE2mG3wUhFRb7StdD&export=download'
        
        # Descargar el archivo
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Leer el CSV directamente
        content = response.text
        try:
            df = pd.read_csv(StringIO(content))
        except UnicodeDecodeError:
            # Si falla, intentar con latin-1
            content = response.content.decode('latin-1')
            df = pd.read_csv(StringIO(content))
        
        return df, "success"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def process_data(df):
    """Procesar datos del CSV"""
    try:
        coordinates_data = []
        complete_data = []
        skipped_records = 0
        
        for i, row in df.iterrows():
            try:
                # Buscar la columna LOCATION
                location_col = None
                for col in df.columns:
                    if 'LOCATION' in col.upper():
                        location_col = col
                        break
                
                if location_col:
                    location_value = row[location_col]
                else:
                    location_value = None
                
                if pd.notna(location_value) and location_value not in ['', 'NaN', 'nan']:
                    # Limpiar y procesar coordenadas
                    location_str = str(location_value).strip('[] ')
                    parts = location_str.split(',')
                    
                    if len(parts) == 2:
                        lon = float(parts[0].strip())
                        lat = float(parts[1].strip())
                        
                        coordinates_data.append({'lat': lat, 'lon': lon})
                        
                        # Buscar otras columnas importantes
                        record = {'lat': lat, 'lon': lon}
                        
                        # Columnas que podrían existir
                        possible_columns = {
                            'clase': ['CLASE_ACCIDENTE', 'CLASE', 'TIPO'],
                            'gravedad': ['GRAVEDAD_ACCIDENTE', 'GRAVEDAD'], 
                            'barrio': ['BARRIO', 'NEIGHBORHOOD'],
                            'comuna': ['COMUNA', 'DISTRICT'],
                            'fecha': ['FECHA_ACCIDENTE', 'FECHA', 'DATE'],
                            'año': ['AÑO', 'YEAR', 'ANIO']
                        }
                        
                        for field, possible_names in possible_columns.items():
                            for name in possible_names:
                                if name in df.columns:
                                    record[field] = row[name]
                                    break
                            else:
                                record[field] = ''
                        
                        complete_data.append(record)
                    else:
                        skipped_records += 1
                else:
                    skipped_records += 1
            except:
                skipped_records += 1
                continue
        
        return pd.DataFrame(coordinates_data), pd.DataFrame(complete_data), skipped_records
        
    except Exception as e:
        st.error(f"Error procesando datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), 0

def create_metric(value, label, icon="📊"):
    """Crear métrica simple"""
    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def setup_folium_map(data):
    """Configurar y mostrar mapa con Folium"""
    try:
        import folium
        from streamlit_folium import st_folium
        from folium.plugins import MarkerCluster
        
        # Centro de Medellín
        medellin_center = [6.2442, -75.5812]
        
        # Crear mapa base
        m = folium.Map(
            location=medellin_center,
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Agrupar marcadores para mejor rendimiento
        marker_cluster = MarkerCluster().add_to(m)
        
        # Agregar marcadores para cada punto
        for _, row in data.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                popup=f"Lat: {row['lat']:.6f}<br>Lon: {row['lon']:.6f}",
                tooltip="Click para ver coordenadas",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
        
        return m
        
    except ImportError:
        st.error("❌ Folium no está disponible. Instala folium y streamlit-folium para ver el mapa.")
        return None
    except Exception as e:
        st.error(f"Error creando el mapa: {e}")
        return None

def get_unique_values(series):
    """Obtener valores únicos de manera segura"""
    try:
        # Filtrar valores nulos y vacíos, luego convertir a string
        unique_vals = series.astype(str).dropna()
        unique_vals = unique_vals[unique_vals != '']
        unique_vals = unique_vals[unique_vals != 'nan']
        unique_vals = unique_vals[unique_vals != 'No disponible']
        return sorted(unique_vals.unique())
    except:
        return []

def main():
    st.title("🗺️ Mapa de Accidentes de Tránsito en Medellín")
    
    # Inicializar session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'filters_applied' not in st.session_state:
        st.session_state.filters_applied = False
    
    # Sidebar para carga de datos
    with st.sidebar:
        st.header("📁 Cargar Datos")
        
        # ENLACE POR DEFECTO - REEMPLAZA CON TU FILE ID REAL
        default_link = "https://drive.google.com/uc?id=1ABC123def456GHI789jkl"  # REEMPLAZA ESTO
        drive_link = st.text_input(
            "Enlace de Google Drive:",
            value=default_link
        )
        
        if st.button("📥 Cargar Datos", type="primary"):
            if drive_link:
                with st.spinner("Descargando datos..."):
                    df, status = load_csv_from_drive(drive_link)
                    if df is not None:
                        st.session_state.df = df
                        st.session_state.data_loaded = True
                        st.session_state.filters_applied = False
                        st.success("✅ Datos cargados correctamente")
                        
                        # Procesar datos
                        with st.spinner("Procesando datos..."):
                            map_data, complete_data, skipped = process_data(df)
                            st.session_state.map_data = map_data
                            st.session_state.complete_data = complete_data
                            st.session_state.skipped = skipped
                    else:
                        st.error(f"❌ {status}")
    
    # Verificar si los datos están cargados
    if not st.session_state.get('data_loaded', False):
        st.info("Por favor, carga los datos desde Google Drive usando la barra lateral.")
        return
    
    # Sidebar para filtros
    with st.sidebar:
        if st.session_state.data_loaded:
            st.markdown("---")
            st.header("🎛️ Controles del Mapa")
            
            # Botón para aplicar/remover filtros
            if not st.session_state.filters_applied:
                if st.button("🚀 Mostrar Mapa Interactivo", type="primary"):
                    st.session_state.filters_applied = True
                    st.rerun()
            else:
                if st.button("📊 Mostrar Solo Datos", type="secondary"):
                    st.session_state.filters_applied = False
                    st.rerun()
            
            if st.session_state.filters_applied:
                st.markdown("---")
                st.header("🔍 Filtros de Datos")
                
                complete_data = st.session_state.complete_data
                
                # Filtro por año (si existe y tiene datos)
                if 'año' in complete_data.columns and not complete_data['año'].empty:
                    años = get_unique_values(complete_data['año'])
                    if años:
                        años_seleccionados = st.multiselect(
                            "Año:",
                            options=años,
                            default=años
                        )
                        st.session_state.años_seleccionados = años_seleccionados
                    else:
                        st.info("No hay datos de año disponibles")
                        st.session_state.años_seleccionados = []
                else:
                    st.session_state.años_seleccionados = []
                
                # Filtro por tipo de accidente
                if 'clase' in complete_data.columns and not complete_data['clase'].empty:
                    clases = get_unique_values(complete_data['clase'])
                    if clases:
                        clases_seleccionadas = st.multiselect(
                            "Tipo de accidente:",
                            options=clases,
                            default=clases
                        )
                        st.session_state.clases_seleccionadas = clases_seleccionadas
                    else:
                        st.session_state.clases_seleccionadas = []
                else:
                    st.session_state.clases_seleccionadas = []
                
                # Filtro por gravedad
                if 'gravedad' in complete_data.columns and not complete_data['gravedad'].empty:
                    gravedades = get_unique_values(complete_data['gravedad'])
                    if gravedades:
                        gravedades_seleccionadas = st.multiselect(
                            "Gravedad:",
                            options=gravedades,
                            default=gravedades
                        )
                        st.session_state.gravedades_seleccionadas = gravedades_seleccionadas
                    else:
                        st.session_state.gravedades_seleccionadas = []
                else:
                    st.session_state.gravedades_seleccionadas = []
    
    # Mostrar métricas principales
    st.header("📊 Estadísticas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(st.session_state.map_data)
        st.markdown(create_metric(f"{total:,}", "Registros Válidos", "✅"), unsafe_allow_html=True)
    
    with col2:
        skipped = st.session_state.skipped
        st.markdown(create_metric(f"{skipped}", "Registros Omitidos", "⚠️"), unsafe_allow_html=True)
    
    with col3:
        original = len(st.session_state.df)
        st.markdown(create_metric(f"{original:,}", "Filas Originales", "📄"), unsafe_allow_html=True)
    
    with col4:
        if total > 0:
            st.markdown(create_metric("Listo", "Estado", "🎯"), unsafe_allow_html=True)
        else:
            st.markdown(create_metric("Error", "Estado", "❌"), unsafe_allow_html=True)
    
    # Mostrar mapa si los filtros están aplicados
    if st.session_state.filters_applied:
        st.header("🗺️ Mapa Interactivo de Accidentes")
        
        # Aplicar filtros
        filtered_data = st.session_state.complete_data.copy()
        total_filtrado = len(filtered_data)
        
        # Aplicar filtros solo si hay selecciones
        if hasattr(st.session_state, 'años_seleccionados') and st.session_state.años_seleccionados:
            filtered_data = filtered_data[filtered_data['año'].astype(str).isin(st.session_state.años_seleccionados)]
        
        if hasattr(st.session_state, 'clases_seleccionadas') and st.session_state.clases_seleccionadas:
            filtered_data = filtered_data[filtered_data['clase'].astype(str).isin(st.session_state.clases_seleccionadas)]
        
        if hasattr(st.session_state, 'gravedades_seleccionadas') and st.session_state.gravedades_seleccionadas:
            filtered_data = filtered_data[filtered_data['gravedad'].astype(str).isin(st.session_state.gravedades_seleccionadas)]
        
        # Mostrar estadísticas de filtros
        st.subheader(f"📈 Datos Filtrados: {len(filtered_data)} de {total_filtrado} registros")
        
        if len(filtered_data) > 0:
            # Verificar si folium está disponible
            try:
                import folium
                from streamlit_folium import st_folium
                
                # Crear y mostrar el mapa
                mapa = setup_folium_map(filtered_data[['lat', 'lon']].dropna())
                if mapa:
                    st_folium(mapa, width=1000, height=600)
                else:
                    st.warning("No se pudo crear el mapa. Mostrando datos en tabla.")
                    st.dataframe(filtered_data, use_container_width=True)
                    
            except ImportError:
                st.error("""
                **❌ Folium no está instalado**
                
                Para ver el mapa interactivo, asegúrate de que tu archivo `requirements.txt` incluya:
                ```
                folium==0.14.0
                streamlit-folium==0.15.1
                ```
                """)
                st.dataframe(filtered_data, use_container_width=True)
            
            # Mostrar datos filtrados
            with st.expander("📋 Ver Datos Filtrados Completos"):
                st.dataframe(filtered_data, use_container_width=True)
        else:
            st.warning("No hay datos que coincidan con los filtros seleccionados")
    
    # Mostrar datos completos si no hay filtros aplicados
    if not st.session_state.filters_applied:
        st.header("📋 Vista Previa de Datos")
        
        if not st.session_state.complete_data.empty:
            st.dataframe(
                st.session_state.complete_data.head(50),
                use_container_width=True,
                height=400
            )
            
            # Análisis básico
            st.header("📈 Análisis de Datos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'clase' in st.session_state.complete_data.columns:
                    st.subheader("Distribución por Tipo de Accidente")
                    clase_counts = st.session_state.complete_data['clase'].value_counts()
                    st.bar_chart(clase_counts)
            
            with col2:
                if 'gravedad' in st.session_state.complete_data.columns:
                    st.subheader("Distribución por Gravedad")
                    gravedad_counts = st.session_state.complete_data['gravedad'].value_counts()
                    st.bar_chart(gravedad_counts)

if __name__ == "__main__":
    main()