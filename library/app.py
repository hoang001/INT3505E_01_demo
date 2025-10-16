from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Hàm kết nối DB ---
def get_db_connection():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- Khởi tạo bảng (chạy 1 lần) ---
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        author TEXT NOT NULL,
                        available INTEGER DEFAULT 1
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS borrows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        book_id INTEGER,
                        borrower TEXT,
                        returned INTEGER DEFAULT 0,
                        FOREIGN KEY(book_id) REFERENCES books(id)
                    )''')
    conn.commit()
    conn.close()

# --- Trang chủ: danh sách sách ---
@app.route("/")
def index():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template("index.html", books=books)

# --- Thêm sách ---
@app.route("/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        conn = get_db_connection()
        conn.execute("INSERT INTO books (title, author, available) VALUES (?, ?, 1)", (title, author))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add_book.html")

# --- Mượn sách ---
@app.route("/borrow/<int:book_id>", methods=["GET", "POST"])
def borrow(book_id):
    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ? AND available = 1", (book_id,)).fetchone()
    if not book:
        conn.close()
        return "Sách không có sẵn hoặc không tồn tại!"
    
    if request.method == "POST":
        borrower = request.form["borrower"]
        conn.execute("INSERT INTO borrows (book_id, borrower) VALUES (?, ?)", (book_id, borrower))
        conn.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("borrow.html", book=book)

# --- Trả sách ---
@app.route("/return/<int:book_id>", methods=["GET", "POST"])
def return_book(book_id):
    conn = get_db_connection()
    borrow_record = conn.execute("SELECT * FROM borrows WHERE book_id = ? AND returned = 0", (book_id,)).fetchone()
    if not borrow_record:
        conn.close()
        return "Không có thông tin mượn sách hoặc sách đã được trả!"
    
    if request.method == "POST":
        conn.execute("UPDATE borrows SET returned = 1 WHERE id = ?", (borrow_record["id"],))
        conn.execute("UPDATE books SET available = 1 WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("return.html", book_id=book_id)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
