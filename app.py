from flask import Flask, render_template, request, redirect, session, url_for
from tinydb import TinyDB, Query
import uuid

app = Flask(__name__)
app.secret_key = "skrivamoTaKljuč"

db = TinyDB("db.json")
all_data = db.all()
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

        users.insert({"username" : username, "password" : password, "note" : {}})
        return redirect("/login")

    return render_template("register.html")

#login
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"] # shranimo spremenljivke iz prijave
        password = request.form["password"]

        user = users.get(User.username == username)
        if user and user["password"] == password:
            session["user"] = username
            session["notes"] = user["note"]  # Load existing notes into session
            if password == "admin":
                return redirect("/admin")
            else:
                return redirect("/dashboard")
    return render_template("login.html")

#admin
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")
    if session["user"] != "admin":
        return redirect("/dashboard")
    print("all users:", get_all_users())
    return render_template("admin.html", uporabnik = session["user"], users = get_all_users())

#dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    print("all users:", get_all_users())
    user = users.get(User.username == session["user"])
    notes = user["note"]
    #print(notes)
    #print(session, "dash")
    return render_template("dashboard.html", uporabnik = session["user"], notes = notes)

def get_all_users():
    return users.all()

#edit_note
@app.route("/dashboard/<id>")
def editNote(id):
    if "user" not in session:
        return redirect("/login")
    user = users.get(User.username == session["user"])
    #return render_template("dashboard.html", id = id, uporabnik = session["user"])
    note = user["note"].get(id, "")
    #print(session, "edit")
    #id = request.args.get('id')
    return render_template("editNote.html", id = id, note = note, uporabnik = session["user"])

#create new note
@app.route("/newNote")
def newNote():
    id = str(uuid.uuid4())
    # Add the new empty note to the session notes
    session["notes"][id] = {"title":"", "content":""}
    # Reassign to make Flask detect the session change
    session["notes"] = session["notes"]
    # Update the database with all notes including the new one
    users.update({"note": session["notes"]}, User.username == session["user"])
    return redirect(url_for('editNote', id=id))

#save_note
@app.route("/saveNote", methods = ["POST"])
def saveNote():
    title = request.form["title"]
    content = request.form["content"]
    id = request.form["id"]
    # Update the note in session
    session["notes"][id] = {"title": title, "content": content}
    # Reassign to make Flask detect the session change
    session["notes"] = session["notes"]
    # Save all notes to the database
    users.update({"note": session["notes"]}, User.username == session["user"])
    return redirect(url_for('editNote', id=id))

@app.route("/deleteNote", methods = ["POST"])
def deleteNote():
    id = request.form["id"]
    # Remove the note from session
    if id in session["notes"]:
        del session["notes"][id]
    # Reassign to make Flask detect the session change
    session["notes"] = session["notes"]
    # Save all notes to the database
    users.update({"note": session["notes"]}, User.username == session["user"])
    return redirect(url_for('dashboard'))

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug = True)