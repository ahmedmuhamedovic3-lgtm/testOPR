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

        users.insert({"username" : username, "password" : password, "admin" : 0, "note" : {}})
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
            session["admin"] = user.get("admin", 0)
            session["notes"] = user["note"]  # Load existing notes into session
            if session["admin"] in (1, 2):
                return redirect("/admin")
            else:
                return redirect("/dashboard")
    return render_template("login.html")

#admin
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")
    if session.get("admin", 0) not in (1, 2):
        return redirect("/dashboard")
    print("all users:", get_all_users())
    return render_template("admin.html", uporabnik = session["user"], users = get_all_users())

#admin user notes view
@app.route("/admin/user/<username>")
def admin_user_notes(username):
    if "user" not in session:
        return redirect("/login")
    if session.get("admin", 0) not in (1, 2):
        return redirect("/dashboard")
    user = users.get(User.username == username)
    if not user:
        return "Uporabnik ne obstaja", 404
    notes = user.get("note", {})
    return render_template("admin_user_notes.html", uporabnik=session["user"], target_user=username, notes=notes)

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
    
    # Check if admin is accessing another user's note
    target_user = request.args.get("user")
    if target_user and session.get("admin", 0) in (1, 2):
        # Admin accessing another user's note
        user = users.get(User.username == target_user)
    else:
        # Regular user accessing their own note
        user = users.get(User.username == session["user"])
        target_user = None
    
    if not user:
        return "Uporabnik ne obstaja", 404
    
    note = user["note"].get(id, "")
    return render_template("editNote.html", id = id, note = note, uporabnik = session["user"], target_user = target_user)

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
    target_user = request.form.get("user", "")
    
    if target_user and session.get("admin", 0) in (1, 2):
        # Admin saving another user's note
        user = users.get(User.username == target_user)
        if user:
            user["note"][id] = {"title": title, "content": content}
            users.update({"note": user["note"]}, User.username == target_user)
    else:
        # Regular user saving their own note
        session["notes"][id] = {"title": title, "content": content}
        session["notes"] = session["notes"]
        users.update({"note": session["notes"]}, User.username == session["user"])
    
    return "OK"

@app.route("/deleteNote", methods = ["POST"])
def deleteNote():
    id = request.form["id"]
    target_user = request.form.get("user", "")
    
    if target_user and session.get("admin", 0) in (1, 2):
        # Admin deleting another user's note
        user = users.get(User.username == target_user)
        if user and id in user["note"]:
            del user["note"][id]
            users.update({"note": user["note"]}, User.username == target_user)
    else:
        # Regular user deleting their own note
        if id in session["notes"]:
            del session["notes"][id]
        session["notes"] = session["notes"]
        users.update({"note": session["notes"]}, User.username == session["user"])
    
    return "OK"

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug = True)