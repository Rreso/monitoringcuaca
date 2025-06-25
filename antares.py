import streamlit as st 
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import folium
import seaborn as sns
from streamlit_folium import st_folium
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.naive_bayes import ComplementNB
from sklearn.tree import DecisionTreeClassifier


# ======= 1. Load Data dari Excel =======
df = pd.read_excel("Data.xlsx", engine="openpyxl")

# Pastikan semua kolom yang dibutuhkan ada
required_columns = {'Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)', 'Decision  Tree', 'Naïve Bayes'}

# Pastikan data memiliki kolom yang sesuai
if required_columns.issubset(df.columns):
    le = LabelEncoder()
    df[['Decision  Tree', 'Naïve Bayes']] = df[['Decision  Tree', 'Naïve Bayes']].apply(le.fit_transform)

    # Pisahkan fitur dan target
    X = df[['Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)']]
    y1 = df['Decision  Tree']
    y2 = df['Naïve Bayes']
    


    X_train, X_test, y1_train, y1_test, y2_train, y2_test = train_test_split(X, y1, y2, test_size=split_ratio, random_state=42)

    # Buat model Decision Tree & Naive Bayes
    dt_model = DecisionTreeClassifier()
    dt_model.fit(X_train, y1_train)

    nb_model = GaussianNB()
    nb_model.fit(X_train, y2_train)

    # Variasi model Decision Tree
    dt_gini = DecisionTreeClassifier(criterion='gini', random_state=42)
    dt_entropy = DecisionTreeClassifier(criterion='entropy', random_state=42)

    dt_gini.fit(X_train, y1_train)
    dt_entropy.fit(X_train, y1_train)

    # Evaluasi
    y_pred_gini = dt_gini.predict(X_test)
    y_pred_entropy = dt_entropy.predict(X_test)

    acc_gini = accuracy_score(y1_test, y_pred_gini)
    acc_entropy = accuracy_score(y1_test, y_pred_entropy)
    
    # Variasi model Naive Bayes 
    nb_model_complement = GaussianNB()
    nb_model_complement.fit(X_train, y2_train)

    nb_model = GaussianNB()
    nb_model.fit(X_train, y2_train)
    y2_pred = nb_model.predict(X_test)
    acc_nb = accuracy_score(y2_test, y2_pred)

    cv_nb_5 = cross_val_score(GaussianNB(), X, y2, cv=5)
    cv_nb_10 = cross_val_score(GaussianNB(), X, y2, cv=10)


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

if st.sidebar.button("Evaluasi Model 📋", use_container_width=True):
    set_menu("Evaluasi Model 📋")

# --- Tampilan Konten Berdasarkan Menu ---
st.title(st.session_state.selected_menu)

if st.session_state.selected_menu == "Dashboard 🏠":  
    st.markdown(
        """
        <style>
        .stApp{
            background-color: #d0eced; /* Warna latar belakang */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
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
        
        st.markdown("<br><br>", unsafe_allow_html=True)  
        
        # Cuaca Real Time
        st.header("Cuaca Realtime Area Polibatam 🌤️")
        col4, col5 = st.columns(2)
        
        with col4:
            st.markdown("<h3 style='text-align: center;'>🌳 Decision Tree</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Decision Tree']}</h2>", unsafe_allow_html=True)
        with col5:
            st.markdown("<h3 style='text-align: center;'>🎲 Naive Bayes</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{data['Naive Bayes']}</h2>", unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)  

        # Prediksi Cuaca 30 Menit Kedepan
        suhu = data['Suhu (°C)']
        kelembapan = data['Kelembapan (%)']
        angin = data['Kecepatan Angin (Km/h)']

        # Gunakan model untuk prediksi cuaca berdasarkan data real-time
        input_data = [[suhu, kelembapan, angin]]
        dt_pred = dt_model.predict(input_data)
        nb_pred = nb_model.predict(input_data)

        # Konversi hasil prediksi ke bentuk label
        dt_result = le.inverse_transform(dt_pred)[0]
        nb_result = le.inverse_transform(nb_pred)[0]

        # Tambahkan hasil prediksi ke tampilan dashboard
        st.header("Prediksi Cuaca 30 Menit Kedepan 🌤️")
        co24, co25 = st.columns(2)
        
        with co24:
            st.markdown("<h3 style='text-align: center;'>🌳 Decision Tree</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{dt_result}</h2>", unsafe_allow_html=True)
        with co25:
            st.markdown("<h3 style='text-align: center;'>🎲 Naive Bayes</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>{nb_result}</h2>", unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
    else:
        st.error("⚠️ Gagal mengambil data terbaru dari Antares.")


elif st.session_state.selected_menu == "Lokasi 📍":
    st.markdown(
        """
        <style>
        .stApp{
            background-color: #d0eced; /* Warna latar belakang */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
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
    st.markdown(
        """
        <style>
        .stApp{
            background-color: #d0eced; /* Warna latar belakang */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    df_history = get_history_data()
    if df_history is not None:
        st.subheader("📜 Riwayat Data Cuaca (10 Data Terakhir)")
        st.dataframe(df_history)
        st.subheader("📈 Grafik Perubahan Cuaca")
        st.line_chart(df_history.set_index("timestamp")[['Suhu (°C)', 'Kelembapan (%)', 'Kecepatan Angin (Km/h)']])
                        
    else:
        st.warning("⚠️ Tidak ada data riwayat yang tersedia di Antares.")


elif st.session_state.selected_menu == "Evaluasi Model 📋":
        st.markdown(
        """
        <style>
        .stApp{
            background-color: #d0eced; /* Warna latar belakang */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
        y1_pred = dt_model.predict(X_test)  # Decision Tree
        y2_pred = nb_model.predict(X_test)  # Naïve Bayes
    
        # === AKURASI ===
        accuracy_dt = accuracy_score(y1_test, y1_pred)    
        accuracy_nb = accuracy_score(y2_test, y2_pred)

        # === CONFUSION MATRIX ===
        conf_matrix_dt = confusion_matrix(y1_test, y1_pred)
        conf_matrix_nb = confusion_matrix(y2_test, y2_pred)

        # === MSE & RMSE ===
        mse_dt = mean_squared_error(y1_test, y1_pred)
        rmse_dt = np.sqrt(mse_dt)

        mse_nb = mean_squared_error(y2_test, y2_pred)
        rmse_nb = np.sqrt(mse_nb)

        # Cross Validation untuk Decision Tree
        cv_scores_dt = cross_val_score(DecisionTreeClassifier(), X, y1, cv=5)
        mean_cv_dt = np.mean(cv_scores_dt)

        # Cross Validation untuk Naive Bayes
        cv_scores_nb = cross_val_score(GaussianNB(), X, y2, cv=5)
        mean_cv_nb = np.mean(cv_scores_nb)

        st.subheader("🌳 Metode Decision Tree")
        st.write(f"🎯 **Akurasi Decision Tree**: {accuracy_dt:.2f}")

        st.write("📌 **Confusion Matrix Decision Tree:**")
        fig1, ax1 = plt.subplots()
        sns.heatmap(conf_matrix_dt, annot=True, fmt='d', cmap='Greens',
                xticklabels=le.classes_, yticklabels=le.classes_, ax=ax1)
        ax1.set_title("Confusion Matrix - Decision Tree")
        ax1.set_xlabel("Predicted Label")
        ax1.set_ylabel("True Label")
        st.pyplot(fig1)

        st.write(f"📉 **MSE Decision Tree**: {mse_dt:.4f}")
        st.write(f"📉 **RMSE Decision Tree**: {rmse_dt:.4f}")

        st.write("🌳 **Decision Tree** - Akurasi per fold:", cv_scores_dt)
        st.write(f"🌳 **Decision Tree** - Rata-rata Akurasi CV: {mean_cv_dt:.3f}")

        st.subheader("🎲 Metode Naive Bayes")
        st.write(f"🎯 **Akurasi Naive Bayes**: {accuracy_nb:.2f}")

        st.write("📌 **Confusion Matrix Naive Bayes:**")
        fig2, ax2 = plt.subplots()
        sns.heatmap(conf_matrix_nb, annot=True, fmt='d', cmap='Greens',
                xticklabels=le.classes_, yticklabels=le.classes_, ax=ax2)
        ax2.set_title("Confusion Matrix - Naive Bayes")
        ax2.set_xlabel("Predicted Label")
        ax2.set_ylabel("True Label")
        st.pyplot(fig2)

        st.write(f"📉 **MSE Naïve Bayes**: {mse_nb:.4f}")
        st.write(f"📉 **RMSE Naïve Bayes**: {rmse_nb:.4f}")

        st.write("🎲 **Naïve Bayes** - Akurasi per fold:", cv_scores_nb)
        st.write(f"🎲 **Naïve Bayes** - Rata-rata Akurasi CV: {mean_cv_nb:.3f}")

        st.subheader("🌳 Perbandingan Fungsi Split Decision Tree")
        # Split data training dan testing
        split_ratio = st.selectbox("Pilih rasio data uji (%)", [0.2, 0.3, 0.4], format_func=lambda x: f"{int(x*100)}%")
        st.write(f"Akurasi Gini: {acc_gini:.2f}")
        st.write(f"Akurasi Entropy: {acc_entropy:.2f}")
         
        st.subheader("🎲 Naive Bayes berdasarkan rasio data")
        st.write(f"Akurasi Naive Bayes (rasio uji {int(split_ratio*100)}%): {acc_nb:.2f}")

        st.write("🎲 Naive Bayes - Akurasi CV 5-fold:", cv_nb_5)
        st.write("🎲 Naive Bayes - Akurasi CV 10-fold:", cv_nb_10)
        st.write(f"Rata-rata CV 5-fold: {cv_nb_5.mean():.3f}")
        st.write(f"Rata-rata CV 10-fold: {cv_nb_10.mean():.3f}")


