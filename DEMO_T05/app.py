from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
import sqlite3
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
api = Api(app)
CORS(app)


# Kết nối SQLite
conn = sqlite3.connect('bookdb.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    published_year INTEGER)""")
conn.commit()

cursor.execute("SELECT COUNT(*) FROM books")
if cursor.fetchone()[0] == 0:
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
    cursor.executemany("INSERT INTO books (title, author, published_year) VALUES (?, ?, ?)", sample_books)
    conn.commit()


# Swagger UI
SWAGGER_URL = '/docs'
API_URL = '/static/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Book Management API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

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
        cursor.execute("SELECT id, title, author, published_year FROM books LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        result = [{"id": r[0], "title": r[1], "author": r[2], "published_year": r[3]} for r in rows]

        cursor.execute("SELECT COUNT(*) FROM books")
        total = cursor.fetchone()[0]

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "books": result
        }, 200

    def post(self):
        data = request.get_json()
        cursor.execute(
            "INSERT INTO books (title, author, published_year) VALUES (?, ?, ?)",
            (data["title"], data["author"], data["published_year"])
        )
        conn.commit()
        book_id = cursor.lastrowid
        return {"id": book_id, **data}, 201

class Book(Resource):
    def get(self, book_id):
        cursor.execute(
            "SELECT id, title, author, published_year FROM books WHERE id=?",
            (book_id,)
        )
        r = cursor.fetchone()
        if r:
            return {"id": r[0], "title": r[1], "author": r[2], "published_year": r[3]}, 200
        return {"message": "Book not found"}, 404

    def delete(self, book_id):
        cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        if cursor.rowcount:
            return {"message": "Book deleted"}, 200
        return {"message": "Book not found"}, 404

# Routes
api.add_resource(BookList, '/api/v1/books')
api.add_resource(Book, '/api/v1/books/<int:book_id>')

if __name__ == "__main__":
    app.run(debug=True)
