import streamlit as st
import pandas as pd
import requests
from io import StringIO
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap

# Configuración de la página
st.set_page_config(
    page_title="Mapa de Accidentes Medellín",
    page_icon="🚗",
    layout="wide"
)

# Estilos CSS mejorados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-card-danger {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    }
    
    .metric-card-success {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
    }
    
    .metric-card-warning {
        background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .map-container {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def load_csv_from_drive(drive_link):
    """Cargar CSV desde Google Drive"""
    try:
        if 'id=' in drive_link:
            file_id = drive_link.split('id=')[1].split('&')[0]
        elif '/d/' in drive_link:
            file_id = drive_link.split('/d/')[1].split('/')[0]
        else:
            return None, "Formato de enlace no válido"
        
        download_url = f'https://drive.google.com/uc?id=1R5JxWJZK_OvFYdGmE2mG3wUhFRb7StdD&export=download'
        response = requests.get(download_url)
        response.raise_for_status()
        
        content = response.text
        try:
            df = pd.read_csv(StringIO(content))
        except:
            content = response.content.decode('latin-1')
            df = pd.read_csv(StringIO(content))
        
        return df, "success"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def process_data(df):
    #"""Procesar datos del CSV"""
    try:
        coordinates_data = []
        complete_data = []
        skipped_records = 0
        
        for i, row in df.iterrows():
            try:
                location_col = None
                for col in df.columns:
                    if 'LOCATION' in col.upper():
                        location_col = col
                        break
                
                if location_col and pd.notna(row[location_col]) and str(row[location_col]) not in ['', 'NaN', 'nan']:
                    location_str = str(row[location_col]).strip('[] ')
                    parts = location_str.split(',')
                    
                    if len(parts) == 2:
                        lon = float(parts[0].strip())
                        lat = float(parts[1].strip())
                        
                        if (6.1 <= lat <= 6.4) and (-75.7 <= lon <= -75.5):
                            coordinates_data.append({'lat': lat, 'lon': lon})
                            
                            record = {'lat': lat, 'lon': lon}
                            record['clase'] = row.get('CLASE_ACCIDENTE', row.get('CLASE', ''))
                            record['gravedad'] = row.get('GRAVEDAD_ACCIDENTE', row.get('GRAVEDAD', ''))
                            record['barrio'] = row.get('BARRIO', '')
                            record['comuna'] = row.get('COMUNA', '')
                            record['año'] = row.get('AÑO', row.get('YEAR', ''))
                            
                            complete_data.append(record)
                        else:
                            skipped_records += 1
                    else:
                        skipped_records += 1
                else:
                    skipped_records += 1
            except:
                skipped_records += 1
                continue
        
        return pd.DataFrame(coordinates_data), pd.DataFrame(complete_data), skipped_records
        
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), 0

def create_metric_card(icon, value, label, card_type="default"):
    """Crear una tarjeta de métrica moderna"""
    card_class = "metric-card"
    if card_type == "danger":
        card_class += " metric-card-danger"
    elif card_type == "success":
        card_class += " metric-card-success"
    elif card_type == "warning":
        card_class += " metric-card-warning"
    
    return f"""
    <div class="{card_class}">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    
def create_advanced_map(data, map_type='markers', zoom_start=12):
    #Crear mapa interactivo con Folium
    try:
        medellin_center = [6.2442, -75.5812]
        
        m = folium.Map(
            location=medellin_center,
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        if map_type == 'markers':
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in data.iterrows():
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=f"Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}",
                    icon=folium.Icon(color='red', icon='car-crash', prefix='fa')
                ).add_to(marker_cluster)
        
        elif map_type == 'heatmap':
            heat_data = [[row['lat'], row['lon']] for _, row in data.iterrows()]
            HeatMap(heat_data, radius=15, blur=10).add_to(m)
        
        else:  # círculos por defecto
            for _, row in data.iterrows():
                folium.CircleMarker(
                    [row['lat'], row['lon']],
                    radius=3,
                    popup=f"Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.6
                ).add_to(m)
        
        return m
    except ImportError:
        return None

def get_unique_values(series):
   # """Obtener valores únicos de una serie de manera segura"""
    try:
        unique_vals = series.astype(str)
        unique_vals = unique_vals[unique_vals != '']
        unique_vals = unique_vals[unique_vals != 'nan']
        return sorted(unique_vals.unique())
    except:
        return []

def main():
    st.markdown('<h1 class="main-header">🗺️ Mapa de Accidentes de Tránsito en Medellín</h1>', unsafe_allow_html=True)
    
    # Inicializar session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'filters_applied' not in st.session_state:
        st.session_state.filters_applied = False
    if 'map_type' not in st.session_state:
        st.session_state.map_type = 'markers'
    if 'zoom_level' not in st.session_state:
        st.session_state.zoom_level = 12
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Cargar Datos")
        
        drive_link = st.text_input(
            "Enlace de Google Drive:",
            value="https://drive.google.com/uc?id=1ABC123def456GHI789jkl"
        )
        
        if st.button("📥 Cargar Datos", type="primary") and drive_link:
            with st.spinner("Cargando datos..."):
                df, status = load_csv_from_drive(drive_link)
                if df is not None:
                    st.session_state.df = df
                    st.session_state.data_loaded = True
                    st.session_state.filters_applied = False
                    
                    map_data, complete_data, skipped = process_data(df)
                    st.session_state.map_data = map_data
                    st.session_state.complete_data = complete_data
                    st.session_state.skipped = skipped
                    st.success("✅ Datos cargados")
                else:
                    st.error(f"❌ {status}")
    
    if not st.session_state.get('data_loaded', False):
        st.info("Carga los datos desde Google Drive usando la barra lateral.")
        return
    
    # Filtros en sidebar
    with st.sidebar:
        if st.session_state.data_loaded:
            st.markdown("---")
            st.header("🎛️ Controles del Mapa")
            
            # Selector de tipo de mapa
            map_type = st.radio(
                "Tipo de Visualización:",
                ["Marcadores", "Mapa de Calor", "Círculos"],
                index=0
            )
            
            # Control de zoom
            zoom_level = st.slider("Nivel de Zoom:", 10, 18, 12)
            
            st.markdown("---")
            st.header("🔍 Filtros de Datos")
            
            if not st.session_state.filters_applied:
                if st.button("🚀 Mostrar Mapa", type="primary"):
                    st.session_state.filters_applied = True
                    st.session_state.map_type = map_type.lower().replace(' ', '_')
                    st.session_state.zoom_level = zoom_level
            else:
                if st.button("📊 Solo Datos", type="secondary"):
                    st.session_state.filters_applied = False
            
            if st.session_state.filters_applied:
                complete_data = st.session_state.complete_data
                
                # Filtros condicionales - INCLUYENDO BARRIOS Y COMUNAS
                if 'año' in complete_data.columns:
                    años = get_unique_values(complete_data['año'])
                    if años:
                        st.session_state.años_sel = st.multiselect("Año:", años, default=años)
                
                if 'clase' in complete_data.columns:
                    clases = get_unique_values(complete_data['clase'])
                    if clases:
                        st.session_state.clases_sel = st.multiselect("Tipo de Accidente:", clases, default=clases)
                
                if 'gravedad' in complete_data.columns:
                    gravedades = get_unique_values(complete_data['gravedad'])
                    if gravedades:
                        st.session_state.gravedades_sel = st.multiselect("Gravedad:", gravedades, default=gravedades)
                
                # ✅ NUEVOS FILTROS DE BARRIOS Y COMUNAS
                if 'barrio' in complete_data.columns:
                    barrios = get_unique_values(complete_data['barrio'])
                    if barrios:
                        st.session_state.barrios_sel = st.multiselect("Barrio:", barrios, default=barrios)
                
                if 'comuna' in complete_data.columns:
                    comunas = get_unique_values(complete_data['comuna'])
                    if comunas:
                        st.session_state.comunas_sel = st.multiselect("Comuna:", comunas, default=comunas)
    
    # Métricas modernas
    col1, col2, col3, col4 = st.columns(4)
    total = len(st.session_state.map_data)
    skipped = st.session_state.skipped
    
    with col1:
        st.markdown(create_metric_card("📊", f"{total:,}", "Registros Válidos", "success"), unsafe_allow_html=True)
    with col2:
        card_type = "warning" if skipped > 0 else "success"
        st.markdown(create_metric_card("⚠️", f"{skipped}", "Registros Omitidos", card_type), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric_card("📄", f"{len(st.session_state.df):,}", "Total Original", "info"), unsafe_allow_html=True)
    with col4:
        status_text = "Listo" if total > 0 else "Error"
        status_icon = "✅" if total > 0 else "❌"
        card_type = "success" if total > 0 else "danger"
        st.markdown(create_metric_card(status_icon, status_text, "Estado", card_type), unsafe_allow_html=True)
    
    # Contenido principal
    if st.session_state.filters_applied:
        st.header("🗺️ Mapa Interactivo")
        
        # Aplicar filtros (INCLUYENDO BARRIOS Y COMUNAS)
        filtered_data = st.session_state.complete_data.copy()
        
        if hasattr(st.session_state, 'años_sel'):
            filtered_data = filtered_data[filtered_data['año'].astype(str).isin(st.session_state.años_sel)]
        if hasattr(st.session_state, 'clases_sel'):
            filtered_data = filtered_data[filtered_data['clase'].astype(str).isin(st.session_state.clases_sel)]
        if hasattr(st.session_state, 'gravedades_sel'):
            filtered_data = filtered_data[filtered_data['gravedad'].astype(str).isin(st.session_state.gravedades_sel)]
        # ✅ APLICAR FILTROS DE BARRIOS Y COMUNAS
        if hasattr(st.session_state, 'barrios_sel'):
            filtered_data = filtered_data[filtered_data['barrio'].astype(str).isin(st.session_state.barrios_sel)]
        if hasattr(st.session_state, 'comunas_sel'):
            filtered_data = filtered_data[filtered_data['comuna'].astype(str).isin(st.session_state.comunas_sel)]
        
        st.write(f"**Mostrando:** {len(filtered_data)} registros")
        
        if len(filtered_data) > 0:
            # Crear y mostrar mapa avanzado
            mapa = create_advanced_map(
                filtered_data[['lat', 'lon']].dropna(), 
                st.session_state.map_type, 
                st.session_state.zoom_level
            )
            
            if mapa:
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st_folium(mapa, width=1000, height=500)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Controles de mapa
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.markdown("### 🎯 Controles")
                    st.write("• 🖱️ Click en marcadores para detalles")
                    st.write("• 🔍 Zoom con rueda del mouse")
                    st.write("• 🗺️ Usa controles de capas")
                    
                    if st.button("🔄 Actualizar Vista"):
                        st.rerun()
            else:
                st.warning("Mapa no disponible - mostrando datos en tabla")
                st.dataframe(filtered_data, use_container_width=True)
        else:
            st.warning("No hay datos con los filtros seleccionados")
            
            if st.button("🗑️ Limpiar Filtros"):
                st.session_state.filters_applied = False
                st.rerun()
    else:
        # Vista de datos
        st.header("📋 Datos Cargados")
        if not st.session_state.complete_data.empty:
            st.dataframe(st.session_state.complete_data.head(100), use_container_width=True)
            
            # Estadísticas rápidas
            st.markdown("---")
            st.subheader("📊 Resumen de Datos")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'clase' in st.session_state.complete_data.columns:
                    st.write("**Tipos de accidente:**")
                    clase_counts = st.session_state.complete_data['clase'].value_counts()
                    st.dataframe(clase_counts, use_container_width=True)
            
            with col2:
                if 'gravedad' in st.session_state.complete_data.columns:
                    st.write("**Gravedad de accidentes:**")
                    gravedad_counts = st.session_state.complete_data['gravedad'].value_counts()
                    st.dataframe(gravedad_counts, use_container_width=True)
            
            with col3:
                if 'comuna' in st.session_state.complete_data.columns:
                    st.write("**Distribución por comuna:**")
                    comuna_counts = st.session_state.complete_data['comuna'].value_counts().head(10)
                    st.dataframe(comuna_counts, use_container_width=True)

if __name__ == "__main__":
    main()
