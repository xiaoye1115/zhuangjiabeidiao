import sqlite3
import os

# Check if database file exists
db_path = 'experts.db'
if not os.path.exists(db_path):
    print(f"Database file {db_path} does not exist")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"- {table[0]}")

# Check if Expert table exists
if ('expert',) in tables:
    # Get columns in Expert table
    cursor.execute("PRAGMA table_info(expert)")
    columns = cursor.fetchall()
    print("\nColumns in expert table:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Count expert records
    cursor.execute("SELECT COUNT(*) FROM expert")
    count = cursor.fetchone()[0]
    print(f"\nNumber of expert records: {count}")
    
    # Sample some records if they exist
    if count > 0:
        cursor.execute("SELECT * FROM expert LIMIT 3")
        experts = cursor.fetchall()
        print("\nSample expert records:")
        for expert in experts:
            print(f"- {expert}")
else:
    print("\nNo 'expert' table found in the database")

# Check if User table exists
if ('user',) in tables:
    # Count user records
    cursor.execute("SELECT COUNT(*) FROM user")
    count = cursor.fetchone()[0]
    print(f"\nNumber of user records: {count}")

# Close the connection
conn.close() 