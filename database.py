import sqlite3
from datetime import datetime

DB_PATH = '/home/Daud8642/fish_feed.db'

def get_user_tokens(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT total_tokens FROM user_tokens WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO user_tokens (user_id, total_tokens, last_updated) VALUES (?,?,?)', (user_id, 0, datetime.now()))
        conn.commit()
        tokens = 0
    else:
        tokens = row[0]
    conn.close()
    return tokens
