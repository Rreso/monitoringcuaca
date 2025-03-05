import streamlit as st 
import requests
import pandas as pd
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import folium
from streamlit_folium import st_folium

# Konfigurasi sesi HTTP dengan retry untuk koneksi yang lebih stabil
session = requests.Session()
retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))

# === Konfigurasi Antares HTTP ===
ACCESSKEY = st.secrets["ACCESSKEY"]
PROJECT_NAME = "SistemMonitoringCuaca"
DEVICE_NAME = "ESP32"

URL_LATEST = f"https://platform.antares.id:8443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}/la"
URL_HISTORY = f"https://platform.antares.id:8443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}?rcn=4&ty=4&fu=1&lim=10"
URL_BASE = "https://platform.antares.id:8443"
headers = {
    "X-M2M-Origin": ACCESSKEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# === Fungsi Mengambil Data Terbaru dari Antares ===
def get_latest_data():
    try:
        response = session.get(URL_LATEST, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return json.loads(data["m2m:cin"]["con"])  # Konversi string JSON ke dictionary
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching latest data: {e}")
        return None

# === Fungsi Mengambil Data Riwayat ===
def get_history_data():
    try:
        response = requests.get(URL_HISTORY, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "m2m:uril" not in data:
            return None
        
        history = []
        for uri in data["m2m:uril"]:
            data_response = requests.get(f"{URL_BASE}/~{uri}", headers=headers, timeout=10)
            data_response.raise_for_status()
            data_content = data_response.json()
            
            if "m2m:cin" in data_content:
                content = json.loads(data_content["m2m:cin"]["con"])
                content["timestamp"] = data_content["m2m:cin"]["ct"]
                history.append(content)
        
        return pd.DataFrame(history) if history else None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching history data: {e}")
        return None

# Menu navigasi di sidebar

st.sidebar.title("🌤 Sistem Monitoring Cuaca")

# State untuk menyimpan menu yang dipilih
if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = "Dashboard 🏠"

# Fungsi untuk mengubah menu saat tombol ditekan
def set_menu(menu_name):
    st.session_state.selected_menu = menu_name

# Tombol Sidebar
if st.sidebar.button("Dashboard 🏠", use_container_width=True):
    set_menu("Dashboard 🏠")

if st.sidebar.button("Lokasi 📍", use_container_width=True):
    set_menu("Lokasi 📍")

if st.sidebar.button("Data Cuaca 📊", use_container_width=True):
    set_menu("Data Cuaca 📊")

# --- Tampilan Konten Berdasarkan Menu ---
st.title(st.session_state.selected_menu)

if st.session_state.selected_menu == "Dashboard 🏠":
    data = get_latest_data()
    if data:
        # Tampilan bersampingan dengan tinggi yang sejajar
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("<h3 style='text-align: center;'>🌡 Suhu</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Suhu (°C)']:.2f}°C</h2>", unsafe_allow_html=True)

        with col2:
            st.markdown("<h3 style='text-align: center;'>💧 Kelembapan</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Kelembapan (%)']:.2f}%</h2>", unsafe_allow_html=True)

        with col3:
            st.markdown("<h3 style='text-align: center;'>🌪️ Angin</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Kecepatan Angin (Km/h)']:.2f} km/h</h2>", unsafe_allow_html=True)

        # Cuaca Real Time
        st.header("Cuaca Realtime Area Polibatam 🌤️")
        col4, col5 = st.columns(2)
        
        with col4:
            st.markdown("<h3 style='text-align: center;'>🌳 Decision Tree</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Decision Tree']}</h2>", unsafe_allow_html=True)
        with col5:
            st.markdown("<h3 style='text-align: center;'>🎲 Naive Bayes</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Naive Bayes']}</h2>", unsafe_allow_html=True)
    else:
        st.error("⚠️ Gagal mengambil data terbaru dari Antares.")

elif st.session_state.selected_menu == "Lokasi 📍":
    latitude = 1.1187578768824524
    longitude = 104.04846548164217
    
    m = folium.Map(location=[latitude, longitude], zoom_start=15)
    folium.Marker(
        [latitude, longitude], 
        popup="Stasiun Cuaca", 
        tooltip="Klik untuk info", 
        icon=folium.Icon(icon="cloud", prefix="fa", color="red")
    ).add_to(m)
    st_folium(m, width=900, height=600)
    
    github_image_url_1 = "https://raw.githubusercontent.com/Rreso/monitoringcuaca/main/politeknik.jpg"
    github_image_url_2 = "https://raw.githubusercontent.com/Rreso/monitoringcuaca/main/batam.jpg"
    
    st.image(github_image_url_1, caption="Politeknik Negeri Batam", use_container_width=True)
    st.image(github_image_url_2, caption="Rooftop Gedung Utama", use_container_width=True)

elif st.session_state.selected_menu == "Data Cuaca 📊":
    df_history = get_history_data()
    if df_history is not None:
        st.subheader("📜 Riwayat Data Cuaca (10 Data Terakhir)")
        st.dataframe(df_history)
        st.subheader("📈 Grafik Perubahan Cuaca")
        st.line_chart(df_history.set_index("timestamp")[['Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)']])
    else:
        st.warning("⚠️ Tidak ada data riwayat yang tersedia di Antares.")



