import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .domain import seed_customers, transactions

DB_PATH=Path(os.environ.get('GREENPATH_DB', Path(__file__).resolve().parents[1]/'data'/'greenpath.db'))

@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(DB_PATH,timeout=15)
    conn.row_factory=sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally: conn.close()

def init_db():
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS transactions (id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, product_id TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS scenarios (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)')
        if db.execute('SELECT COUNT(*) FROM customers').fetchone()[0]==0:
            for c in seed_customers():
                db.execute('INSERT INTO customers VALUES (?,?)',(c['customer_id'],json.dumps(c)))
                db.executemany('INSERT INTO transactions VALUES (?,?,?)',[(t['transaction_id'],c['customer_id'],json.dumps(t)) for t in transactions(c)])

def all_customers():
    with connection() as db: return [json.loads(r['payload']) for r in db.execute('SELECT payload FROM customers ORDER BY id')]

def customer(cid):
    with connection() as db:
        row=db.execute('SELECT payload FROM customers WHERE id=?',(cid,)).fetchone()
    return json.loads(row['payload']) if row else None

def customer_transactions(cid):
    with connection() as db: return [json.loads(r['payload']) for r in db.execute('SELECT payload FROM transactions WHERE customer_id=? ORDER BY id',(cid,))]
