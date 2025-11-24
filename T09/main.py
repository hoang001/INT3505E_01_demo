import os
from typing import List

from apiflask import APIFlask, Schema
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from marshmallow import fields
from mongoengine import Document, FloatField, StringField, connect

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")
connect(host=MONGODB_URI, db=MONGODB_DB)


# MongoEngine Document Model
class Product(Document):
    name = StringField(required=True)
    price = FloatField(required=True)
    description = StringField(default="")

    meta = {"collection": "products"}


app = APIFlask(__name__, title="Products API", version="1.0.0")


# Marshmallow Schemas for API
class ProductIn(Schema):
    name = fields.String(
        required=True, metadata={"description": "Product name", "example": "Laptop"}
    )
    price = fields.Float(
        required=True, metadata={"description": "Product price", "example": 999.99}
    )
    description = fields.String(
        load_default="",
        metadata={
            "description": "Product description",
            "example": "High-performance laptop",
        },
    )


class ProductOut(Schema):
    id = fields.String(required=True, metadata={"description": "Product ID"})
    name = fields.String(required=True, metadata={"description": "Product name"})
    price = fields.Float(required=True, metadata={"description": "Product price"})
    description = fields.String(
        required=True, metadata={"description": "Product description"}
    )


class ProductsList(Schema):
    products = fields.List(fields.Nested(ProductOut), required=True)


class MessageSchema(Schema):
    message = fields.String(required=True)


@app.get("/products")
@app.output(ProductsList)
def get_products():
    products = Product.objects()
    return {
        "products": [
            {
                "id": str(p.id),
                "name": p.name,
                "price": p.price,
                "description": p.description or "",
            }
            for p in products
        ]
    }


@app.post("/products")
@app.input(ProductIn)
@app.output(ProductOut, status_code=201)
def create_product(data):
    product = Product(**data)
    product.save()
    return {
        "id": str(product.id),
        "name": product.name,
        "price": product.price,
        "description": product.description or "",
    }


@app.get("/products/<id>")
@app.output(ProductOut)
def get_product(id):
    if not ObjectId.is_valid(id):
        return {"message": "Invalid product ID"}, 400
    try:
        product = Product.objects.get(id=id)
        return {
            "id": str(product.id),
            "name": product.name,
            "price": product.price,
            "description": product.description or "",
        }
    except Product.DoesNotExist:
        return {"message": "Product not found"}, 404
    except InvalidId:
        return {"message": "Invalid product ID"}, 400


@app.put("/products/<id>")
@app.input(ProductIn)
@app.output(ProductOut)
def update_product(id, data):
    try:
        product = Product.objects.get(id=id)
        product.name = data["name"]
        product.price = data["price"]
        product.description = data.get("description", "")
        product.save()
        return {
            "id": str(product.id),
            "name": product.name,
            "price": product.price,
            "description": product.description or "",
        }
    except ValidationError:
        return {"message": "Invalid product ID"}, 400
    except ValidationError:
        return {"message": "Invalid product ID"}, 400
    except Product.DoesNotExist:
        return {"message": "Product not found"}, 404
    except InvalidId:
        return {"message": "Invalid product ID"}, 400


@app.delete("/products/<id>")
@app.output(MessageSchema)
def delete_product(id):
    if not ObjectId.is_valid(id):
        return {"message": "Invalid product ID"}, 400
    try:
        product = Product.objects.get(id=id)
        product.delete()
        return {"message": "Product deleted"}
    except Product.DoesNotExist:
        return {"message": "Product not found"}, 404


if __name__ == "__main__":
    app.run(debug=True)
