# Varanger Golfpark Vedlikeholdsapp

Denne appen hjelper frivillige i Varanger Golfklubb med å koordinere vedlikehold av golfbanen og driving rangen. Funksjoner inkluderer registrering av frivillige, vaktlister, vedlikeholdsplanlegger med kalendervisning, oppgavehåndtering, simulert robotklipperstatus, værdata fra Yr, banestatus, og gamification med poeng.

## Oppsett

1. **Klon repositoryet** (hvis du bruker Git):
   ```bash
   git clone https://github.com/DITT_BRUKERNAVN/varanger-golfpark-app.git
   cd varanger-golfpark-app
   ```
   Alternativt, last ned filene som ZIP fra GitHub og pakk dem ut.

2. **Installer avhengigheter**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurer e-postvarsling**:
   - Opprett en Gmail-konto og generer et "App Password" (krever 2-faktor autentisering).
   - Oppdater `app.py` med:
     - `SMTP_EMAIL = "din_gmail@gmail.com"`
     - `SMTP_PASSWORD = "din_app_password"`

4. **Kjør appen lokalt**:
   ```bash
   streamlit run app.py
   ```

5. **For distribusjon**:
   - Last opp til GitHub og distribuer via [Streamlit Community Cloud](https://share.streamlit.io).
   - Velg `app.py` som hovedfil i Streamlit Cloud.

## Krav
- Python 3.8 eller nyere
- Avhengigheter (se `requirements.txt`):
  - streamlit==1.38.0
  - pandas==2.2.2
  - requests==2.32.3
  - sqlite3
  - streamlit-calendar==0.3.1

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

## Merknader
- Mobilvennlig design via `style.css`.
- Oppgaver inkluderer klipping av rough, tilsyn av vanningsanlegg, og generelle oppgaver for fairways og greener.