# Varanger Golfpark Vedlikeholdsapp

Denne appen hjelper frivillige i Varanger Golfklubb med å koordinere vedlikehold av golfbanen og driving rangen. Funksjoner inkluderer vaktlister, oppgavehåndtering, robotklipperstatus (simulert), værdata fra Yr, og banestatus.

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

3. **Kjør appen lokalt**:
   ```bash
   streamlit run app.py
   ```

4. **For distribusjon**:
   - Last opp til GitHub og distribuer via [Streamlit Community Cloud](https://share.streamlit.io).
   - Velg `app.py` som hovedfil i Streamlit Cloud.

## Krav
- Python 3.8 eller nyere
- Avhengigheter (se `requirements.txt`):
  - streamlit==1.38.0
  - pandas==2.2.2
  - requests==2.32.3
  - sqlite3

## Konfigurasjon
- **Værdata**: Appen bruker Yr API (MET Weather API) for værdata i Vadsø (koordinater: 70.1068, 29.3656). Ingen API-nøkkel kreves, men en User-Agent (`VarangerGolfparkApp/1.0 kontakt@varangergolfklubb.no`) er konfigurert.
- **Robotklipper**: Data er simulert. For ekte data, integrer Husqvarna Fleet Services API (krever tilgang).

## Bruk
- **Hjem**: Viser dagens vær, robotklipperstatus og oppgaver.
- **Vaktlister**: Planlegg frivillige vakter.
- **Oppgaver**: Administrer vedlikeholdsoppgaver for fairways, greener, tees og driving range.
- **Robotklipper**: Se simulert status eller start klipping i soner.
- **Banestatus**: Rapporter og se status for banen.
- **Vær**: Detaljert værinfo fra Yr med vedlikeholdsanbefalinger.