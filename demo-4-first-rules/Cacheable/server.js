const express = require('express');
const app = express();

const books = [
  { id: 1, title: 'Đắc Nhân Tâm' },
  { id: 2, title: 'Nhà Giả Kim' }
];

app.get('/api/books', (req, res) => {
  res.set('Cache-Control', 'public, max-age=30'); // cache 30 giây
  res.json(books);
});

app.listen(3002, () => console.log('Cacheable API running on 3002'));
