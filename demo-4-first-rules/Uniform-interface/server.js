const express = require('express');
const app = express();
app.use(express.json());

let books = [
  { id: 1, title: 'Tôi thấy hoa vàng trên cỏ xanh' }
];

// GET: lấy tất cả
app.get('/api/books', (req, res) => res.json(books));

// GET: lấy theo id
app.get('/api/books/:id', (req, res) => {
  const book = books.find(b => b.id == req.params.id);
  book ? res.json(book) : res.status(404).json({ message: 'Not found' });
});

// POST: thêm mới
app.post('/api/books', (req, res) => {
  const newBook = { id: Date.now(), title: req.body.title };
  books.push(newBook);
  res.status(201).json(newBook);
});

// PUT: cập nhật
app.put('/api/books/:id', (req, res) => {
  const index = books.findIndex(b => b.id == req.params.id);
  if (index === -1) return res.status(404).json({ message: 'Not found' });
  books[index].title = req.body.title;
  res.json(books[index]);
});

// DELETE: xóa
app.delete('/api/books/:id', (req, res) => {
  books = books.filter(b => b.id != req.params.id);
  res.status(204).send();
});

app.listen(3003, () => console.log('Uniform Interface API running on 3003'));
