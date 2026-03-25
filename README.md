# 📦 Trackr

**A full-stack inventory management system with an automated PDF-to-database pipeline — built and deployed for a real print shop.**

Trackr eliminates manual data entry for small businesses processing wholesale activewear orders. Upload an S&S Activewear invoice PDF, and the system automatically extracts, cleans, and loads every line item into a searchable, sortable inventory — no manual input required.

Deployed live on PythonAnywhere for Black Dog Prints

---

## The Problem

Small print shops receive wholesale invoices as PDFs - sometimes dozens per week. Every shirt (brand, description, color, size, quantity) has to be manually entered into a spreadsheet or notebook. It's tedious, error-prone, and doesn't scale.

## The Solution

Upload the PDF. Trackr handles the rest.

The system parses unstructured invoice text using patterns found in the PDF markup, including hyphen-delimited fields, reverse-index color detection, and item code validation. It then normalizes the data, removes duplicates against existing inventory, and loads it directly into SQLite. The inventory system is now ready to search, sort, and manage through the web interface.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│               PDF Extraction Pipeline                │
│               SSpdfDataExtraction.py                 │
│                                                      │
│   Invoice PDF  ──►  pdfplumber  ──►  Line-by-line    │
│                      (raw text)      parsing with    │
│                                      positional      │
│                                      patterns        │
│                          │                           │
│                          ▼                           │
│                  Cleaned shirt data                  │
│           [brand, description, color, size, qty]     │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                  Database Layer                      │
│                 db.py + createDatabase.py            │
│                                                      │
│   Un-duplication  ──►  Insert logic  ──►  SQLite     │
│   (match on desc,     (update qty       (users,      │
│    color, size,        if exists,        shirts,     │
│    userID)             insert if not)    logs)       │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                  Flask Web App                                    │
│                     app.py                                        │
│                                                                   │
│ Authentication  ──►  Inventory Dashboard  ──►  CRUD + Search      │
│   (register, login,   (sort, filter,                              │
│    password recovery)  upload PDF)                                │
└───────────────────────────────────────────────────────────────────┘
```

---

## Features

**PDF Pipeline**
- Parses S&S Activewear invoice PDFs using `pdfplumber` with custom positional extraction logic
- Handles multi-word colors, variable field widths, and malformed rows gracefully
- Deduplicates on insert — if a shirt already exists in your inventory, the quantity is updated rather than creating a duplicate

**Inventory Management**
- Search across brand, description, color, and size
- Sort by any column with custom ordering for garment sizes (NB → 4XL)
- Inline increment/decrement via async `fetch` calls — no page reloads
- Bulk select and delete
- Manual entry form for one-off additions

**Authentication & Security**
- User registration and login with password hashing (Werkzeug)
- Cookie-based session management
- Token-based password recovery via email (itsdangerous + flask-mailman)
- SQL injection protection on sort parameters

---

## Project Structure

```
Trackr/
├── app.py                  # Flask server, route registration, mail config
├── auth.py                 # Registration, login, logout with password hashing
├── inventory.py            # Inventory CRUD, search, sort, PDF upload handler
├── SSpdfDataExtraction.py  # PDF parsing engine — positional text extraction
├── db.py                   # Database connection + upsert logic
├── createDatabase.py       # Schema definition (users, shirts, shirt_logs)
├── resetPassword.py        # Token-based email password recovery
├── landing.py              # Landing page routing
├── uploadMe.pdf            # Sample S&S invoice for testing
├── shirts.db               # SQLite database
└── templates/
    ├── landingPage.html
    ├── login.html
    ├── register.html
    ├── index.html              # Main inventory dashboard
    ├── accountRecoveryEmail.html
    ├── emailSent.html
    └── resetPasswordForm.html
```

---

## Getting Started

```bash
git clone https://github.com/lukecbutler/Trackr.git
cd Trackr
pip install flask pdfplumber flask-mailman itsdangerous
python createDatabase.py
python app.py
```

Navigate to `http://localhost:80`, register an account, and upload the included `uploadMe.pdf` to see the pipeline in action.

---

## Tech Stack

| Layer | Technology |
|---|---|
| PDF Extraction | `pdfplumber` |
| Backend | Python, Flask |
| Database | SQLite |
| Auth | Werkzeug (password hashing), itsdangerous (token generation) |
| Email | flask-mailman (SMTP) |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript (fetch API) |
| Deployment | PythonAnywhere |

---

## Author

**Luke Butler** — [GitHub](https://github.com/lukecbutler)
