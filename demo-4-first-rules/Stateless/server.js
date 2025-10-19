const express = require('express');
const app = express();
app.use(express.json());

const users = [{ id: 1, name: 'Hoàng', token: 'abc123' }];

app.get('/api/profile', (req, res) => {
  const token = req.headers['authorization'];
  const user = users.find(u => `Bearer ${u.token}` === token);
  if (!user) return res.status(401).json({ message: 'Unauthorized' });
  res.json({ id: user.id, name: user.name });
});

app.listen(3001, () => console.log('Stateless API running on 3001'));
