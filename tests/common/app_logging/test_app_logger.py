"""
Unit tests for AppLogger.

This module contains comprehensive tests for the AppLogger class
which provides structured logging, performance monitoring, and
context management capabilities.
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.common.app_logging.app_logger import AppLogger


class TestAppLogger:
    """Test cases for the AppLogger class."""

    def test_app_logger_initialization(self):
        """Test AppLogger initialization."""
        mock_config = Mock()
        logger = AppLogger(config=mock_config)

        assert logger.logger is None
        assert logger.config == mock_config

    def test_app_logger_initialization_without_config(self):
        """Test AppLogger initialization without config."""
        logger = AppLogger(config=None)

        assert logger.logger is None
        assert logger.config is None

    @patch("logging.getLogger")
    def test_setup_logging(self, mock_get_logger):
        """Test logging setup with file and console handlers."""
        mock_config = Mock()
        mock_config.log_level = logging.DEBUG

        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            result = logger.setup(temp_file_path)

            assert result == mock_logger_instance
            assert logger.logger == mock_logger_instance
            mock_logger_instance.setLevel.assert_called_once_with(logging.DEBUG)
            assert mock_logger_instance.addHandler.call_count == 2
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_setup_logging_with_default_level(self, mock_get_logger):
        """Test logging setup with default log level when config is None."""
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=None)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            result = logger.setup(temp_file_path)

            assert result == mock_logger_instance
            mock_logger_instance.setLevel.assert_called_once_with(logging.INFO)
        finally:
            os.unlink(temp_file_path)

    def test_structured_log_without_setup(self):
        """Test structured_log raises error when logger not initialized."""
        logger = AppLogger(config=None)

        with pytest.raises(RuntimeError) as exc_info:
            logger.structured_log(logging.INFO, "Test message")

        assert "Logger not initialized" in str(exc_info.value)

    @patch("logging.getLogger")
    def test_structured_log_with_context(self, mock_get_logger):
        """Test structured logging with context information."""
        mock_config = Mock()
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            logger.structured_log(
                logging.INFO, "Test message", user_id=123, operation="read"
            )

            mock_logger_instance.log.assert_called_once()
            call_args = mock_logger_instance.log.call_args
            assert call_args[0][0] == logging.INFO
            assert "Test message" in call_args[0][1]
            assert "user_id=123" in call_args[0][1]
            assert "operation=read" in call_args[0][1]
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_log_performance_decorator_success(self, mock_get_logger):
        """Test performance logging decorator with successful execution."""
        mock_config = Mock()
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            @logger.log_performance
            def test_function():
                time.sleep(0.01)  # Small delay to ensure measurable time
                return "success"

            result = test_function()

            assert result == "success"
            mock_logger_instance.log.assert_called_once()
            call_args = mock_logger_instance.log.call_args
            assert "completed" in call_args[0][1]
            assert "success" in call_args[0][1]
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_log_performance_decorator_failure(self, mock_get_logger):
        """Test performance logging decorator with failed execution."""
        mock_config = Mock()
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            @logger.log_performance
            def test_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                test_function()

            mock_logger_instance.log.assert_called_once()
            call_args = mock_logger_instance.log.call_args
            assert "failed" in call_args[0][1]
            assert "error" in call_args[0][1]
            assert "ValueError" in call_args[0][1]
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_log_context_manager(self, mock_get_logger):
        """Test log context manager functionality."""
        mock_config = Mock()
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            with logger.log_context(user_id=123, session_id="abc"):
                logger.structured_log(logging.INFO, "Test message")

            mock_logger_instance.log.assert_called_once()
            call_args = mock_logger_instance.log.call_args
            assert "user_id=123" in call_args[0][1]
            assert "session_id=abc" in call_args[0][1]
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_log_context_manager_nested(self, mock_get_logger):
        """Test nested log context managers."""
        mock_config = Mock()
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            with logger.log_context(user_id=123):
                with logger.log_context(session_id="abc"):
                    logger.structured_log(logging.INFO, "Test message")

            mock_logger_instance.log.assert_called_once()
            call_args = mock_logger_instance.log.call_args
            assert "user_id=123" in call_args[0][1]
            assert "session_id=abc" in call_args[0][1]
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_log_context_manager_exception_handling(self, mock_get_logger):
        """Test log context manager with exception handling."""
        mock_config = Mock()
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            with pytest.raises(ValueError):
                with logger.log_context(user_id=123):
                    logger.structured_log(logging.INFO, "Test message")
                    raise ValueError("Test exception")

            # Context should still be applied even with exception
            mock_logger_instance.log.assert_called_once()
            call_args = mock_logger_instance.log.call_args
            assert "user_id=123" in call_args[0][1]
        finally:
            os.unlink(temp_file_path)


class TestAppLoggerIntegration:
    """Integration tests for AppLogger."""

    @patch("logging.getLogger")
    def test_complete_logging_workflow(self, mock_get_logger):
        """Test complete logging workflow with all features."""
        mock_config = Mock()
        mock_config.log_level = logging.DEBUG
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Setup logging
            logger.setup(temp_file_path)

            # Test structured logging with context
            with logger.log_context(user_id=123, session_id="abc"):
                logger.structured_log(
                    logging.INFO,
                    "Processing request",
                    operation="read",
                    file_path="/test/file.txt",
                )

            # Test performance logging
            @logger.log_performance
            def process_data():
                time.sleep(0.01)
                return "processed"

            result = process_data()

            assert result == "processed"

            # Verify all logging calls
            assert mock_logger_instance.log.call_count >= 2
        finally:
            os.unlink(temp_file_path)

    @patch("logging.getLogger")
    def test_logger_config_integration(self, mock_get_logger):
        """Test logger integration with configuration."""
        mock_config = Mock()
        mock_config.log_level = logging.WARNING
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance

        logger = AppLogger(config=mock_config)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger.setup(temp_file_path)

            # Should use config log level
            mock_logger_instance.setLevel.assert_called_once_with(logging.WARNING)
        finally:
            os.unlink(temp_file_path)
