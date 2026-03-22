"""
Database connection utilities for WellFit
Provides reusable PostgreSQL connection helpers using psycopg2
"""
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
from contextlib import contextmanager
import os


def get_db_connection():
    """
    Create a new database connection.
    
    Returns:
        psycopg2 connection: Database connection
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    conn = psycopg2.connect(database_url)
    return conn


@contextmanager
def get_db():
    """
    Context manager for database connections.
    Automatically handles connection closing.
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
        list: List of dict-like objects
    """
    # Convert SQLite ? placeholders to PostgreSQL %s
    query = query.replace('?', '%s')
    
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
    query = query.replace('?', '%s').strip().rstrip(';')

    # PostgreSQL needs RETURNING id. Do not duplicate (case-insensitive).
    # Note: "RETURNING id" not in query.upper() was wrong — "RETURNING ID" in SQL
    # would not match lowercase "id", causing a second RETURNING and syntax errors.
    if not re.search(r'\bRETURNING\s+id\b', query, re.IGNORECASE):
        query = f"{query} RETURNING id"

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None


def execute_update(query: str, params: tuple = ()) -> int:
    """
    Execute an UPDATE or DELETE query and return affected rows.
    
    Args:
        query: SQL UPDATE/DELETE query
        params: Query parameters
        
    Returns:
        int: Number of affected rows
    """
    query = query.replace('?', '%s')
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

