import sqlite3

DB_PATH = r'C:\Users\HESSEFREDERICK\PycharmProjects\CARE_App\data\CARE_Database.db'

try:
    conn = sqlite3.connect(DB_PATH)
    print("Database connection successful!")
    conn.close()
except sqlite3.OperationalError as e:
    print("Failed to connect to the database:", e)
