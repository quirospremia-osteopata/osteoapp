import os

import requests
from google.oauth2.credentials import Credentials

DIES_CAT = {
    "Monday": "Dilluns",
    "Tuesday": "Dimarts",
    "Wednesday": "Dimecres",
    "Thursday": "Dijous",
    "Friday": "Divendres",
    "Saturday": "Dissabte",
    "Sunday": "Diumenge",
}

MESOS_CAT = {
    1: "Gener",
    2: "Febrer",
    3: "Març",
    4: "Abril",
    5: "Maig",
    6: "Juny",
    7: "Juliol",
    8: "Agost",
    9: "Setembre",
    10: "Octubre",
    11: "Novembre",
    12: "Desembre",
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

Disculpa les molèsties i gràcies per la teva comprensió.""",
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
        "grant_type": "refresh_token",
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
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return creds
    except Exception as e:
        print("❌ Error refrescant token:", e)
        return None
