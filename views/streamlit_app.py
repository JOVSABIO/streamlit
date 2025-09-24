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

# Estilos CSS
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
    """Procesar datos del CSV"""
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

def create_metric(value, label, icon="📊"):
    return f"""
    <div class="metric-card">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def create_map(data):
    """Crear mapa con Folium"""
    try:
        import folium
        from streamlit_folium import st_folium
        
        m = folium.Map(location=[6.2442, -75.5812], zoom_start=12)
        
        for _, row in data.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                popup=f"Lat: {row['lat']:.4f}, Lon: {row['lon']:.4f}",
                icon=folium.Icon(color='red')
            ).add_to(m)
        
        return m
    except ImportError:
        return None

def get_unique_values(series):
    try:
        unique_vals = series.astype(str)
        unique_vals = unique_vals[unique_vals != '']
        unique_vals = unique_vals[unique_vals != 'nan']
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
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Cargar Datos")
        
        drive_link = st.text_input(
            "Enlace de Google Drive:",
            value="https://drive.google.com/uc?id=1ABC123def456GHI789jkl"  # REEMPLAZA ESTO
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
            st.header("🎛️ Controles")
            
            if not st.session_state.filters_applied:
                if st.button("🚀 Mostrar Mapa", type="primary"):
                    st.session_state.filters_applied = True
            else:
                if st.button("📊 Solo Datos", type="secondary"):
                    st.session_state.filters_applied = False
            
            if st.session_state.filters_applied:
                st.markdown("---")
                st.header("🔍 Filtros")
                
                complete_data = st.session_state.complete_data
                
                # Filtros condicionales
                if 'año' in complete_data.columns:
                    años = get_unique_values(complete_data['año'])
                    if años:
                        st.session_state.años_sel = st.multiselect("Año:", años, default=años)
                
                if 'clase' in complete_data.columns:
                    clases = get_unique_values(complete_data['clase'])
                    if clases:
                        st.session_state.clases_sel = st.multiselect("Tipo:", clases, default=clases)
                
                if 'gravedad' in complete_data.columns:
                    gravedades = get_unique_values(complete_data['gravedad'])
                    if gravedades:
                        st.session_state.gravedades_sel = st.multiselect("Gravedad:", gravedades, default=gravedades)
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    total = len(st.session_state.map_data)
    
    with col1:
        st.markdown(create_metric(f"{total:,}", "Registros", "✅"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_metric(f"{st.session_state.skipped}", "Omitidos", "⚠️"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_metric(f"{len(st.session_state.df):,}", "Original", "📄"), unsafe_allow_html=True)
    with col4:
        status_icon = "🎯" if total > 0 else "❌"
        st.markdown(create_metric("Listo" if total > 0 else "Error", "Estado", status_icon), unsafe_allow_html=True)
    
    # Contenido principal
    if st.session_state.filters_applied:
        st.header("🗺️ Mapa Interactivo")
        
        # Aplicar filtros
        filtered_data = st.session_state.complete_data.copy()
        
        if hasattr(st.session_state, 'años_sel'):
            filtered_data = filtered_data[filtered_data['año'].astype(str).isin(st.session_state.años_sel)]
        if hasattr(st.session_state, 'clases_sel'):
            filtered_data = filtered_data[filtered_data['clase'].astype(str).isin(st.session_state.clases_sel)]
        if hasattr(st.session_state, 'gravedades_sel'):
            filtered_data = filtered_data[filtered_data['gravedad'].astype(str).isin(st.session_state.gravedades_sel)]
        
        st.write(f"**Mostrando:** {len(filtered_data)} registros")
        
        if len(filtered_data) > 0:
            # Intentar mostrar mapa
            mapa = create_map(filtered_data[['lat', 'lon']].dropna())
            if mapa:
                st_folium(mapa, width=1000, height=500)
            else:
                st.warning("Mapa no disponible - mostrando datos en tabla")
                st.dataframe(filtered_data, use_container_width=True)
        else:
            st.warning("No hay datos con los filtros seleccionados")
    else:
        # Vista de datos
        st.header("📋 Datos Cargados")
        if not st.session_state.complete_data.empty:
            st.dataframe(st.session_state.complete_data.head(100), use_container_width=True)

if __name__ == "__main__":
    main()
