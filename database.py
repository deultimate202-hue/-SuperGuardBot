import sqlite3
import json
from config import DB_NAME

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            anti_spam INTEGER DEFAULT 1,
            anti_flood INTEGER DEFAULT 1,
            blocked_words TEXT DEFAULT '[]',
            blocked_domains TEXT DEFAULT '[]',
            warn_limit INTEGER DEFAULT 3,
            mute_duration INTEGER DEFAULT 60
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_state (
            chat_id INTEGER,
            user_id INTEGER,
            warnings INTEGER DEFAULT 0,
            muted_until INTEGER DEFAULT 0,
            last_msg_time REAL DEFAULT 0,
            msg_count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')
    conn.commit()
    conn.close()

def get_settings(chat_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        # Initialize default settings if not exists
        conn = get_db()
        conn.cursor().execute("INSERT INTO settings (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
        return get_settings(chat_id)
    
    return {
        "chat_id": row["chat_id"],
        "anti_spam": bool(row["anti_spam"]),
        "anti_flood": bool(row["anti_flood"]),
        "blocked_words": json.loads(row["blocked_words"]),
        "blocked_domains": json.loads(row["blocked_domains"]),
        "warn_limit": row["warn_limit"],
        "mute_duration": row["mute_duration"]
    }

def update_settings(chat_id, key, value):
    conn = get_db()
    if key in ["blocked_words", "blocked_domains"]:
        value = json.dumps(value)
    conn.cursor().execute(f"UPDATE settings SET {key} = ? WHERE chat_id = ?", (value, chat_id))
    conn.commit()
    conn.close()

def get_user_state(chat_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_state WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"warnings": 0, "muted_until": 0, "last_msg_time": 0, "msg_count": 0}
    return dict(row)

def update_user_state(chat_id, user_id, state):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_state (chat_id, user_id, warnings, muted_until, last_msg_time, msg_count)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id, user_id) 
        DO UPDATE SET warnings=excluded.warnings, muted_until=excluded.muted_until, 
                      last_msg_time=excluded.last_msg_time, msg_count=excluded.msg_count
    ''', (chat_id, user_id, state["warnings"], state["muted_until"], state["last_msg_time"], state["msg_count"]))
    conn.commit()
    conn.close()
