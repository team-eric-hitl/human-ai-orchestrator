"""
Tests for Common Dependency Injection Container

This module contains tests for the CommonDIContainer class, which manages
dependencies for common application components.
"""

from unittest.mock import Mock

from dependency_injector import containers, providers

from src.common.common_di_container import CommonDIContainer


class TestCommonDIContainer:
    """Test cases for CommonDIContainer."""

    def test_container_initialization(self):
        """Test container initialization."""
        container = CommonDIContainer()
        assert isinstance(container, containers.Container)

    def test_container_providers_are_singletons(self):
        """Test that all providers are configured as singletons."""
        container = CommonDIContainer()

        # Check that providers are singleton providers
        assert isinstance(container.app_file_handler, providers.Singleton)
        assert isinstance(container.config, providers.Singleton)
        assert isinstance(container.app_logger, providers.Singleton)
        assert isinstance(container.error_handler_factory, providers.Singleton)

    def test_app_file_handler_provider(self):
        """Test app_file_handler provider configuration."""
        container = CommonDIContainer()

        # Get the provider
        provider = container.app_file_handler

        # Verify it's configured correctly
        assert isinstance(provider, providers.Singleton)

    def test_config_provider(self):
        """Test config provider configuration."""
        container = CommonDIContainer()

        # Get the provider
        provider = container.config

        # Verify it's configured correctly
        assert isinstance(provider, providers.Singleton)

    def test_app_logger_provider(self):
        """Test app_logger provider configuration."""
        container = CommonDIContainer()

        # Get the provider
        provider = container.app_logger

        # Verify it's configured correctly
        assert isinstance(provider, providers.Singleton)

    def test_error_handler_factory_provider(self):
        """Test error_handler_factory provider configuration."""
        container = CommonDIContainer()

        # Get the provider
        provider = container.error_handler_factory

        # Verify it's configured correctly
        assert isinstance(provider, providers.Singleton)

    def test_wire_file_handler_error_handling(self):
        """Test wiring error handling in file handler."""
        container = CommonDIContainer()

        # Mock the components
        mock_file_handler = Mock()
        mock_logger = Mock()
        container.app_file_handler.override(mock_file_handler)
        container.app_logger.override(mock_logger)

        # Call the wiring method
        container.wire_file_handler_error_handling()

        # Verify the logger was set
        mock_file_handler.set_error_logger.assert_called_once_with(mock_logger)

    def test_wire_config_manager_error_handling(self):
        """Test wiring error handling in config manager."""
        container = CommonDIContainer()

        # Mock the components
        mock_config = Mock()
        mock_logger = Mock()
        container.config.override(mock_config)
        container.app_logger.override(mock_logger)

        # Call the wiring method
        container.wire_config_manager_error_handling()

        # Verify the logger was set
        mock_config.set_error_logger.assert_called_once_with(mock_logger)

    def test_wire_all_error_handling(self):
        """Test wiring error handling in all components."""
        container = CommonDIContainer()

        # Mock the components
        mock_file_handler = Mock()
        mock_config = Mock()
        mock_logger = Mock()
        container.app_file_handler.override(mock_file_handler)
        container.config.override(mock_config)
        container.app_logger.override(mock_logger)

        # Call the wiring method
        container.wire_all_error_handling()

        # Verify both components had their loggers set
        mock_file_handler.set_error_logger.assert_called_once_with(mock_logger)
        mock_config.set_error_logger.assert_called_once_with(mock_logger)


class TestCommonDIContainerIntegration:
    """Integration tests for CommonDIContainer."""

    def test_container_with_real_components(self):
        """Test container with real component instances."""
        # This test would require the actual component classes to be available
        # For now, we'll test the container structure
        container = CommonDIContainer()

        # Verify container structure
        assert hasattr(container, "app_file_handler")
        assert hasattr(container, "config")
        assert hasattr(container, "app_logger")
        assert hasattr(container, "error_handler_factory")

        # Verify provider types
        assert isinstance(container.app_file_handler, providers.Singleton)
        assert isinstance(container.config, providers.Singleton)
        assert isinstance(container.app_logger, providers.Singleton)
        assert isinstance(container.error_handler_factory, providers.Singleton)

    def test_container_error_handling_isolation(self):
        """Test that error handling components are properly isolated."""
        container = CommonDIContainer()

        # Verify that error handling components can be accessed
        # without causing circular dependency issues
        assert container.error_handler_factory is not None

        # Verify that the error handler factory can be configured
        # with a logger without issues
        mock_logger = Mock()
        container.error_handler_factory.override(Mock(app_logger=mock_logger))

    def test_container_provider_dependencies(self):
        """Test that provider dependencies are correctly configured."""
        container = CommonDIContainer()

        # Verify that providers exist and can be accessed
        assert container.app_file_handler is not None
        assert container.config is not None
        assert container.app_logger is not None
        assert container.error_handler_factory is not None

        # Verify that the container can be initialized without errors
        # This tests that all dependencies are properly configured
        assert isinstance(container, containers.Container)
