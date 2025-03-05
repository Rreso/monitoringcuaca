import streamlit as st
import requests
import pandas as pd
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# === Konfigurasi Antares HTTP ===
ACCESSKEY = st.secrets["ACCESSKEY"]
PROJECT_NAME = "SistemMonitoringCuaca"
DEVICE_NAME = "ESP32"

URL_LATEST = f"https://platform.antares.id:8443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}/la"
URL_HISTORY = f"https://platform.antares.id:8443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}?rcn=4&ty=4&lim=10"

headers = {
    "X-M2M-Origin": ACCESSKEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# === Konfigurasi Session untuk Retry (Mengatasi Timeout) ===
session = requests.Session()
retry = Retry(
    total=5, 
    backoff_factor=1, 
    status_forcelist=[500, 502, 503, 504]
)
session.mount("https://", HTTPAdapter(max_retries=retry))

# === Fungsi Mengambil Data Terbaru dari Antares ===
def get_latest_data():
    try:
        response = session.get(URL_LATEST, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return json.loads(data["m2m:cin"]["con"])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching latest data: {e}")
        return None

# === Fungsi Mengambil Data History dari Antares ===
def get_history_data():
    try:
        response = session.get(URL_HISTORY, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Pastikan struktur JSON sesuai
        if "m2m:cnt" not in data or "m2m:cin" not in data["m2m:cnt"]:
            st.warning("⚠️ Data history tidak tersedia atau belum dikirim ke Antares.")
            return None

        # Ekstrak data historis
        history = []
        for item in data["m2m:cnt"]["m2m:cin"]:
            try:
                content = json.loads(item["con"])
                content["timestamp"] = pd.to_datetime(item["ct"])  # Konversi timestamp ke format waktu
                history.append(content)
            except (json.JSONDecodeError, KeyError):
                st.error("⚠️ Format data di Antares tidak valid.")
                return None

        return pd.DataFrame(history) if history else None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching history data: {e}")
        return None

# === Membuat Dashboard Streamlit ===
st.title("🌦️ Dashboard Monitoring Cuaca")

# 🔹 **Tampilkan Data Terbaru**
data = get_latest_data()
if data:
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ Suhu (°C)", f"{data['Suhu (°C)']}°C")
    col2.metric("💧 Kelembapan (%)", f"{data['Kelembapan (%)']}%")
    col3.metric("🌬️ Kecepatan Angin (Km/h)", f"{data['Kecepatan Angin (Km/h)']} km/h")

    st.subheader("🔍 Prediksi Cuaca")
    st.write(f"**🌳 Decision Tree:** {data['Decision Tree']}")
    st.write(f"**📊 Naive Bayes:** {data['Naive Bayes']}")
else:
    st.error("⚠️ Gagal mengambil data terbaru dari Antares.")

# 🔹 **Tampilkan Riwayat Data**
df_history = get_history_data()
if df_history is not None and not df_history.empty:
    st.subheader("📜 Riwayat Data Cuaca (10 Data Terakhir)")
    st.dataframe(df_history)

    # 🔹 **Buat Grafik Perubahan Cuaca**
    st.subheader("📈 Grafik Perubahan Cuaca")
    st.line_chart(df_history.set_index("timestamp")[["Suhu (°C)", "Kelembapan (%)", "Kecepatan Angin (Km/h)"]])
else:
    st.warning("⚠️ Tidak ada data riwayat yang tersedia di Antares.")
