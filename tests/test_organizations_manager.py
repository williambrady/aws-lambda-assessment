"""
Tests for the organizations_manager module
"""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from modules.organizations_manager import OrganizationsManager


class TestOrganizationsManager:
    """Test cases for OrganizationsManager."""

    @pytest.fixture
    def mock_aws_client(self):
        """Create a mock AWS client manager."""
        mock_client = Mock()
        mock_client.default_region = 'us-east-1'
        return mock_client

    @pytest.fixture
    def org_manager(self, mock_aws_client):
        """Create OrganizationsManager instance with mock client."""
        return OrganizationsManager(mock_aws_client)

    def test_init(self, mock_aws_client):
        """Test OrganizationsManager initialization."""
        manager = OrganizationsManager(mock_aws_client)
        assert manager.aws_client == mock_aws_client
        assert manager.logger is not None

    @patch('boto3.Session')
    def test_create_cross_account_session_with_profile(self, mock_session_class, org_manager):
        """Test creating cross-account session using profile."""
        # Mock successful profile-based session
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_session.client.return_value = mock_sts_client
        mock_session_class.return_value = mock_session

        result = org_manager.create_cross_account_session('123456789012')

        assert result == mock_session
        mock_session_class.assert_called_with(profile_name='123456789012')

    def test_get_organization_accounts_success(self, org_manager):
        """Test successful retrieval of organization accounts."""
        # Mock organization client
        mock_org_client = Mock()
        mock_org_client.describe_organization.return_value = {
            'Organization': {
                'Id': 'o-example123456',
                'MasterAccountId': '111111111111'
            }
        }

        # Mock STS client
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': '111111111111'
        }

        # Mock paginator
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [
            {
                'Accounts': [
                    {
                        'Id': '111111111111',
                        'Name': 'Management Account',
                        'Email': 'management@example.com',
                        'Status': 'ACTIVE',
                        'JoinedMethod': 'INVITED'
                    },
                    {
                        'Id': '222222222222',
                        'Name': 'Member Account',
                        'Email': 'member@example.com',
                        'Status': 'ACTIVE',
                        'JoinedMethod': 'CREATED'
                    }
                ]
            }
        ]
        mock_org_client.get_paginator.return_value = mock_paginator

        # Setup mocks
        org_manager.aws_client.get_organizations_client.return_value = mock_org_client
        org_manager.aws_client.get_client.return_value = mock_sts_client

        accounts = org_manager.get_organization_accounts()

        assert len(accounts) == 2
        assert accounts[0]['Id'] == '111111111111'
        assert accounts[0]['Name'] == 'Management Account'
        assert accounts[1]['Id'] == '222222222222'
        assert accounts[1]['Name'] == 'Member Account'

    def test_get_organization_accounts_not_management_account(self, org_manager):
        """Test error when not using management account."""
        # Mock organization client
        mock_org_client = Mock()
        mock_org_client.describe_organization.return_value = {
            'Organization': {
                'Id': 'o-example123456',
                'MasterAccountId': '111111111111'
            }
        }

        # Mock STS client - different account
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {
            'Account': '222222222222'  # Different from management account
        }

        # Setup mocks
        org_manager.aws_client.get_organizations_client.return_value = mock_org_client
        org_manager.aws_client.get_client.return_value = mock_sts_client

        with pytest.raises(ValueError, match="not the organization management account"):
            org_manager.get_organization_accounts()

    def test_get_organization_accounts_organizations_not_enabled(self, org_manager):
        """Test error when Organizations is not enabled."""
        mock_org_client = Mock()
        mock_org_client.describe_organization.side_effect = ClientError(
            {'Error': {'Code': 'AWSOrganizationsNotInUseException'}},
            'DescribeOrganization'
        )

        org_manager.aws_client.get_organizations_client.return_value = mock_org_client

        with pytest.raises(ValueError, match="AWS Organizations is not enabled"):
            org_manager.get_organization_accounts()

    def test_validate_organization_access_success(self, org_manager):
        """Test successful organization access validation."""
        mock_org_client = Mock()
        mock_org_client.describe_organization.return_value = {'Organization': {}}

        org_manager.aws_client.get_organizations_client.return_value = mock_org_client

        result = org_manager.validate_organization_access()
        assert result is True

    def test_validate_organization_access_failure(self, org_manager):
        """Test failed organization access validation."""
        mock_org_client = Mock()
        mock_org_client.describe_organization.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException'}},
            'DescribeOrganization'
        )

        org_manager.aws_client.get_organizations_client.return_value = mock_org_client

        result = org_manager.validate_organization_access()
        assert result is False
