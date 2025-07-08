"""
Subset of comprehensive configuration tests that can run without full system imports.
Tests the core configuration logic independently.
"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest


class MockConfigManager:
    """Mock implementation of ConfigManager for testing"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.models_data = self._load_models_config()
        self.system_data = self._load_system_config()
        self.prompts_data = self._load_prompts_config()

    def _load_models_config(self) -> dict[str, Any]:
        """Load models configuration"""
        models_file = self.config_dir / "models.json"
        if not models_file.exists():
            raise FileNotFoundError(f"Models config not found: {models_file}")

        with open(models_file) as f:
            return json.load(f)

    def _load_system_config(self) -> dict[str, Any]:
        """Load system configuration"""
        system_file = self.config_dir / "system_config.json"
        if not system_file.exists():
            raise FileNotFoundError(f"System config not found: {system_file}")

        with open(system_file) as f:
            return json.load(f)

    def _load_prompts_config(self) -> dict[str, Any]:
        """Load prompts configuration"""
        prompts_file = self.config_dir / "prompts.yaml"
        if not prompts_file.exists():
            return {}

        # Simple YAML-like parsing for test
        content = prompts_file.read_text()
        return {"content": content}

    def get_available_models(self) -> list:
        """Get list of available models"""
        available = []
        for provider_name, provider_config in self.models_data.get(
            "providers", {}
        ).items():
            for model_name, model_config in provider_config.get("models", {}).items():
                if model_config.get("available", False):
                    available.append(model_name)
        return available

    def get_primary_model(self) -> tuple:
        """Get primary model (provider, model)"""
        for provider_name, provider_config in self.models_data.get(
            "providers", {}
        ).items():
            for model_name, model_config in provider_config.get("models", {}).items():
                if model_config.get("available", False):
                    return provider_name, model_name
        return None, None

    def get_summary(self) -> dict[str, Any]:
        """Get configuration summary"""
        total_models = 0
        available_models = []

        for provider_config in self.models_data.get("providers", {}).values():
            for model_name, model_config in provider_config.get("models", {}).items():
                total_models += 1
                if model_config.get("available", False):
                    available_models.append(model_name)

        primary_provider, primary_model = self.get_primary_model()

        return {
            "total_models_configured": total_models,
            "available_models": available_models,
            "primary_model": primary_model,
            "provider_strategy": self.models_data.get("strategy", "unknown"),
        }


class TestConfigurationManagement:
    """Test configuration management without external dependencies"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create comprehensive test configuration
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
                            },
                            "gpt-3.5-turbo": {
                                "name": "gpt-3.5-turbo",
                                "type": "openai",
                                "max_tokens": 4000,
                                "temperature": 0.7,
                                "available": True,
                            },
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

            prompts_config = """
answer_agent:
  system_prompt: "You are a helpful assistant."
  user_prompt: "Answer the following question: {query}"
evaluator_agent:
  system_prompt: "Evaluate the response quality."
"""

            # Write config files
            with open(config_dir / "models.json", "w") as f:
                json.dump(models_config, f, indent=2)
            with open(config_dir / "system_config.json", "w") as f:
                json.dump(system_config, f, indent=2)
            with open(config_dir / "prompts.yaml", "w") as f:
                f.write(prompts_config)

            yield config_dir

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create MockConfigManager instance"""
        return MockConfigManager(str(temp_config_dir))

    def test_config_manager_initialization(self, config_manager):
        """Test MockConfigManager initialization"""
        assert config_manager is not None
        assert config_manager.config_dir is not None
        assert config_manager.models_data is not None
        assert config_manager.system_data is not None

    def test_models_configuration_loading(self, config_manager):
        """Test models configuration loading"""
        models_data = config_manager.models_data

        assert "providers" in models_data
        assert len(models_data["providers"]) == 2
        assert "openai" in models_data["providers"]
        assert "local" in models_data["providers"]

        openai_provider = models_data["providers"]["openai"]
        assert "gpt-4" in openai_provider["models"]
        assert "gpt-3.5-turbo" in openai_provider["models"]

        gpt4_model = openai_provider["models"]["gpt-4"]
        assert gpt4_model["name"] == "gpt-4"
        assert gpt4_model["type"] == "openai"
        assert gpt4_model["available"] is True

    def test_system_configuration_loading(self, config_manager):
        """Test system configuration loading"""
        system_data = config_manager.system_data

        assert "evaluation" in system_data
        assert "logging" in system_data

        evaluation_config = system_data["evaluation"]
        assert evaluation_config["complexity_threshold"] == 0.7
        assert evaluation_config["escalation_threshold"] == 0.8
        assert evaluation_config["context_window"] == 5

        logging_config = system_data["logging"]
        assert logging_config["level"] == "INFO"
        assert logging_config["environment"] == "test"
        assert logging_config["console_enabled"] is True
        assert logging_config["file_enabled"] is False

    def test_get_available_models(self, config_manager):
        """Test getting available models"""
        available = config_manager.get_available_models()

        assert "gpt-4" in available
        assert "gpt-3.5-turbo" in available
        assert "llama-7b" not in available  # Not available
        assert len(available) == 2

    def test_get_primary_model(self, config_manager):
        """Test getting primary model"""
        provider, model = config_manager.get_primary_model()

        assert provider == "openai"
        assert model in ["gpt-4", "gpt-3.5-turbo"]  # Either is valid

    def test_configuration_summary(self, config_manager):
        """Test configuration summary generation"""
        summary = config_manager.get_summary()

        assert "total_models_configured" in summary
        assert "available_models" in summary
        assert "primary_model" in summary
        assert "provider_strategy" in summary

        assert summary["total_models_configured"] == 3
        assert len(summary["available_models"]) == 2
        assert summary["primary_model"] in ["gpt-4", "gpt-3.5-turbo"]
        assert summary["provider_strategy"] == "best_available"

    def test_missing_config_files(self, temp_config_dir):
        """Test handling of missing configuration files"""
        # Remove models.json
        (temp_config_dir / "models.json").unlink()

        with pytest.raises(FileNotFoundError):
            MockConfigManager(str(temp_config_dir))

    def test_invalid_json_config(self, temp_config_dir):
        """Test handling of invalid JSON configuration"""
        # Write invalid JSON
        with open(temp_config_dir / "models.json", "w") as f:
            f.write("{ invalid json content }")

        with pytest.raises(json.JSONDecodeError):
            MockConfigManager(str(temp_config_dir))

    def test_configuration_with_no_available_models(self, temp_config_dir):
        """Test configuration where no models are available"""
        # Create config with no available models
        models_config = {
            "providers": {
                "test": {
                    "models": {
                        "unavailable-model": {
                            "name": "unavailable-model",
                            "type": "test",
                            "available": False,
                        }
                    }
                }
            },
            "strategy": "best_available",
        }

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(models_config, f)

        config_manager = MockConfigManager(str(temp_config_dir))

        available = config_manager.get_available_models()
        assert len(available) == 0

        provider, model = config_manager.get_primary_model()
        assert provider is None
        assert model is None

    def test_configuration_validation_logic(self, config_manager):
        """Test configuration validation logic"""
        models_data = config_manager.models_data

        # Validate required fields are present
        assert "providers" in models_data
        assert "strategy" in models_data

        # Validate provider structure
        for provider_name, provider_config in models_data["providers"].items():
            assert isinstance(provider_name, str)
            assert "models" in provider_config

            # Validate model structure
            for model_name, model_config in provider_config["models"].items():
                assert isinstance(model_name, str)
                assert "name" in model_config
                assert "type" in model_config
                assert "available" in model_config
                assert isinstance(model_config["available"], bool)

    def test_prompts_configuration_loading(self, config_manager):
        """Test prompts configuration loading"""
        prompts_data = config_manager.prompts_data

        assert prompts_data is not None
        assert "content" in prompts_data

        content = prompts_data["content"]
        assert "answer_agent" in content
        assert "evaluator_agent" in content
        assert "system_prompt" in content


class TestConfigurationEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory for edge case tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Create basic system config for edge case tests
            system_config = {
                "evaluation": {"complexity_threshold": 0.7},
                "logging": {"level": "INFO", "environment": "test"},
            }

            with open(config_dir / "system_config.json", "w") as f:
                json.dump(system_config, f)
            with open(config_dir / "prompts.yaml", "w") as f:
                f.write("answer_agent:\n  system_prompt: 'Test'\n")

            yield config_dir

    def test_empty_configuration_directory(self):
        """Test with empty configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileNotFoundError):
                MockConfigManager(temp_dir)

    def test_configuration_with_empty_providers(self, temp_config_dir):
        """Test configuration with empty providers"""
        models_config = {"providers": {}, "strategy": "best_available"}

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(models_config, f)

        config_manager = MockConfigManager(str(temp_config_dir))

        available = config_manager.get_available_models()
        assert len(available) == 0

        summary = config_manager.get_summary()
        assert summary["total_models_configured"] == 0
        assert len(summary["available_models"]) == 0

    def test_configuration_field_validation(self, temp_config_dir):
        """Test configuration field validation"""
        # Test with missing required fields
        invalid_models_config = {
            "providers": {
                "test": {
                    "models": {
                        "invalid-model": {
                            # Missing required fields
                            "name": "invalid-model"
                            # Missing "type" and "available"
                        }
                    }
                }
            }
        }

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(invalid_models_config, f)

        config_manager = MockConfigManager(str(temp_config_dir))

        # Should handle missing fields gracefully
        models_data = config_manager.models_data
        invalid_model = models_data["providers"]["test"]["models"]["invalid-model"]

        assert invalid_model["name"] == "invalid-model"
        # Missing fields should be handled by the application logic
        assert invalid_model.get("type") is None
        assert invalid_model.get("available") is None

    def test_large_configuration_performance(self, temp_config_dir):
        """Test performance with large configuration"""
        # Create large configuration
        large_models_config = {"providers": {}, "strategy": "best_available"}

        # Add many providers and models
        for i in range(10):
            provider_name = f"provider_{i}"
            large_models_config["providers"][provider_name] = {"models": {}}

            for j in range(20):
                model_name = f"model_{i}_{j}"
                large_models_config["providers"][provider_name]["models"][
                    model_name
                ] = {
                    "name": model_name,
                    "type": f"type_{i}",
                    "available": j % 2 == 0,  # Half available
                }

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(large_models_config, f)

        # Should handle large config efficiently
        config_manager = MockConfigManager(str(temp_config_dir))

        summary = config_manager.get_summary()
        assert summary["total_models_configured"] == 200  # 10 providers * 20 models
        assert len(summary["available_models"]) == 100  # Half available

        # Should still be fast
        available = config_manager.get_available_models()
        assert len(available) == 100

    def test_configuration_modification_during_runtime(self, temp_config_dir):
        """Test behavior when configuration is modified during runtime"""
        # Create initial models config
        initial_models_config = {
            "providers": {
                "test": {
                    "models": {
                        "model1": {"name": "model1", "type": "test", "available": True}
                    }
                }
            },
            "strategy": "best_available",
        }

        with open(temp_config_dir / "models.json", "w") as f:
            json.dump(initial_models_config, f)

        # Initial configuration
        config_manager = MockConfigManager(str(temp_config_dir))
        initial_summary = config_manager.get_summary()

        # Modify configuration file
        models_file = temp_config_dir / "models.json"
        with open(models_file) as f:
            models_data = json.load(f)

        # Add a new model
        models_data["providers"]["test"]["models"]["model2"] = {
            "name": "model2",
            "type": "test",
            "available": True,
        }

        with open(models_file, "w") as f:
            json.dump(models_data, f)

        # Create new config manager (simulating reload)
        new_config_manager = MockConfigManager(str(temp_config_dir))
        new_summary = new_config_manager.get_summary()

        # Should reflect changes
        assert (
            new_summary["total_models_configured"]
            > initial_summary["total_models_configured"]
        )
        assert "model2" in new_config_manager.get_available_models()
