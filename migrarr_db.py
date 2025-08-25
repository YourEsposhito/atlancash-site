import sqlite3

conn = sqlite3.connect("atlancash.db")
cur = conn.cursor()

# Revisar si existe cada columna y agregar si falta
columns_to_add = {
    "earnings": "REAL DEFAULT 0",
    "pending_deposit": "REAL DEFAULT 0",
    "pending_withdraw": "REAL DEFAULT 0",
    "plan_percent": "REAL DEFAULT 0"
}

for col, definition in columns_to_add.items():
    try:
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        print(f"✅ Columna {col} agregada correctamente.")
    except sqlite3.OperationalError:
        print(f"⚠️ Columna {col} ya existe, saltando.")

conn.commit()
conn.close()
