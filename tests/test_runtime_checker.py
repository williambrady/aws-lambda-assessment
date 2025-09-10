"""
Tests for the RuntimeChecker module
"""

import pytest
from modules.runtime_checker import RuntimeChecker


@pytest.fixture(name='checker')
def runtime_checker_fixture():
    """Fixture for RuntimeChecker instance."""
    return RuntimeChecker()


class TestRuntimeChecker:
    """Test cases for RuntimeChecker class."""

    def test_get_runtime_info_known_runtime(self, checker):
        """Test getting runtime info for a known runtime."""
        result = checker.get_runtime_info('python3.11')

        assert result['language_name'] == 'Python'
        assert result['language_version'] == '3.11'
        assert result['aws_supported'] is True
        assert result['support_status'] == 'supported'
        assert result['runtime_identifier'] == 'python3.11'

    def test_get_runtime_info_deprecated_runtime(self, checker):
        """Test getting runtime info for a deprecated runtime."""
        result = checker.get_runtime_info('python3.7')

        assert result['language_name'] == 'Python'
        assert result['language_version'] == '3.7'
        assert result['aws_supported'] is False
        assert result['support_status'] == 'deprecated'

    def test_get_runtime_info_unknown_runtime(self, checker):
        """Test getting runtime info for an unknown runtime."""
        result = checker.get_runtime_info('unknown-runtime-1.0')

        assert result['language_name'] == 'Unknown'
        assert result['aws_supported'] is False
        assert result['support_status'] == 'deprecated'

    def test_check_runtime_support_supported(self, checker):
        """Test checking support for a supported runtime."""
        assert checker.check_runtime_support('python3.11') is True

    def test_check_runtime_support_deprecated(self, checker):
        """Test checking support for a deprecated runtime."""
        assert checker.check_runtime_support('python3.7') is False

    def test_get_language_summary(self, checker):
        """Test generating language summary."""
        runtimes = ['python3.11', 'python3.7', 'nodejs18.x', 'java17']
        summary = checker.get_language_summary(runtimes)

        assert summary['total_runtimes'] == 4
        assert summary['supported_count'] == 3
        assert summary['deprecated_count'] == 1
        assert 'Python' in summary['languages']
        assert 'Node.js' in summary['languages']
        assert 'Java' in summary['languages']

    def test_parse_python_runtime(self, checker):
        """Test parsing Python runtime patterns."""
        # Test with unknown runtime that should be parsed
        result = checker.get_runtime_info('python3.13')
        assert result['language_name'] == 'Python'
        assert result['language_version'] == '3.13'

    def test_parse_nodejs_runtime(self, checker):
        """Test parsing Node.js runtime patterns."""
        # Test with unknown runtime that should be parsed
        result = checker.get_runtime_info('nodejs22.x')
        assert result['language_name'] == 'Node.js'
        assert result['language_version'] == '22.x'

    def test_parse_java_runtime(self, checker):
        """Test parsing Java runtime patterns."""
        # Test with unknown runtime that should be parsed
        result = checker.get_runtime_info('java22')
        assert result['language_name'] == 'Java'
        assert result['language_version'] == '22'
