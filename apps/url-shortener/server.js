const express = require('express');
const Database = require('better-sqlite3');
const path = require('path');
const crypto = require('crypto';

const app = express();
const PORT = process.env.PORT || 3001;

// Initialize SQLite database
const db = new Database('./urls.db');

// Create table if not exists
db.exec(`
  CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT NOT NULL,
    short_code TEXT UNIQUE NOT NULL,
    clicks INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Generate short code
function generateShortCode(length = 6) {
  return crypto.randomBytes(length)
    .toString('base64')
    .replace(/[+/=]/g, '')
    .substring(0, length);
}

// Is valid URL
function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
}

// POST /api/shorten - Create short URL
app.post('/api/shorten', (req, res) => {
  const { url } = req.body;

  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  if (!isValidUrl(url)) {
    return res.status(400).json({ error: 'Invalid URL format' });
  }

  // Check if URL already exists
  const existing = db.prepare('SELECT short_code FROM urls WHERE original_url = ?').get(url);
  if (existing) {
    const shortUrl = `${req.protocol}://${req.get('host')}/${existing.short_code}`;
    return res.json({ shortCode: existing.short_code, shortUrl, exists: true });
  }

  // Generate unique short code
  let shortCode;
  let isUnique = false;
  while (!isUnique) {
    shortCode = generateShortCode();
    const exists = db.prepare('SELECT 1 FROM urls WHERE short_code = ?').get(shortCode);
    if (!exists) isUnique = true;
  }

  // Insert into database
  try {
    db.prepare('INSERT INTO urls (original_url, short_code) VALUES (?, ?)').run(url, shortCode);
    const shortUrl = `${req.protocol}://${req.get('host')}/${shortCode}`;
    res.status(201).json({ shortCode, shortUrl });
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to create short URL' });
  }
});

// GET /api/stats - Get all URLs with stats
app.get('/api/stats', (req, res) => {
  try {
    const urls = db.prepare(`
      SELECT 
        id,
        original_url as originalUrl,
        short_code as shortCode,
        clicks,
        created_at as createdAt
      FROM urls 
      ORDER BY created_at DESC
    `).all();
    
    res.json({ 
      count: urls.length,
      urls: urls
    });
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

// GET /:code - Redirect to original URL
app.get('/:code', (req, res) => {
  const { code } = req.params;

  const url = db.prepare('SELECT original_url, id FROM urls WHERE short_code = ?').get(code);
  
  if (!url) {
    return res.status(404).json({ error: 'Short URL not found' });
  }

  // Increment click counter
  db.prepare('UPDATE urls SET clicks = clicks + 1 WHERE id = ?').run(url.id);

  // Redirect
  res.redirect(302, url.original_url);
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Serve index.html for root
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 URL Shortener running on port ${PORT}`);
  console.log(`📊 API Docs: http://localhost:${PORT}/api/stats`);
});

module.exports = app;
