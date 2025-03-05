import streamlit as st
import requests
import json

# === Konfigurasi Antares HTTP ===
ACCESSKEY = st.secrets["ACCESSKEY"]
PROJECT_NAME = "SistemMonitoringCuaca"
DEVICE_NAME = "ESP32"
URL = f"https://platform.antares.id:443/~/antares-cse/antares-id/{PROJECT_NAME}/{DEVICE_NAME}/la"

headers = {
    "X-M2M-Origin": ACCESSKEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
response = requests.get(URL, headers=headers)

if response.status_code == 200:
    print("✅ Streamlit Cloud bisa akses Antares!")
else:
    print(f"❌ Gagal akses Antares! Status Code: {response.status_code}")
    
# === Fungsi Mengambil Data dari Antares ===
def get_antares_data():
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        content = data["m2m:cin"]["con"]
        return json.loads(content)  # Konversi JSON String ke Dictionary
    return None

# === Membuat Dashboard Streamlit ===
st.title("Dashboard Monitoring Cuaca")

data = get_antares_data()
if data:
    st.metric("Suhu (°C)", f"{data['Suhu (°C)']}°C")
    st.metric("Kelembapan (%)", f"{data['Kelembapan (%)']}%")
    st.metric("Kecepatan Angin (Km/h)", f"{data['Kecepatan Angin (Km/h)']} km/h")
    st.subheader("Prediksi Cuaca")
    st.write(f"**Decision Tree:** {data['Decision Tree']}")
    st.write(f"**Naive Bayes:** {data['Naive Bayes']}")
else:
    st.error("Gagal mengambil data dari Antares.")

