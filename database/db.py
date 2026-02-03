"""
Database connection utilities for WellFit
Provides reusable SQLite connection helpers
"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


def get_db_path() -> Path:
    """
    Get the absolute path to the database file.
    
    Returns:
        Path: Absolute path to wellfit.db
    """
    # Get the project root (parent of database directory)
    project_root = Path(__file__).parent.parent
    db_path = project_root / "database" / "wellfit.db"
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    return db_path


def get_db_connection() -> sqlite3.Connection:
    """
    Create a new database connection.
    
    Returns:
        sqlite3.Connection: Database connection with row factory enabled
    """
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    
    # Enable row factory for dict-like access
    conn.row_factory = sqlite3.Row
    
    return conn


@contextmanager
def get_db():
    """
    Context manager for database connections.
    Automatically handles connection closing.
    
    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
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
    """
    Execute a SELECT query and return results.
    
    Args:
        query: SQL SELECT query
        params: Query parameters (optional)
        
    Returns:
        list: List of Row objects
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_insert(query: str, params: tuple = ()) -> int:
    """
    Execute an INSERT query and return the last row ID.
    
    Args:
        query: SQL INSERT query
        params: Query parameters
        
    Returns:
        int: Last inserted row ID
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid


def execute_update(query: str, params: tuple = ()) -> int:
    """
    Execute an UPDATE or DELETE query and return affected rows.
    
    Args:
        query: SQL UPDATE/DELETE query
        params: Query parameters
        
    Returns:
        int: Number of affected rows
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount
