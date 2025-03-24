import sqlite3

conn = sqlite3.connect("storage.db")
cursor = conn.cursor()

def calculate_total_value():
    cursor.execute("SELECT SUM(price) FROM documents")
    total_value = cursor.fetchone()[0]
    return total_value

print(f"Calculating total {calculate_total_value()}")