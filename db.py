import sqlite3

conn = sqlite3.connect('market.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()