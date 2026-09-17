import sqlite3

from darukaa.measurements.profile import EnvironmentalProfile


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, profile_json TEXT)")
    conn.commit()


def load_profile(conn: sqlite3.Connection, session_id: str) -> EnvironmentalProfile:
    row = conn.execute("SELECT profile_json FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    if row is None:
        return EnvironmentalProfile()
    return EnvironmentalProfile.model_validate_json(row[0])


def save_profile(conn: sqlite3.Connection, session_id: str, profile: EnvironmentalProfile) -> None:
    conn.execute(
        "INSERT INTO sessions (session_id, profile_json) VALUES (?, ?) "
        "ON CONFLICT(session_id) DO UPDATE SET profile_json=excluded.profile_json",
        (session_id, profile.model_dump_json()),
    )
    conn.commit()
