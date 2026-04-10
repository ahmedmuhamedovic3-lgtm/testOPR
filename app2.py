from flask import Flask, render_template, request, redirect, session, jsonify, url_for, send_from_directory
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
import threading
import os

app = Flask(__name__, template_folder="templates2")
app.secret_key = "skrivamoTaKljuč"

# Upload konfiguracija
UPLOAD_FOLDER = "uploads2"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Ustvari uploads folder če ne obstaja
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

db = TinyDB("db2.json")
all_data = db.all()
users = db.table("users")

db_lock = threading.Lock()

User = Query()

# Route za serviranje uploadanih slik
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

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
        # Existing user setting up security question
        if session.get("need_security"):
            question = request.form["security_question"]
            answer = request.form["security_answer"].lower()
            with db_lock:
                users.update({"security_question": question, "security_answer": generate_password_hash(answer)}, User.username == session["user"])
            session.pop("need_security", None)
            return redirect("/dashboard")
        # New user registration
        username = request.form["username"] # shranimo spremenljivke iz registracije
        password = request.form["password"]
        #print(username, password)

        if users.search(User.username == username):
            return render_template("register.html", error="Uporabniško ime že obstaja")

        users.insert({"username" : username, "password" : generate_password_hash(password), "admin" : 0, "note" : {}, "security_question": request.form["security_question"], "security_answer": generate_password_hash(request.form["security_answer"].lower())})
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
            # Check if security question is set
            if not user.get("security_question"):
                session["need_security"] = True
                return redirect("/register")
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
    
    # Pripravi vse objave uporabnika
    posts = []
    for note_id, note in user.get("note", {}).items():
        posts.append({
            "id": note_id,
            "content": note.get("content", ""),
            "images": note.get("images", []),
            "like": note.get("like", 0),
            "dislike": note.get("dislike", 0),
            "comment": note.get("comment", [])
        })
    
    return render_template("admin_user_notes.html", uporabnik=session["user"], target_user=username, posts=posts, admin=session.get("admin", 0), target_admin=user.get("admin", 0))

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
    all_users = get_all_users()
    posts = []
    for user in all_users:
        for note_id, note in user.get("note", {}).items():
            posts.append({
                "username": user["username"],
                "id": note_id,
                "content": note.get("content", ""),
                "images": note.get("images", []),
                "like": note.get("like", 0),
                "dislike": note.get("dislike", 0),
                "comment": note.get("comment", [])
            })
    print(session, "dash")
    return render_template("dashboard.html", uporabnik = session["user"], posts = posts, admin = session.get("admin", 0))

#like
@app.route("/like", methods=["POST"])
def like():
    note_id = request.form["id"]
    username = session["user"]
    with db_lock:
        all_users = users.all()
        for user in all_users:
            if note_id in user.get("note", {}):
                note = user["note"][note_id]
                like_users = note.get("like_users", [])
                dislike_users = note.get("dislike_users", [])
                if username in like_users:
                    like_users.remove(username)
                else:
                    like_users.append(username)
                    if username in dislike_users:
                        dislike_users.remove(username)
                note["like"] = len(like_users)
                note["dislike"] = len(dislike_users)
                note["like_users"] = like_users
                note["dislike_users"] = dislike_users
                users.update({"note": user["note"]}, User.username == user["username"])
                return jsonify({"like": note["like"], "dislike": note["dislike"], "likeActive": username in like_users, "dislikeActive": username in dislike_users})
    return "OK"

#dislike
@app.route("/dislike", methods=["POST"])
def dislike():
    note_id = request.form["id"]
    username = session["user"]
    with db_lock:
        all_users = users.all()
        for user in all_users:
            if note_id in user.get("note", {}):
                note = user["note"][note_id]
                like_users = note.get("like_users", [])
                dislike_users = note.get("dislike_users", [])
                if username in dislike_users:
                    dislike_users.remove(username)
                else:
                    dislike_users.append(username)
                    if username in like_users:
                        like_users.remove(username)
                note["like"] = len(like_users)
                note["dislike"] = len(dislike_users)
                note["like_users"] = like_users
                note["dislike_users"] = dislike_users
                users.update({"note": user["note"]}, User.username == user["username"])
                return jsonify({"like": note["like"], "dislike": note["dislike"], "likeActive": username in like_users, "dislikeActive": username in dislike_users})
    return "OK"

#comment
@app.route("/comments/<id>", methods=["GET", "POST"])
def comments(id):
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        action = request.form.get("action")
        index = int(request.form.get("index", -1))
        with db_lock:
            all_users = users.all()
            for user in all_users:
                if id in user.get("note", {}):
                    note = user["note"][id]
                    comment_list = note.get("comment", [])
                    if action == "delete" and 0 <= index < len(comment_list):
                        comment_list.pop(index)
                        print(f"Komentar izbrisan (index: {index}) za note: {id}")
                    else:
                        content = request.form.get("content")
                        if not content or content.strip() == "":
                            return "Prazen komentar", 400
                        comment_list.append({"username": session["user"], "content": content})
                        print(f"Nov komentar od {session['user']}: {content}")
                    note["comment"] = comment_list
                    users.update({"note": user["note"]}, User.username == user["username"])
                    print(f"Posodobljena baza za uporabnika: {user['username']}")
                    return "OK"
            return "Note ne obstaja", 404
    all_users = users.all()
    comments_list = []
    for user in all_users:
        if id in user.get("note", {}):
            for c in user["note"][id].get("comment", []):
                comments_list.append(c)
            break
    return render_template("comments.html", id=id, uporabnik=session["user"], comments=comments_list)
#profile
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    user = users.get(User.username == session["user"])
    if not user:
        return redirect("/login")
    posts = []
    for note_id, note in user.get("note", {}).items():
        posts.append({
            "username": user["username"],
            "id": note_id,
            "content": note.get("content", ""),
            "images": note.get("images", []),
            "like": note.get("like", 0),
            "dislike": note.get("dislike", 0),
            "comment": note.get("comment", [])
        })
    return render_template("profile.html", uporabnik = session["user"], posts = posts, admin = session.get("admin", 0))

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
        notes[id] = {"content": "", "images": [], "like": 0, "dislike": 0, "comment": []}
        users.update({"note": notes}, User.username == session["user"])
    return redirect(url_for('editNote', id=id))

#save_note
@app.route("/saveNote", methods = ["POST"])
def saveNote():
    content = request.form["content"]
    id = request.form["id"]
    target_user = request.form.get("user", "")

    with db_lock:
        if target_user and session.get("admin", 0) in (1, 2):
            # Admin saving another user's note
            user = users.get(User.username == target_user)
            if user:
                user["note"][id]["content"] = content
                users.update({"note": user["note"]}, User.username == target_user)
        else:
            # User saving their own note
            user = users.get(User.username == session["user"])
            if user:
                notes = user.get("note", {})
                notes[id]["content"] = content
                
                # Shrani uploadane slike
                files = request.files.getlist("images")
                images = notes[id].get("images", [])
                for file in files:
                    if file and file.filename != "" and allowed_file(file.filename):
                        # Generiraj unikatno ime za sliko
                        ext = file.filename.rsplit(".", 1)[1].lower()
                        unique_filename = f"{uuid.uuid4().hex}.{ext}"
                        file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_filename))
                        images.append(unique_filename)
                
                # Omeji na 3 slike
                notes[id]["images"] = images[:3]
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

#remove_image - odstrani posamezno sliko iz beležke
@app.route("/removeImage", methods=["POST"])
def removeImage():
    note_id = request.form["id"]
    filename = request.form["filename"]
    target_user = request.form.get("user", "")

    with db_lock:
        if target_user and session.get("admin", 0) in (1, 2):
            # Admin odstranjuje sliko drugega uporabnika
            user = users.get(User.username == target_user)
            if user and note_id in user["note"]:
                images = user["note"][note_id].get("images", [])
                if filename in images:
                    images.remove(filename)
                    # Izbriši datoteko iz uploads folderja
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                user["note"][note_id]["images"] = images
                users.update({"note": user["note"]}, User.username == target_user)
                return "OK"
        else:
            # Uporabnik odstranjuje svojo sliko
            user = users.get(User.username == session["user"])
            if user and note_id in user["note"]:
                images = user["note"][note_id].get("images", [])
                if filename in images:
                    images.remove(filename)
                    # Izbriši datoteko iz uploads folderja
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                user["note"][note_id]["images"] = images
                users.update({"note": user["note"]}, User.username == session["user"])
                return "OK"
    return "Slika ne obstaja", 404

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

#forgot password - step 1: enter username
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form["username"]
        user = users.get(User.username == username)
        if user:
            question = user.get("security_question", "")
            session["reset_username"] = username
            return render_template("forgot.html", question=question, username=username)
        return render_template("forgot.html", error="Uporabniško ime ne obstaja")
    return render_template("forgot.html")

#forgot password - step 2: verify answer
@app.route("/forgot/verify", methods=["POST"])
def forgot_verify():
    username = request.form["username"]
    answer = request.form["security_answer"].lower()
    user = users.get(User.username == username)
    if user and check_password_hash(user.get("security_answer", ""), answer):
        temp_password = uuid.uuid4().hex[:8]
        with db_lock:
            users.update({"password": generate_password_hash(temp_password)}, User.username == username)
        return render_template("forgot.html", temp_password=temp_password, username=username)
    return render_template("forgot.html", error="Napačen odgovor", question=user.get("security_question", ""), username=username)

#change password
@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        user = users.get(User.username == session["user"])
        if not check_password_hash(user["password"], current_password):
            return render_template("change_password.html", error="Trenutno geslo ni pravilno")
        if new_password != confirm_password:
            return render_template("change_password.html", error="Novi gesli se ne ujemata")
        with db_lock:
            users.update({"password": generate_password_hash(new_password)}, User.username == session["user"])
        return redirect("/dashboard")
    return render_template("change_password.html")

app.run(debug = True, port=5002)
