# Base Interfaces - Common Module

This module contains all abstract base classes and interfaces for the application. These classes define the contracts that concrete implementations must follow.

## Overview

The base interfaces are organized in a dedicated package structure to provide:
- **Clear separation** between interfaces and implementations
- **Centralized documentation** of all available contracts
- **Easy discovery** for AI assistants and developers
- **Consistent dependency direction** (implementations depend on base interfaces)
- **Scalable organization** for future interface categories

## Package Structure

```
src/
├── base_interfaces/
│   ├── common/           # ← This module
│   │   ├── base_app_logger.py
│   │   ├── base_config_manager.py
│   │   ├── base_error_handler.py
│   │   └── base_app_file_handler.py
│   ├── model_testing/    # Future expansion
│   └── data_processing/  # Future expansion
└── common/               # Concrete implementations
    ├── app_logging/
    ├── config_management/
    ├── error_handling/
    └── app_file_handling/
```

## Available Base Classes

### BaseAppLogger
**Location**: `base_app_logger.py`

Defines the logging interface for the application.

**Key Methods**:
- `__init__(config: BaseConfigManager) -> None`: Initialize logger with configuration
- `setup(log_file: str) -> logging.Logger`: Configure logging with file and console handlers
- `structured_log(level: int, message: str, **kwargs) -> None`: Log structured messages with context
- `log_performance(func: Callable) -> Callable`: Performance logging decorator
- `log_context(**kwargs) -> contextlib.AbstractContextManager`: Context manager for logging

### BaseConfigManager
**Location**: `base_config_manager.py`

Defines the configuration management interface.

**Key Methods**:
- `__init__(config_dir: Optional[Path], app_file_handler: Optional[Any]) -> None`: Initialize with config directory and file handler
- `get_config() -> SimpleNamespace`: Get complete configuration object
- `_load_configurations() -> None`: Load all configuration files
- `_load_nested_configurations() -> Dict[str, Any]`: Load nested configurations
- `_merge_configurations(main_config, nested_configs) -> Dict[str, Any]`: Merge configurations
- `_deep_merge(dict1, dict2) -> Dict[str, Any]`: Recursively merge dictionaries
- `_dict_to_namespace(d) -> Any`: Convert dict to SimpleNamespace

### BaseErrorHandler
**Location**: `base_error_handler.py`

Defines the error handling interface (inherits from Exception).

**Key Methods**:
- `__init__(message: str, app_logger: Optional[BaseAppLogger], log_level: int, **kwargs) -> None`: Initialize error handler
- `log() -> None`: Log error with specified level and context

### BaseAppFileHandler
**Location**: `base_app_file_handler.py`

Defines the file handling interface for various file types.

**Key Methods**:
- `read_yaml(path) -> Dict[str, Any]`, `write_yaml(data, path) -> None`: YAML file operations
- `read_json(path) -> Dict[str, Any]`, `write_json(data, path) -> None`: JSON file operations
- `read_csv(path) -> pd.DataFrame`, `write_csv(df, path) -> None`: CSV file operations
- `ensure_directory(path) -> None`: Directory management
- `join_paths(*paths) -> Path`: Path manipulation
- `resolve_project_root_path(path: str) -> str`: Path resolution
- `load_yaml_files_in_directory(directory, required_files) -> Dict[str, Any]`: Batch YAML loading
- `create_temp_directory() -> ContextManager[str]`: Temporary directory management
- `save_figure(fig, path) -> None`: Matplotlib figure saving

## Usage

To use these base classes in your implementations:

```python
from src.base_interfaces.common import BaseAppLogger, BaseConfigManager

class MyLogger(BaseAppLogger):
    def __init__(self, config: BaseConfigManager) -> None:
        # Implementation here
        pass
    
    def setup(self, log_file: str) -> logging.Logger:
        # Implementation here
        pass
    
    # Implement other abstract methods...
```

## Benefits for AI Assistants

This centralized structure allows AI assistants to:
1. **Quickly understand** all available interfaces
2. **Generate consistent implementations** following established patterns
3. **Maintain type safety** with proper inheritance
4. **Discover dependencies** between different components
5. **Provide better suggestions** based on interface contracts
6. **Scale with new interface categories** as the project grows


