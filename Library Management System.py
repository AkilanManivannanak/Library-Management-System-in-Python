
import sqlite3
from datetime import datetime, timedelta
from textwrap import dedent

DB_NAME = "library_system.db"

# --- Database helpers ---

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Enforce foreign keys (off by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Books table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE,
        copies_total INTEGER NOT NULL DEFAULT 1,
        copies_available INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)

    # Borrowers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS borrowers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Loans table (many-to-many between books and borrowers)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        borrower_id INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'Issued', -- Issued, Returned, Overdue
        late_fee REAL DEFAULT 0,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
        FOREIGN KEY(borrower_id) REFERENCES borrowers(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# --- Core operations ---

def add_book(title, author, isbn=None, copies=1):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO books (title, author, isbn, copies_total, copies_available, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, author, isbn, copies, copies, now))
    conn.commit()
    print(f"✅ Book '{title}' by {author} added with {copies} copies.")
    conn.close()

def list_books(show_all=True):
    conn = get_connection()
    cur = conn.cursor()
    if show_all:
        cur.execute("SELECT * FROM books ORDER BY id;")
    else:
        cur.execute("SELECT * FROM books WHERE copies_available > 0 ORDER BY id;")

    rows = cur.fetchall()
    if not rows:
        print("No books found.")
        conn.close()
        return

    print("\n--- Books ---")
    for r in rows:
        print(
            f"ID: {r['id']} | "
            f"Title: {r['title']} | "
            f"Author: {r['author']} | "
            f"ISBN: {r['isbn'] or '-'} | "
            f"Available: {r['copies_available']}/{r['copies_total']}"
        )
    conn.close()

def search_books(keyword):
    conn = get_connection()
    cur = conn.cursor()
    pattern = f"%{keyword}%"
    cur.execute("""
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
        ORDER BY title
    """, (pattern, pattern, pattern))
    rows = cur.fetchall()
    if not rows:
        print("No matching books.")
        conn.close()
        return

    print("\n--- Search Results ---")
    for r in rows:
        print(
            f"ID: {r['id']} | "
            f"Title: {r['title']} | "
            f"Author: {r['author']} | "
            f"ISBN: {r['isbn'] or '-'} | "
            f"Available: {r['copies_available']}/{r['copies_total']}"
        )
    conn.close()

def add_borrower(name, email=None):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO borrowers (name, email, created_at)
        VALUES (?, ?, ?)
    """, (name, email, now))
    conn.commit()
    print(f"✅ Borrower '{name}' added.")
    conn.close()

def list_borrowers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM borrowers ORDER BY id;")
    rows = cur.fetchall()
    if not rows:
        print("No borrowers found.")
        conn.close()
        return
    print("\n--- Borrowers ---")
    for r in rows:
        print(
            f"ID: {r['id']} | Name: {r['name']} | Email: {r['email'] or '-'}"
        )
    conn.close()

def issue_book(book_id, borrower_id, days=14, daily_fee=0.5):
    conn = get_connection()
    cur = conn.cursor()

    # Validate book
    cur.execute("SELECT * FROM books WHERE id = ?;", (book_id,))
    book = cur.fetchone()
    if not book:
        print("❌ Book not found.")
        conn.close()
        return
    if book["copies_available"] <= 0:
        print("❌ No available copies for this book.")
        conn.close()
        return

    # Validate borrower
    cur.execute("SELECT * FROM borrowers WHERE id = ?;", (borrower_id,))
    borrower = cur.fetchone()
    if not borrower:
        print("❌ Borrower not found.")
        conn.close()
        return

    issue_date = datetime.now()
    due_date = issue_date + timedelta(days=days)

    cur.execute("""
        INSERT INTO loans (book_id, borrower_id, issue_date, due_date, status)
        VALUES (?, ?, ?, ?, 'Issued')
    """, (
        book_id,
        borrower_id,
        issue_date.strftime("%Y-%m-%d"),
        due_date.strftime("%Y-%m-%d"),
    ))

    # Decrement available copies
    cur.execute("""
        UPDATE books
        SET copies_available = copies_available - 1
        WHERE id = ?;
    """, (book_id,))

    conn.commit()
    print(
        f"📕 Book issued to '{borrower['name']}'. "
        f"Due date: {due_date.strftime('%Y-%m-%d')}."
    )
    conn.close()

def _calculate_late_fee(due_date_str, return_date_str, daily_fee):
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
    return_date = datetime.strptime(return_date_str, "%Y-%m-%d")
    late_days = (return_date - due_date).days
    if late_days <= 0:
        return 0.0, 0
    return round(late_days * daily_fee, 2), late_days

def return_book(loan_id, daily_fee=0.5):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT loans.*, books.title AS book_title
        FROM loans
        JOIN books ON loans.book_id = books.id
        WHERE loans.id = ? AND loans.status = 'Issued';
    """, (loan_id,))
    loan = cur.fetchone()
    if not loan:
        print("❌ Active loan not found for given ID.")
        conn.close()
        return

    return_date = datetime.now().strftime("%Y-%m-%d")
    fee, late_days = _calculate_late_fee(
        loan["due_date"], return_date, daily_fee
    )

    status = "Returned"
    if late_days > 0:
        status = "Overdue"

    # Update loan
    cur.execute("""
        UPDATE loans
        SET return_date = ?, status = ?, late_fee = ?
        WHERE id = ?;
    """, (return_date, status, fee, loan_id))

    # Increment book copies_available
    cur.execute("""
        UPDATE books
        SET copies_available = copies_available + 1
        WHERE id = ?;
    """, (loan["book_id"],))

    conn.commit()
    if late_days > 0:
        print(
            f"✅ Book '{loan['book_title']}' returned with {late_days} late day(s). "
            f"Late fee: ${fee:.2f}."
        )
    else:
        print(f"✅ Book '{loan['book_title']}' returned on time. No late fee.")
    conn.close()

# --- Reporting / views ---

def list_active_loans():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT loans.id, books.title, borrowers.name, loans.issue_date,
               loans.due_date, loans.status
        FROM loans
        JOIN books ON loans.book_id = books.id
        JOIN borrowers ON loans.borrower_id = borrowers.id
        WHERE loans.status = 'Issued'
        ORDER BY loans.due_date;
    """)
    rows = cur.fetchall()
    if not rows:
        print("No active loans.")
        conn.close()
        return
    print("\n--- Active Loans ---")
    for r in rows:
        print(
            f"Loan ID: {r['id']} | Book: {r['title']} | Borrower: {r['name']} | "
            f"Issued: {r['issue_date']} | Due: {r['due_date']} | Status: {r['status']}"
        )
    conn.close()

def list_overdue_loans():
    conn = get_connection()
    cur = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cur.execute("""
        SELECT loans.id, books.title, borrowers.name, loans.issue_date,
               loans.due_date
        FROM loans
        JOIN books ON loans.book_id = books.id
        JOIN borrowers ON loans.borrower_id = borrowers.id
        WHERE loans.status = 'Issued' AND loans.due_date < ?
        ORDER BY loans.due_date;
    """, (today_str,))
    rows = cur.fetchall()
    if not rows:
        print("No overdue loans.")
        conn.close()
        return
    print("\n--- Overdue Loans ---")
    for r in rows:
        print(
            f"Loan ID: {r['id']} | Book: {r['title']} | Borrower: {r['name']} | "
            f"Issued: {r['issue_date']} | Due: {r['due_date']}"
        )
    conn.close()

def borrower_history(borrower_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT loans.id, books.title, loans.issue_date, loans.due_date,
               loans.return_date, loans.status, loans.late_fee
        FROM loans
        JOIN books ON loans.book_id = books.id
        WHERE loans.borrower_id = ?
        ORDER BY loans.issue_date DESC;
    """, (borrower_id,))
    rows = cur.fetchall()
    if not rows:
        print("No history for this borrower.")
        conn.close()
        return
    print("\n--- Borrower Loan History ---")
    for r in rows:
        print(
            f"Loan ID: {r['id']} | Book: {r['title']} | "
            f"Issued: {r['issue_date']} | Due: {r['due_date']} | "
            f"Returned: {r['return_date'] or '-'} | Status: {r['status']} | "
            f"Late fee: ${r['late_fee']:.2f}"
        )
    conn.close()

# --- CLI utilities ---

def input_int(prompt, allow_empty=False):
    while True:
        value = input(prompt).strip()
        if allow_empty and value == "":
            return None
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid integer.")

def main_menu():
    init_db()

    MENU = dedent("""
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
    """)

    while True:
        print(MENU)
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            title = input("Enter book title: ").strip()
            author = input("Enter book author: ").strip()
            isbn = input("Enter ISBN (optional): ").strip() or None
            copies = input_int("Enter number of copies (default 1): ", allow_empty=True)
            copies = copies if copies and copies > 0 else 1
            add_book(title, author, isbn, copies)

        elif choice == "2":
            list_books(show_all=True)

        elif choice == "3":
            list_books(show_all=False)

        elif choice == "4":
            keyword = input("Enter title/author/ISBN to search: ").strip()
            if keyword:
                search_books(keyword)
            else:
                print("Keyword cannot be empty.")

        elif choice == "5":
            name = input("Enter borrower name: ").strip()
            email = input("Enter borrower email (optional): ").strip() or None
            if not name:
                print("Name is required.")
            else:
                add_borrower(name, email)

        elif choice == "6":
            list_borrowers()

        elif choice == "7":
            book_id = input_int("Enter book ID to issue: ")
            borrower_id = input_int("Enter borrower ID: ")
            days = input_int("Loan duration in days (default 14): ", allow_empty=True)
            days = days if days and days > 0 else 14
            issue_book(book_id, borrower_id, days=days)

        elif choice == "8":
            loan_id = input_int("Enter loan ID to return: ")
            return_book(loan_id)

        elif choice == "9":
            list_active_loans()

        elif choice == "10":
            list_overdue_loans()

        elif choice == "11":
            borrower_id = input_int("Enter borrower ID: ")
            borrower_history(borrower_id)

        elif choice == "0":
            print("Exiting system. Goodbye!")
            break

        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main_menu()

