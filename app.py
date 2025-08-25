
import os
import sqlite3
from datetime import datetime
from functools import wraps

import pytz
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("DB_FILE", "atlancash.db")
TZ = os.getenv("TZ", "America/Santo_Domingo")
BRAND_NAME = os.getenv("BRAND_NAME", "AtlanCash")
SUPPORT_TELEGRAM = os.getenv("SUPPORT_TELEGRAM", "@soporte")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "changeme")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-this")

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def now_str():
    tz = pytz.timezone(TZ)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def ensure_interest_logs_schema(conn):
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS interest_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, interest REAL, percent REAL, base_principal REAL, balance_before REAL, balance_after REAL, applied_at TEXT)")
    cur.connection.commit()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_brand():
    return dict(BRAND_NAME=BRAND_NAME, SUPPORT_TELEGRAM=SUPPORT_TELEGRAM)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        user_id = request.form.get("user_id", "").strip()
        if not username or not user_id.isdigit():
            flash("Usuario o ID inválido", "error")
            return redirect(url_for("login"))
        con = get_conn(); cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND user_id = ?", (username, int(user_id)))
        row = cur.fetchone()
        if not row:
            flash("No se encontró el usuario. Contacta soporte si crees que es un error.", "error")
            return redirect(url_for("login"))
        session["user_id"] = row["user_id"]
        session["username"] = row["username"]
        # Opcional: marcar admin si coincide con ADMIN_ID de tu .env del bot (no imprescindible para la web)
        session["is_admin"] = False
        flash("Bienvenido/a", "ok")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["is_admin"] = True
            session["user_id"] = -1
            return redirect(url_for("admin_home"))
        flash("Credenciales inválidas", "error")
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    con = get_conn(); cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()
    # historial reciente
    cur.execute("SELECT * FROM interest_logs WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,))
    interests = cur.fetchall()
    cur.execute("SELECT * FROM deposits WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,))
    deposits = cur.fetchall()
    cur.execute("SELECT * FROM withdrawals WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,))
    withdrawals = cur.fetchall()
    return render_template("dashboard.html", user=user, interests=interests, deposits=deposits, withdrawals=withdrawals)

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        amount = float(request.form.get("amount", "0") or 0)
        txhash = request.form.get("txhash", "").strip() or None
        con = get_conn(); cur = con.cursor()
        cur.execute("INSERT INTO deposits (user_id, amount, txhash, status, created_at) VALUES (?,?,?,?,?)",
                    (session["user_id"], amount, txhash, "pending", now_str()))
        con.commit()
        flash("Depósito enviado para revisión.", "ok")
        return redirect(url_for("dashboard"))
    return render_template("deposit.html")

@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    if request.method == "POST":
        amount = float(request.form.get("amount", "0") or 0)
        address = request.form.get("address", "").strip()
        con = get_conn(); cur = con.cursor()
        cur.execute("INSERT INTO withdrawals (user_id, amount, address, status, created_at) VALUES (?,?,?,?,?)",
                    (session["user_id"], amount, address, "pending", now_str()))
        con.commit()
        flash("Retiro solicitado. Será revisado por el administrador.", "ok")
        return redirect(url_for("dashboard"))
    return render_template("withdraw.html")

# ------------------ ADMIN ------------------
@app.route("/admin")
@admin_required
def admin_home():
    con = get_conn(); cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    users_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM deposits WHERE status='pending'")
    dep_pend = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM withdrawals WHERE status='pending'")
    w_pend = cur.fetchone()["c"]
    return render_template("admin_home.html", users_count=users_count, dep_pend=dep_pend, w_pend=w_pend)

@app.route("/admin/users")
@admin_required
def admin_users():
    con = get_conn(); cur = con.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC LIMIT 200")
    users = cur.fetchall()
    return render_template("admin_users.html", users=users)

@app.route("/admin/deposits", methods=["GET", "POST"])
@admin_required
def admin_deposits():
    con = get_conn(); cur = con.cursor()
    if request.method == "POST":
        action = request.form.get("action")
        dep_id = int(request.form.get("id"))
        cur.execute("SELECT * FROM deposits WHERE id=?", (dep_id,))
        dep = cur.fetchone()
        if not dep: abort(404)
        if action == "approve":
            cur.execute("UPDATE users SET total_recharged = COALESCE(total_recharged,0)+?, balance=COALESCE(balance,0)+? WHERE user_id=?",
                        (dep["amount"], dep["amount"], dep["user_id"]))
            cur.execute("UPDATE deposits SET status='approved' WHERE id=?", (dep_id,))
        elif action == "reject":
            cur.execute("UPDATE deposits SET status='rejected' WHERE id=?", (dep_id,))
        con.commit()
        flash("Depósito actualizado.", "ok")
    cur.execute("SELECT * FROM deposits ORDER BY id DESC LIMIT 200")
    rows = cur.fetchall()
    return render_template("admin_deposits.html", rows=rows)

@app.route("/admin/withdrawals", methods=["GET", "POST"])
@admin_required
def admin_withdrawals():
    con = get_conn(); cur = con.cursor()
    if request.method == "POST":
        action = request.form.get("action")
        wid = int(request.form.get("id"))
        cur.execute("SELECT * FROM withdrawals WHERE id=?", (wid,))
        w = cur.fetchone()
        if not w: abort(404)
        if action == "approve":
            cur.execute("UPDATE users SET balance = COALESCE(balance,0)-? WHERE user_id=?", (w["amount"], w["user_id"]))
            cur.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (wid,))
        elif action == "reject":
            cur.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
        con.commit()
        flash("Retiro actualizado.", "ok")
    cur.execute("SELECT * FROM withdrawals ORDER BY id DESC LIMIT 200")
    rows = cur.fetchall()
    return render_template("admin_withdrawals.html", rows=rows)

@app.route("/admin/force-interest", methods=["POST"])
@admin_required
def admin_force_interest():
    con = get_conn(); ensure_interest_logs_schema(con); cur = con.cursor()
    cur.execute("SELECT user_id, balance, earnings, total_recharged, plan_percent FROM users WHERE COALESCE(total_recharged,0) > 0 AND COALESCE(plan_percent,0) > 0")
    users = cur.fetchall()
    count = 0
    for u in users:
        base = u["total_recharged"] or 0.0
        percent = u["plan_percent"] or 0.0
        interest = round(base * (percent/100.0), 8)
        bal_before = u["balance"] or 0.0
        bal_after = bal_before + interest
        cur.execute("UPDATE users SET balance=?, earnings=COALESCE(earnings,0)+? WHERE user_id=?",
                    (bal_after, interest, u["user_id"]))
        cur.execute("""INSERT INTO interest_logs (user_id, interest, percent, base_principal, balance_before, balance_after, applied_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (u["user_id"], interest, percent, base, bal_before, bal_after, now_str()))
        count += 1
    con.commit()
    flash(f"Intereses aplicados a {count} usuarios.", "ok")
    return redirect(url_for("admin_home"))

if __name__ == "__main__":
    con = get_conn(); cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 0,
        earnings REAL DEFAULT 0,
        total_recharged REAL DEFAULT 0,
        plan_percent REAL DEFAULT 0,
        active_plan TEXT,
        ref_by INTEGER,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        txhash TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        address TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    con.commit()
    ensure_interest_logs_schema(con)
    app.run(host="0.0.0.0", port=5000, debug=True)
