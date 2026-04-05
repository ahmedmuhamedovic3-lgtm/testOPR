from flask import Flask, render_template, request, redirect, session, url_for
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import threading

app = Flask(__name__)
app.secret_key = "skrivamoTaKljuč"

db = TinyDB("db.json")
all_data = db.all()
users = db.table("users")

db_lock = threading.Lock()

User = Query()

#home
@app.route("/")
def home():
    if users:
        if "user" in session:
            return redirect("/dashboard")
        return redirect("/login")
    return redirect("/register")
#register
@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"] # shranimo spremenljivke iz registracije
        password = request.form["password"]
        #print(username, password)

        if users.search(User.username == username):
            return render_template("register.html", error="Uporabniško ime že obstaja")

        users.insert({"username" : username, "password" : generate_password_hash(password), "admin" : 0, "note" : {}})
        return redirect("/login")

    return render_template("register.html")

#login
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"] # shranimo spremenljivke iz prijave
        password = request.form["password"]

        user = users.get(User.username == username)
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["admin"] = user.get("admin", 0)
            return redirect("/dashboard")
        return render_template("login.html", error="Napačno uporabniško ime ali geslo")
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
    return render_template("admin_user_notes.html", uporabnik=session["user"], target_user=username, notes=notes, admin=session.get("admin", 0), target_admin=user.get("admin", 0))

@app.route("/admin/updateRole", methods=["POST"])
def update_user_role():
    username = request.form["username"]
    new_role = int(request.form["role"])
    with db_lock:
        user = users.get(User.username == username)
        if user:
            users.update({"admin": new_role}, User.username == username)
    return "OK"

#dashboard
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    print("all users:", get_all_users())
    user = users.get(User.username == session["user"])
    notes = user["note"]
    #print(notes)
    print(session, "dash")
    return render_template("dashboard.html", uporabnik = session["user"], notes = notes, admin = session.get("admin", 0))

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
    with db_lock:
        user = users.get(User.username == session["user"])
        notes = user.get("note", {})
        notes[id] = {"title": "", "content": ""}
        users.update({"note": notes}, User.username == session["user"])
    return redirect(url_for('editNote', id=id))

#save_note
@app.route("/saveNote", methods = ["POST"])
def saveNote():
    title = request.form["title"]
    content = request.form["content"]
    id = request.form["id"]
    target_user = request.form.get("user", "")

    with db_lock:
        if target_user and session.get("admin", 0) in (1, 2):
            # Admin saving another user's note
            user = users.get(User.username == target_user)
            if user:
                user["note"][id] = {"title": title, "content": content}
                users.update({"note": user["note"]}, User.username == target_user)
        else:
            # User saving their own note
            user = users.get(User.username == session["user"])
            if user:
                notes = user.get("note", {})
                notes[id] = {"title": title, "content": content}
                users.update({"note": notes}, User.username == session["user"])

    return "OK"

@app.route("/deleteNote", methods = ["POST"])
def deleteNote():
    id = request.form["id"]
    target_user = request.form.get("user", "")

    with db_lock:
        if target_user and session.get("admin", 0) in (1, 2):
            # Admin deleting another user's note
            user = users.get(User.username == target_user)
            if user and id in user["note"]:
                del user["note"][id]
                users.update({"note": user["note"]}, User.username == target_user)
        else:
            # User deleting their own note
            user = users.get(User.username == session["user"])
            if user:
                notes = user.get("note", {})
                if id in notes:
                    del notes[id]
                users.update({"note": notes}, User.username == session["user"])

    return "OK"

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug = True)