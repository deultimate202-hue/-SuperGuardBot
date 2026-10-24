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
            content_filter_enabled INTEGER DEFAULT 1,
            rate_limit_enabled INTEGER DEFAULT 1,
            filtered_terms TEXT DEFAULT '[]',
            filtered_domains TEXT DEFAULT '[]',
            notify_limit INTEGER DEFAULT 3,
            restrict_duration INTEGER DEFAULT 60
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_state (
            chat_id INTEGER,
            user_id INTEGER,
            notifications INTEGER DEFAULT 0,
            restricted_until INTEGER DEFAULT 0,
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
        conn = get_db()
        conn.cursor().execute("INSERT INTO settings (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
        return get_settings(chat_id)
    
    return {
        "chat_id": row["chat_id"],
        "content_filter_enabled": bool(row["content_filter_enabled"]),
        "rate_limit_enabled": bool(row["rate_limit_enabled"]),
        "filtered_terms": json.loads(row["filtered_terms"]),
        "filtered_domains": json.loads(row["filtered_domains"]),
        "notify_limit": row["notify_limit"],
        "restrict_duration": row["restrict_duration"]
    }

def update_settings(chat_id, key, value):
    conn = get_db()
    if key in ["filtered_terms", "filtered_domains"]:
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
        return {"notifications": 0, "restricted_until": 0, "last_msg_time": 0, "msg_count": 0}
    return dict(row)

def update_user_state(chat_id, user_id, state):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_state (chat_id, user_id, notifications, restricted_until, last_msg_time, msg_count)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id, user_id) 
        DO UPDATE SET notifications=excluded.notifications, restricted_until=excluded.restricted_until, 
                      last_msg_time=excluded.last_msg_time, msg_count=excluded.msg_count
    ''', (chat_id, user_id, state["notifications"], state["restricted_until"], state["last_msg_time"], state["msg_count"]))
    conn.commit()
    conn.close()
