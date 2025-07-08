"""
Basic test to validate the testing framework is working.
This tests the test infrastructure itself before running comprehensive tests.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


def test_pytest_is_working():
    """Basic test to verify pytest is working"""
    assert True


def test_mocking_works():
    """Test that unittest.mock works"""
    mock_obj = Mock()
    mock_obj.test_method.return_value = "test_result"

    result = mock_obj.test_method()
    assert result == "test_result"
    mock_obj.test_method.assert_called_once()


def test_patching_works():
    """Test that patching works"""
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "test_content"

        # This would normally open a file
        with open("test_file.txt") as f:
            content = f.read()

        assert content == "test_content"


def test_temp_files_work():
    """Test that temporary files work"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as temp_file:
        test_data = {"test": "data"}
        json.dump(test_data, temp_file)
        temp_path = temp_file.name

    # Read it back
    with open(temp_path) as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data

    # Cleanup
    Path(temp_path).unlink()


class TestFrameworkFeatures:
    """Test class-based testing works"""

    @pytest.fixture
    def sample_data(self):
        """Test fixture creation"""
        return {"fixture": "data"}

    def test_fixtures_work(self, sample_data):
        """Test that fixtures work"""
        assert sample_data["fixture"] == "data"

    def test_parametrized_tests(self):
        """Test basic functionality"""
        test_values = [1, 2, 3]
        for value in test_values:
            assert isinstance(value, int)

    def test_exception_handling(self):
        """Test exception handling in tests"""
        with pytest.raises(ValueError):
            raise ValueError("Test exception")


def test_imports_work():
    """Test that we can import basic Python modules"""
    import json
    import os
    import sys
    import tempfile
    from datetime import datetime
    from pathlib import Path
    from unittest.mock import Mock, patch

    # All imports should work
    assert os is not None
    assert sys is not None
    assert json is not None
    assert tempfile is not None
    assert Path is not None
    assert datetime is not None
    assert Mock is not None
    assert patch is not None
