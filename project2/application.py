from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)

socket = SocketIO(app)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/join", methods=["POST", "GET"])
def join():
    return render_template("join.html")


@app.route("/chat")
def chat():
    return render_template("chat.html")

