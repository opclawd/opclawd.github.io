const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Initialize SQLite database
const db = new sqlite3.Database('./expenses.db', (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to SQLite database.');
    db.run(`CREATE TABLE IF NOT EXISTS expenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      amount REAL NOT NULL,
      category TEXT NOT NULL,
      description TEXT,
      date TEXT NOT NULL
    )`, (err) => {
      if (err) {
        console.error('Error creating table:', err.message);
      } else {
        console.log('Expenses table ready.');
      }
    });
  }
});

// GET /api/expenses - Get all expenses or filter by category
app.get('/api/expenses', (req, res) => {
  const { category } = req.query;
  let sql = 'SELECT * FROM expenses ORDER BY date DESC, id DESC';
  let params = [];

  if (category) {
    sql = 'SELECT * FROM expenses WHERE category = ? ORDER BY date DESC, id DESC';
    params = [category];
  }

  db.all(sql, params, (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// POST /api/expenses - Add new expense
app.post('/api/expenses', (req, res) => {
  const { amount, category, description, date } = req.body;

  if (!amount || !category || !date) {
    return res.status(400).json({ error: 'Amount, category, and date are required' });
  }

  const sql = 'INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)';
  const params = [amount, category, description || '', date];

  db.run(sql, params, function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.status(201).json({
      id: this.lastID,
      amount,
      category,
      description: description || '',
      date
    });
  });
});

// DELETE /api/expenses/:id - Delete expense
app.delete('/api/expenses/:id', (req, res) => {
  const { id } = req.params;

  db.run('DELETE FROM expenses WHERE id = ?', [id], function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: 'Expense not found' });
    }
    res.json({ message: 'Expense deleted' });
  });
});

// GET /api/summary - Get totals by category
app.get('/api/summary', (req, res) => {
  const sql = `
    SELECT category, SUM(amount) as total
    FROM expenses
    GROUP BY category
    ORDER BY total DESC
  `;

  db.all(sql, [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    const summary = {};
    rows.forEach(row => {
      summary[row.category] = row.total;
    });
    res.json(summary);
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Expense Tracker server running on http://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  db.close((err) => {
    if (err) {
      console.error('Error closing database:', err.message);
    } else {
      console.log('Database connection closed.');
    }
    process.exit(0);
  });
});
