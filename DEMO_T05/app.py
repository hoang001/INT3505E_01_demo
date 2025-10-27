from flask import Flask, request, jsonify, redirect, g
from flask_restful import Resource, Api
from flask_cors import CORS
import sqlite3
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
api = Api(app)
CORS(app)


# Database helpers: per-request connection (safer & better concurrency)
DATABASE = 'bookdb.db'

def get_db():
    if 'db' not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)


# Initialize DB and seed sample data (runs once at import under app context)
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        published_year INTEGER)""")
    conn.commit()

    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ("Clean Code", "Robert C. Martin", 2008),
            ("Design Patterns", "GoF", 1994),
            ("The Pragmatic Programmer", "Andrew Hunt", 1999),
            ("Refactoring", "Martin Fowler", 1999),
            ("Code Complete", "Steve McConnell", 2004),
            ("Effective Java", "Joshua Bloch", 2008),
            ("Domain-Driven Design", "Eric Evans", 2003),
            ("Head First Design Patterns", "Eric Freeman", 2004)
        ]
        c.executemany("INSERT INTO books (title, author, published_year) VALUES (?, ?, ?)", sample_books)
        conn.commit()
    conn.close()


# Swagger UI
SWAGGER_URL = '/docs'
API_URL = '/static/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Book Management API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Root route: redirect to Swagger UI
@app.route('/')
def index():
    return redirect(SWAGGER_URL)

# Resource API
class BookList(Resource):
    def get(self):
        try:
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 5))
        except ValueError:
            page = 1
            limit = 5
        offset = (page - 1) * limit
        conn = get_db()
        cur = conn.execute("SELECT id, title, author, published_year FROM books LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
        result = [{"id": r[0], "title": r[1], "author": r[2], "published_year": r[3]} for r in rows]

        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "books": result
        }, 200

    def post(self):
        data = request.get_json()
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO books (title, author, published_year) VALUES (?, ?, ?)",
            (data["title"], data["author"], data["published_year"])
        )
        conn.commit()
        book_id = cur.lastrowid
        return {"id": book_id, **data}, 201

class Book(Resource):
    def get(self, book_id):
        conn = get_db()
        r = conn.execute(
            "SELECT id, title, author, published_year FROM books WHERE id=?",
            (book_id,)
        ).fetchone()
        if r:
            return {"id": r[0], "title": r[1], "author": r[2], "published_year": r[3]}, 200
        return {"message": "Book not found"}, 404

    def delete(self, book_id):
        conn = get_db()
        cur = conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        if cur.rowcount:
            return {"message": "Book deleted"}, 200
        return {"message": "Book not found"}, 404

# Routes
api.add_resource(BookList, '/api/v1/books')
api.add_resource(Book, '/api/v1/books/<int:book_id>')

# Ensure DB is initialized when module is loaded
with app.app_context():
    init_db()

if __name__ == "__main__":
    # Dev server (kept for convenience). For production-like usage, use run.ps1 with Waitress.
    app.run(debug=True)
