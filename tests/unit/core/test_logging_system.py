"""
Comprehensive tests for the logging and error handling system.
Tests AppLogger, error handlers, formatters, and custom exceptions.
"""

import json
import logging
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.logging import (
    AppErrorHandler,
    AppLogger,
    get_logger,
    setup_development_logging,
    setup_production_logging,
)
from src.core.logging.exceptions import (
    ConfigurationError,
    EscalationError,
    ModelError,
    ValidationError,
)
from src.core.logging.formatters import (
    ConsoleFormatter,
    JSONFormatter,
    StructuredFormatter,
)
from src.core.logging.handlers import FileHandler, LangSmithHandler, MetricsHandler


class TestAppLogger:
    """Test suite for the AppLogger class"""

    @pytest.fixture
    def logger(self):
        """Create a test logger instance"""
        return AppLogger("test_module")

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for log files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_logger_initialization(self, logger):
        """Test logger initialization"""
        assert logger.name == "test_module"
        assert logger.logger is not None
        assert logger.context == {}

    def test_basic_logging_levels(self, logger):
        """Test all logging levels work correctly"""
        with (
            patch.object(logger.logger, "debug") as mock_debug,
            patch.object(logger.logger, "info") as mock_info,
            patch.object(logger.logger, "warning") as mock_warning,
            patch.object(logger.logger, "error") as mock_error,
            patch.object(logger.logger, "critical") as mock_critical,
        ):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            mock_debug.assert_called_once()
            mock_info.assert_called_once()
            mock_warning.assert_called_once()
            mock_error.assert_called_once()
            mock_critical.assert_called_once()

    def test_context_management(self, logger):
        """Test context setting and persistence"""
        # Set context
        logger.set_context(user_id="test_user", session_id="test_session")

        assert logger.context["user_id"] == "test_user"
        assert logger.context["session_id"] == "test_session"

        # Update context
        logger.update_context(operation="test_operation")
        assert logger.context["operation"] == "test_operation"

        # Clear context
        logger.clear_context()
        assert logger.context == {}

    def test_user_interaction_logging(self, logger):
        """Test user interaction logging"""
        with patch.object(logger.logger, "info") as mock_info:
            logger.user_interaction(
                user_id="user123",
                query="How do I reset my password?",
                response_type="ai_handled",
                escalated=False,
            )

            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "user_interaction" in str(call_args)

    def test_model_call_logging(self, logger):
        """Test model call logging"""
        with patch.object(logger.logger, "info") as mock_info:
            logger.model_call(
                model_name="gpt-4",
                operation="generate_response",
                duration=1.23,
                token_count=150,
                cost=0.002,
            )

            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "model_call" in str(call_args)

    def test_performance_metric_logging(self, logger):
        """Test performance metric logging"""
        with patch.object(logger.logger, "info") as mock_info:
            logger.performance_metric("query_processing", 2.45)

            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "performance_metric" in str(call_args)

    def test_error_logging_with_context(self, logger):
        """Test error logging with context preservation"""
        logger.set_context(user_id="test_user", session_id="test_session")

        with patch.object(logger.logger, "error") as mock_error:
            logger.error("Test error message", extra={"error_code": "E001"})

            mock_error.assert_called_once()
            call_args = mock_error.call_args
            # Context should be included in the log
            assert "user_id" in str(call_args) or "test_user" in str(call_args)

    def test_thread_safety(self, logger):
        """Test thread-safe logging operations"""
        results = []

        def log_messages():
            for i in range(100):
                logger.info(f"Message {i}")
                logger.set_context(thread_id=threading.current_thread().ident)
                results.append(logger.context.get("thread_id"))

        threads = [threading.Thread(target=log_messages) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Each thread should have set its own context
        assert len(set(results)) > 1  # Multiple different thread IDs


class TestAppErrorHandler:
    """Test suite for the AppErrorHandler class"""

    @pytest.fixture
    def error_handler(self):
        """Create error handler instance"""
        return AppErrorHandler()

    def test_error_handler_initialization(self, error_handler):
        """Test error handler initialization"""
        assert error_handler.errors == []
        assert error_handler.logger is not None

    def test_model_error_handling(self, error_handler):
        """Test handling of ModelError exceptions"""
        error = ModelError(
            message="Model failed to generate response",
            model_name="gpt-4",
            operation="generate_response",
        )

        with patch.object(error_handler.logger, "error") as mock_error:
            result = error_handler.handle_error(error)

            assert result["error_type"] == "ModelError"
            assert result["model_name"] == "gpt-4"
            assert result["operation"] == "generate_response"
            assert "error_id" in result
            assert "timestamp" in result

            mock_error.assert_called_once()

    def test_configuration_error_handling(self, error_handler):
        """Test handling of ConfigurationError exceptions"""
        error = ConfigurationError(
            message="Invalid configuration file",
            config_file="models.json",
            field="invalid_field",
        )

        result = error_handler.handle_error(error)

        assert result["error_type"] == "ConfigurationError"
        assert result["config_file"] == "models.json"
        assert result["field"] == "invalid_field"
        assert len(error_handler.errors) == 1

    def test_validation_error_handling(self, error_handler):
        """Test handling of ValidationError exceptions"""
        error = ValidationError(
            message="Invalid field value",
            field="temperature",
            value="invalid",
            expected_type="float",
        )

        result = error_handler.handle_error(error)

        assert result["error_type"] == "ValidationError"
        assert result["field"] == "temperature"
        assert result["value"] == "invalid"
        assert result["expected_type"] == "float"

    def test_escalation_error_handling(self, error_handler):
        """Test handling of EscalationError exceptions"""
        error = EscalationError(
            message="Human agent not available",
            escalation_reason="complex_query",
            user_id="user123",
        )

        result = error_handler.handle_error(error)

        assert result["error_type"] == "EscalationError"
        assert result["escalation_reason"] == "complex_query"
        assert result["user_id"] == "user123"

    def test_generic_error_handling(self, error_handler):
        """Test handling of generic exceptions"""
        error = ValueError("Generic error message")

        result = error_handler.handle_error(error, context={"operation": "test"})

        assert result["error_type"] == "ValueError"
        assert result["message"] == "Generic error message"
        assert result["context"]["operation"] == "test"

    def test_error_recovery_strategies(self, error_handler):
        """Test error recovery strategy suggestions"""
        # Model error should suggest fallback
        model_error = ModelError("Model timeout", model_name="gpt-4")
        result = error_handler.handle_error(model_error)

        assert "recovery_strategy" in result
        assert "fallback" in result["recovery_strategy"]

        # Configuration error should suggest fix
        config_error = ConfigurationError("Missing API key", config_file="config.json")
        result = error_handler.handle_error(config_error)

        assert "recovery_strategy" in result
        assert "configuration" in result["recovery_strategy"]

    def test_error_statistics(self, error_handler):
        """Test error statistics collection"""
        # Generate various errors
        errors = [
            ModelError("Model error 1", model_name="gpt-4"),
            ModelError("Model error 2", model_name="gpt-3.5"),
            ConfigurationError("Config error", config_file="test.json"),
            ValidationError("Validation error", field="test"),
            ValueError("Generic error"),
        ]

        for error in errors:
            error_handler.handle_error(error)

        stats = error_handler.get_error_statistics()

        assert stats["total_errors"] == 5
        assert stats["by_category"]["ModelError"] == 2
        assert stats["by_category"]["ConfigurationError"] == 1
        assert stats["by_category"]["ValidationError"] == 1
        assert stats["by_category"]["ValueError"] == 1

        # Check severity distribution
        assert "by_severity" in stats
        assert stats["by_severity"]["high"] >= 2  # Model errors are high severity

    def test_error_rate_tracking(self, error_handler):
        """Test error rate tracking over time"""
        # Generate errors over time
        for i in range(10):
            error_handler.handle_error(ValueError(f"Error {i}"))
            if i % 3 == 0:
                time.sleep(0.1)  # Simulate time passing

        stats = error_handler.get_error_statistics()

        assert "error_rate" in stats
        assert stats["error_rate"]["last_minute"] >= 0
        assert stats["error_rate"]["last_hour"] >= 0

    def test_context_preservation_in_errors(self, error_handler):
        """Test that context is preserved when handling errors"""
        context = {
            "user_id": "test_user",
            "session_id": "test_session",
            "operation": "query_processing",
        }

        error = ModelError("Test error", model_name="gpt-4")
        result = error_handler.handle_error(error, context=context)

        assert result["context"]["user_id"] == "test_user"
        assert result["context"]["session_id"] == "test_session"
        assert result["context"]["operation"] == "query_processing"


class TestCustomExceptions:
    """Test suite for custom exception classes"""

    def test_model_error_creation(self):
        """Test ModelError exception creation"""
        error = ModelError(
            message="Model generation failed",
            model_name="gpt-4",
            operation="generate_response",
            token_count=150,
        )

        assert str(error) == "Model generation failed"
        assert error.model_name == "gpt-4"
        assert error.operation == "generate_response"
        assert error.token_count == 150
        assert error.severity == "high"

    def test_configuration_error_creation(self):
        """Test ConfigurationError exception creation"""
        error = ConfigurationError(
            message="Invalid configuration",
            config_file="models.json",
            field="invalid_field",
        )

        assert str(error) == "Invalid configuration"
        assert error.config_file == "models.json"
        assert error.field == "invalid_field"
        assert error.severity == "medium"

    def test_validation_error_creation(self):
        """Test ValidationError exception creation"""
        error = ValidationError(
            message="Invalid value",
            field="temperature",
            value="invalid",
            expected_type="float",
        )

        assert str(error) == "Invalid value"
        assert error.field == "temperature"
        assert error.value == "invalid"
        assert error.expected_type == "float"

    def test_escalation_error_creation(self):
        """Test EscalationError exception creation"""
        error = EscalationError(
            message="Escalation failed",
            escalation_reason="complex_query",
            user_id="user123",
        )

        assert str(error) == "Escalation failed"
        assert error.escalation_reason == "complex_query"
        assert error.user_id == "user123"

    def test_error_serialization(self):
        """Test error serialization for logging"""
        error = ModelError(message="Test error", model_name="gpt-4", operation="test")

        serialized = error.to_dict()

        assert serialized["message"] == "Test error"
        assert serialized["model_name"] == "gpt-4"
        assert serialized["operation"] == "test"
        assert serialized["severity"] == "high"
        assert "error_type" in serialized


class TestLogFormatters:
    """Test suite for log formatters"""

    def test_structured_formatter(self):
        """Test StructuredFormatter"""
        formatter = StructuredFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add context
        record.user_id = "test_user"
        record.session_id = "test_session"

        formatted = formatter.format(record)

        assert "test_logger" in formatted
        assert "Test message" in formatted
        assert "user_id" in formatted
        assert "session_id" in formatted

    def test_console_formatter(self):
        """Test ConsoleFormatter with colors"""
        formatter = ConsoleFormatter()

        # Test different log levels
        info_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Info message",
            args=(),
            exc_info=None,
        )

        error_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        info_formatted = formatter.format(info_record)
        error_formatted = formatter.format(error_record)

        assert "Info message" in info_formatted
        assert "Error message" in error_formatted
        # Colors should be applied (ANSI codes)
        assert "\033[" in info_formatted or "\033[" in error_formatted

    def test_json_formatter(self):
        """Test JSONFormatter"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["name"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed


class TestLogHandlers:
    """Test suite for custom log handlers"""

    def test_file_handler(self, temp_log_dir):
        """Test custom FileHandler"""
        log_file = temp_log_dir / "test.log"

        handler = FileHandler(str(log_file))

        # Create and emit a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        handler.close()

        # Check file was created and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_langsmith_handler(self):
        """Test LangSmithHandler"""
        mock_client = Mock()
        handler = LangSmithHandler(client=mock_client)

        # Create log record with structured data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Model call",
            args=(),
            exc_info=None,
        )
        record.event_type = "model_call"
        record.model_name = "gpt-4"
        record.duration = 1.23

        handler.emit(record)

        # Should have called the LangSmith client
        mock_client.create_run.assert_called_once()

    def test_metrics_handler(self):
        """Test MetricsHandler"""
        handler = MetricsHandler()

        # Create performance metric record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Performance metric",
            args=(),
            exc_info=None,
        )
        record.event_type = "performance_metric"
        record.metric_name = "query_processing"
        record.value = 2.45

        handler.emit(record)

        # Should have stored the metric
        assert len(handler.metrics) == 1
        assert handler.metrics[0]["metric_name"] == "query_processing"
        assert handler.metrics[0]["value"] == 2.45


class TestLoggingSetup:
    """Test suite for logging setup functions"""

    def test_development_logging_setup(self):
        """Test development logging configuration"""
        with patch("src.core.logging.get_logger") as mock_get_logger:
            setup_development_logging()

            # Should configure console and file logging
            mock_get_logger.assert_called()

    def test_production_logging_setup(self):
        """Test production logging configuration"""
        with patch("src.core.logging.get_logger") as mock_get_logger:
            setup_production_logging()

            # Should configure structured logging
            mock_get_logger.assert_called()

    def test_logging_configuration_from_config(self):
        """Test logging configuration from ConfigManager"""
        from src.core.config.schemas import LoggingConfig

        config = LoggingConfig(
            level="DEBUG",
            environment="development",
            console_enabled=True,
            file_enabled=True,
            langsmith_enabled=False,
        )

        with patch("src.core.logging.configure_logging") as mock_configure:
            from src.core.logging import setup_logging_from_config

            setup_logging_from_config(config)

            mock_configure.assert_called_once()


class TestIntegrationWithSystem:
    """Test integration of logging system with other components"""

    def test_config_manager_logging_integration(self):
        """Test that ConfigManager uses logging correctly"""
        with patch("src.core.config.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # This would normally create a ConfigManager and trigger logging
            # The actual test would depend on the specific implementation
            # For now, just verify the logger is obtained

            # Verify logging is integrated
            assert mock_get_logger.called

    def test_error_recovery_integration(self):
        """Test error recovery integration with logging"""
        error_handler = AppErrorHandler()

        # Simulate a model error with recovery
        model_error = ModelError("Model timeout", model_name="gpt-4")

        with patch.object(error_handler, "_attempt_recovery") as mock_recovery:
            mock_recovery.return_value = True

            result = error_handler.handle_error(model_error)

            assert result["recovery_attempted"] is True
            mock_recovery.assert_called_once()

    def test_context_propagation_across_system(self):
        """Test that context propagates correctly across system components"""
        logger = get_logger("test_system")

        # Set initial context
        logger.set_context(user_id="test_user", session_id="test_session")

        # Simulate passing through different components
        with patch.object(logger, "info") as mock_info:
            # Each component should include context
            logger.info("Component A processing")
            logger.info("Component B processing")
            logger.info("Component C processing")

            # All calls should include context
            assert mock_info.call_count == 3
            for call in mock_info.call_args_list:
                # Context should be preserved in each call
                assert any("user_id" in str(arg) for arg in call[0]) or any(
                    "test_user" in str(arg) for arg in call[0]
                )
