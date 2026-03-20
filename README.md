**Trackr**:

A PDF-to-database data pipeline with a Flask inventory management interface — built for small print shops processing activewear wholesale orders.

<br><br>

**Pipeline Architecture**:

PDF Invoice

⬇️
  
[ Extract ]  — pdfplumber parses raw text and tables from unstructured PDF pages

⬇️
  
[ Clean ]    — strips whitespace, handles merged cells, rejects malformed rows

⬇️
  
[ Normalize ] — maps fields to a consistent schema (style, color, size, qty, price)

⬇️
  
[ Load ]     — inserts normalized records into SQLite via structured table writes

⬇️
  
SQLite Database  →  Flask Web Interface

<br><br>

**Getting Started**

```bash
git clone https://github.com/lukecbutler/Trackr.git
cd Trackr
pip install flask pdfplumber
python createDatabase.py
python app.py
```
⬇️

Then navigate to http://localhost:5000 and upload an S&S invoice PDF to run the pipeline.
A sample invoice (```uploadMe.pdf```) is included in the repo for testing.

<br><br>

**Tech Stack**
| Layer | Technology |
|---|---|
| PDF Extraction | `pdfplumber` |
| Data Processing | Python |
| Database | SQLite |
| Web Framework | Flask |
| Frontend | HTML / CSS |
