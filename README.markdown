# Varanger Golfpark Vedlikeholdsapp

Denne appen hjelper frivillige i Varanger Golfklubb med å koordinere vedlikehold av golfbanen og driving rangen. Funksjoner inkluderer registrering av frivillige, vaktlister, vedlikeholdsplanlegger med kalendervisning, oppgavehåndtering, simulert robotklipperstatus, værdata fra Yr, banestatus, og gamification med poeng.

## Oppsett

1. **Klon repositoryet** (hvis du bruker Git):
   ```bash
   git clone https://github.com/bapeder/vedlikeholdsapp3.git
   cd vedlikeholdsapp3
   ```
   Alternativt, last ned filene som ZIP fra GitHub og pakk dem ut.

2. **Installer avhengigheter**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurer e-postvarsling**:
   - Opprett en Gmail-konto og aktiver 2-faktor autentisering.
   - Generer et "App Password" i Google-kontoinnstillinger under "Sikkerhet" > "App-passord" (velg "App: Mail", "Enhet: Annen").
   - Oppdater `app.py` med:
     - `SMTP_EMAIL = "din_gmail@gmail.com"`
     - `SMTP_PASSWORD = "din_app_password"`
   - Test e-postkonfigurasjon lokalt:
     ```bash
     python -c "import smtplib; from email.mime.text import MIMEText; msg = MIMEText('Test'); msg['Subject'] = 'Test e-post'; msg['From'] = 'din_gmail@gmail.com'; msg['To'] = 'test@example.com'; with smtplib.SMTP('smtp.gmail.com', 587) as server: server.starttls(); server.login('din_gmail@gmail.com', 'din_app_password'); server.sendmail('din_gmail@gmail.com', 'test@example.com', msg.as_string())"
     ```

4. **Kjør appen lokalt**:
   ```bash
   streamlit run app.py
   ```

5. **For distribusjon**:
   - Last opp til GitHub og distribuer via [Streamlit Community Cloud](https://share.streamlit.io).
   - Velg `app.py` som hovedfil og Python 3.11 i "Advanced Settings" for best kompatibilitet.

## Krav
- Python 3.8 eller nyere (anbefalt: 3.11 for Streamlit Cloud)
- Avhengigheter (se `requirements.txt`):
  - streamlit==1.38.0
  - pandas==2.2.2
  - requests==2.32.3
  - streamlit-calendar==0.4.0
  - numpy==1.26.4

## Konfigurasjon
- **Værdata**: Yr API for værdata i Vadsø (koordinater: 70.1068, 29.3656). Ingen API-nøkkel kreves.
- **E-postvarsling**: Gmail SMTP brukes for varsler. Oppdater SMTP-detaljer i `app.py`.
- **Robotklipper**: Data er simulert. For ekte data, integrer Husqvarna Automower Connect API (krever tilgang).
- **Kalender**: `streamlit-calendar` viser oppgaver i en månedlig kalendervisning.

## Bruk
- **Hjem**: Viser dagens vær, robotklipperstatus og oppgaver.
- **Registrering**: Registrer frivillige med navn, e-post og rolle (Frivillig/Administrator).
- **Vaktlister**: Planlegg vakter og send e-postvarsler.
- **Vedlikeholdsplanlegger**: Administratorer kan opprette og administrere oppgaver med kalendervisning.
- **Oppgaver**: Administrer vedlikeholdsoppgaver for fairways, greener, tees, driving range, rough, og vanningsanlegg.
- **Robotklipper**: Se simulert status eller start klipping i soner.
- **Banestatus**: Rapporter og se status for banen.
- **Vær**: Detaljert værinfo fra Yr.
- **Poengoversikt**: Vis rangering av frivillige basert på poeng.

## Feilsøking
- **SMTP-autentisering feiler**:
  - Sjekk at `SMTP_EMAIL` og `SMTP_PASSWORD` er korrekt i `app.py`.
  - Generer et nytt App Password i Google-kontoinnstillinger.
  - Test e-post manuelt (se oppsett-trinn 3).
  - Sørg for at "Mindre sikker app-tilgang" er deaktivert i Google-kontoen.
  - Sjekk Gmail-sikkerhetsvarsler for mislykkede påloggingsforsøk og godkjenn dem om nødvendig.
- **Kalenderfeil**:
  - Sjekk at `streamlit-calendar==0.4.0` er i `requirements.txt`.
  - Prøv `streamlit-calendar==0.3.1` hvis 0.4.0 feiler.
  - Tving reinstallasjon i Streamlit Cloud ved å legge til en tom linje i `requirements.txt`.
- **Pandas-installasjon henger**:
  - Prøv `pandas==2.2.3` i `requirements.txt` hvis `2.2.2` ikke fungerer.
- **Databasefeil**:
  - Sjekk skrivetilgang til mappen der `golfpark.db` lagres.
  - Kjør `init_db()` manuelt:
    ```bash
    python -c "from app import init_db; init_db()"
    ```

## Merknader
- Mobilvennlig design via `style.css`.
- Oppgaver inkluderer klipping av rough, tilsyn av vanningsanlegg, og generelle oppgaver for fairways og greener.
- Fallback-tabell vises hvis `streamlit-calendar` ikke fungerer.