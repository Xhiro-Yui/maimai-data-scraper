import os
import sys
import sqlite3

def get_db_path():
    if getattr(sys, 'frozen', False):
        # Compiled exe → stay next to exe
        base_path = os.path.dirname(sys.executable)
        app_folder = os.path.join(base_path, "application")
    else:
        # Dev mode → one folder up
        base_path = os.path.dirname(os.path.abspath(__file__))
        app_folder = os.path.abspath(os.path.join(base_path, "../application"))

    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, "maimai_data.db")
    # return os.path.join(app_folder, "maimai_scores.db")

def get_connection():
    db_path = get_db_path()
    return sqlite3.connect(db_path)

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS play_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idx TEXT,
            title TEXT,
            difficulty TEXT,
            music_type TEXT,
            track TEXT,
            place TEXT,
            played_at TEXT,
            achievement TEXT,
            score TEXT,
            dx_stars INTEGER,
            rank TEXT,
            fc_status TEXT,
            sync_status TEXT,
            max_combo TEXT,
            max_sync TEXT,
            fast INTEGER,
            late INTEGER,
            tap_detail TEXT,
            hold_detail TEXT,
            slide_detail TEXT,
            touch_detail TEXT,
            break_detail TEXT,
            new_achievement BOOLEAN,
            new_dx_score BOOLEAN
        )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_plays INTEGER
        )""")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_play_data_idx ON play_data(idx)")
    conn.commit()
    conn.close()


