"""
Comprehensive tests for the configuration management system.
Tests ConfigManager, loaders, validators, and schema validation.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from src.core.config import ConfigManager
from src.core.config.schemas import (
    LoggingConfig,
    ModelConfig,
    ProviderConfig,
    SystemConfig,
)
from src.core.logging.exceptions import ConfigurationError, ValidationError


class TestConfigManager:
    """Test suite for ConfigManager core functionality"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with test config files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create test model config
            models_config = {
                "providers": {
                    "openai": {
                        "api_key_env": "OPENAI_API_KEY",
                        "models": {
                            "gpt-4": {
                                "name": "gpt-4",
                                "type": "openai",
                                "max_tokens": 4000,
                                "temperature": 0.7,
                                "available": True,
                            }
                        },
                    },
                    "local": {
                        "models": {
                            "llama-7b": {
                                "name": "llama-7b",
                                "type": "llama",
                                "model_path": "/models/llama-7b.gguf",
                                "available": False,
                            }
                        }
                    },
                },
                "strategy": "best_available",
            }

            # Create test system config
            system_config = {
                "evaluation": {
                    "complexity_threshold": 0.7,
                    "escalation_threshold": 0.8,
                    "context_window": 5,
                },
                "logging": {
                    "level": "INFO",
                    "environment": "test",
                    "console_enabled": True,
                    "file_enabled": False,
                },
            }

            # Create test prompts
            prompts_config = {
                "answer_agent": {
                    "system_prompt": "You are a helpful assistant.",
                    "user_prompt": "Answer the following question: {query}",
                },
                "evaluator_agent": {"system_prompt": "Evaluate the response quality."},
            }

            # Write config files
            with open(config_dir / "models.json", "w") as f:
                json.dump(models_config, f)
            with open(config_dir / "system_config.json", "w") as f:
                json.dump(system_config, f)
            with open(config_dir / "prompts.yaml", "w") as f:
                yaml.dump(prompts_config, f)

            yield config_dir

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager with test configuration"""
        return ConfigManager(str(temp_config_dir))

    def test_initialization_success(self, config_manager):
        """Test successful ConfigManager initialization"""
        assert config_manager is not None
        assert config_manager.config_dir is not None
        assert config_manager.models is not None
        assert config_manager.system is not None
        assert config_manager.prompts is not None

    def test_initialization_missing_directory(self):
        """Test initialization with missing config directory"""
        with pytest.raises(ConfigurationError, match="Config directory not found"):
            ConfigManager("/nonexistent/path")

    def test_initialization_missing_files(self, temp_config_dir):
        """Test initialization with missing config files"""
        # Remove models.json
        (temp_config_dir / "models.json").unlink()

        with pytest.raises(ConfigurationError, match="Required config file not found"):
            ConfigManager(str(temp_config_dir))

    def test_model_configuration_loading(self, config_manager):
        """Test model configuration loading and validation"""
        assert len(config_manager.models.providers) == 2
        assert "openai" in config_manager.models.providers
        assert "local" in config_manager.models.providers

        openai_provider = config_manager.models.providers["openai"]
        assert "gpt-4" in openai_provider.models
        assert openai_provider.models["gpt-4"].available

        local_provider = config_manager.models.providers["local"]
        assert "llama-7b" in local_provider.models
        assert not local_provider.models["llama-7b"].available

    def test_system_configuration_loading(self, config_manager):
        """Test system configuration loading and validation"""
        assert config_manager.system.evaluation.complexity_threshold == 0.7
        assert config_manager.system.evaluation.escalation_threshold == 0.8
        assert config_manager.system.evaluation.context_window == 5

        assert config_manager.system.logging.level == "INFO"
        assert config_manager.system.logging.environment == "test"

    def test_prompts_configuration_loading(self, config_manager):
        """Test prompts configuration loading"""
        assert "answer_agent" in config_manager.prompts
        assert "evaluator_agent" in config_manager.prompts

        answer_prompts = config_manager.prompts["answer_agent"]
        assert "system_prompt" in answer_prompts
        assert "user_prompt" in answer_prompts

    def test_environment_variable_override(self, config_manager):
        """Test environment variable overrides"""
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4"}):
            provider, model = config_manager.get_active_model()
            assert provider == "openai"
            assert model == "gpt-4"

    def test_get_available_models(self, config_manager):
        """Test retrieval of available models"""
        available = config_manager.get_available_models()
        assert "gpt-4" in available
        assert "llama-7b" not in available  # Not available

    def test_get_primary_model(self, config_manager):
        """Test primary model selection"""
        provider, model = config_manager.get_primary_model()
        assert provider == "openai"
        assert model == "gpt-4"

    def test_model_availability_checking(self, config_manager):
        """Test model availability validation"""
        # Mock file system checks
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            # Should update availability
            config_manager.validate_model_availability()
            local_model = config_manager.models.providers["local"].models["llama-7b"]
            assert local_model.available

    def test_configuration_summary(self, config_manager):
        """Test configuration summary generation"""
        summary = config_manager.get_summary()

        assert "total_models_configured" in summary
        assert "available_models" in summary
        assert "primary_model" in summary
        assert "provider_strategy" in summary
        assert "validation_results" in summary

        assert summary["total_models_configured"] == 2
        assert len(summary["available_models"]) == 1
        assert summary["primary_model"] == "gpt-4"

    def test_invalid_json_handling(self, temp_config_dir):
        """Test handling of invalid JSON files"""
        # Write invalid JSON
        with open(temp_config_dir / "models.json", "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            ConfigManager(str(temp_config_dir))

    def test_invalid_yaml_handling(self, temp_config_dir):
        """Test handling of invalid YAML files"""
        # Write invalid YAML
        with open(temp_config_dir / "prompts.yaml", "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            ConfigManager(str(temp_config_dir))

    def test_schema_validation_errors(self, temp_config_dir):
        """Test schema validation error handling"""
        # Create invalid model config (missing required fields)
        invalid_config = {
            "providers": {
                "openai": {
                    "models": {
                        "gpt-4": {
                            # Missing required 'name' field
                            "type": "openai"
                        }
                    }
                }
            }
        }

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(invalid_config, f)

        with pytest.raises(ValidationError):
            ConfigManager(str(temp_config_dir))

    def test_concurrent_access(self, config_manager):
        """Test thread-safe configuration access"""
        import threading
        import time

        results = []

        def access_config():
            for _ in range(10):
                summary = config_manager.get_summary()
                results.append(summary["primary_model"])
                time.sleep(0.001)

        threads = [threading.Thread(target=access_config) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All results should be consistent
        assert all(result == "gpt-4" for result in results)

    def test_configuration_reloading(self, config_manager, temp_config_dir):
        """Test configuration reloading functionality"""
        # Initial state
        assert config_manager.get_primary_model()[1] == "gpt-4"

        # Modify config file
        updated_config = {
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "models": {
                        "gpt-3.5-turbo": {
                            "name": "gpt-3.5-turbo",
                            "type": "openai",
                            "max_tokens": 4000,
                            "temperature": 0.7,
                            "available": True,
                        }
                    },
                }
            },
            "strategy": "best_available",
        }

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(updated_config, f)

        # Reload configuration
        config_manager.reload()

        # Should reflect changes
        assert config_manager.get_primary_model()[1] == "gpt-3.5-turbo"


class TestConfigurationSchemas:
    """Test suite for configuration schema validation"""

    def test_model_config_validation(self):
        """Test ModelConfig validation"""
        # Valid config
        valid_config = ModelConfig(
            name="gpt-4",
            type="openai",
            max_tokens=4000,
            temperature=0.7,
            available=True,
        )
        assert valid_config.name == "gpt-4"
        assert valid_config.is_available()

        # Invalid temperature
        with pytest.raises(ValidationError):
            ModelConfig(
                name="test",
                type="openai",
                temperature=2.0,  # Invalid range
            )

    def test_logging_config_validation(self):
        """Test LoggingConfig validation"""
        # Valid config
        valid_config = LoggingConfig(
            level="INFO",
            environment="development",
            console_enabled=True,
            file_enabled=True,
        )
        assert valid_config.level == "INFO"
        assert valid_config.is_development()

        # Invalid log level
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID_LEVEL")

    def test_system_config_validation(self):
        """Test SystemConfig validation"""
        # Valid config with all sections
        valid_config = SystemConfig(
            evaluation={
                "complexity_threshold": 0.7,
                "escalation_threshold": 0.8,
                "context_window": 5,
            },
            logging={"level": "INFO", "environment": "development"},
        )
        assert valid_config.evaluation.complexity_threshold == 0.7
        assert valid_config.logging.level == "INFO"

    def test_provider_config_validation(self):
        """Test ProviderConfig validation"""
        # Valid provider config
        valid_config = ProviderConfig(
            api_key_env="OPENAI_API_KEY",
            models={"gpt-4": ModelConfig(name="gpt-4", type="openai", available=True)},
        )
        assert len(valid_config.models) == 1
        assert valid_config.has_available_models()

        # Provider with no available models
        no_available_config = ProviderConfig(
            models={
                "unavailable-model": ModelConfig(
                    name="unavailable-model", type="test", available=False
                )
            }
        )
        assert not no_available_config.has_available_models()


class TestConfigurationLoaders:
    """Test suite for configuration loading utilities"""

    def test_json_loader_success(self):
        """Test successful JSON loading"""
        from src.core.config.loaders import load_json_config

        test_data = {"key": "value", "number": 42}
        json_content = json.dumps(test_data)

        with patch("builtins.open", mock_open(read_data=json_content)):
            result = load_json_config("test.json")
            assert result == test_data

    def test_json_loader_file_not_found(self):
        """Test JSON loader with missing file"""
        from src.core.config.loaders import load_json_config

        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(ConfigurationError, match="Config file not found"):
                load_json_config("missing.json")

    def test_yaml_loader_success(self):
        """Test successful YAML loading"""
        from src.core.config.loaders import load_yaml_config

        test_data = {"key": "value", "list": [1, 2, 3]}
        yaml_content = yaml.dump(test_data)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_yaml_config("test.yaml")
            assert result == test_data

    def test_yaml_loader_invalid_syntax(self):
        """Test YAML loader with invalid syntax"""
        from src.core.config.loaders import load_yaml_config

        invalid_yaml = "key: value\ninvalid: yaml: [unclosed"

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                load_yaml_config("invalid.yaml")


class TestConfigurationValidators:
    """Test suite for configuration validation logic"""

    def test_model_availability_validator(self):
        """Test model availability validation"""
        from src.core.config.validators import validate_model_availability

        model_config = ModelConfig(
            name="test-model",
            type="llama",
            model_path="/path/to/model.gguf",
            available=False,
        )

        # File exists - should be available
        with patch("pathlib.Path.exists", return_value=True):
            result = validate_model_availability(model_config)
            assert result.available

        # File doesn't exist - should not be available
        with patch("pathlib.Path.exists", return_value=False):
            result = validate_model_availability(model_config)
            assert not result.available

    def test_api_key_validator(self):
        """Test API key validation"""
        from src.core.config.validators import validate_api_key

        # Valid API key in environment
        with patch.dict(os.environ, {"TEST_API_KEY": "valid-key"}):
            assert validate_api_key("TEST_API_KEY")

        # Missing API key
        with patch.dict(os.environ, {}, clear=True):
            assert not validate_api_key("MISSING_API_KEY")

    def test_configuration_consistency_validator(self):
        """Test overall configuration consistency"""
        from src.core.config.validators import validate_configuration_consistency

        # Create test configuration
        config = {
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "models": {
                        "gpt-4": {"name": "gpt-4", "type": "openai", "available": True}
                    },
                }
            },
            "strategy": "best_available",
        }

        # Should pass validation
        with patch.dict(os.environ, {"OPENAI_API_KEY": "valid-key"}):
            errors = validate_configuration_consistency(config)
            assert len(errors) == 0

        # Should fail validation (missing API key)
        with patch.dict(os.environ, {}, clear=True):
            errors = validate_configuration_consistency(config)
            assert len(errors) > 0
            assert any("API key" in error for error in errors)
