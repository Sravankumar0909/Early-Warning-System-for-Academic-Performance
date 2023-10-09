import sqlite3
# Establish a connection to the SQLite database file (or create a new one)
conn = sqlite3.connect('ews.db')
# Create a cursor object
cursor = conn.cursor()
# Define SQL command to create a table
delete = """drop table if exists users;"""
cursor.execute(delete)
create_table_sql = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
);
"""


# Execute the SQL command to create the table
cursor.execute(create_table_sql)
# Define SQL command to insert data
insert_data_sql = """
INSERT INTO users (username, password)
VALUES
    ('Sravankumar','20eg110103');
"""
# Execute the SQL command to insert data
cursor.execute(insert_data_sql)
retrieve = """select * from users;"""
cursor.execute(retrieve)
rows = cursor.fetchall()
for row in rows:
    print(row)
# Commit the changes to the database
conn.commit()

# Close the cursor and the database connection
cursor.close()
conn.close()
