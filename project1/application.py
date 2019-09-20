import os
import requests


from flask import Flask, session, render_template, request, redirect, url_for
from flask import jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    try:
        if session["logged_in"]:
            return redirect(url_for("home"))
    except: pass

    return render_template("login.html", error=False, loggedout=True)


@app.route("/login", methods=["POST"])
def login():
    try:
        if session["logged_in"]:
            return redirect(url_for("home"))
    except: pass

    username = request.form.get("username")
    password = request.form.get("password")

    userquery = db.execute("SELECT * from users where \
                           username=:username and password=:password",
                           {"username": username, "password": password})
    if userquery.rowcount == 1:
        session['logged_in'] = True
        session['user_id'] = userquery.first()['id']
        session['username'] = username

        return redirect(url_for("home"))

    else:
        return render_template("login.html", error=True, loggedout=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/registration")
def registration():
    try:
        if session["logged_in"]:
            return redirect(url_for("home"))
    except: pass

    return render_template("registration.html", loggedout=True)


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    query = db.execute("SELECT * from users where username=:username",
                       {"username": username})
    if query.fetchall():
        message = f"The username '{username}' is already taken."
        next_url = f"/registration"
        return redirect(f"/message/error?message={message}&next_url={next_url}")

    else:
        try:
            db.execute("INSERT INTO users (username, password) values \
                       (:username, :password)", {"username": username,
                                                 "password": password})
            db.commit()
        except:
            message = "Error: Could not add the user!"
            next_url = f"/registration"
            return redirect(f"/message/error?message={message}&next_url={next_url}")

        else:
            message = "Your account is created. Click on 'Go Back' to login."
            next_url = f"/"
            return redirect(f"/message/success?message={message}&next_url={next_url}")




@app.route("/home")
def home():
    try: assert session["logged_in"]
    except: return redirect(url_for("index"))

    user_id = session["user_id"]
    username = session["username"]

    recent_reviews = db.execute("SELECT reviews.id, title, author, review_text \
                   from books join reviews  on reviews.book_id = books.id \
                   where user_id= :user_id order by reviews.id DESC limit 5",
                                {"user_id": user_id}).fetchall()
    recent_checks = db.execute("SELECT books.id, title, author\
                   from books join checks on checks.book_id = books.id \
                   where user_id= :user_id order by checks.id DESC limit 5",
                                {"user_id": user_id}).fetchall()

    return render_template("home.html", username=username,
                           recent_reviews=recent_reviews,
                           recent_checks = recent_checks)


@app.route("/search", methods=["POST"])
def search():
    try: assert session["logged_in"]
    except: return redirect(url_for("index"))

    search_string = request.form.get("search_string")

    search_results = db.execute("SELECT * FROM books WHERE title like\
                                :search_string or author like :search_string\
                                or CAST(isbn as VARCHAR) like :search_string",
                                {"search_string": f"%{search_string}%"})

    search_results = search_results.fetchall()

    return render_template("results.html", search_results=search_results,
                           search_string=search_string)


@app.route("/book/<int:book_id>")
def book(book_id):
    try: assert session["logged_in"]
    except: return redirect(url_for("index"))
    user_id = session["user_id"]


    book_data = db.execute("SELECT * from books where id=:book_id",
                           {"book_id": book_id}).fetchone()
    if book_data:
        check_query = db.execute("SELECT * from checks where user_id=:user_id\
                                 and book_id=:book_id",
                                 {"user_id": user_id, "book_id": book_id})
        if check_query.fetchone():
            db.execute("DELETE from checks where user_id=:user_id\
                                 and book_id=:book_id",
                                 {"user_id": user_id, "book_id": book_id})

        db.execute("insert into checks (user_id, book_id) VALUES \
                   (:user_id, :book_id)", {"user_id": user_id,
                                           "book_id": book_id})
        db.commit()

    book_reviews = db.execute("SELECT reviews.id, user_id, username, review_text from \
                              users join reviews on reviews.user_id=\
                              users.id where reviews.book_id=:book_id",
                              {"book_id": book_id}).fetchall()

    goodreads_api_key = os.getenv("GOODREADS_API")
    book_isbn = book_data["isbn"]

    api_response = requests.get("https://www.goodreads.com/book/review_counts.json",
                                params = {"isbns": str(book_isbn),
                                          "key": goodreads_api_key})
    if api_response.status_code == 200:
        goodreads_data = api_response.json()["books"][0]
    else:
        goodreads_data = {}

    return render_template("book.html", book_data=book_data, book_reviews=
                           book_reviews, goodreads_data = goodreads_data)


@app.route("/addreview", methods=["POST"])
def addreview():
    try: assert session["logged_in"]
    except: return redirect(url_for("index"))

    user_id = session["user_id"]
    book_id = request.form.get("book_id")
    review_text = request.form.get("review_text")

    previous_review = db.execute("SELECT * FROM reviews WHERE user_id=:user_id\
                        AND book_id=:book_id", {"user_id": user_id,
                                                "book_id": book_id}).fetchall()

    if previous_review:
        message = "You have already added a review for this book."
        next_url = f"/book/{book_id}"
        return redirect(f"/message/error?message={message}&next_url={next_url}")

    try:
        db.execute("INSERT INTO reviews (user_id, book_id, review_text) VALUES \
                (:user_id, :book_id, :review_text)", {"user_id": user_id,
                                                        "book_id": book_id,
                                                        "review_text": review_text
                                                        })
        db.commit()

    except Exception:
        message = "Error: Could not add the Review"
        next_url = "/book/"+str(book_id)
        return redirect(f"/message/error?message={{message}}&next_url=\
                        {{next_url}}")

    return redirect(url_for('book', book_id=book_id))

@app.route("/message/<string:msgtype>")
def message(msgtype):
    """Render a message to the user with a go back button
    Message Type:
        1) error
        2) success
        3) neutral

    Query Strings:
        1) message: the Message to Display
        2) next_url: url for the go back button
    """
    message = request.args.get("message")
    next_url = request.args.get("next_url")


    return render_template("message.html", msgtype=msgtype, message=message,
                           next_url=next_url)

@app.route("/delete/<int:review_id>")
def delete(review_id):
    try: assert session["logged_in"]
    except: return redirect(url_for("index"))

    review_data = db.execute("SELECT * from reviews where id=:review_id",
                             {"review_id": review_id}).fetchone()
    if review_data:
        if review_data.user_id == session["user_id"]:
            db.execute("DELETE from reviews where id=:review_id",
                       {"review_id": review_id})
            db.commit()
            message = "The review has been removed."
            next_url = f"/home"
            return redirect(f"/message/success?message={message}&next_url={next_url}")
        else:
            message = "Unable to delete. You need to login as the review owner."
            next_url = f"/home"
            return redirect(f"/message/error?message={message}&next_url={next_url}")
    else:
        message = "Erro: Review not found."
        next_url = f"/home"
        return redirect(f"/message/error?message={message}&next_url={next_url}")

@app.route("/api/<int:isbn>")
def api(isbn):

    book_data = db.execute("SELECT * from books where isbn=:isbn",
                           {"isbn": isbn}).fetchone()

    if book_data:
        goodreads_api_key = os.getenv("GOODREADS_API")
        book_isbn = book_data["isbn"]
        api_response = requests.get("https://www.goodreads.com/book/review_counts.json",
                                    params = {"isbns": str(book_isbn),
                                            "key": goodreads_api_key})
        if api_response.status_code == 200:
            goodreads_data = api_response.json()["books"][0]
        else:
            goodreads_data = {}


        return jsonify({
            "name": book_data["title"],
            "author": book_data["author"],
            "year": book_data["year"],
            "isbn": book_isbn,
            "reviews_count": goodreads_data.get("reviews_count"),
            "average_rating": goodreads_data.get("average_rating")
        })
    else:
        return jsonify({"error": "Book not found."}), 422
