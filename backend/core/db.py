"""
SQLite database utility for Settings, Products, and Personas
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("database")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.DATA_DIR)
DB_PATH = os.path.join(DB_DIR, "settings.db")

def get_db_connection() -> sqlite3.Connection:
    """Get a SQLite connection, creating the DB + tables if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables."""
    conn = get_db_connection()
    try:
        # Generic Settings table (language, llm, guardrails, integrations, sector, content)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                brand_id    TEXT NOT NULL,
                type        TEXT NOT NULL,
                config_json TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                PRIMARY KEY (brand_id, type)
            )
        """)
        
        # Products table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id          TEXT PRIMARY KEY,
                brand_id    TEXT NOT NULL,
                data_json   TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        
        # Personas table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id                TEXT PRIMARY KEY,
                brand_id          TEXT NOT NULL,
                data_json         TEXT NOT NULL,
                created_at        TEXT NOT NULL,
                updated_at        TEXT NOT NULL
            )
        """)
        
        conn.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()

def get_db():
    """Get database connection."""
    conn = get_db_connection()
    try:
        return conn
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        raise
