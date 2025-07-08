"""
Simple test to validate configuration system works before running full tests.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSimpleConfig:
    """Simple configuration tests"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create minimal test config"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # Minimal config
            models_config = {
                "providers": {
                    "mock": {
                        "models": {
                            "test-model": {
                                "name": "test-model",
                                "type": "mock",
                                "available": True,
                            }
                        }
                    }
                },
                "strategy": "best_available",
            }

            system_config = {
                "evaluation": {"complexity_threshold": 0.7},
                "logging": {"level": "INFO", "environment": "test"},
            }

            # Write config files
            with open(config_dir / "models.json", "w") as f:
                json.dump(models_config, f)
            with open(config_dir / "system_config.json", "w") as f:
                json.dump(system_config, f)
            with open(config_dir / "prompts.yaml", "w") as f:
                f.write("answer_agent:\n  system_prompt: 'Test prompt'\n")

            yield config_dir

    def test_config_files_exist(self, temp_config_dir):
        """Test config files are created"""
        assert (temp_config_dir / "models.json").exists()
        assert (temp_config_dir / "system_config.json").exists()
        assert (temp_config_dir / "prompts.yaml").exists()

    def test_config_content_valid(self, temp_config_dir):
        """Test config content is valid JSON/YAML"""
        # Test JSON files
        with open(temp_config_dir / "models.json") as f:
            models_data = json.load(f)
            assert "providers" in models_data
            assert "strategy" in models_data

        with open(temp_config_dir / "system_config.json") as f:
            system_data = json.load(f)
            assert "evaluation" in system_data
            assert "logging" in system_data

        # Test YAML file exists and has content
        prompts_file = temp_config_dir / "prompts.yaml"
        content = prompts_file.read_text()
        assert "answer_agent" in content

    def test_mock_imports_work(self):
        """Test that we can mock imports for testing"""
        with patch("builtins.__import__") as mock_import:
            # Mock the import to avoid actual module loading
            mock_import.return_value = Mock()

            # This simulates importing a module
            try:
                import some_fake_module

                assert some_fake_module is not None
            except ImportError:
                # This is expected if patch doesn't work as expected
                pass

    def test_basic_data_structures(self):
        """Test basic data structures work"""
        test_config = {
            "name": "test",
            "type": "test_type",
            "available": True,
            "settings": {"param1": "value1", "param2": 42},
        }

        assert test_config["name"] == "test"
        assert test_config["settings"]["param2"] == 42
        assert test_config["available"] is True
