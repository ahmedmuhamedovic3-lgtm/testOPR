from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__, template_folder="templates3", static_folder="static3")

# SQLAlchemy konfiguracija
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db3.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "skrivnostniKljucZa3Nalogo"

# Inicializacija baze
db = SQLAlchemy(app)


# =====================================================
# MODELI
# =====================================================

class Favourite(db.Model):
    """Priljubljeni dogodki"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.String(100), nullable=False)
    event_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Note(db.Model):
    """Beležke uporabnikov"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class History(db.Model):
    """Zgodovina ogledov"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False)
    date_viewed = db.Column(db.String(20), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    # Ustvari bazo če še ne obstaja
    with app.app_context():
        db.create_all()

    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr

    odgovor = requests.get(f"https://free.freeipapi.com/api/json/{ip}")
    data = odgovor.json()
    kraj = data["cityName"]
    lat = data["latitude"]
    lon = data["longitude"]

    x = datetime.now()
    day = x.day
    month = x.month
    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/events.json")
    data = odgovor.json()
    events = data.get("events", [])
    meseci = ['', 'januar', 'februar', 'marec', 'april', 'maj', 'junij',
              'julij', 'avgust', 'september', 'oktober', 'november', 'december']
    monthName = meseci[int(month)]

    return render_template("home.html", kraj=kraj, lat=lat, lon=lon, day=day, month=monthName, events=events)

#/date/<month>/<day> - dogodki za določen datum
@app.route("/events/<month>/<day>")
def date(month, day):
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr

    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/events.json")
    data = odgovor.json()
    events = data.get("events", [])
    meseci = ['', 'januar', 'februar', 'marec', 'april', 'maj', 'junij',
              'julij', 'avgust', 'september', 'oktober', 'november', 'december']
    monthName = meseci[int(month)]

    # Zabeleži ogled v zgodovino (samo enkrat na IP + datum)
    obstojeci = History.query.filter_by(ip_address=ip, date_viewed=f"{monthName}/{day}").first()
    if obstojeci:
        obstojeci.viewed_at = datetime.utcnow()
    else:
        nov_obisk = History(ip_address=ip, date_viewed=f"{monthName}/{day}")
        db.session.add(nov_obisk)
    db.session.commit()

    return render_template("events.html", month=monthName, day=day, events=events)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True, port=5003)