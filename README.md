# Library Management System (CLI + SQLite)

A lightweight **command-line library management system** built in **Python (standard library only)** with **SQLite** storage. Supports **multiple copies per book**, borrower management, loan issuance/returns, due-date tracking, **late fee calculation**, and basic reporting (active loans, overdue loans, borrower history).

> Note: This is a CLI application intended for learning and small-scale usage. It is not designed for concurrent multi-user access.

---

## Features

### Book inventory
- Add books with **title**, **author**, optional **ISBN**, and **copy count**
- List all books or only those with available copies
- Search books by title / author / ISBN
- Inventory tracked using:
  - `copies_total` (how many copies exist)
  - `copies_available` (how many are currently available)

### Borrowers
- Add borrowers (name + optional email)
- List borrowers

### Loans + returns
- Issue a book to a borrower (default loan duration: **14 days**)
- Automatically calculates **due date**
- Return a book:
  - sets `return_date`
  - calculates late fee if returned after due date (**default: $0.50/day**)
  - updates status:
    - `Returned` = returned on time
    - `Overdue` = returned late (returned, but overdue at return time)

### Reporting
- View active loans (currently issued)
- View overdue loans (still issued and past due date)
- View full loan history and late fees for a borrower

---

## Tech Stack
- Python 3.8+
- SQLite (`sqlite3`)
- `datetime`, `textwrap`

No external packages required.

---

## Quick Start

1) Put `advanced_library_system.py` in a folder.

2) Run:

```bash
python file name .py
```
---
# CLI MENU

===== Advanced Library Management =====
1. Add Book
2. List All Books
3. List Available Books Only
4. Search Books
5. Add Borrower
6. List Borrowers
7. Issue Book
8. Return Book
9. View Active Loans
10. View Overdue Loans
11. View Borrower History
0. Exit
----
## Example Workflow

# 1) Add a book
Choose 1
Enter title/author
Optional ISBN
Copies (default = 1)

# 2) Add a borrower
Choose 5
Enter name (+ optional email)

# 3) Issue a book
Choose 7
Enter:
Book ID
Borrower ID
Loan duration (default = 14 days)

# 4) Return a book
Choose 8
Enter loan ID (from active loans list)
Late fees apply if returned after due date (default $0.50/day)
---
## Database Schema
The database is created automatically in library_system.db.

# books

- id (PK)
- title, author
- isbn (UNIQUE, optional)
- copies_total, copies_available
- created_at

# borrowers

- id (PK)
- name, email
- created_at

# loans

- id (PK)
- book_id (FK → books.id)
- borrower_id (FK → borrowers.id)
- issue_date, due_date, return_date
- status (Issued, Returned, Overdue)
- late_fee

Foreign key enforcement is enabled via:

PRAGMA foreign_keys = ON;

---
# Roadmap (Upgrade)

- Expose a REST API using FastAPI (reuse the same DB + core functions)
- Add reservations/holds and notifications
- Add admin/librarian roles (auth)
- Add tests + CI (pytest + GitHub Actions)
- Improve input validation and error handling for edge cases
---

