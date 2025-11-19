import os
import re
from datetime import datetime, timedelta

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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
        if response.status_code != 200:
            # Intenta mostrar informació detallada de l'error de Google
            try:
                err = response.json()
            except Exception:
                err = {"raw": response.text}
            print(
                "❌ Error refrescant token (HTTP {}): {}".format(
                    response.status_code, err
                )
            )
            return None
        token_data = response.jsozn()

        access_token = token_data.get("access_token")
        if not access_token:
            print("❌ No s'ha rebut access_token")
            return None

        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        return creds

    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petició HTTP: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(f"   Resposta del servidor: {e.response.json()}")
            except Exception:
                print(f"   Resposta del servidor: {e.response.text}")
        return None
    except KeyError as e:
        print(f"❌ Error: clau no trobada a la resposta - {e}")
        return None


def _mask(value: str, keep: int = 6):
    if not value:
        return None
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "..." + (value[-3:] if len(value) > keep + 3 else "")


def verify_google_oauth_config():
    """Verifica que les variables d'entorn de Google OAuth siguin coherents i funcionals.

    Retorna un diccionari amb:
      - ok: bool
      - status: http status del refresh si s'ha provat
      - error: missatge (si n'hi ha)
      - error_description: si Google el proporciona
      - details: informació addicional
      - env: valors enmascarats de les variables
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")

    result = {
        "ok": False,
        "env": {
            "GOOGLE_CLIENT_ID": _mask(client_id or ""),
            "GOOGLE_CLIENT_SECRET": _mask(client_secret or ""),
            "GOOGLE_REFRESH_TOKEN_present": bool(refresh_token),
            "GOOGLE_CALENDAR_ID": calendar_id,
        },
        "details": {},
    }

    # Validacions bàsiques de format
    issues = []
    if not client_id:
        issues.append("Falta GOOGLE_CLIENT_ID")
    elif not re.match(r"^\d+-[\w-]+\.apps\.googleusercontent\.com$", client_id):
        issues.append("Format de GOOGLE_CLIENT_ID inesperat")

    if not client_secret:
        issues.append("Falta GOOGLE_CLIENT_SECRET")

    if not refresh_token:
        issues.append("Falta GOOGLE_REFRESH_TOKEN")

    if issues:
        result["error"] = "; ".join(issues)
        return result

    # Prova de refresh token directament contra Google
    token_uri = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        resp = requests.post(token_uri, data=data)
        result["status"] = resp.status_code
        if resp.status_code == 200:
            j = resp.json()
            result["ok"] = True
            result["details"]["scopes"] = j.get("scope")
            result["details"]["token_type"] = j.get("token_type")
            return result
        else:
            try:
                j = resp.json()
            except Exception:
                j = {"raw": resp.text}
            result["error"] = j.get("error") or "refresh_failed"
            result["error_description"] = j.get("error_description") or j
            # Suggeriments comuns
            suggestions = []
            if result["error"] in {"invalid_client", "unauthorized_client"}:
                suggestions.append(
                    "Revisa que CLIENT_ID i SECRET coincideixin amb el projecte on es va obtenir el refresh_token."
                )
            if result["error"] in {"invalid_grant"}:
                suggestions.append(
                    "El refresh_token pot ser invàlid, revocat o pertànyer a unes credencials diferents. Torna a generar-lo."
                )
            if not calendar_id:
                suggestions.append("Falta GOOGLE_CALENDAR_ID o usa 'primary'.")
            result["details"]["suggestions"] = suggestions
            return result
    except requests.exceptions.RequestException as e:
        result["error"] = "http_request_error"
        result["error_description"] = str(e)
        return result
    except Exception as e:
        print(f"❌ Error refrescant token: {e}")
        return None


def get_cites_dia(date_str):
    try:
        creds = get_google_credentials()
        if not creds:
            return None

        service = build("calendar", "v3", credentials=creds)
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

        dia_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start = dia_obj.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = (dia_obj + timedelta(days=1)).replace(
            hour=0, minute=0, second=0
        ).isoformat() + "Z"

        dia_en = dia_obj.strftime("%A").capitalize()
        dia_setmana_cat = DIES_CAT.get(dia_en, dia_en)
        mes_cat = MESOS_CAT[dia_obj.month]
        dia_fmt = f"{dia_setmana_cat} {dia_obj.day} de {mes_cat} de {dia_obj.year}"

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
                fields="items(start,summary,description,location)",
            )
            .execute()
        )

        events = events_result.get("items", [])
        cites = []

        for event in events:
            start_raw = event["start"].get("dateTime") or event["start"].get("date")
            hora = start_raw[11:16] if "T" in start_raw else "Sense hora"

            text = " ".join(
                [
                    event.get("summary", ""),
                    event.get("description", ""),
                    event.get("location", ""),
                ]
            )

            match = re.search(r"(\+?\d[\d\s\-().]{8,})", text)
            if match:
                tel_raw = match.group(1)
                tel = re.sub(r"\D", "", tel_raw)
                if tel.startswith("34"):
                    tel = "+" + tel
                elif tel.startswith("6") or tel.startswith("7"):
                    tel = "+34" + tel
                else:
                    tel = "+" + tel
                nom_complet = (
                    event.get("summary", "").replace(match.group(1), "").strip()
                )
            else:
                tel = ""
                nom_complet = event.get("summary", "").strip()

            nom_net = re.sub(r"[^\w\sÀ-ÿ]", "", nom_complet)
            nom_pila = nom_net.split()[0] if nom_net else "client"

            missatges = {}
            for clau, plantilla in PLANTILLES.items():
                text = (
                    plantilla.replace("{{nom}}", nom_pila)
                    .replace("{{dia}}", dia_fmt)
                    .replace("{{hora}}", hora)
                )
                missatges[clau] = text

            cites.append(
                {
                    "hora": hora,
                    "nom": nom_complet,
                    "nom_net": nom_net,
                    "nom_pila": nom_pila,
                    "tel": tel,
                    "missatges": missatges,
                }
            )

        return cites
    except Exception as e:
        print("❌ Error accedint a Google Calendar:", e)
        return None
