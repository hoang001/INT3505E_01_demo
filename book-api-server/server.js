import express from "express";
import swaggerUi from "swagger-ui-express";
import YAML from "yamljs";

const app = express();
app.use(express.json());

// Đọc file YAML
const swaggerDocument = YAML.load("./book-api.yaml");

// Tích hợp Swagger UI
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// Fake data (demo)
let books = [
  { id: "1", title: "Lập trình Java căn bản", author: "Nguyễn Văn A", publisher: "NXB Giáo dục", year: 2023 },
  { id: "2", title: "Cấu trúc dữ liệu & Giải thuật", author: "Trần Thị B", publisher: "NXB Đại học", year: 2022 },
];

// Routes
app.get("/api/books", (req, res) => res.json(books));

app.post("/api/books", (req, res) => {
  const newBook = { id: String(Date.now()), ...req.body };
  books.push(newBook);
  res.status(201).json(newBook);
});

app.get("/api/books/:id", (req, res) => {
  const book = books.find(b => b.id === req.params.id);
  if (!book) return res.status(404).json({ message: "Không tìm thấy sách" });
  res.json(book);
});

app.put("/api/books/:id", (req, res) => {
  const index = books.findIndex(b => b.id === req.params.id);
  if (index === -1) return res.status(404).json({ message: "Không tìm thấy sách" });
  books[index] = { ...books[index], ...req.body };
  res.json(books[index]);
});

app.delete("/api/books/:id", (req, res) => {
  books = books.filter(b => b.id !== req.params.id);
  res.status(204).send();
});

// Khởi động server
app.listen(3000, () => {
  console.log("✅ Server chạy tại: http://localhost:3000");
  console.log("📘 Swagger UI: http://localhost:3000/api-docs");
});
