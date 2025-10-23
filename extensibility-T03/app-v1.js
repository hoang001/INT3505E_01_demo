import express from "express";
const app = express();
app.use(express.json());

let products = [
  { id: 1, name: "Laptop", price: 1500 },
  { id: 2, name: "Mouse", price: 25 },
];

//lấy danh sách sản phẩm
app.get("/api/v1/products", (req, res) => {
  res.json(products);
});

//thêm sản phẩm
app.post("/api/v1/products", (req, res) => {
  const { name, price } = req.body;
  const newProduct = { id: products.length + 1, name, price };
  products.push(newProduct);
  res.status(201).json(newProduct);
});

app.listen(3000, () => console.log("API v1 running on http://localhost:3000"));
