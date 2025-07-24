"""
Context management for storing and retrieving conversation context
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from ..core.logging import get_logger
from ..interfaces.core.context import ContextEntry, ContextProvider
from .database_config import DatabaseConfig


class SQLiteContextProvider(ContextProvider):
    """SQLite-based context provider"""

    def __init__(self, db_path: str | None = None, config_manager=None):
        """
        Initialize SQLite context provider
        
        Args:
            db_path: Optional explicit database path (overrides configuration)
            config_manager: Configuration manager for centralized database settings
        """
        self.config_manager = config_manager
        self.db_config = DatabaseConfig(config_manager)

        # Use explicit path or get from configuration
        if db_path is not None:
            self.db_path = db_path
        else:
            self.db_path = self.db_config.get_db_path()

        self.logger = get_logger(__name__)
        self.logger.info(
            "SQLite context provider initialized",
            extra={
                "db_path": self.db_path,
                "using_config": config_manager is not None,
                "operation": "__init__"
            }
        )
        self._init_database()

    def _init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_entries (
                    entry_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_session ON context_entries(user_id, session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON context_entries(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entry_type ON context_entries(entry_type)"
            )

    def save_context_entry(self, entry: ContextEntry) -> bool:
        """Save a context entry to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO context_entries 
                    (entry_id, user_id, session_id, timestamp, entry_type, content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.entry_id,
                        entry.user_id,
                        entry.session_id,
                        entry.timestamp.isoformat(),
                        entry.entry_type,
                        entry.content,
                        json.dumps(entry.metadata),
                    ),
                )
                return True
        except Exception as e:
            self.logger.error(
                "Failed to save context entry",
                extra={
                    "entry_id": entry.entry_id,
                    "user_id": entry.user_id,
                    "session_id": entry.session_id,
                    "error": str(e),
                    "operation": "save_context_entry",
                },
            )
            return False

    def get_context_summary(self, user_id: str, session_id: str) -> dict[str, Any]:
        """Get context summary for user/session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get basic counts
                cursor = conn.execute(
                    """
                    SELECT entry_type, COUNT(*) as count
                    FROM context_entries
                    WHERE user_id = ? AND session_id = ?
                    GROUP BY entry_type
                """,
                    (user_id, session_id),
                )

                type_counts = dict(cursor.fetchall())

                # Get recent queries
                cursor = conn.execute(
                    """
                    SELECT content
                    FROM context_entries
                    WHERE user_id = ? AND session_id = ? AND entry_type = 'query'
                    ORDER BY timestamp DESC
                    LIMIT 5
                """,
                    (user_id, session_id),
                )

                recent_queries = [row[0] for row in cursor.fetchall()]

                # Get escalation count
                escalation_count = type_counts.get("escalation", 0)

                return {
                    "entries_count": sum(type_counts.values()),
                    "type_breakdown": type_counts,
                    "recent_queries": recent_queries,
                    "escalation_count": escalation_count,
                    "last_activity": self._get_last_activity(user_id, session_id),
                }
        except Exception as e:
            self.logger.error(
                "Failed to get context summary",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e),
                    "operation": "get_context_summary",
                },
            )
            return {
                "entries_count": 0,
                "type_breakdown": {},
                "recent_queries": [],
                "escalation_count": 0,
                "last_activity": None,
            }

    def get_context(
        self,
        user_id: str = None,
        session_id: str = None,
        limit: int = None,
        offset: int = 0,
        since: datetime = None
    ) -> list[ContextEntry]:
        """Get context entries with flexible filtering"""
        try:
            where_conditions = []
            params = []

            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)

            if session_id:
                where_conditions.append("session_id = ?")
                params.append(session_id)

            if since:
                where_conditions.append("timestamp >= ?")
                params.append(since.isoformat())

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = f"""
                SELECT entry_id, user_id, session_id, timestamp, entry_type, content, metadata
                FROM context_entries
                WHERE {where_clause}
                ORDER BY timestamp DESC
            """

            if limit:
                query += " LIMIT ?"
                params.append(limit)
                if offset:
                    query += " OFFSET ?"
                    params.append(offset)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)

                entries = []
                for row in cursor.fetchall():
                    entry = ContextEntry(
                        entry_id=row[0],
                        user_id=row[1],
                        session_id=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        entry_type=row[4],
                        content=row[5],
                        metadata=json.loads(row[6]) if row[6] else {},
                    )
                    entries.append(entry)

                self.logger.debug(
                    "Context entries retrieved",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "count": len(entries),
                        "operation": "get_context"
                    }
                )

                return entries

        except Exception as e:
            self.logger.error(
                "Failed to retrieve context entries",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e),
                    "operation": "get_context"
                }
            )
            return []

    def get_recent_context(
        self, user_id: str, session_id: str, limit: int = 10
    ) -> list[ContextEntry]:
        """Get recent context entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT entry_id, user_id, session_id, timestamp, entry_type, content, metadata
                    FROM context_entries
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (user_id, session_id, limit),
                )

                entries = []
                for row in cursor.fetchall():
                    entry = ContextEntry(
                        entry_id=row[0],
                        user_id=row[1],
                        session_id=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        entry_type=row[4],
                        content=row[5],
                        metadata=json.loads(row[6]),
                    )
                    entries.append(entry)

                return entries
        except Exception as e:
            self.logger.error(
                "Failed to get recent context",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "limit": limit,
                    "error": str(e),
                    "operation": "get_recent_context",
                },
            )
            return []

    def _get_last_activity(self, user_id: str, session_id: str) -> datetime | None:
        """Get timestamp of last activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT timestamp
                    FROM context_entries
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """,
                    (user_id, session_id),
                )

                row = cursor.fetchone()
                if row:
                    return datetime.fromisoformat(row[0])
                return None
        except Exception as e:
            self.logger.error(
                "Failed to get last activity",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e),
                    "operation": "get_last_activity",
                },
            )
            return None

    def cleanup_old_entries(self, days: int = 30):
        """Clean up old context entries"""
        cutoff_date = datetime.now() - timedelta(days=days)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    DELETE FROM context_entries
                    WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )
                self.logger.info(
                    "Cleaned up old context entries",
                    extra={
                        "days": days,
                        "cutoff_date": cutoff_date.isoformat(),
                        "operation": "cleanup_old_entries",
                    },
                )
        except Exception as e:
            self.logger.error(
                "Failed to cleanup old entries",
                extra={
                    "days": days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "error": str(e),
                    "operation": "cleanup_old_entries",
                },
            )

    def get_context_metrics(self) -> dict[str, Any]:
        """Get context metrics and statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total queries
                cursor.execute("SELECT COUNT(*) FROM context_entries WHERE entry_type = 'query'")
                total_queries = cursor.fetchone()[0]

                # Total users
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM context_entries")
                total_users = cursor.fetchone()[0]

                # Total sessions
                cursor.execute("SELECT COUNT(DISTINCT session_id) FROM context_entries")
                total_sessions = cursor.fetchone()[0]

                # Escalated queries
                cursor.execute("""
                    SELECT COUNT(*) FROM context_entries 
                    WHERE entry_type = 'query' AND json_extract(metadata, '$.escalated') = 1
                """)
                escalated_queries = cursor.fetchone()[0]

                # Average response time
                cursor.execute("""
                    SELECT AVG(CAST(json_extract(metadata, '$.response_time') AS REAL))
                    FROM context_entries 
                    WHERE entry_type = 'query' AND json_extract(metadata, '$.response_time') IS NOT NULL
                """)
                avg_response_time_result = cursor.fetchone()[0]
                avg_response_time = avg_response_time_result if avg_response_time_result else 0.0

                escalation_rate = escalated_queries / total_queries if total_queries > 0 else 0.0

                metrics = {
                    "total_queries": total_queries,
                    "total_users": total_users,
                    "total_sessions": total_sessions,
                    "escalation_rate": escalation_rate,
                    "avg_response_time": avg_response_time,
                    "escalated_queries": escalated_queries
                }

                self.logger.debug(
                    "Context metrics calculated",
                    extra={
                        "metrics": metrics,
                        "operation": "get_context_metrics"
                    }
                )

                return metrics

        except Exception as e:
            self.logger.error(
                "Failed to calculate context metrics",
                extra={
                    "error": str(e),
                    "operation": "get_context_metrics"
                }
            )
            return {
                "total_queries": 0,
                "total_users": 0,
                "total_sessions": 0,
                "escalation_rate": 0.0,
                "avg_response_time": 0.0,
                "escalated_queries": 0
            }
