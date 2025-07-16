"""
Database configuration provider for centralized database management
"""

import os
from pathlib import Path
from typing import Optional

from .logging import get_logger


class DatabaseConfig:
    """Centralized database configuration management"""
    
    def __init__(self, config_manager=None):
        """
        Initialize database configuration
        
        Args:
            config_manager: Configuration manager instance for loading settings
        """
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self._ensure_data_directory()
    
    def get_db_path(self, db_name: Optional[str] = None) -> str:
        """
        Get full database path with centralized storage directory
        
        Args:
            db_name: Optional database name override
            
        Returns:
            Full path to database file
        """
        try:
            if self.config_manager:
                config = self.config_manager.get_config()
                storage_dir = getattr(config.providers.context, 'storage_directory', 'data')
                default_db_name = getattr(config.providers.context, 'db_name', 'hybrid_system.db')
            else:
                # Fallback configuration
                storage_dir = 'data'
                default_db_name = 'hybrid_system.db'
            
            db_name = db_name or default_db_name
            
            # Handle special case for in-memory databases
            if db_name == ':memory:':
                return ':memory:'
            
            # Ensure storage directory exists
            storage_path = Path(storage_dir)
            storage_path.mkdir(parents=True, exist_ok=True)
            
            db_path = storage_path / db_name
            
            self.logger.debug(
                "Database path resolved",
                extra={
                    "storage_directory": storage_dir,
                    "db_name": db_name,
                    "full_path": str(db_path),
                    "operation": "get_db_path"
                }
            )
            
            return str(db_path)
            
        except Exception as e:
            self.logger.error(
                "Failed to resolve database path",
                extra={
                    "db_name": db_name,
                    "error": str(e),
                    "operation": "get_db_path"
                }
            )
            # Fallback to simple path
            return db_name or "hybrid_system.db"
    
    def get_backup_path(self, db_name: Optional[str] = None) -> str:
        """
        Get backup directory path for database
        
        Args:
            db_name: Optional database name
            
        Returns:
            Full path to backup directory
        """
        try:
            if self.config_manager:
                config = self.config_manager.get_config()
                storage_dir = getattr(config.providers.context, 'storage_directory', 'data')
            else:
                storage_dir = 'data'
            
            backup_dir = Path(storage_dir) / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            return str(backup_dir)
            
        except Exception as e:
            self.logger.error(
                "Failed to resolve backup path",
                extra={
                    "db_name": db_name,
                    "error": str(e),
                    "operation": "get_backup_path"
                }
            )
            return "data/backups"
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        try:
            if self.config_manager:
                config = self.config_manager.get_config()
                storage_dir = getattr(config.providers.context, 'storage_directory', 'data')
            else:
                storage_dir = 'data'
            
            Path(storage_dir).mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            self.logger.warning(
                "Failed to ensure data directory",
                extra={
                    "error": str(e),
                    "operation": "_ensure_data_directory"
                }
            )
    
    def migrate_database(self, old_path: str, new_path: Optional[str] = None) -> bool:
        """
        Migrate database from old location to new centralized location
        
        Args:
            old_path: Current database file path
            new_path: Optional new path (if None, uses configured path)
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            old_db = Path(old_path)
            if not old_db.exists():
                self.logger.warning(
                    "Database file not found for migration",
                    extra={
                        "old_path": old_path,
                        "operation": "migrate_database"
                    }
                )
                return False
            
            if new_path is None:
                new_path = self.get_db_path(old_db.name)
            
            new_db = Path(new_path)
            
            # Don't migrate if paths are the same
            if old_db.resolve() == new_db.resolve():
                self.logger.info(
                    "Database already in correct location",
                    extra={
                        "path": str(old_db),
                        "operation": "migrate_database"
                    }
                )
                return True
            
            # Ensure target directory exists
            new_db.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the database file
            import shutil
            shutil.copy2(old_db, new_db)
            
            self.logger.info(
                "Database migrated successfully",
                extra={
                    "old_path": old_path,
                    "new_path": new_path,
                    "operation": "migrate_database"
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to migrate database",
                extra={
                    "old_path": old_path,
                    "new_path": new_path,
                    "error": str(e),
                    "operation": "migrate_database"
                }
            )
            return False
    
    def cleanup_old_databases(self, old_paths: list[str], keep_backups: bool = True) -> bool:
        """
        Clean up old database files after migration
        
        Args:
            old_paths: List of old database file paths to clean up
            keep_backups: Whether to keep backup copies
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            backup_dir = None
            if keep_backups:
                backup_dir = Path(self.get_backup_path()) / 'migration_backups'
                backup_dir.mkdir(parents=True, exist_ok=True)
            
            for old_path in old_paths:
                old_db = Path(old_path)
                if not old_db.exists():
                    continue
                
                if keep_backups:
                    backup_path = backup_dir / old_db.name
                    import shutil
                    shutil.copy2(old_db, backup_path)
                    self.logger.info(
                        "Database backed up before cleanup",
                        extra={
                            "original_path": old_path,
                            "backup_path": str(backup_path),
                            "operation": "cleanup_old_databases"
                        }
                    )
                
                old_db.unlink()
                self.logger.info(
                    "Old database file removed",
                    extra={
                        "path": old_path,
                        "operation": "cleanup_old_databases"
                    }
                )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to cleanup old databases",
                extra={
                    "old_paths": old_paths,
                    "error": str(e),
                    "operation": "cleanup_old_databases"
                }
            )
            return False