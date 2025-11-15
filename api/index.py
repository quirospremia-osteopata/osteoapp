from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
import re
import calendar
import requests

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

print("✅ Flask ha arrencat")  # Forcem traça al log

app = Flask(__name__)

@app.route('/test')
def test():
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

        return jsonify({
            "client_id": client_id[:10] + "..." if client_id else None,
            "calendar_id": calendar_id,
            "refresh_token_present": bool(refresh_token)
        })
    except Exception as e:
        print("❌ Error a /test:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dia')
def dia():
    date_str = request.args.get('date')
    if date_str == 'avui' or not date_str:
        dia_obj = datetime.today()
    else:
        dia_obj = datetime.strptime(date_str, '%Y-%m-%d')

    dia_en = dia_obj.strftime('%A').capitalize()
    dia_setmana_cat = DIES_CAT.get(dia_en, dia_en)
    mes_cat = MESOS_CAT[dia_obj.month]
    dia_fmt = f"{dia_setmana_cat} {dia_obj.day} de {mes_cat} de {dia_obj.year}"

    dia_anterior = (dia_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    dia_seguent = (dia_obj + timedelta(days=1)).strftime('%Y-%m-%d')

    cites = get_cites_dia(dia_obj.strftime('%Y-%m-%d'))

    return render_template('dia.html',
        dia_fmt=dia_fmt,
        raw_date=dia_obj.strftime('%Y-%m-%d'),
        dia_anterior=dia_anterior,
        dia_seguent=dia_seguent,
        cites=cites
    )

@app.route('/calendari')
def calendari():
    return render_template('index.html')

DIES_CAT = {
    'Monday': 'Dilluns', 'Tuesday': 'Dimarts', 'Wednesday': 'Dimecres',
    'Thursday': 'Dijous', 'Friday': 'Divendres', 'Saturday': 'Dissabte', 'Sunday': 'Diumenge'
}

MESOS_CAT = {
    1: 'Gener', 2: 'Febrer', 3: 'Març', 4: 'Abril',
    5: 'Maig', 6: 'Juny', 7: 'Juliol', 8: 'Agost',
    9: 'Setembre', 10: 'Octubre', 11: 'Novembre', 12: 'Desembre'
}

os.environ["LC_TIME"] = "C"

PLANTILLES = {
    "confirmacio": """✅Hola {{nom}}, has reservat correctament el {{dia}} a les {{hora}}.

📌 Carrer de l'Eixample, 37, 08330 Premià de Mar

⏰ La cancel·lació és gratuïta fins a 24 h abans. 

Si tens dubtes, pots respondre aquest missatge. Fins aviat!""",

    "recordatori": """⏰Bon dia {{nom}}, et recordem que demà dia {{dia}} a les {{hora}}, tens cita a:

📌 Carrer de l'Eixample, 37, 08330 Premià de Mar

👕 Porta pantaló curt o roba molt còmoda.

💶 Recorda portar 60€ en metàl·lic.

❗ Aquesta cita ja no es pot cancel·lar. 

Gràcies per la teva confiança! ⭐""",

    "fidelitzacio": """Hola {{nom}}, espero que hagi estat tot al teu gust.

Si vols, pots deixar una ressenya personal a Google.

Gràcies per ajudar-nos a créixer i per confiar en nosaltres!

https://g.page/r/CcSAOGuyaArMEAE/review 

⭐⭐⭐⭐⭐""",

    "cancelacio": """❌ Hola {{nom}}, la teva cita del dia {{dia}} a les {{hora}} ha estat cancelada correctament! 

Si vols reprogramar-la, escriu-nos i busquem una nova data.

Disculpa les molèsties i gràcies per la teva comprensió."""
}

def get_google_credentials():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    token_uri = "https://oauth2.googleapis.com/token"

    if not all([client_id, client_secret, refresh_token]):
        print("❌ Falten variables d'entorn per a l'autenticació")
        return None

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    try:
        response = requests.post(token_uri, data=data)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        return creds
    except Exception as e:
        print("❌ Error refrescant token:", e)
        return None

def get_cites_dia(date_str):
    try:
        creds = get_google_credentials()
        if not creds:
            return []

        service = build('calendar', 'v3', credentials=creds)
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

        dia_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start = dia_obj.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end = (dia_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'

        dia_en = dia_obj.strftime('%A').capitalize()
        dia_setmana_cat = DIES_CAT.get(dia_en, dia_en)
        mes_cat = MESOS_CAT[dia_obj.month]
        dia_fmt = f"{dia_setmana_cat} {dia_obj.day} de {mes_cat} de {dia_obj.year}"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime',
            fields='items(start,summary,description,location)'
        ).execute()

        events = events_result.get('items', [])
        cites = []

        for event in events:
            start_raw = event['start'].get('dateTime') or event['start'].get('date')
            hora = start_raw[11:16] if 'T' in start_raw else 'Sense hora'

            text = ' '.join([
                event.get('summary', ''),
                event.get('description', ''),
                event.get('location', '')
            ])

            match = re.search(r'(\+?\d[\d\s\-().]{8,})', text)
            if match:
                tel_raw = match.group(1)
                tel = re.sub(r'\D', '', tel_raw)
                if tel.startswith('34'):
                    tel = '+' + tel
                elif tel.startswith('6') or tel.startswith('7'):
                    tel = '+34' + tel
                else:
                    tel = '+' + tel
                nom_complet = event.get('summary', '').replace(match.group(1), '').strip()
            else:
                tel = ''
                nom_complet = event.get('summary', '').strip()

            nom_net = re.sub(r'[^\w\sÀ-ÿ]', '', nom_complet)
            nom_pila = nom_net.split()[0] if nom_net else 'client'

            missatges = {}
            for clau, plantilla in PLANTILLES.items():
                text = plantilla.replace("{{nom}}", nom_pila).replace("{{dia}}", dia_fmt).replace("{{hora}}", hora)
                missatges[clau] = text

            cites.append({
                "hora": hora,
                "nom": nom_complet,
                "nom_net": nom_net,
                "nom_pila": nom_pila,
                "tel": tel,
                "missatges": missatges
            })

        return cites
    except Exception as e:
        print("❌ Error accedint a Google Calendar:", e)
        return []
