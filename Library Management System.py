# advanced_library_system.py
import sqlite3
from datetime import datetime

# Initialize database and tables
conn = sqlite3.connect('library_system.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    status TEXT DEFAULT 'Available'
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    borrower TEXT,
    issue_date TEXT,
    return_date TEXT,
    returned INTEGER DEFAULT 0,
    FOREIGN KEY(book_id) REFERENCES books(id)
)''')

conn.commit()

# --- Functions ---

def add_book(title, author):
    cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    conn.commit()
    print(f"✅ Book '{title}' by {author} added successfully.")

def show_books():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    if books:
        for book in books:
            print(f"ID: {book[0]} | Title: {book[1]} | Author: {book[2]} | Status: {book[3]}")
    else:
        print("No books found.")

def search_books(keyword):
    cursor.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ?", (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    for book in results:
        print(f"ID: {book[0]} | Title: {book[1]} | Author: {book[2]} | Status: {book[3]}")

def issue_book(book_id, borrower):
    cursor.execute("SELECT status FROM books WHERE id=?", (book_id,))
    result = cursor.fetchone()
    if result and result[0] == 'Available':
        issue_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO transactions (book_id, borrower, issue_date) VALUES (?, ?, ?)", (book_id, borrower, issue_date))
        cursor.execute("UPDATE books SET status='Issued' WHERE id=?", (book_id,))
        conn.commit()
        print("📕 Book issued successfully.")
    else:
        print("❌ Book not available or does not exist.")

def return_book(book_id):
    return_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("UPDATE transactions SET return_date=?, returned=1 WHERE book_id=? AND returned=0", (return_date, book_id))
    cursor.execute("UPDATE books SET status='Available' WHERE id=?", (book_id,))
    conn.commit()
    print("✅ Book returned successfully.")

def main_menu():
    while True:
        print("\n===== Library Management System =====")
        print("1. Add Book")
        print("2. Show All Books")
        print("3. Search Books")
        print("4. Issue Book")
        print("5. Return Book")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            title = input("Enter book title: ")
            author = input("Enter book author: ")
            add_book(title, author)
        elif choice == '2':
            show_books()
        elif choice == '3':
            keyword = input("Enter title or author to search: ")
            search_books(keyword)
        elif choice == '4':
            book_id = int(input("Enter book ID to issue: "))
            borrower = input("Enter borrower name: ")
            issue_book(book_id, borrower)
        elif choice == '5':
            book_id = int(input("Enter book ID to return: "))
            return_book(book_id)
        elif choice == '6':
            print("Exiting system. Goodbye!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main_menu()
    conn.close()
