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
        notes = user["note"]
        if user and user["password"] == password:
            session["user"] = username
            session["notes"] = notes
            return redirect("/dashboard")
    return render_template("login.html")

#dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    user = users.get(User.username == session["user"])
    session["notes"].update(user["note"])
    print(session, "dash")
    return render_template("dashboard.html", uporabnik = session["user"])

#edit_note
@app.route("/dashboard/<id>")
def editNote(id):
    if "user" not in session:
        return redirect("/login")
    user = users.get(User.username == session["user"])
    #return render_template("dashboard.html", id = id, uporabnik = session["user"])
    note = user["note"].get(id, "")
    print(session, "edit")
    #id = request.args.get('id')
    return render_template("editNote.html", id = id, note = note, uporabnik = session["user"])

#create new note
@app.route("/newNote")
def newNote():
    #{f"{id}title": "", 
    id = str(uuid.uuid4())
    user = users.get(User.username == session["user"])
    session["notes"].update(user["note"])
    print(session, "new1")
    session["notes"].update({id: ""})
    print(session, "new2")
    #user["note"].update({id: ""})
    users.update({"note": session["notes"]}, User.username == session["user"])
    #print(user)
    return redirect(url_for('editNote', id=id))

#save_note
@app.route("/saveNote", methods = ["POST"])
def saveNote():
    note = request.form["note"]
    id = request.form["id"]
    #print(id)
    session["notes"].update({id: note})
    print(session, "save")
    users.update({"note": session["notes"]}, User.username == session["user"])
    return redirect(url_for('editNote', id=id))
#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug = True)