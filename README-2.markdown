# Varanger Golfpark Vedlikeholdsapp

Denne appen hjelper frivillige i Varanger Golfklubb med å koordinere vedlikehold av golfbanen og driving rangen. Funksjoner inkluderer registrering av frivillige, vaktlister, vedlikeholdsplanlegger, oppgavehåndtering, robotklipperstatus (simulert), værdata fra Yr, banestatus, og gamification med poeng.

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

3. **Konfigurer Twilio for SMS**:
   - Opprett en konto på [Twilio](https://www.twilio.com).
   - Oppdater `app.py` med `TWILIO_SID`, `TWILIO_AUTH_TOKEN`, og `TWILIO_PHONE`.

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
  - twilio==9.3.0

## Konfigurasjon
- **Værdata**: Yr API (MET Weather API) for værdata i Vadsø (koordinater: 70.1068, 29.3656). Ingen API-nøkkel kreves, men User-Agent (`VarangerGolfparkApp/1.0 kontakt@varangergolfklubb.no`) er konfigurert.
- **SMS**: Twilio brukes for SMS-varsling. Oppdater `TWILIO_SID`, `TWILIO_AUTH_TOKEN`, og `TWILIO_PHONE` i `app.py`.
- **Robotklipper**: Data er simulert. For ekte data, integrer Husqvarna Fleet Services API (krever tilgang).

## Bruk
- **Hjem**: Viser dagens vær, robotklipperstatus og oppgaver.
- **Registrering**: Registrer frivillige med navn, mobilnummer og rolle (Frivillig/Administrator).
- **Vaktlister**: Planlegg vakter og send SMS-varsler.
- **Vedlikeholdsplanlegger**: Administratorer kan opprette og administrere oppgaver (inkludert klipping av rough, tilsyn vanningsanlegg).
- **Oppgaver**: Administrer vedlikeholdsoppgaver for fairways, greener, tees, driving range, rough, og vanningsanlegg.
- **Robotklipper**: Se simulert status eller start klipping i soner.
- **Banestatus**: Rapporter og se status for banen.
- **Vær**: Detaljert værinfo fra Yr med vedlikeholdsanbefalinger.
- **Poengoversikt**: Vis rangering av frivillige basert på poeng for utførte oppgaver.