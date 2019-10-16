from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import sys

app = Flask(__name__)
app.config["SECRET_KEY"] = "1k3jflakj3243kljs"

socket = SocketIO(app)

# {"username": "room currently in"}
users = {} 

# {"room":[ ("Sender", "Text"), ("Sender", "Text") ] }
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

def leave_group(username):
    if users[username]:
        chat_rooms[users[username]].append((username, "Left the group."))
    users[username] = None
    

@app.route("/")
def index():
    if session.get("logged_in") and session.get("username") in users:
        return redirect("/join")
    print(users, file=sys.stdout)
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    gender = request.form.get("gender")

    if username in users: 
       flash("The Username Is Already Taken.", "warning")
       return redirect(url_for("index"))
    else:
        users[username] = None
        session["logged_in"] = True
        session["username"] = username
        session["gender"] = gender
    flash(f"Welcome {username}. Create A New Chat Room or Join Existing One Below.", "primary")
    return redirect(url_for("join"))


@app.route("/join")
def join():
    username = session.get("username")
    if not (session.get("logged_in") and username in users):
        flash("Please Log In First.", "error")
        return redirect("/")
    if users[username]:
        return redirect(f"/chat/{users[username]}")

    room_names = list(chat_rooms.keys())

    return render_template("join.html", room_names=room_names, username=username)


@app.route("/create", methods=["POST"])
def create_room():
    if not (session.get("logged_in") and session.get("username") in users):
        flash("Please Log In First.", "error")
        return redirect("/")

    username = session["username"]

    room_name = request.form.get("name")
    topic = request.form.get("topic")

    if room_name in chat_rooms.keys():
        flash("There Is Already A Room With That Name. Choose A Different Name.", "warning")
        return redirect(url_for("join"))

    else:
        chat_rooms[room_name] = []
        chat_rooms[room_name].append((username, "Created Group"))
        users[username] = room_name
        return redirect(f"/chat/{room_name}")
    

@app.route("/join_room", methods=["POST"])
def join_room():

    if not (session.get("logged_in") and session.get("username") in users):
        flash("Please Log In First.", "error")
        return redirect("/")

    username = session.get("username")

    room_name = request.form.get("room_name")

    if room_name in chat_rooms.keys():
        users[username] = room_name
        chat_rooms[room_name].append((username, "Joined the Chat"))
        return redirect(f"/chat/{room_name}")

    else:
        flash("Sorry The Room You Requested To Join Does Not Exist.", "error")
        return redirect(url_for("join"))


@app.route("/chat/<string:room_name>")
def chat(room_name):
    if not (session.get("logged_in") and session.get("username") in users):
        flash("Please Log In First.", "error")
        return redirect("/")
    username = session.get("username")
    if room_name not in chat_rooms.keys():
        flash("Sorry The Room You Requested To Join Does Not Exist.", "error")
        return redirect(url_for("join"))
    else:
        messages = chat_rooms[room_name]
        return render_template("chat.html", username=username, messages=messages, 
        room_name=room_name)

@app.route("/add", methods=["POST"])
def add_message():
    if not (session.get("logged_in") and session.get("username") in users):
        flash("Please Log In First.", "error")
        return redirect("/")
    username = session.get("username")
    room_name = request.form.get("room_name")
    message = request.form.get("message")
    if room_name not in chat_rooms.keys():
        flash("Sorry The Room You Requested To Join Does Not Exist.", "error")
        return redirect(url_for("join"))
    else:
        chat_rooms[room_name].append((username, message))
        return redirect(f"/chat/{room_name}")

@app.route("/logout")
def logout():
    if not (session.get("logged_in") and session.get("username") in users):
        flash("Please Log In First.", "error")
        return redirect("/")

    username = session.get("username")
    try:
        leave_group(username)

        users.pop(username)

        session.clear()
    except: pass
    flash("Logged Out Successfully.", "success")
    return redirect("/")


@app.route("/leave/<string:room_name>")
def leave(room_name):
    if not (session.get("logged_in") and session.get("username") in users):
        flash("Please Log In First.", "error")
        return redirect("/")
    username = session.get("username")
    leave_group(username)
    flash(f"Left Chat Room '{room_name}'. Join A Different One Below or Create A New One.", "success")
    return redirect("/join")


    
if __name__== "__main__":
    socket.run(app, debug=True)