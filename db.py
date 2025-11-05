import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "dmts.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        approved INTEGER DEFAULT 0,
        valid_till TEXT,
        password_expiry TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS hdd_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_no TEXT,
        unit_space TEXT,
        team_code TEXT,
        premise_name TEXT,
        date_search TEXT,
        date_seized TEXT,
        data_details TEXT,
        created_by TEXT,
        created_on TEXT,
        barcode_value TEXT,
        status TEXT DEFAULT 'available'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        ts TEXT
    )''')
    conn.commit(); conn.close()

def get_columns(table):
    conn = get_conn(); c = conn.cursor()
    cols = [r[1] for r in c.execute(f'PRAGMA table_info({table})').fetchall()]
    conn.close()
    return cols
