import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from waitress import serve

from consts import DIES_CAT, MESOS_CAT, get_cites_dia

load_dotenv()  # Load environment variables from .env file
print("✅ Flask ha arrencat")  # Forcem traça al log

app = Flask(__name__, template_folder="templates")


@app.route("/test")
def test():
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

        return jsonify(
            {
                "client_id": client_id[:10] + "..." if client_id else None,
                "calendar_id": calendar_id,
                "refresh_token_present": bool(refresh_token),
            }
        )
    except Exception as e:
        print("❌ Error a /test:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dia")
def dia():
    date_str = request.args.get("date")
    if date_str == "avui" or not date_str:
        dia_obj = datetime.today()
    else:
        dia_obj = datetime.strptime(date_str, "%Y-%m-%d")

    dia_en = dia_obj.strftime("%A").capitalize()
    dia_setmana_cat = DIES_CAT.get(dia_en, dia_en)
    mes_cat = MESOS_CAT[dia_obj.month]
    dia_fmt = f"{dia_setmana_cat} {dia_obj.day} de {mes_cat} de {dia_obj.year}"

    dia_anterior = (dia_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    dia_seguent = (dia_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    cites = get_cites_dia(dia_obj.strftime("%Y-%m-%d"))

    return render_template(
        "dia.html",
        dia_fmt=dia_fmt,
        raw_date=dia_obj.strftime("%Y-%m-%d"),
        dia_anterior=dia_anterior,
        dia_seguent=dia_seguent,
        cites=cites,
    )


@app.route("/calendari")
def calendari():
    return render_template("index.html")


if __name__ == "__main__":

    load_dotenv()  # Ensure environment variables are loaded
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8080))
    socket = os.getenv("SOCKET", None)

    if socket:
        host = "unix://" + socket
        port = None
        print(f"Listening on socket {socket}...")
        serve(
            app,
            socket=socket,
        )
    else:
        print(f"Listening on port http://{host}:{port}...")
        serve(
            app,
            host=host,
            port=port,
        )
