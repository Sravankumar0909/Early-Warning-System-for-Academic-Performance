import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('ews.db')

# Create a cursor object
cursor = conn.cursor()

# Define the SQL query to retrieve data
query = "SELECT model_name FROM model"

# Execute the SQL query
cursor.execute(query)

# Fetch all rows
rows = cursor.fetchall()

# Process and work with the retrieved data
for row in rows:
    print(row)  # Example: Print each row

# Close the cursor and the database connection
cursor.close()
conn.close()
