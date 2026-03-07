import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "calls.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS franchises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            whatsapp TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT NOT NULL,
            franchise_id INTEGER NOT NULL,
            to_phone TEXT NOT NULL,
            status TEXT DEFAULT 'initiated',
            meeting_booked BOOLEAN DEFAULT 0,
            transcript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(franchise_id) REFERENCES franchises(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_franchise(name: str, whatsapp: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO franchises (name, whatsapp) VALUES (?, ?)', (name, whatsapp))
    franchise_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return franchise_id

def get_franchises():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM franchises')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_franchise(franchise_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM franchises WHERE id = ?', (franchise_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_call_record(call_id: str, franchise_id: int, to_phone: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO calls (call_id, franchise_id, to_phone) VALUES (?, ?, ?)',
        (call_id, franchise_id, to_phone)
    )
    conn.commit()
    conn.close()

def update_call_record(call_id: str, status: str, transcript: str, meeting_booked: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE calls SET status = ?, transcript = ?, meeting_booked = ? WHERE call_id = ?',
        (status, transcript, meeting_booked, call_id)
    )
    conn.commit()
    conn.close()

def get_call_history():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM calls ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
