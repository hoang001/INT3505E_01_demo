import requests
import random

BASE_URL = "http://127.0.0.1:5000/products"

# Danh sách tên mẫu
names = ["Laptop Dell", "MacBook Pro", "iPhone 15", "Samsung Galaxy", "Chuột Logitech", 
         "Bàn phím cơ", "Tai nghe Sony", "Màn hình LG", "Sạc dự phòng", "Loa Bluetooth"]

print("Đang tạo 20 sản phẩm mẫu...")

for i in range(20):
    name = f"{random.choice(names)} {i}"
    price = random.randint(100, 2000)
    payload = {
        "name": name,
        "price": float(price),
        "description": f"Mô tả cho {name}"
    }
    try:
        r = requests.post(BASE_URL, json=payload)
        if r.status_code == 201:
            print(f"Đã tạo: {name} - ${price}")
    except Exception as e:
        print("Lỗi: Server chưa chạy hoặc sai URL")
        break

print("Hoàn tất! Giờ bạn có thể test phân trang.")