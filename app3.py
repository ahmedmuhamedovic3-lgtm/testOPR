from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__, template_folder="templates3", static_folder="static3")

# SQLAlchemy konfiguracija
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///history3.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "skrivnostniKljucZa3Nalogo"

# Inicializacija baze
db = SQLAlchemy(app)


# =====================================================
# HELPER FUNKCIJE
# =====================================================

def get_client_ip():
    """Vrne IP naslov trenutnega uporabnika"""
    return request.remote_addr


# =====================================================
# ROUTE - dodaj nove route tukaj
# =====================================================

#/ - domača stran
@app.route("/")
def home():
    if request.headers.get('X-Forwarded-For'): 
        ip = request.headers.get('X-Forwarded-For').split(',')[0] 
    else:
        ip = request.remote_addr

    odgovor = requests.get(f"https://free.freeipapi.com/api/json/{ip}")
    data = odgovor.json()
    kraj = data["cityName"]
    lat = data["latitude"]
    lon = data["longitude"]
    return render_template("home.html", kraj=kraj, lat=lat, lon=lon)

#/date/<month>/<day> - dogodki za določen datum
@app.route("/date/<month>/<day>")
def date(month, day):
    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/events.json")
    if odgovor.status_code != 200:
        return f"Napaka: API je vrnil status {odgovor.status_code}", 404
    try:
        data = odgovor.json()
        dogodki = data.get("events", [])
    except requests.exceptions.JSONDecodeError:
        return "Napaka: API ni vrnil veljavnega JSON-a", 500
    return render_template("date.html", month=month, day=day, dogodki=dogodki)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True, port=5003)