# OpenClaw Expense Tracker

A production-ready expense tracking application built with Express, SQLite, and Chart.js.

## Features

- 📝 Add, view, and delete expenses
- 📊 Visual summary with pie charts by category
- 🔍 Filter expenses by category
- 🌙 Dark theme UI
- 💾 SQLite database for data persistence

## Categories

- Food
- Transport
- Entertainment
- Bills
- Shopping
- Other

## API Documentation

### GET /api/expenses
Retrieve all expenses or filter by category.

**Query Parameters:**
- `category` (optional): Filter by category name

**Response:**
```json
[
  {
    "id": 1,
    "amount": 50.00,
    "category": "Food",
    "description": "Lunch",
    "date": "2026-02-06"
  }
]
```

### POST /api/expenses
Create a new expense.

**Request Body:**
```json
{
  "amount": 50.00,
  "category": "Food",
  "description": "Lunch",
  "date": "2026-02-06"
}
```

**Response:**
```json
{
  "id": 1,
  "amount": 50.00,
  "category": "Food",
  "description": "Lunch",
  "date": "2026-02-06"
}
```

### DELETE /api/expenses/:id
Delete an expense by ID.

**Response:**
```json
{ "message": "Expense deleted" }
```

### GET /api/summary
Get total expenses grouped by category.

**Response:**
```json
{
  "Food": 150.00,
  "Transport": 45.00,
  "Entertainment": 80.00,
  "Bills": 200.00,
  "Shopping": 120.00,
  "Other": 30.00
}
```

## Installation

```bash
npm install
npm start
```

The server will start on port 3000 by default.

## Environment Variables

- `PORT`: Server port (default: 3000)
