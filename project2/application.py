from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import sys

app = Flask(__name__)
app.config["SECRET_KEY"] = "1k3jflakj3243kljs"

socket = SocketIO(app)

users = []

# {"room":[ ("Sender", "Text") ] }
chat_rooms = {}



@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    print(file=sys.stdout)
    print("----------------------------",file=sys.stdout)
    print("Chat Rooms: ", chat_rooms, file=sys.stdout)
    print("Users: ", users, file=sys.stdout)
    print(session)
    print("----------------------------",file=sys.stdout)
    print(file=sys.stdout)
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect("/join")
    print(users, file=sys.stdout)
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    gender = request.form.get("gender")

    if username in users: 
        return render_template("index.html", taken=True)
    else:
        users.append(username)
        session["logged_in"] = True
        session["username"] = username
        session["gender"] = gender
    return redirect(url_for("join"))


@app.route("/join")
def join():
    if not session.get("logged_in"):
        return redirect("/")
    username = session.get("username")
    room_names = list(chat_rooms.keys())
    return render_template("join.html", room_names=room_names, username=username)


@app.route("/create", methods=["POST"])
def create_room():
    if not session.get("logged_in"):
        return redirect("/")

    room_name = request.form.get("name")
    topic = request.form.get("topic")

    if room_name in chat_rooms.keys():
        return redirect(url_for("join"))

    else:
        chat_rooms[room_name] = []
        chat_rooms[room_name].append((session["username"], "Created Group"))
        return redirect(f"/chat/{room_name}")
    

@app.route("/join_room", methods=["POST"])
def join_room():
    room_name = request.form.get("room_name")
    if not session.get("logged_in"):
        return redirect("/")
    if room_name in chat_rooms.keys():
        return redirect(f"/chat/{room_name}")
    else:
        return redirect(url_for("join"))


@app.route("/chat/<string:room_name>")
def chat(room_name):
    if not session.get("logged_in"):
        return redirect("/")
    username = session.get("username")
    if room_name not in chat_rooms.keys():
        return redirect(url_for("join"))
    else:
        messages = chat_rooms[room_name]
        return render_template("chat.html", username=username, messages=messages, 
        room_name=room_name)

@app.route("/add", methods=["POST"])
def add_message():
    if not session.get("logged_in"):
        return redirect("/")
    username = session.get("username")
    room_name = request.form.get("room_name")
    message = request.form.get("message")
    if room_name not in chat_rooms.keys():
        return redirect(url_for("join"))
    else:
        chat_rooms[room_name].append((username, message))
        return redirect(f"/chat/{room_name}")

@app.route("/logout")
def logout():
    username = session.get("username")
    try:
        del session["logged_in"]
        del session["username"]
        del session["gender"]
        users.remove(username)
    except: pass
    return redirect("/")

    
if __name__== "__main__":
    socket.run(app, debug=True)