import streamlit as st
import requests
import pandas as pd
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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
    "X-M2M-Origin": "YOUR_ACCESS_KEY",
    "Content-Type": "application/json;ty=4",
    "Accept": "application/json"
}


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

def get_history_data():
    try:
        # Ambil daftar URI dari histori
        response = requests.get(f"{URL_BASE}/~/antares-cse/antares-id/SistemMonitoringCuaca/ESP32?rcn=4&fu=1&ty=4&lim=10",
                                headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 🛑 Debugging response pertama
        print("🔍 Response dari Antares (Daftar URI):")
        print(json.dumps(data, indent=4))

        if "m2m:uril" not in data:
            print("⚠️ Tidak ada data URI yang ditemukan!")
            return None

        history = []
        for uri in data["m2m:uril"]:
            # Request untuk mendapatkan isi data di setiap URI
            data_response = requests.get(f"{URL_BASE}/~{uri}", headers=headers, timeout=10)
            data_response.raise_for_status()
            data_content = data_response.json()

            # 🛑 Debugging response isi data
            print(f"📥 Data dari {uri}:")
            print(json.dumps(data_content, indent=4))

            if "m2m:cin" in data_content:
                content = json.loads(data_content["m2m:cin"]["con"])  # Parsing JSON dalam "con"
                content["timestamp"] = data_content["m2m:cin"]["ct"]  # Tambahkan timestamp
                history.append(content)

        # Konversi ke Pandas DataFrame
        if history:
            return pd.DataFrame(history)
        else:
            print("⚠️ Tidak ada data riwayat yang tersedia di Antares.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching history data: {e}")
        return None
st.title("Dashboard Monitoring Cuaca")

# Tampilkan Data Terbaru
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

# Tampilkan Data History
df_history = get_history_data()
if df_history is not None:
    st.subheader("📜 Riwayat Data Cuaca (10 Data Terakhir)")
    st.dataframe(df_history)

    # Buat Grafik
    st.subheader("📈 Grafik Perubahan Cuaca")
    st.line_chart(df_history.set_index("timestamp")[['Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)']])
else:
    st.warning("⚠️ Tidak ada data riwayat yang tersedia di Antares.")
