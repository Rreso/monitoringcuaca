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
st.sidebar.markdown("""
## 🟠 ANTARES
""", unsafe_allow_html=True)

menu_options = {
    "🏠 Dashboard",
    "📊 Lokasi"
}

menu_selection = st.sidebar.radio("Navigasi", list(menu_options.keys()), index=0)

if menu_selection == "🏠 Dashboard":
    st.title("Dashboard Monitoring Cuaca")
    data = get_latest_data()
    if data:
        st.metric("Suhu (°C)", f"{data['Suhu (°C)']}°C")
        st.metric("Kelembapan (%)", f"{data['Kelembapan (%)']}%")
        st.metric("Kecepatan Angin (Km/h)", f"{data['Kecepatan Angin (Km/h)']} km/h")
        st.subheader("Prediksi Cuaca")
        st.write(f"🌦 **Decision Tree:** {data['Decision Tree']}")
        st.write(f"☁ **Naive Bayes:** {data['Naive Bayes']}")
    else:
        st.error("⚠️ Gagal mengambil data terbaru dari Antares.")

elif menu_selection == "📊 Lokasi":
    st.title("Lokasi Stasiun Cuaca")
    latitude = 1.1187578768824524
    longitude = 104.04846548164217
    
    m = folium.Map(location=[latitude, longitude], zoom_start=15)
    folium.Marker(
        [latitude, longitude], 
        popup="Stasiun Cuaca", 
        tooltip="Klik untuk info", 
        icon=folium.Icon(icon="cloud", prefix="fa", color="blue")
    ).add_to(m)
    st_folium(m, width=900, height=600)
    
    github_image_url_1 = "https://raw.githubusercontent.com/username/repository/main/image1.jpg"
    github_image_url_2 = "https://raw.githubusercontent.com/username/repository/main/image2.jpg"
    
    st.image(github_image_url_1, caption="Gambar Lokasi 1", use_container_width=True)
    st.image(github_image_url_2, caption="Gambar Lokasi 2", use_container_width=True)

elif menu_selection == "Data Cuaca":
    st.title("Data Cuaca")
    df_history = get_history_data()
    if df_history is not None:
        st.subheader("📜 Riwayat Data Cuaca (10 Data Terakhir)")
        st.dataframe(df_history)
        st.subheader("📈 Grafik Perubahan Cuaca")
        st.line_chart(df_history.set_index("timestamp")[['Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)']])
    else:
        st.warning("⚠️ Tidak ada data riwayat yang tersedia di Antares.")



