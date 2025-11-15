import re
from datetime import date

def netejar_nom(nom):
    """
    Elimina emojis, símbols i espais innecessaris del nom.
    Exemple: "💪 Joan 😊" → "Joan"
    """
    return re.sub(r'[^\w\s]', '', nom).strip()

def format_dia(dia: date) -> str:
    """
    Retorna el dia en format català: 'Dijous 13/11/2025'
    """
    dies_setmana = ['Dilluns', 'Dimarts', 'Dimecres', 'Dijous', 'Divendres', 'Dissabte', 'Diumenge']
    nom_dia = dies_setmana[dia.weekday()]
    return f"{nom_dia} {dia.day:02d}/{dia.month:02d}/{dia.year}"

def generar_missatges(nom, hora):
    """
    Retorna un diccionari amb missatges personalitzats per WhatsApp.
    """
    return {
        "confirmacio": f"✅ Hola {nom}, confirmem la teva cita a les {hora}.",
        "recordatori": f"🕣 Recordatori: tens cita a les {hora}.",
        "fidelitzacio": f"⭐ Gràcies per confiar en nosaltres, {nom}!",
        "cancelacio": f"❌ La teva cita de les {hora} ha estat cancel·lada."
    }
