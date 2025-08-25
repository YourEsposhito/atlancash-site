import sqlite3

DB_NAME = "atlancash.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# 1. Verificar columnas de la tabla users
cur.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cur.fetchall()]

if "user_id" not in columns:
    print("⚡ Migrando: Agregando columna user_id a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN user_id INTEGER")

if "username" not in columns:
    print("⚡ Migrando: Agregando columna username a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN username TEXT")

if "first_name" not in columns:
    print("⚡ Migrando: Agregando columna first_name a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN first_name TEXT")

if "balance" not in columns:
    print("⚡ Migrando: Agregando columna balance a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")

if "total_recharged" not in columns:
    print("⚡ Migrando: Agregando columna total_recharged a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN total_recharged REAL DEFAULT 0")

if "active_plan" not in columns:
    print("⚡ Migrando: Agregando columna active_plan a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN active_plan TEXT DEFAULT NULL")

if "plan_pct" not in columns:
    print("⚡ Migrando: Agregando columna plan_pct a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN plan_pct REAL DEFAULT 0")

if "created_at" not in columns:
    print("⚡ Migrando: Agregando columna created_at a tabla users...")
    cur.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

conn.commit()
conn.close()

print("✅ Migración completada correctamente (sin UNIQUE en user_id).")
