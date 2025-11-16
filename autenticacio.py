import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# 🔄 Carrega variables d'entorn locals (només en desenvolupament)
load_dotenv()

# 🔐 Credencials OAuth llegides des de variables d'entorn
client_config = {
    "installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

# 🔒 Escopes necessaris
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# 🔁 Inicia el flux OAuth
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

# 💾 Desa el token.json
with open("token.json", "w") as token_file:
    token_file.write(creds.to_json())

print("✅ token.json generat correctament.")
