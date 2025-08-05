import streamlit as st
import pandas as pd
import datetime
import requests
import sqlite3
import smtplib
import websocket
import json
import threading
from uuid import uuid4
from email.mime.text import MIMEText
from streamlit_calendar import calendar

# Konfigurasjon
st.set_page_config(page_title="Varanger Golfpark Vedlikehold", layout="wide")
VADSO_LAT, VADSO_LON = 70.1068, 29.3656
DB_FILE = "golfpark.db"
USER_AGENT = "VarangerGolfparkApp/1.0 kontakt@varangergolfklubb.no"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "DIN_GMAIL@GMAIL.COM"  # Erstatt med din Gmail-adresse
SMTP_PASSWORD = "DIN_APP_PASSWORD"  # Erstatt med Gmail App Password
HUSQVARNA_API_KEY = "DIN_HUSQVARNA_API_KEY"  # Erstatt med Application Key
HUSQVARNA_API_SECRET = "DIN_HUSQVARNA_API_SECRET"  # Erstatt med Application Secret
HUSQVARNA_USERNAME = "DIN_HUSQVARNA_USERNAME"  # Erstatt med Husqvarna brukernavn
HUSQVARNA_PASSWORD = "DIN_HUSQVARNA_PASSWORD"  # Erstatt med Husqvarna passord

# CSS for mobilvennlighet
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialiser SQLite-database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id TEXT, date TEXT, task TEXT, volunteer TEXT, status TEXT, points INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS status 
                 (id TEXT, area TEXT, report TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS volunteers 
                 (id TEXT, name TEXT, email TEXT, role TEXT, points INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Hjelpefunksjoner
def get_weather():
    try:
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={VADSO_LAT}&lon={VADSO_LON}"
        headers = {"User-Agent": USER_AGENT}
        if "last_modified" in st.session_state:
            headers["If-Modified-Since"] = st.session_state["last_modified"]
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 304:
            return st.session_state.get("weather_data", {
                "temp": "N/A", "desc": "Bruker cached data", "wind": "N/A", "precip": "N/A"
            })
        
        if response.status_code == 200 or response.status_code == 203:
            data = response.json()
            st.session_state["last_modified"] = response.headers.get("Last-Modified", "")
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

# Husqvarna API-autentisering
def get_husqvarna_token():
    try:
        url = "https://iam-api.dss.husqvarnagroup.net/api/v3/token"
        headers = {"Content-Type": "application/json"}
        data = {
            "data": {
                "attributes": {
                    "username": HUSQVARNA_USERNAME,
                    "password": HUSQVARNA_PASSWORD,
                    "client_id": HUSQVARNA_API_KEY
                },
                "type": "token"
            }
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            token_data = response.json()
            st.session_state["husqvarna_token"] = token_data["data"]["attributes"]["access_token"]
            return True
        else:
            st.error(f"Autentisering feilet: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Autentisering feilet: {str(e)}")
        return False

# Husqvarna WebSocket for sanntidsstatus
def get_mower_status():
    if "husqvarna_token" not in st.session_state:
        get_husqvarna_token()
    
    def on_message(ws, message):
        data = json.loads(message)
        if "data" in data and "attributes" in data["data"]:
            status = data["data"]["attributes"]
            st.session_state["mower_status"] = {
                "activity": status.get("mower", {}).get("activity", "UNKNOWN"),
                "battery": status.get("battery", {}).get("batteryPercent", 0),
                "position": status.get("positions", [{}])[0].get("latitude", "N/A"),
                "error": status.get("system", {}).get("lastErrorCode", 0)
            }
    
    def on_error(ws, error):
        st.error(f"WebSocket feil: {str(error)}")
    
    def on_open(ws):
        ws.send(json.dumps({"data": {"type": "request", "attributes": {"mowerId": "YOUR_MOWER_ID"}}))  # Erstatt med din mowerId
    
    try:
        ws = websocket.WebSocketApp(
            "wss://amc-api.dss.husqvarnagroup.net/v1/mowers/YOUR_MOWER_ID/status",  # Erstatt med din mowerId
            header={"Authorization": f"Bearer {st.session_state['husqvarna_token']}"},
            on_message=on_message,
            on_error=on_error,
            on_open=on_open
        )
        threading.Thread(target=ws.run_forever, daemon=True).start()
    except Exception as e:
        st.error(f"WebSocket tilkobling feilet: {str(e)}")
        st.session_state["mower_status"] = {
            "activity": "N/A",
            "battery": 0,
            "position": "N/A",
            "error": "Tilkoblingsfeil"
        }

# Start WebSocket i bakgrunnen
if "mower_status" not in st.session_state:
    st.session_state["mower_status"] = {
        "activity": "N/A",
        "battery": 0,
        "position": "N/A",
        "error": "Ikke tilkoblet"
    }
    get_mower_status()

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Kunne ikke sende e-post: {str(e)}")
        return False

def get_points_for_task(task):
    points_map = {
        "Rake bunker": 10,
        "Etterfyll sand på tees": 15,
        "Rengjør greener": 20,
        "Plukk baller på driving rangen": 15,
        "Jevn ut sand på driving range tees": 15,
        "Klipp rough": 20,
        "Tilsyn vanningsanlegg": 25,
        "Generelle oppgaver på fairways": 15,
        "Generelle oppgaver på greener": 20
    }
    return points_map.get(task, 10)

# Hovedapp
st.sidebar.title("Varanger Golfpark")
page = st.sidebar.selectbox("Velg side", ["Hjem", "Registrering", "Vaktlister", "Vedlikeholdsplanlegger", "Oppgaver", "Robotklipper", "Banestatus", "Vær", "Poengoversikt"])

if "volunteer_id" not in st.session_state:
    st.session_state["volunteer_id"] = None
    st.session_state["volunteer_role"] = None

if page == "Hjem":
    st.title("Velkommen til Varanger Golfpark Vedlikehold")
    st.write("Koordiner vedlikehold av golfbanen og driving rangen.")
    
    weather = get_weather()
    st.subheader("Dagens vær i Vadsø")
    st.write(f"Temperatur: {weather['temp']} °C")
    st.write(f"Vær: {weather['desc']}")
    st.write(f"Vind: {weather['wind']} m/s")
    st.write(f"Nedbør (neste time): {weather['precip']} mm")
    if weather["wind"] > 5:
        st.warning("Sterk vind! Vurder å utsette ballplukking.")
    if weather["precip"] > 0:
        st.warning("Nedbør ventet. Sjekk drenering på greener og driving range.")

    st.subheader("Robotklipper Status")
    mower = st.session_state["mower_status"]
    st.write(f"Aktivitet: {mower['activity']}")
    st.progress(mower["battery"] / 100)
    st.write(f"Batteri: {mower['battery']}%")
    st.write(f"Posisjon: {mower['position']}")
    if mower["error"] != 0:
        st.error(f"Feilkode: {mower['error']}")

    st.subheader("Dagens oppgaver")
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query(f"SELECT * FROM tasks WHERE date = '{datetime.date.today()}'", conn)
    conn.close()
    if not tasks.empty:
        st.dataframe(tasks[["task", "volunteer", "status", "points"]])
    else:
        st.write("Ingen oppgaver for i dag.")

elif page == "Registrering":
    st.title("Registrering av frivillige")
    name = st.text_input("Navn")
    email = st.text_input("E-postadresse")
    role = st.selectbox("Rolle", ["Frivillig", "Administrator"])
    if st.button("Registrer"):
        if name and email:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            volunteer_id = str(uuid4())
            c.execute("INSERT INTO volunteers (id, name, email, role, points) VALUES (?, ?, ?, ?, ?)",
                      (volunteer_id, name, email, role, 0))
            conn.commit()
            conn.close()
            st.success(f"{name} registrert som {role}!")
            send_email(email, "Velkommen til Varanger Golfpark",
                      f"Hei {name},\n\nDu er registrert som {role} i Varanger Golfpark Vedlikeholdsapp.")
        else:
            st.error("Fyll ut alle felt.")
    
    st.subheader("Registrerte frivillige")
    conn = sqlite3.connect(DB_FILE)
    volunteers = pd.read_sql_query("SELECT name, email, role, points FROM volunteers", conn)
    conn.close()
    if not volunteers.empty:
        st.dataframe(volunteers)
    else:
        st.write("Ingen frivillige registrert.")

elif page == "Vaktlister":
    st.title("Vaktlister")
    date = st.date_input("Velg dato", datetime.date.today())
    task = st.selectbox("Oppgave", [
        "Rake bunker", "Etterfyll sand på tees", "Rengjør greener",
        "Plukk baller på driving rangen", "Jevn ut sand på driving range tees",
        "Klipp rough", "Tilsyn vanningsanlegg", "Generelle oppgaver på fairways",
        "Generelle oppgaver på greener"
    ])
    conn = sqlite3.connect(DB_FILE)
    volunteers = pd.read_sql_query("SELECT name FROM volunteers", conn)
    conn.close()
    volunteer = st.selectbox("Frivillig", volunteers["name"].tolist())
    if st.button("Legg til vakt"):
        if volunteer:
            points = get_points_for_task(task)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            task_id = str(uuid4())
            c.execute("INSERT INTO tasks (id, date, task, volunteer, status, points) VALUES (?, ?, ?, ?, ?, ?)",
                      (task_id, str(date), task, volunteer, "Planlagt", points))
            c.execute("UPDATE volunteers SET points = points + ? WHERE name = ?", (points, volunteer))
            conn.commit()
            volunteer_email = pd.read_sql_query(f"SELECT email FROM volunteers WHERE name = '{volunteer}'", conn)["email"].iloc[0]
            conn.close()
            send_email(volunteer_email, "Ny vakt tildelt",
                      f"Hei {volunteer},\n\nDu er tildelt oppgaven '{task}' på {date}. Poeng: {points}")
            st.success(f"Vakt lagt til for {volunteer} på {date}!")
        else:
            st.error("Velg en frivillig.")
    
    st.subheader("Planlagte vakter")
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query(f"SELECT * FROM tasks WHERE date = '{date}'", conn)
    conn.close()
    if not tasks.empty:
        st.dataframe(tasks[["date", "task", "volunteer", "status", "points"]])
    else:
        st.write("Ingen vakter planlagt for valgt dato.")

elif page == "Vedlikeholdsplanlegger":
    st.title("Vedlikeholdsplanlegger")
    conn = sqlite3.connect(DB_FILE)
    user_role = pd.read_sql_query(f"SELECT role FROM volunteers WHERE id = '{st.session_state.get('volunteer_id', '')}'", conn)
    conn.close()
    if not user_role.empty and user_role["role"].iloc[0] == "Administrator":
        st.subheader("Legg til ny oppgave")
        area = st.selectbox("Område", ["Fairways", "Greener", "Tees", "Driving Range", "Rough", "Vanningsanlegg"])
        task = st.selectbox("Oppgave", [
            "Rake bunker", "Etterfyll sand på tees", "Rengjør greener",
            "Plukk baller på driving rangen", "Jevn ut sand på driving range tees",
            "Klipp rough", "Tilsyn vanningsanlegg", "Generelle oppgaver på fairways",
            "Generelle oppgaver på greener"
        ])
        date = st.date_input("Dato", datetime.date.today())
        volunteer = st.selectbox("Tildel frivillig", ["TBD"] + volunteers["name"].tolist())
        status = st.selectbox("Status", ["Planlagt", "Pågår", "Fullført"])
        if st.button("Legg til oppgave"):
            points = get_points_for_task(task)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            task_id = str(uuid4())
            c.execute("INSERT INTO tasks (id, date, task, volunteer, status, points) VALUES (?, ?, ?, ?, ?, ?)",
                      (task_id, str(date), f"{area}: {task}", volunteer, status, points))
            if volunteer != "TBD" and status == "Fullført":
                c.execute("UPDATE volunteers SET points = points + ? WHERE name = ?", (points, volunteer))
            conn.commit()
            if volunteer != "TBD":
                volunteer_email = pd.read_sql_query(f"SELECT email FROM volunteers WHERE name = '{volunteer}'", conn)["email"].iloc[0]
                send_email(volunteer_email, "Ny oppgave tildelt",
                          f"Hei {volunteer},\n\nDu er tildelt oppgaven '{task}' på {area} for {date}. Poeng: {points}")
            conn.close()
            st.success("Oppgave lagt til!")
        
        # Kalendervisning
        st.subheader("Kalenderoversikt")
        conn = sqlite3.connect(DB_FILE)
        tasks = pd.read_sql_query("SELECT * FROM tasks", conn)
        conn.close()
        events = [
            {
                "title": f"{row['task']} ({row['volunteer']})",
                "start": row["date"],
                "end": row["date"],
                "resourceId": row["status"]
            } for _, row in tasks.iterrows()
        ]
        calendar_options = {
            "initialView": "dayGridMonth",
            "events": events,
            "editable": True,
            "selectable": True
        }
        calendar(calendar_options=calendar_options)
        
        st.subheader("Administrer oppgaver")
        conn = sqlite3.connect(DB_FILE)
        tasks = pd.read_sql_query("SELECT * FROM tasks", conn)
        conn.close()
        if not tasks.empty:
            st.dataframe(tasks[["date", "task", "volunteer", "status", "points"]])
            task_id = st.selectbox("Velg oppgave å oppdatere", tasks["id"].tolist(), format_func=lambda x: tasks[tasks["id"] == x]["task"].iloc[0])
            new_status = st.selectbox("Ny status", ["Planlagt", "Pågår", "Fullført"], key="update_status")
            new_volunteer = st.selectbox("Ny frivillig", ["TBD"] + volunteers["name"].tolist(), key="update_volunteer")
            if st.button("Oppdater oppgave"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE tasks SET status = ?, volunteer = ? WHERE id = ?", (new_status, new_volunteer, task_id))
                if new_status == "Fullført" and new_volunteer != "TBD":
                    points = tasks[tasks["id"] == task_id]["points"].iloc[0]
                    c.execute("UPDATE volunteers SET points = points + ? WHERE name = ?", (points, new_volunteer))
                    volunteer_email = pd.read_sql_query(f"SELECT email FROM volunteers WHERE name = '{new_volunteer}'", conn)["email"].iloc[0]
                    send_email(volunteer_email, "Oppgave fullført",
                              f"Hei {new_volunteer},\n\nOppgaven '{tasks[tasks['id'] == task_id]['task'].iloc[0]}' er markert som fullført. Du får {points} poeng!")
                conn.commit()
                conn.close()
                st.success("Oppgave oppdatert!")
    else:
        st.error("Kun administratorer kan bruke vedlikeholdsplanleggeren.")

elif page == "Oppgaver":
    st.title("Vedlikeholdsoppgaver")
    area = st.selectbox("Område", ["Fairways", "Greener", "Tees", "Driving Range", "Rough", "Vanningsanlegg"])
    task = st.text_input("Beskriv oppgave (f.eks. 'Rake bunker på hull 3')")
    status = st.selectbox("Status", ["Planlagt", "Pågår", "Fullført"])
    if st.button("Legg til oppgave"):
        points = get_points_for_task(task)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        task_id = str(uuid4())
        c.execute("INSERT INTO tasks (id, date, task, volunteer, status, points) VALUES (?, ?, ?, ?, ?, ?)",
                  (task_id, str(datetime.date.today()), f"{area}: {task}", "TBD", status, points))
        conn.commit()
        conn.close()
        st.success("Oppgave lagt til!")
    
    st.subheader("Alle oppgaver")
    conn = sqlite3.connect(DB_FILE)
    tasks = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    if not tasks.empty:
        st.dataframe(tasks[["date", "task", "volunteer", "status", "points"]])
    else:
        st.write("Ingen oppgaver registrert.")

elif page == "Robotklipper":
    st.title("Robotklipper Status")
    mower = st.session_state["mower_status"]
    st.write(f"Aktivitet: {mower['activity']}")
    st.progress(mower["battery"] / 100)
    st.write(f"Batteri: {mower['battery']}%")
    st.write(f"Posisjon: {mower['position']}")
    if mower["error"] != 0:
        st.error(f"Feilkode: {mower['error']}")
    zone = st.selectbox("Velg sone å klippe", ["Fairways", "Driving Range"])
    if st.button("Start klipping i sone"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state['husqvarna_token']}"}
            requests.post(
                "https://amc-api.dss.husqvarnagroup.net/v1/mowers/YOUR_MOWER_ID/control",
                headers=headers,
                json={"action": "start"}
            )
            st.success(f"Klipping startet i {zone}.")
        except Exception as e:
            st.error(f"Kunne ikke starte klipper: {str(e)}")

elif page == "Banestatus":
    st.title("Banestatus")
    area = st.selectbox("Område", ["Fairways", "Greener", "Tees", "Driving Range", "Rough", "Vanningsanlegg"])
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

elif page == "Poengoversikt":
    st.title("Poengoversikt")
    st.write("Rangering av frivillige basert på poeng for utførte oppgaver.")
    conn = sqlite3.connect(DB_FILE)
    volunteers = pd.read_sql_query("SELECT name, points FROM volunteers ORDER BY points DESC", conn)
    conn.close()
    if not volunteers.empty:
        st.dataframe(volunteers)
        st.subheader("Topp 3 frivillige")
        for i, row in volunteers.head(3).iterrows():
            st.write(f"{i+1}. {row['name']} - {row['points']} poeng")
    else:
        st.write("Ingen frivillige registrert.")