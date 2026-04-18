from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from random import randrange, choice
import requests
import os
import uuid

app = Flask(__name__, template_folder="templates3", static_folder="static3")

# SQLAlchemy konfiguracija
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////workspaces/testOPR/db3.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "skrivnostniKljucZa3Nalogo"

# Permanent sessions
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)  # 1 year (browser-compatible)

# Inicializacija baze
db = SQLAlchemy(app)

# Ustvari tabele če še ne obstajajo
with app.app_context():
    db.create_all()


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
    date_viewed = db.Column(db.String(50), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
# HELPER FUNKCIJE
# =====================================================

def get_client_ip():
    """Vrne unikatni ID uporabnika iz session-a (vsak brskalnik ima svojega)"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
        session.permanent = True
    return session['user_id']

def get_random_date_advanced():
    start_date = datetime(2024, 1, 1) # Prestopno leto za varnost pri 29. feb
    end_date = datetime(2024, 12, 31)
    
    # Izračunamo razliko v dneh
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    
    # Dodamo naključno število dni začetnemu datumu
    random_number_of_days = randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    
    return random_date.month, random_date.day

def month_name(month):
    meseci = ['', 'januar', 'februar', 'marec', 'april', 'maj', 'junij',
              'julij', 'avgust', 'september', 'oktober', 'november', 'december']
    return meseci[int(month)]


# =====================================================
# ROUTE - dodaj nove route tukaj
# =====================================================

#/ - domača stran
@app.route("/")
def home():
    # Geolokacija potrebuje pravi IP
    real_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
    odgovor = requests.get(f"https://free.freeipapi.com/api/json/{real_ip}")
    data = odgovor.json()
    kraj = data["cityName"]
    lat = data["latitude"]
    lon = data["longitude"]

    x = datetime.now()
    day = x.day
    month = x.month

    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/events.json")
    data = odgovor.json()
    events_list = data.get("events", [])
    
    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/births.json")
    data = odgovor.json()
    births_list = data.get("births", [])

    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/deaths.json")
    data = odgovor.json()
    deaths_list = data.get("deaths", [])

    month = month_name(month)

    return render_template("home.html", kraj=kraj, lat=lat, lon=lon, day=day, month=month, events=events_list, births=births_list, deaths=deaths_list)

#/events - stran z izbiro datuma (ali AJAX za dogodke)
@app.route("/events")
def events():
    # Če je AJAX klic z month/day parametri, vrni JSON
    if request.args.get('month') and request.args.get('day'):
        ip = get_client_ip()
        month = request.args.get('month')
        day = request.args.get('day')
        odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/events.json")
        data = odgovor.json()
        events_list = data.get("events", [])
        monthName = month_name(month)

        # Zabeleži ogled v zgodovino (samo enkrat na IP + datum + tip)
        date_key = f"events/{monthName}/{day}"
        obstojeci = History.query.filter_by(ip_address=ip, date_viewed=date_key).first()
        if obstojeci:
            obstojeci.viewed_at = datetime.utcnow()
        else:
            nov_obisk = History(ip_address=ip, date_viewed=date_key)
            db.session.add(nov_obisk)
        db.session.commit()

        return jsonify({"month": monthName, "day": day, "events": events_list})

    # Običajen obisk - prikaži stran
    return render_template("history.html", type="events", typesl="dogodki")

#/births - stran z izbiro datuma (ali AJAX za dogodke)
@app.route("/births")
def births():
    # Če je AJAX klic z month/day parametri, vrni JSON
    if request.args.get('month') and request.args.get('day'):
        ip = get_client_ip()

        month = request.args.get('month')
        day = request.args.get('day')

        odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/births.json")
        data = odgovor.json()
        births_list = data.get("births", [])
        monthName = month_name(month)

        # Zabeleži ogled v zgodovino (samo enkrat na IP + datum + tip)
        date_key = f"births/{monthName}/{day}"
        obstojeci = History.query.filter_by(ip_address=ip, date_viewed=date_key).first()
        if obstojeci:
            obstojeci.viewed_at = datetime.utcnow()
        else:
            nov_obisk = History(ip_address=ip, date_viewed=date_key)
            db.session.add(nov_obisk)
        db.session.commit()

        return jsonify({"month": monthName, "day": day, "births": births_list})

    # Običajen obisk - prikaži stran
    return render_template("history.html", type="births", typesl="rojstva")

#/deaths - stran z izbiro datuma (ali AJAX za dogodke)
@app.route("/deaths")
def deaths():
    # Če je AJAX klic z month/day parametri, vrni JSON
    if request.args.get('month') and request.args.get('day'):
        ip = get_client_ip()

        month = request.args.get('month')
        day = request.args.get('day')

        odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/deaths.json")
        data = odgovor.json()
        deaths_list = data.get("deaths", [])
        monthName = month_name(month)

        # Zabeleži ogled v zgodovino (samo enkrat na IP + datum + tip)
        date_key = f"deaths/{monthName}/{day}"
        obstojeci = History.query.filter_by(ip_address=ip, date_viewed=date_key).first()
        if obstojeci:
            obstojeci.viewed_at = datetime.utcnow()
        else:
            nov_obisk = History(ip_address=ip, date_viewed=date_key)
            db.session.add(nov_obisk)
        db.session.commit()

        return jsonify({"month": monthName, "day": day, "deaths": deaths_list})

    # Običajen obisk - prikaži stran
    return render_template("history.html", type="deaths", typesl="smrti")

#naključno
@app.route("/random")
def random_event():
    ip = get_client_ip()

    # Pridobi naključen datum
    month, day = get_random_date_advanced()

    # Izbiraj med dogodki, rojstva in smrti, da bo bolj zanimivo
    tip = choice(["events", "births", "deaths"])
    if tip == "events":
        typesl = "dogodki"
    elif tip == "births":
        typesl = "rojstva"
    else:
        typesl = "smrti"

    # Pridobi podatke za ta datum
    odgovor = requests.get(f"https://byabbe.se/on-this-day/{month}/{day}/{tip}.json")
    data = odgovor.json()
    items = data.get(tip, [])

    # Slovensko ime meseca za prikaz
    monthName = month_name(month)

    # Zabeleži ogled v zgodovino (samo enkrat na IP + datum + tip)
    date_key = f"random/{monthName}/{day}"
    obstojeci = History.query.filter_by(ip_address=ip, date_viewed=date_key).first()
    if obstojeci:
        obstojeci.viewed_at = datetime.utcnow()
    else:
        nov_obisk = History(ip_address=ip, date_viewed=date_key)
        db.session.add(nov_obisk)
    db.session.commit()

    return render_template("history.html", objects=items, type=tip, typesl=typesl, month=monthName, day=day)

#priljubljeni dogodki
@app.route("/favourites", methods=["GET", "POST"])
def favourites():
    if request.method == "POST":
        ip = get_client_ip()

        # Sprejmi form data (jQuery pošilja kot form-encoded)
        event_type = request.form.get("type", "")
        year = request.form.get("year", "")
        description = request.form.get("description", "")
        wikipedia = request.form.get("wikipedia", "[]")

        # Ustvari unikatni event_id iz tipa in leta/opisa
        event_id = f"{event_type}_{year}_{description[:50]}"

        # Shrani celoten dogodek kot JSON string
        import json
        event_data = json.dumps({
            "type": event_type,
            "year": year,
            "description": description,
            "wikipedia": json.loads(wikipedia)
        })

        # Preveri ali že obstaja v priljubljenih
        obstojeci = Favourite.query.filter_by(ip_address=ip, event_id=event_id).first()
        if obstojeci:
            db.session.delete(obstojeci)
            db.session.commit()
            return jsonify({"message": "Dogodek odstranjen iz priljubljenih"})

        nov_fav = Favourite(ip_address=ip, event_id=event_id, event_data=event_data)
        db.session.add(nov_fav)
        db.session.commit()
        return jsonify({"message": "Dogodek dodan med priljubljene"})

    # GET - prikaži priljubljene dogodke
    import json
    ip = get_client_ip()
    priljubljeni = Favourite.query.filter_by(ip_address=ip).all()

    # Parse JSON event_data za prikaz v predlogi
    parsed_favourites = []
    for fav in priljubljeni:
        try:
            parsed_favourites.append(json.loads(fav.event_data))
        except (json.JSONDecodeError, TypeError):
            parsed_favourites.append({"year": "?", "description": fav.event_data, "wikipedia": []})

    return render_template("favourites.html", favourites=parsed_favourites)

#zgodovina ogledov
@app.route("/history")
def history():
    ip = get_client_ip()
    zgodovina = History.query.filter_by(ip_address=ip).order_by(History.viewed_at.desc()).all()
    return render_template("user_history.html", history=zgodovina)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True, port=5003)