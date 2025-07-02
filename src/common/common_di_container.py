"""
Common Dependency Injection Container

This module provides a dependency injection container for common application
dependencies. It uses the dependency_injector library to manage the lifecycle
and dependencies of core application components.
"""

from dependency_injector import containers, providers

# Concrete classes
from src.common.app_file_handling.app_file_handler import LocalAppFileHandler
from src.common.app_logging.app_logger import AppLogger
from src.common.config_management.config_manager import ConfigManager
from src.common.error_handling.error_handler_factory import ErrorHandlerFactory


class CommonDIContainer(containers.Container):
    """
    Container for common application dependencies.

    This container manages the lifecycle and dependencies of core application
    components including file handling, configuration management, logging,
    error handling, data access, and data validation.
    """

    # Core file handling
    app_file_handler: providers.Provider[LocalAppFileHandler] = providers.Singleton(
        LocalAppFileHandler
    )

    # Configuration management
    config: providers.Provider[ConfigManager] = providers.Singleton(
        ConfigManager, app_file_handler=app_file_handler
    )

    # Application logging
    app_logger: providers.Provider[AppLogger] = providers.Singleton(
        AppLogger, config=config
    )

    # Error handling
    error_handler_factory: providers.Provider[ErrorHandlerFactory] = (
        providers.Singleton(ErrorHandlerFactory, app_logger=app_logger)
    )

    # Wire up error handling in file handler after logger is available
    def wire_file_handler_error_handling(self):
        """Wire up error handling in the file handler."""
        file_handler = self.app_file_handler()
        logger = self.app_logger()
        file_handler.set_error_logger(logger)

    # Wire up error handling in config manager after logger is available
    def wire_config_manager_error_handling(self):
        """Wire up error handling in the config manager."""
        config_manager = self.config()
        logger = self.app_logger()
        config_manager.set_error_logger(logger)

    def wire_all_error_handling(self):
        """Wire up error handling in all components that need it."""
        self.wire_file_handler_error_handling()
        self.wire_config_manager_error_handling()
