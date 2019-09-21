import os
from time import sleep

# Library for parsing the csv
from csv import reader

# Library for interacting with the postgresql database
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


with open("books.csv") as booksfile:
    next(booksfile)  # Skip the first (heading) line
    books_data = booksfile.readlines()

    print(f"Total Rows: {len(books_data)}")
    print("Inserting into database...")
    sleep(3)

    try:
        for isbn, book_name, author, year in reader(books_data):
                print(f"INSERTING ISBN # {isbn}")
                db.execute("INSERT into books (isbn, title, author, year) \
                    VALUES (:isbn, :book_name, :author, :year)", {"isbn": isbn,
                    "book_name": book_name, "author": author, "year": year})
                db.commit()
                print()

    except Exception:
        print("Error! Could not add the data.")

    else:
        print("Success! Complete")

    print("Exiting")
