from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)

socket = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/join", methods=["POST"])
def join():
    return render_template("join.html")


@app.route("/chat")
def chat():
    return render_template("chat.html")

