from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os
import re
import calendar

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# ✅ Diccionaris en català
DIES_CAT = {
    'Monday': 'Dilluns', 'Tuesday': 'Dimarts', 'Wednesday': 'Dimecres',
    'Thursday': 'Dijous', 'Friday': 'Divendres', 'Saturday': 'Dissabte', 'Sunday': 'Diumenge'
}

MESOS_CAT = {
    1: 'Gener', 2: 'Febrer', 3: 'Març', 4: 'Abril',
    5: 'Maig', 6: 'Juny', 7: 'Juliol', 8: 'Agost',
    9: 'Setembre', 10: 'Octubre', 11: 'Novembre', 12: 'Desembre'
}

# ✅ Configuració regional segura per Vercel
os.environ["LC_TIME"] = "C"

# ✅ Missatges WhatsApp
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

# ✅ Obtenir cites des de Google Calendar
def get_cites_dia(date_str):
    try:
        creds = Credentials.from_authorized_user_file('token.json')
        service = build('calendar', 'v3', credentials=creds)

        dia_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start = dia_obj.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end = (dia_obj + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'

        dia_en = dia_obj.strftime('%A').capitalize()
        dia_setmana_cat = DIES_CAT.get(dia_en, dia_en)
        mes_cat = MESOS_CAT[dia_obj.month]
        dia_fmt = f"{dia_setmana_cat} {dia_obj.day} de {mes_cat} de {dia_obj.year}"

        events_result = service.events().list(
            calendarId='primary',
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime',
            fields='items(start,summary,description,location)'
        ).execute()

        events = events_result.get('items', [])
        cites = []

        for event in events:
            hora = event['start'].get('dateTime', event['start'].get('date'))[11:16]
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
        print("Error accedint a Google Calendar:", e)
        return []

@app.route('/')
def index():
    return dia()

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
                           cites=cites)

@app.route('/calendari')
def calendari():
    mes_str = request.args.get('mes')
    if mes_str:
        any, mes = map(int, mes_str.split('-'))
        data = datetime(any, mes, 1)
    else:
        data = datetime.today()

    mes_actual = f"{MESOS_CAT[data.month]} {data.year}"
    mes_anterior = (data - timedelta(days=1)).strftime('%Y-%m')
    mes_seguent = (data + timedelta(days=31)).strftime('%Y-%m')
    avui = datetime.today().strftime('%Y-%m-%d')

    dies = generar_dies_del_mes(data)

    return render_template('calendari.html',
        mes_actual=mes_actual,
        mes_anterior=mes_anterior,
        mes_seguent=mes_seguent,
        avui=avui,
        dies=dies
    )

def generar_dies_del_mes(data):
    primer = data.replace(day=1)
    inici = primer.weekday()
    if data.month == 12:
        fi = data.replace(year=data.year + 1, month=1, day=1)
    else:
        fi = data.replace(month=data.month + 1, day=1)
    total = (fi - primer).days

    dies = []
    for _ in range(inici):
        dies.append(None)
    for i in range(1, total + 1):
        dia = primer.replace(day=i)
        dies.append({
            'date': dia.strftime('%Y-%m-%d'),
            'num': i,
            'avui': dia.date() == datetime.today().date()
        })
    return dies

# ✅ Exposa l'aplicació per a Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True)
