"""
Comprehensive tests for context management system.
Tests SQLiteContextProvider, context storage, retrieval, and summarization.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.context_manager import ContextEntry, SQLiteContextProvider
from src.core.logging.exceptions import ConfigurationError, ValidationError


class TestContextEntry:
    """Test suite for ContextEntry data model"""

    def test_context_entry_creation(self):
        """Test ContextEntry creation and validation"""
        entry = ContextEntry(
            user_id="test_user",
            session_id="test_session",
            query_id="query_123",
            query="How do I reset my password?",
            response="To reset your password, go to...",
            timestamp=datetime.now(),
            escalated=False,
            response_time=1.23,
            token_count=150,
        )

        assert entry.user_id == "test_user"
        assert entry.session_id == "test_session"
        assert entry.query_id == "query_123"
        assert entry.query == "How do I reset my password?"
        assert entry.response == "To reset your password, go to..."
        assert entry.escalated is False
        assert entry.response_time == 1.23
        assert entry.token_count == 150

    def test_context_entry_serialization(self):
        """Test ContextEntry serialization to dict"""
        entry = ContextEntry(
            user_id="test_user",
            session_id="test_session",
            query_id="query_123",
            query="Test query",
            response="Test response",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            escalated=True,
            response_time=2.5,
            token_count=200,
        )

        entry_dict = entry.to_dict()

        assert entry_dict["user_id"] == "test_user"
        assert entry_dict["session_id"] == "test_session"
        assert entry_dict["query_id"] == "query_123"
        assert entry_dict["query"] == "Test query"
        assert entry_dict["response"] == "Test response"
        assert entry_dict["escalated"] is True
        assert entry_dict["response_time"] == 2.5
        assert entry_dict["token_count"] == 200

    def test_context_entry_from_dict(self):
        """Test ContextEntry creation from dictionary"""
        entry_dict = {
            "user_id": "test_user",
            "session_id": "test_session",
            "query_id": "query_123",
            "query": "Test query",
            "response": "Test response",
            "timestamp": "2023-01-01T12:00:00",
            "escalated": False,
            "response_time": 1.5,
            "token_count": 100,
        }

        entry = ContextEntry.from_dict(entry_dict)

        assert entry.user_id == "test_user"
        assert entry.session_id == "test_session"
        assert entry.query_id == "query_123"
        assert entry.query == "Test query"
        assert entry.response == "Test response"
        assert entry.escalated is False
        assert entry.response_time == 1.5
        assert entry.token_count == 100

    def test_context_entry_validation(self):
        """Test ContextEntry validation"""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            ContextEntry(
                user_id="",  # Empty user_id
                session_id="test_session",
                query_id="query_123",
                query="Test query",
                response="Test response",
                timestamp=datetime.now(),
            )

        # Invalid response_time should raise ValidationError
        with pytest.raises(ValidationError):
            ContextEntry(
                user_id="test_user",
                session_id="test_session",
                query_id="query_123",
                query="Test query",
                response="Test response",
                timestamp=datetime.now(),
                response_time=-1.0,  # Negative time
            )

    def test_context_entry_summary(self):
        """Test ContextEntry summary generation"""
        entry = ContextEntry(
            user_id="test_user",
            session_id="test_session",
            query_id="query_123",
            query="How do I reset my password?",
            response="To reset your password, go to the settings page...",
            timestamp=datetime.now(),
            escalated=False,
            response_time=1.23,
            token_count=150,
        )

        summary = entry.get_summary()

        assert "password reset" in summary.lower()
        assert "settings" in summary.lower()
        assert len(summary) <= 200  # Should be concise


class TestSQLiteContextProvider:
    """Test suite for SQLiteContextProvider"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = temp_file.name
        yield db_path
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def context_provider(self, temp_db_path):
        """Create SQLiteContextProvider instance"""
        return SQLiteContextProvider(temp_db_path)

    @pytest.fixture
    def sample_context_entries(self):
        """Create sample context entries for testing"""
        base_time = datetime.now()
        return [
            ContextEntry(
                user_id="user1",
                session_id="session1",
                query_id="query1",
                query="How do I reset my password?",
                response="To reset your password, go to settings...",
                timestamp=base_time - timedelta(minutes=10),
                escalated=False,
                response_time=1.2,
                token_count=100,
            ),
            ContextEntry(
                user_id="user1",
                session_id="session1",
                query_id="query2",
                query="I still can't reset my password",
                response="Let me help you with that...",
                timestamp=base_time - timedelta(minutes=5),
                escalated=True,
                response_time=2.1,
                token_count=150,
            ),
            ContextEntry(
                user_id="user2",
                session_id="session2",
                query_id="query3",
                query="What are your business hours?",
                response="Our business hours are...",
                timestamp=base_time - timedelta(minutes=3),
                escalated=False,
                response_time=0.8,
                token_count=80,
            ),
        ]

    def test_initialization_creates_database(self, temp_db_path):
        """Test that initialization creates database and tables"""
        provider = SQLiteContextProvider(temp_db_path)

        assert Path(temp_db_path).exists()

        # Check that tables were created
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "context_entries" in tables
            assert "session_metadata" in tables

    def test_initialization_with_invalid_path(self):
        """Test initialization with invalid database path"""
        with pytest.raises(ConfigurationError):
            SQLiteContextProvider("/invalid/path/that/does/not/exist.db")

    def test_save_context_entry(self, context_provider, sample_context_entries):
        """Test saving context entries"""
        entry = sample_context_entries[0]

        # Should not raise exception
        context_provider.save_context_entry(entry)

        # Verify entry was saved
        with sqlite3.connect(context_provider.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM context_entries")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_save_multiple_context_entries(
        self, context_provider, sample_context_entries
    ):
        """Test saving multiple context entries"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Verify all entries were saved
        with sqlite3.connect(context_provider.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM context_entries")
            count = cursor.fetchone()[0]
            assert count == len(sample_context_entries)

    def test_save_duplicate_query_id(self, context_provider, sample_context_entries):
        """Test saving entries with duplicate query_id"""
        entry = sample_context_entries[0]

        # Save first time
        context_provider.save_context_entry(entry)

        # Save again with same query_id - should handle gracefully
        context_provider.save_context_entry(entry)

        # Should still have only one entry
        with sqlite3.connect(context_provider.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM context_entries")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_get_context_by_user_id(self, context_provider, sample_context_entries):
        """Test retrieving context by user_id"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Get context for user1
        user1_context = context_provider.get_context(user_id="user1")
        assert len(user1_context) == 2
        assert all(entry.user_id == "user1" for entry in user1_context)

        # Get context for user2
        user2_context = context_provider.get_context(user_id="user2")
        assert len(user2_context) == 1
        assert user2_context[0].user_id == "user2"

        # Get context for non-existent user
        no_context = context_provider.get_context(user_id="nonexistent")
        assert len(no_context) == 0

    def test_get_context_by_session_id(self, context_provider, sample_context_entries):
        """Test retrieving context by session_id"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Get context for session1
        session1_context = context_provider.get_context(session_id="session1")
        assert len(session1_context) == 2
        assert all(entry.session_id == "session1" for entry in session1_context)

        # Get context for session2
        session2_context = context_provider.get_context(session_id="session2")
        assert len(session2_context) == 1
        assert session2_context[0].session_id == "session2"

    def test_get_context_with_limit(self, context_provider, sample_context_entries):
        """Test retrieving context with limit"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Get limited context
        limited_context = context_provider.get_context(user_id="user1", limit=1)
        assert len(limited_context) == 1

        # Should return most recent entry
        assert limited_context[0].query_id == "query2"

    def test_get_context_with_date_range(
        self, context_provider, sample_context_entries
    ):
        """Test retrieving context within date range"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Get context from last 7 minutes
        since_time = datetime.now() - timedelta(minutes=7)
        recent_context = context_provider.get_context(user_id="user1", since=since_time)

        assert len(recent_context) == 1
        assert recent_context[0].query_id == "query2"

    def test_get_context_ordering(self, context_provider, sample_context_entries):
        """Test that context is returned in correct order (most recent first)"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        user1_context = context_provider.get_context(user_id="user1")

        # Should be ordered by timestamp descending
        assert user1_context[0].query_id == "query2"  # More recent
        assert user1_context[1].query_id == "query1"  # Older

    def test_get_session_summary(self, context_provider, sample_context_entries):
        """Test session summary generation"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        summary = context_provider.get_session_summary("session1")

        assert "query_count" in summary
        assert "escalation_count" in summary
        assert "avg_response_time" in summary
        assert "total_tokens" in summary
        assert "topics" in summary

        assert summary["query_count"] == 2
        assert summary["escalation_count"] == 1
        assert summary["avg_response_time"] == (1.2 + 2.1) / 2
        assert summary["total_tokens"] == 250

    def test_summarize_context_entries(self, context_provider, sample_context_entries):
        """Test context summarization"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        user1_context = context_provider.get_context(user_id="user1")
        summary = context_provider.summarize_context(user1_context)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "password" in summary.lower()

    def test_cleanup_old_entries(self, context_provider, sample_context_entries):
        """Test cleanup of old context entries"""
        # Create old entries
        old_entries = []
        for i, entry in enumerate(sample_context_entries):
            entry.timestamp = datetime.now() - timedelta(days=35)  # Older than 30 days
            entry.query_id = f"old_query_{i}"
            old_entries.append(entry)

        # Save old entries
        for entry in old_entries:
            context_provider.save_context_entry(entry)

        # Save recent entry
        recent_entry = ContextEntry(
            user_id="user1",
            session_id="session1",
            query_id="recent_query",
            query="Recent query",
            response="Recent response",
            timestamp=datetime.now(),
            escalated=False,
            response_time=1.0,
            token_count=50,
        )
        context_provider.save_context_entry(recent_entry)

        # Cleanup old entries
        cutoff_date = datetime.now() - timedelta(days=30)
        deleted_count = context_provider.cleanup_old_entries(cutoff_date)

        assert deleted_count == len(old_entries)

        # Verify only recent entry remains
        with sqlite3.connect(context_provider.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM context_entries")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_database_transactions(self, context_provider, sample_context_entries):
        """Test database transaction handling"""
        entry = sample_context_entries[0]

        # Mock database error during save
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn

            # Should handle database error gracefully
            with pytest.raises(Exception):
                context_provider.save_context_entry(entry)

    def test_concurrent_access(self, context_provider, sample_context_entries):
        """Test concurrent access to context provider"""
        import threading
        import time

        results = []

        def save_entries():
            for entry in sample_context_entries:
                entry.query_id = f"{entry.query_id}_{threading.current_thread().ident}"
                context_provider.save_context_entry(entry)
                results.append(entry.query_id)
                time.sleep(0.001)  # Small delay to encourage race conditions

        # Start multiple threads
        threads = [threading.Thread(target=save_entries) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All entries should be saved
        assert len(results) == len(sample_context_entries) * 3

        # Verify all entries are in database
        with sqlite3.connect(context_provider.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM context_entries")
            count = cursor.fetchone()[0]
            assert count == len(results)

    def test_context_search(self, context_provider, sample_context_entries):
        """Test context search functionality"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Search for password-related queries
        password_context = context_provider.search_context(
            search_term="password", user_id="user1"
        )

        assert len(password_context) == 2
        assert all("password" in entry.query.lower() for entry in password_context)

    def test_context_metrics(self, context_provider, sample_context_entries):
        """Test context metrics calculation"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        metrics = context_provider.get_context_metrics()

        assert "total_queries" in metrics
        assert "total_users" in metrics
        assert "total_sessions" in metrics
        assert "escalation_rate" in metrics
        assert "avg_response_time" in metrics

        assert metrics["total_queries"] == 3
        assert metrics["total_users"] == 2
        assert metrics["total_sessions"] == 2
        assert metrics["escalation_rate"] == 1 / 3  # 1 escalated out of 3

    def test_context_entry_update(self, context_provider, sample_context_entries):
        """Test updating existing context entries"""
        entry = sample_context_entries[0]
        context_provider.save_context_entry(entry)

        # Update entry
        entry.response = "Updated response"
        entry.escalated = True

        context_provider.update_context_entry(entry)

        # Verify update
        retrieved_entries = context_provider.get_context(user_id=entry.user_id)
        updated_entry = next(
            e for e in retrieved_entries if e.query_id == entry.query_id
        )

        assert updated_entry.response == "Updated response"
        assert updated_entry.escalated is True

    def test_context_provider_close(self, context_provider):
        """Test context provider cleanup"""
        # Should not raise exception
        context_provider.close()

        # Should be able to call multiple times
        context_provider.close()

    def test_memory_usage_optimization(self, context_provider):
        """Test memory usage optimization with large datasets"""
        # Create many entries
        entries = []
        for i in range(1000):
            entry = ContextEntry(
                user_id=f"user_{i % 10}",
                session_id=f"session_{i % 100}",
                query_id=f"query_{i}",
                query=f"Query {i}",
                response=f"Response {i}",
                timestamp=datetime.now() - timedelta(minutes=i),
                escalated=i % 10 == 0,
                response_time=1.0 + (i % 5) * 0.1,
                token_count=100 + (i % 50),
            )
            entries.append(entry)

        # Save all entries
        for entry in entries:
            context_provider.save_context_entry(entry)

        # Retrieve with limit should not load everything into memory
        limited_context = context_provider.get_context(user_id="user_1", limit=5)
        assert len(limited_context) == 5

        # Pagination should work
        page1 = context_provider.get_context(user_id="user_1", limit=10, offset=0)
        page2 = context_provider.get_context(user_id="user_1", limit=10, offset=10)

        assert len(page1) == 10
        assert len(page2) > 0
        assert page1[0].query_id != page2[0].query_id

    def test_database_schema_migration(self, temp_db_path):
        """Test database schema migration handling"""
        # Create initial database with old schema
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE context_entries (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    query TEXT,
                    response TEXT
                )
            """)

        # Creating context provider should handle migration
        provider = SQLiteContextProvider(temp_db_path)

        # Should be able to use new schema
        entry = ContextEntry(
            user_id="test_user",
            session_id="test_session",
            query_id="test_query",
            query="Test query",
            response="Test response",
            timestamp=datetime.now(),
            escalated=False,
            response_time=1.0,
            token_count=100,
        )

        # Should not raise exception
        provider.save_context_entry(entry)

    def test_context_export_import(self, context_provider, sample_context_entries):
        """Test context export and import functionality"""
        for entry in sample_context_entries:
            context_provider.save_context_entry(entry)

        # Export context
        exported_data = context_provider.export_context(user_id="user1")

        assert len(exported_data) == 2
        assert all(isinstance(entry, dict) for entry in exported_data)

        # Import context to new provider
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            new_db_path = temp_file.name

        try:
            new_provider = SQLiteContextProvider(new_db_path)
            new_provider.import_context(exported_data)

            # Verify import
            imported_context = new_provider.get_context(user_id="user1")
            assert len(imported_context) == 2

        finally:
            Path(new_db_path).unlink(missing_ok=True)
