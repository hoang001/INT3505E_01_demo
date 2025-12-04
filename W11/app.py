import logging
import uuid
from typing import List

from apiflask import APIFlask, Schema, abort, pagination
from marshmallow import fields
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics

# --- 1. Cấu hình Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_logger")

# --- 2. Khởi tạo App & Extension ---
app = APIFlask(__name__, title="Products API", version="1.0.0")

metrics = PrometheusMetrics(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# --- 3. Database giả lập (In-memory) ---
products_db = []

# --- 4. Định nghĩa Schemas (Data Models) ---

# Schema cho dữ liệu đầu vào khi tạo/sửa sản phẩm
class ProductIn(Schema):
    name = fields.String(
        required=True, 
        metadata={"description": "Product name", "example": "Laptop"}
    )
    price = fields.Float(
        required=True, 
        metadata={"description": "Product price", "example": 999.99}
    )
    description = fields.String(
        load_default="",
        metadata={
            "description": "Product description",
            "example": "High-performance laptop",
        },
    )

# Schema hiển thị thông tin chi tiết một sản phẩm
class ProductOut(Schema):
    id = fields.String(required=True, metadata={"description": "Product ID"})
    name = fields.String(required=True, metadata={"description": "Product name"})
    price = fields.Float(required=True, metadata={"description": "Product price"})
    description = fields.String(
        required=True, metadata={"description": "Product description"}
    )

# [NEW] Schema cho các tham số lọc và phân trang (Query Parameters)
class ProductQuery(Schema):
    page = fields.Integer(load_default=1, metadata={"description": "Page number (default: 1)"})
    per_page = fields.Integer(load_default=10, metadata={"description": "Items per page (default: 10)"})
    name = fields.String(load_default=None, metadata={"description": "Filter by name (partial match)"})
    min_price = fields.Float(load_default=None, metadata={"description": "Filter by minimum price"})
    max_price = fields.Float(load_default=None, metadata={"description": "Filter by maximum price"})

# [NEW] Schema cho danh sách sản phẩm có phân trang (Envelope Pattern)
class PaginatedProducts(Schema):
    total = fields.Integer(metadata={"description": "Total number of items found"})
    page = fields.Integer(metadata={"description": "Current page"})
    per_page = fields.Integer(metadata={"description": "Items per page"})
    products = fields.List(fields.Nested(ProductOut), required=True)

class MessageSchema(Schema):
    message = fields.String(required=True)

# --- 5. Các Endpoints ---

# [UPDATED] GET /products: Hỗ trợ Filter & Pagination
@app.get("/products")
@app.input(ProductQuery, location='query') # Nhận tham số từ URL query string
@app.output(PaginatedProducts)
@limiter.limit("20 per minute")
def get_products(query_data):
    # Lấy tham số
    page = query_data["page"]
    per_page = query_data["per_page"]
    name_filter = query_data["name"]
    min_price = query_data["min_price"]
    max_price = query_data["max_price"]

    logger.info(f"Querying products: page={page}, filter_name={name_filter}")

    # Bước 1: Filtering (Lọc dữ liệu)
    filtered_products = products_db

    if name_filter:
        filtered_products = [
            p for p in filtered_products 
            if name_filter.lower() in p["name"].lower()
        ]
    
    if min_price is not None:
        filtered_products = [p for p in filtered_products if p["price"] >= min_price]
        
    if max_price is not None:
        filtered_products = [p for p in filtered_products if p["price"] <= max_price]

    # Bước 2: Pagination (Cắt dữ liệu theo trang)
    total = len(filtered_products)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_items = filtered_products[start:end]

    # Bước 3: Trả về kết quả đóng gói
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "products": paginated_items
    }

@app.post("/products")
@app.input(ProductIn)
@app.output(ProductOut, status_code=201)
@limiter.limit("5 per minute")
def create_product(data):
    product_id = str(uuid.uuid4())
    new_product = {
        "id": product_id,
        "name": data["name"],
        "price": data["price"],
        "description": data.get("description", "")
    }
    products_db.append(new_product)
    logger.info(f"Product created with ID: {product_id}")
    return new_product

@app.get("/products/<id>")
@app.output(ProductOut)
@limiter.limit("10 per minute")
def get_product(id):
    product = next((p for p in products_db if p["id"] == id), None)
    if not product:
        logger.warning(f"Product not found: {id}")
        abort(404, message="Product not found")
    return product

@app.put("/products/<id>")
@app.input(ProductIn)
@app.output(ProductOut)
@limiter.limit("5 per minute")
def update_product(id, data):
    product = next((p for p in products_db if p["id"] == id), None)
    if not product:
        logger.warning(f"Attempted update on non-existent product: {id}")
        abort(404, message="Product not found")
    
    product["name"] = data["name"]
    product["price"] = data["price"]
    product["description"] = data.get("description", "")
    
    logger.info(f"Product updated: {id}")
    return product

@app.delete("/products/<id>")
@app.output(MessageSchema)
@limiter.limit("5 per minute")
def delete_product(id):
    product = next((p for p in products_db if p["id"] == id), None)
    if not product:
        logger.warning(f"Attempted delete on non-existent product: {id}")
        abort(404, message="Product not found")
    
    products_db.remove(product)
    logger.info(f"Product deleted: {id}")
    return {"message": "Product deleted"}

if __name__ == "__main__":
    app.run(debug=True)