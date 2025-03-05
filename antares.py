import streamlit as st
import requests
import pandas as pd
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=5, 
    backoff_factor=1, 
    status_forcelist=[500, 502, 503, 504]
)
session.mount("https://", HTTPAdapter(max_retries=retry))

def get_antares_data():
    try:
        response = session.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return json.loads(data["m2m:cin"]["con"])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
        
# === Konfigurasi Antares HTTP ===
ACCESSKEY = st.secrets["ACCESSKEY"]
PROJECT_NAME = "SistemMonitoringCuaca"
DEVICE_NAME = "ESP32"
URL_LATEST = f"https://platform.antares.id:8443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}/la"
URL_HISTORY = f"https://platform.antares.id:8443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}/cnt/la?fu=2&lim=10"

headers = {
    "X-M2M-Origin": ACCESSKEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# === Fungsi Mengambil Data Terbaru dari Antares ===
def get_latest_data():
    try:
        response = requests.get(URL_LATEST, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return json.loads(data["m2m:cin"]["con"])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching latest data: {e}")
        return None

# === Fungsi Mengambil Data History dari Antares ===
def get_history_data():
    try:
        response = requests.get(URL_HISTORY, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        history = []
        for item in data["m2m:cnt"]["m2m:cin"]:
            content = json.loads(item["con"])
            content["timestamp"] = item["ct"]  # Tambahkan timestamp
            history.append(content)
        
        return pd.DataFrame(history)  # Konversi ke DataFrame
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching history data: {e}")
        return None

# === Membuat Dashboard Streamlit ===
st.title("Dashboard Monitoring Cuaca")

# Tampilkan Data Terbaru
data = get_latest_data()
if data:
    st.metric("Suhu (°C)", f"{data['Suhu (°C)']}°C")
    st.metric("Kelembapan (%)", f"{data['Kelembapan (%)']}%")
    st.metric("Kecepatan Angin (Km/h)", f"{data['Kecepatan Angin (Km/h)']} km/h")
    st.subheader("Prediksi Cuaca")
    st.write(f"**Decision Tree:** {data['Decision Tree']}")
    st.write(f"**Naive Bayes:** {data['Naive Bayes']}")
else:
    st.error("Gagal mengambil data terbaru dari Antares.")

# Tampilkan Data History
df_history = get_history_data()
if df_history is not None:
    st.subheader("Riwayat Data Cuaca (10 Data Terakhir)")
    st.dataframe(df_history)
    
    # Buat Grafik
    st.subheader("Grafik Perubahan Cuaca")
    st.line_chart(df_history.set_index("timestamp")[['Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)']])
else:
    st.error("Gagal mengambil riwayat data dari Antares.")a['Decision Tree']}")
    st.write(f"**Naive Bayes:** {data['Naive Bayes']}")
else:
    st.error("Gagal mengambil data dari Antares.")

