from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB = "library.db"

# Tạo bảng SQLite
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template("index.html", books=books)

@app.route("/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("add_book.html")

@app.route("/borrow_return/<int:book_id>")
def borrow_return(book_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # lấy trạng thái sách
    c.execute("SELECT available FROM books WHERE id=?", (book_id,))
    available = c.fetchone()[0]
    # đổi trạng thái
    new_status = 0 if available == 1 else 1
    c.execute("UPDATE books SET available=? WHERE id=?", (new_status, book_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
