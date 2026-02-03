
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


def get_db_path() -> Path:
    # Get the project root (parent of database directory)
    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "wellfit.db"
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    return db_path


def get_db_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    
    # Enable row factory for dict-like access
    conn.row_factory = sqlite3.Row
    
    return conn


@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_insert(query: str, params: tuple = ()) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_update(query: str, params: tuple = ()) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount
