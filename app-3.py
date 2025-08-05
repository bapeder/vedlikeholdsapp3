import streamlit as st
import pandas as pd
import datetime
import requests
import sqlite3
from uuid import uuid4
# from twilio.rest import Client
# from twilio.base.exceptions import TwilioRestException

# Konfigurasjon
st.set_page_config(page_title="Varanger Golfpark Vedlikehold", layout="wide")
VADSO_LAT, VADSO_LON = 70.1068, 29.3656
DB_FILE = "golfpark.db"
USER_AGENT = "VarangerGolfparkApp/1.0 kontakt@varangergolfklubb.no"
# TWILIO_SID = "YOUR_TWILIO_SID"  # Erstatt med Twilio Account SID
# TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"  # Erstatt med Twilio Auth Token
# TWILIO_PHONE = "YOUR_TWILIO_PHONE"  # Erstatt med Twilio-telefonnummer

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
                 (id TEXT, name TEXT, phone TEXT, role TEXT, points INTEGER)''')
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

def simulate_mower_status():
    total_area = 31000 + 5000
    mowed_area = 20000
    battery = 75
    return {
        "progress": (mowed_area / total_area) * 100,
        "battery": battery,
        "time_left": (total_area - mowed_area) / 1700
    }

def send_sms(phone, message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=phone
        )
        return True
    except TwilioRestException as e:
        st.error(f"Kunne ikke sende SMS: {str(e)}")
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

# Sjekk om bruker er logget inn som frivillig
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

    mower = simulate_mower_status()
    st.subheader("Robotklipper Status")
    st.progress(mower["progress"] / 100)
    st.write(f"Prosent klippet: {mower['progress']:.1f}%")
    st.write(f"Batteri: {mower['battery']}%")
    st.write(f"Estimert tid igjen: {mower['time_left']:.1f} timer")

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
    phone = st.text_input("Mobilnummer (f.eks. +4791234567)")
    role = st.selectbox("Rolle", ["Frivillig", "Administrator"])
    if st.button("Registrer"):
        if name and phone:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            volunteer_id = str(uuid4())
            c.execute("INSERT INTO volunteers (id, name, phone, role, points) VALUES (?, ?, ?, ?, ?)",
                      (volunteer_id, name, phone, role, 0))
            conn.commit()
            conn.close()
            st.success(f"{name} registrert som {role}!")
            send_sms(phone, f"Velkommen til Varanger Golfpark, {name}! Du er registrert som {role}.")
        else:
            st.error("Fyll ut alle felt.")
    
    st.subheader("Registrerte frivillige")
    conn = sqlite3.connect(DB_FILE)
    volunteers = pd.read_sql_query("SELECT name, phone, role, points FROM volunteers", conn)
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
            volunteer_phone = pd.read_sql_query(f"SELECT phone FROM volunteers WHERE name = '{volunteer}'", conn)["phone"].iloc[0]
            conn.close()
            send_sms(volunteer_phone, f"Du er tildelt oppgaven '{task}' på {date}. Poeng: {points}")
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
                volunteer_phone = pd.read_sql_query(f"SELECT phone FROM volunteers WHERE name = '{volunteer}'", conn)["phone"].iloc[0]
                send_sms(volunteer_phone, f"Du er tildelt oppgaven '{task}' på {area} for {date}. Poeng: {points}")
            conn.close()
            st.success("Oppgave lagt til!")
        
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
                    volunteer_phone = pd.read_sql_query(f"SELECT phone FROM volunteers WHERE name = '{new_volunteer}'", conn)["phone"].iloc[0]
                    send_sms(volunteer_phone, f"Oppgaven '{tasks[tasks['id'] == task_id]['task'].iloc[0]}' er markert som fullført. Du får {points} poeng!")
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
