from app.auth.database import get_connection

connection = get_connection()

tables = connection.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' "
    "ORDER BY name"
).fetchall()

print("Existing tables:")
print([dict(row) for row in tables])

connection.close()