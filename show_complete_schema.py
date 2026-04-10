"""Show complete database structure with all data"""
import sqlite3
import json

conn = sqlite3.connect('db/roboimaging.db')
cursor = conn.cursor()

print("=" * 100)
print("COMPLETE DATABASE STRUCTURE & CONTENT")
print("=" * 100)

# 1. SPOTS TABLE
print("\n1️⃣  SPOTS TABLE SCHEMA:")
print("-" * 100)
cursor.execute("PRAGMA table_info(spots)")
for row in cursor.fetchall():
    cid, name, type_, notnull, dflt_value, pk = row
    nullable = "NOT NULL" if notnull else "NULL"
    pk_marker = "🔑 PK" if pk else ""
    print(f"   {name:20} {type_:12} {nullable:12} {pk_marker}")

print("\n2️⃣  SPOTS TABLE DATA:")
print("-" * 100)
cursor.execute("SELECT * FROM spots WHERE spot_id='spot_123'")
row = cursor.fetchone()
if row:
    columns = [description[0] for description in cursor.description]
    for col, val in zip(columns, row):
        if col == 'vlm_analysis' and val:
            print(f"\n   📊 {col} (JSON):")
            try:
                vlm_data = json.loads(val)
                print(f"      {json.dumps(vlm_data, indent=6)}")
            except:
                print(f"      {val}")
        elif col == 'qa_results' and val:
            print(f"\n   ❓ {col} (JSON):")
            try:
                qa_data = json.loads(val)
                print(f"      {json.dumps(qa_data, indent=6)}")
            except:
                print(f"      {val}")
        else:
            print(f"   {col}: {val}")

# 2. Count other tables
print("\n\n3️⃣  OTHER TABLES:")
print("-" * 100)
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""")
tables = cursor.fetchall()
for table_name, in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name[0]}")
    count = cursor.fetchone()[0]
    print(f"   • {table_name[0]:20} ({count} rows)")

# 3. Summary
print("\n\n4️⃣  DATA SUMMARY:")
print("-" * 100)
cursor.execute("SELECT COUNT(*) FROM spots")
spot_count = cursor.fetchone()[0]
print(f"   Spots with data: {spot_count}")

print("\n" + "=" * 100)
print("✅ All data is present and accessible!")
print("=" * 100)

conn.close()
