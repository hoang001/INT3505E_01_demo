from flask import Blueprint, request
from apiflask import APIFlask, Schema, fields, abort
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    BooleanField,
    AutoField,
    DoesNotExist,
    ForeignKeyField,
)

db = SqliteDatabase("library.db")

class BaseModel(Model):
    class Meta:
        database = db

class Author(BaseModel):
    id = AutoField()
    name = CharField(unique=True)

class Book(BaseModel):
    id = AutoField()
    title = CharField()
    author = ForeignKeyField(Author, backref='books')
    available = BooleanField(default=True)

def initialize_database():
    db.connect(reuse_if_open=True)
    db.create_tables([Author, Book])

class LibraryService:
    def create_book(self, data):
        author, _ = Author.get_or_create(name=data["author_name"])
        book = Book.create(title=data["title"], author=author)
        return book

    def get_book_by_id(self, book_id):
        return Book.get_or_none(Book.id == book_id)

    def get_books_by_author(self, author_id):
        author = Author.get_or_none(Author.id == author_id)
        if author is None:
            return None
        return author.books

app = APIFlask(__name__, docs_ui='elements',  title="Library API")
library_service = LibraryService()

class AuthorSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String()

class BookV1Schema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String()
    author = fields.String(attribute="author.name")

class BookV2SimpleSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String()
    author = fields.String(attribute="author.name")
    is_available = fields.Boolean(attribute="available")

class BookV2DetailedSchema(Schema):
    id = fields.Integer(dump_only=True)
    full_title = fields.String(dump_only=True)
    author = fields.Nested(AuthorSchema)
    is_available = fields.Boolean(attribute="available")

class BookCreateSchema(Schema):
    title = fields.String(required=True)
    author_name = fields.String(required=True)

bp_v1 = Blueprint("api_v1", __name__, url_prefix="/v1")

@bp_v1.get("/books/<int:book_id>")
@app.output(BookV1Schema)
def get_book_v1(book_id):
    book = library_service.get_book_by_id(book_id)
    if book is None:
        abort(404, message=f"Book with id {book_id} not found")
    return book

bp_v2 = Blueprint("api_v2", __name__, url_prefix="/v2")

@bp_v2.get("/books/<int:book_id>")
@app.output(BookV2DetailedSchema)
def get_book_v2(book_id):
    book = library_service.get_book_by_id(book_id)
    if book is None:
        abort(404, message=f"Book with id {book_id} not found")

    show_details = request.args.get('details', 'false').lower() == 'true'

    if show_details:
        schema = BookV2DetailedSchema()
        book.full_title = f"{book.title} by {book.author.name}"
    else:
        schema = BookV2SimpleSchema()

    return schema.dump(book)

@bp_v2.get("/authors/<int:author_id>/books")
@app.output(BookV2DetailedSchema(many=True))
def get_author_books(author_id):
    books = library_service.get_books_by_author(author_id)
    if books is None:
        abort(404, message=f"Author with id {author_id} not found")

    show_details = request.args.get('details', 'false').lower() == 'true'
    
    if show_details:
        schema = BookV2DetailedSchema(many=True)
        for book in books:
            book.full_title = f"{book.title} by {book.author.name}"
    else:
        schema = BookV2SimpleSchema(many=True)
        
    return schema.dump(books)

@app.post("/books")
@app.input(BookCreateSchema)
@app.output(BookV1Schema, status_code=201)
def add_book(json_data):
    book = library_service.create_book(json_data)
    return book

app.register_blueprint(bp_v1)
app.register_blueprint(bp_v2)

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, port=5001)