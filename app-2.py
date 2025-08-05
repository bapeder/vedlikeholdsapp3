import streamlit as st
import pandas as pd
import datetime
import json
import requests
import sqlite3
from uuid import uuid4

# Konfigurasjon
st.set_page_config(page_title="Varanger Golfpark Vedlikehold", layout="wide")
VADSO_LAT, VADSO_LON = 70.1068, 29.3656  # Rundet til 4 desimaler
DB_FILE = "golfpark.db"
USER_AGENT = "VarangerGolfparkApp/1.0 kontakt@varangergolfklubb.no"

# Initialiser SQLite-database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id TEXT, date TEXT, task TEXT, volunteer TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS status 
                 (id TEXT, area TEXT, report TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Hjelpefunksjoner for Yr API
def get_weather():
    try:
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={VADSO_LAT}&lon={VADSO_LON}"
        headers = {"User-Agent": USER_AGENT}
        # Sjekk om vi har cached data
        if "last_modified" in st.session_state:
            headers["If-Modified-Since"] = st.session_state["last_modified"]
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 304:  # Data ikke endret
            return st.session_state.get("weather_data", {
                "temp": "N/A",
                "desc": "Bruker cached data",
                "wind": "N/A",
                "precip": "N/A"
            })
        
        if response.status_code == 200 or response.status_code == 203:
            data = response.json()
            # Lagre Last-Modified for caching
            st.session_state["last_modified"] = response.headers.get("Last-Modified", "")
            # Hent første timen i timeseries
            timeseries = data["properties"]["timeseries"][0]["data"]
            next_1_hours = timeseries.get("next_1_hours", {})
            weather_data = {
                "temp": timeseries["instant"]["details"]["air_temperature"],
                "desc": next_1_hours.get("summary", {}).get("symbol_code", "N/A"),
                "wind": timeseries["instant"]["details"]["wind_speed"],
                "precip": next_1_hours.get("details", {}).get("precipitation_amount", 0)
            }
            st.session_state["weather_data"] = weather_data
            return weather_data
        else:
            return {"temp": "N/A", "desc": f"Feil: {response.status_code}", "wind": "N/A", "precip": "N/A"}
    except Exception as e:
        return {"temp": "N/A", "desc": f"Feil: {str(e)}", "wind": "N/A", "precip": "N/A"}

def simulate_mower_status():
    total_area = 31000 + 5000  # Fairways + estimert driving range
    mowed_area = 20000  # Eksempelverdi
    battery = 75  # Eksempelverdi
    return {
        "progress": (mowed_area / total_area) * 100,
        "battery": battery,
        "time_left": (total_area - mowed_area) / 1700  # Middels kapasitet
    }

# Hovedapp
st.sidebar.title("Varanger Golfpark")
page = st.sidebar.selectbox("Velg side", ["Hjem", "Vaktlister", "Oppgaver", "Robotklipper", "Banestatus", "Vær"])

if page == "Hjem":
    st.title("Velkommen til Varanger Golfpark Vedlikehold")
    st.write("Denne appen hjelper frivillige med å koordinere vedlikehold av golfbanen og driving rangen.")
    
    # Værdata
    weather = get_weather()
    st.subheader("Dagens vær i Vadsø")
    st.write(f"Temperatur: {weather['temp']} °C")
    st.write(f"Vær: {weather['desc']}")
    st.write(f"Vind: {weather['wind']} m/s")
    st.write(f"Nedbør (neste time): {weather['precip']} mm")
    if weather["wind"] > 5:
        st.warning("Sterk vind! Vurder å utsette ballplukking på driving rangen.")
    if weather["precip"] > 0:
        st.warning("Nedbør ventet. Sjekk drenering på greener og driving range.")

    # Robotklipperstatus
    mower = simulate_mower_status()
    st.subheader("Robotklipper Status")
    st.progress(mower["progress"] / 100)
    st.write(f"Prosent klippet: {mower['progress']:.1f}%")
    st.write(f"Batteri: {mower['battery']}%")
    st.write(f"Estimert tid igjen: {mower['time_left']:.1f} timer")

    # Dagens oppgaver
    st.subheader("Dagens oppgaver")
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query(f"SELECT * FROM tasks WHERE date = '{datetime.date.today()}'", conn)
    conn.close()
    if not tasks.empty:
        st.dataframe(tasks[["task", "volunteer", "status"]])
    else:
        st.write("Ingen oppgaver for i dag.")

elif page == "Vaktlister":
    st.title("Vaktlister")
    date = st.date_input("Velg dato", datetime.date.today())
    task = st.selectbox("Oppgave", [
        "Rake bunker", "Etterfyll sand på tees", "Rengjør greener", 
        "Plukk baller på driving rangen", "Jevn ut sand på driving range tees"
    ])
    volunteer = st.text_input("Navn på frivillig")
    if st.button("Legg til vakt"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        task_id = str(uuid4())
        c.execute("INSERT INTO tasks (id, date, task, volunteer, status) VALUES (?, ?, ?, ?, ?)",
                  (task_id, str(date), task, volunteer, "Planlagt"))
        conn.commit()
        conn.close()
        st.success(f"Vakt lagt til for {volunteer} på {date}!")
    
    st.subheader("Planlagte vakter")
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query(f"SELECT * FROM tasks WHERE date = '{date}'", conn)
    conn.close()
    if not tasks.empty:
        st.dataframe(tasks[["date", "task", "volunteer", "status"]])
    else:
        st.write("Ingen vakter planlagt for valgt dato.")

elif page == "Oppgaver":
    st.title("Vedlikeholdsoppgaver")
    area = st.selectbox("Område", ["Fairways", "Greener", "Tees", "Driving Range"])
    task = st.text_input("Beskriv oppgave (f.eks. 'Rake bunker på hull 3')")
    status = st.selectbox("Status", ["Planlagt", "Pågår", "Fullført"])
    if st.button("Legg til oppgave"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        task_id = str(uuid4())
        c.execute("INSERT INTO tasks (id, date, task, volunteer, status) VALUES (?, ?, ?, ?, ?)",
                  (task_id, str(datetime.date.today()), f"{area}: {task}", "TBD", status))
        conn.commit()
        conn.close()
        st.success("Oppgave lagt til!")
    
    st.subheader("Alle oppgaver")
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    if not tasks.empty:
        st.dataframe(tasks[["date", "task", "volunteer", "status"]])
    else:
        st.write("Ingen oppgaver registrert.")

elif page == "Robotklipper":
    st.title("Robotklipper Status")
    mower = simulate_mower_status()
    st.progress(mower["progress"] / 100)
    st.write(f"Prosent klippet: {mower['progress']:.1f}% (av 36 000 kvm)")
    st.write(f"Batteri: {mower['battery']}%")
    st.write(f"Estimert tid igjen: {mower['time_left']:.1f} timer")
    zone = st.selectbox("Velg sone å klippe", ["Fairways", "Driving Range"])
    if st.button("Start klipping i sone"):
        st.success(f"Klipping startet i {zone} (simulert).")

elif page == "Banestatus":
    st.title("Banestatus")
    area = st.selectbox("Område", ["Fairways", "Greener", "Tees", "Driving Range"])
    report = st.text_area("Rapporter status eller problem")
    if st.button("Send rapport"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        status_id = str(uuid4())
        c.execute("INSERT INTO status (id, area, report, date) VALUES (?, ?, ?, ?)",
                  (status_id, area, report, str(datetime.date.today())))
        conn.commit()
        conn.close()
        st.success("Rapport sendt!")
    
    st.subheader("Siste statusrapporter")
    conn = sqlite3.connect(DB_FILE)
    reports = pd.read_sql_query("SELECT * FROM status ORDER BY date DESC LIMIT 10", conn)
    conn.close()
    if not reports.empty:
        st.dataframe(reports[["date", "area", "report"]])
    else:
        st.write("Ingen rapporter registrert.")

elif page == "Vær":
    st.title("Vær i Vadsø")
    weather = get_weather()
    st.write(f"Temperatur: {weather['temp']} °C")
    st.write(f"Vær: {weather['desc']}")
    st.write(f"Vind: {weather['wind']} m/s")
    st.write(f"Nedbør (neste time): {weather['precip']} mm")
    if weather["wind"] > 5:
        st.warning("Sterk vind! Unngå ballplukking eller utsatt arbeid.")
    if weather["precip"] > 0:
        st.warning("Nedbør ventet. Sjekk drenering på greener og driving range.")