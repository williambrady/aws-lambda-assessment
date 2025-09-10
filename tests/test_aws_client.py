"""
Tests for the AWSClientManager module
"""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ProfileNotFound, NoCredentialsError

from modules.aws_client import AWSClientManager


class TestAWSClientManager:
    """Test cases for AWSClientManager class."""

    @patch('modules.aws_client.boto3.Session')
    def test_init_success(self, mock_session_class):
        """Test successful initialization."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'test-arn'}
        mock_session.client.return_value = mock_sts_client

        manager = AWSClientManager('test-profile', 'us-east-1')

        assert manager.profile == 'test-profile'
        assert manager.default_region == 'us-east-1'
        mock_session_class.assert_called_once_with(profile_name='test-profile')

    @patch('modules.aws_client.boto3.Session')
    def test_init_profile_not_found(self, mock_session_class):
        """Test initialization with invalid profile."""
        mock_session_class.side_effect = ProfileNotFound(profile='invalid-profile')

        with pytest.raises(ProfileNotFound):
            AWSClientManager('invalid-profile', 'us-east-1')

    @patch('modules.aws_client.boto3.Session')
    def test_init_no_credentials(self, mock_session_class):
        """Test initialization with no credentials."""
        mock_session_class.side_effect = NoCredentialsError()

        with pytest.raises(NoCredentialsError):
            AWSClientManager('test-profile', 'us-east-1')

    @patch('modules.aws_client.boto3.Session')
    def test_get_client(self, mock_session_class):
        """Test getting a client for a service."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'test-arn'}

        mock_lambda_client = Mock()

        def client_side_effect(service, **_kwargs):
            if service == 'sts':
                return mock_sts_client
            if service == 'lambda':
                return mock_lambda_client
            return Mock()

        mock_session.client.side_effect = client_side_effect

        manager = AWSClientManager('test-profile', 'us-east-1')

        # Test getting lambda client
        client = manager.get_client('lambda', 'us-west-2')
        assert client == mock_lambda_client

        # Test getting the same client again (should be cached)
        client2 = manager.get_client('lambda', 'us-west-2')
        assert client2 == mock_lambda_client

    @patch('modules.aws_client.boto3.Session')
    def test_get_lambda_client(self, mock_session_class):
        """Test getting a Lambda client specifically."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'test-arn'}

        mock_lambda_client = Mock()

        def client_side_effect(service, **_kwargs):
            if service == 'sts':
                return mock_sts_client
            if service == 'lambda':
                return mock_lambda_client
            return Mock()

        mock_session.client.side_effect = client_side_effect

        manager = AWSClientManager('test-profile', 'us-east-1')

        client = manager.get_lambda_client('us-west-2')
        assert client == mock_lambda_client

    @patch('modules.aws_client.boto3.Session')
    def test_get_account_id(self, mock_session_class):
        """Test account ID retrieval."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}

        def client_side_effect(service, **_kwargs):
            if service == 'sts':
                return mock_sts_client
            return Mock()

        mock_session.client.side_effect = client_side_effect

        manager = AWSClientManager('test-profile', 'us-east-1')

        account_id = manager.get_account_id()
        assert account_id == '123456789012'

    @patch('modules.aws_client.boto3.Session')
    def test_get_account_id_error(self, mock_session_class):
        """Test account ID retrieval with error."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock successful initialization but failed get_account_id
        call_count = 0
        def get_caller_identity_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call during initialization - succeed
                return {'Arn': 'test-arn', 'Account': '123456789012'}
            # Second call during get_account_id - fail
            raise RuntimeError("STS error")

        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.side_effect = get_caller_identity_side_effect

        def client_side_effect(service, **_kwargs):
            if service == 'sts':
                return mock_sts_client
            return Mock()

        mock_session.client.side_effect = client_side_effect

        manager = AWSClientManager('test-profile', 'us-east-1')

        account_id = manager.get_account_id()
        assert account_id == "unknown"
