const express = require('express');
const app = express();
const PORT = 3000;

const books = [
  { id: 1, title: 'Dế Mèn Phiêu Lưu Ký' },
  { id: 2, title: 'Tuổi thơ dữ dội' }
];

// Server chỉ cung cấp dữ liệu JSON
app.get('/api/books', (req, res) => {
  res.json(books);
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
