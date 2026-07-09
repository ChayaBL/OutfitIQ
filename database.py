import sqlite3

connection = sqlite3.connect("outfitiq.db")

cursor = connection.cursor()

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Wardrobe Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS wardrobe(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    color TEXT NOT NULL,
    season TEXT NOT NULL,
    image TEXT NOT NULL
)
""")


connection.commit()
connection.close()

print("Database created successfully!")