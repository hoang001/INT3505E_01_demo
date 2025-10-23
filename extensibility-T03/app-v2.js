// app_v2.js
import express from "express";
const app = express();
app.use(express.json());

let products = [
  { id: 1, name: "Laptop", price: 1500, category: "Electronics" },
  { id: 2, name: "Mouse", price: 25, category: "Accessories" },
];

// Giữ nguyên API cũ
app.get("/api/v1/products", (req, res) => {
  res.json(products.map(({ id, name, price }) => ({ id, name, price })));
});

// Mở rộng thêm API mới
app.get("/api/v2/products", (req, res) => {
  const { category } = req.query;
  let result = products;
  if (category) {
    result = products.filter((p) => p.category === category);
  }
  res.json(result);
});

app.post("/api/v2/products", (req, res) => {
  const { name, price, category } = req.body;
  const newProduct = { id: products.length + 1, name, price, category };
  products.push(newProduct);
  res.status(201).json(newProduct);
});

app.listen(3000, () => console.log("API v2 running on http://localhost:3000"));
