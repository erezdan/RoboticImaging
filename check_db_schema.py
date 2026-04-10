"""Check database schema"""
import sqlite3
from pathlib import Path

# Connect to database
db_path = Path("db/roboimaging.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get schema
cursor.execute("PRAGMA table_info(spots)")
columns = cursor.fetchall()

print('=' * 70)
print('SPOTS TABLE SCHEMA')
print('=' * 70)
for col in columns:
    cid, name, type_, notnull, dflt_value, pk = col
    print(f'{name:20} {type_:15} PK={pk} NOT NULL={notnull}')

print('\n' + '=' * 70)
print('TABLE CREATION STATEMENT')
print('=' * 70)
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='spots'")
result = cursor.fetchone()
if result:
    print(result[0])
else:
    print('Table not found!')

conn.close()
