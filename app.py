from flask import Flask, render_template, request, redirect, session, url_for
from tinydb import TinyDB, Query
import uuid

app = Flask(__name__)
app.secret_key = "skrivamoTaKljuč"

db = TinyDB("db.json")
users = db.table("users")

User = Query()

#home
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")
#register
@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"] # shranimo spremenljivke iz registracije
        password = request.form["password"]
        #print(username, password)

        if users.search(User.username == username):
            return "Uporabnik obstaja"

        users.insert({"username" : username, "password" : password, "note" : None})
        return redirect("/login")

    return render_template("register.html")

#login
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"] # shranimo spremenljivke iz prijave
        password = request.form["password"]

        user = users.get(User.username == username)
        #print(user)
        if user and user["password"] == password:
            session["user"] = username
            return redirect("/dashboard")
    return render_template("login.html")

#dashboard


#edit_note
@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")
    user = users.get(User.username == session["user"])
    if request.method == "POST":
        edit = request.form["edit"]
        return redirect("/dashboard")
    if edit == "0":
        return render_template("dashboard.html", id = id, uporabnik = session["user"])
    note = user["note"].get("563812a5-ee16-4816-af38-f11099536da0", "")
    id = request.args.get('id')
    return render_template("editNote.html", id = id, note = note, uporabnik = session["user"])

#create new note
@app.route("/newNote")
def newNote():
    id = str(uuid.uuid4())
    users.update({"note": {id : ""}}, User.username == session["user"])
    return redirect(url_for('dashboard', id=id))

#save_note
@app.route("/saveNote", methods = ["POST"])
def saveNote():
    note = request.form["note"]
    users.update({"note": {"563812a5-ee16-4816-af38-f11099536da0": note}}, User.username == session["user"])
    return "SAVED"
#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug = True)