"""Human agents database setup and schema management."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from .database_config import DatabaseConfig


class HumanAgentsDatabase:
    """Manages human agents database setup and schema."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        if db_path is None:
            db_config = DatabaseConfig()
            self.db_path = db_config.get_human_agents_db_path()
        else:
            self.db_path = db_path
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize_database(self) -> None:
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self._get_schema_sql())
            conn.commit()

    def _get_schema_sql(self) -> str:
        """Get the SQL schema for human agents tables."""
        return """
        -- Human Agents table
        CREATE TABLE IF NOT EXISTS human_agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'offline',
            specializations TEXT NOT NULL DEFAULT '[]',  -- JSON array
            max_concurrent_conversations INTEGER NOT NULL DEFAULT 3,
            experience_level INTEGER NOT NULL DEFAULT 1,
            languages TEXT NOT NULL DEFAULT '["en"]',  -- JSON array
            shift_start TEXT,  -- HH:MM format
            shift_end TEXT,    -- HH:MM format
            metadata TEXT NOT NULL DEFAULT '{}',  -- JSON object
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_activity TEXT
        );

        -- Workload metrics table
        CREATE TABLE IF NOT EXISTS agent_workload (
            agent_id TEXT PRIMARY KEY,
            active_conversations INTEGER NOT NULL DEFAULT 0,
            queue_length INTEGER NOT NULL DEFAULT 0,
            avg_response_time_minutes REAL NOT NULL DEFAULT 0.0,
            satisfaction_score REAL NOT NULL DEFAULT 5.0,
            stress_level REAL NOT NULL DEFAULT 1.0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES human_agents (id) ON DELETE CASCADE
        );

        -- Conversation assignments table
        CREATE TABLE IF NOT EXISTS conversation_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            assigned_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL DEFAULT 'active',  -- active, completed, transferred
            FOREIGN KEY (agent_id) REFERENCES human_agents (id) ON DELETE CASCADE
        );

        -- Agent performance metrics table
        CREATE TABLE IF NOT EXISTS agent_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            metric_type TEXT NOT NULL,  -- response_time, satisfaction, stress, etc.
            value REAL NOT NULL,
            timestamp TEXT NOT NULL,
            conversation_id TEXT,
            FOREIGN KEY (agent_id) REFERENCES human_agents (id) ON DELETE CASCADE
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_agents_status ON human_agents (status);
        CREATE INDEX IF NOT EXISTS idx_agents_specializations ON human_agents (specializations);
        CREATE INDEX IF NOT EXISTS idx_agents_email ON human_agents (email);
        CREATE INDEX IF NOT EXISTS idx_workload_agent ON agent_workload (agent_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_agent ON conversation_assignments (agent_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_conversation ON conversation_assignments (conversation_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_status ON conversation_assignments (status);
        CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_metrics (agent_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_type ON agent_metrics (metric_type);
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agent_metrics (timestamp);
        """

    def reset_database(self) -> None:
        """Reset database by dropping all tables and recreating schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Drop all tables
            conn.execute("DROP TABLE IF EXISTS agent_metrics")
            conn.execute("DROP TABLE IF EXISTS conversation_assignments") 
            conn.execute("DROP TABLE IF EXISTS agent_workload")
            conn.execute("DROP TABLE IF EXISTS human_agents")
            conn.commit()
            
        # Recreate schema
        self.initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn

    def backup_database(self, backup_path: str) -> None:
        """Create a backup of the database."""
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)

    def get_table_info(self) -> dict:
        """Get information about database tables."""
        with self.get_connection() as conn:
            tables = {}
            
            # Get all table names
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            # Get info for each table
            for table_name in table_names:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                tables[table_name] = {
                    'columns': [dict(col) for col in columns],
                    'row_count': row_count
                }
            
            return tables