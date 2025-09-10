"""
AWS Organizations Manager

Handles AWS Organizations operations for multi-account scanning.
"""

import logging
from typing import List, Dict

import boto3
from botocore.exceptions import ClientError


class OrganizationsManager:
    """Manages AWS Organizations operations for multi-account Lambda scanning."""

    def __init__(self, aws_client_manager):
        """
        Initialize Organizations manager.

        Args:
            aws_client_manager: AWSClientManager instance
        """
        self.aws_client = aws_client_manager
        self.logger = logging.getLogger(__name__)

    def get_organization_accounts(self) -> List[Dict]:
        """
        Get all active member accounts in the organization.

        Returns:
            List of account dictionaries with Id, Name, Status, etc.
        """
        try:
            org_client = self.aws_client.get_organizations_client()

            # Check if this account is the management account
            org_info = org_client.describe_organization()
            management_account_id = org_info['Organization']['MasterAccountId']

            # Get caller identity to verify we're in the management account
            sts_client = self.aws_client.get_client('sts', self.aws_client.default_region)
            caller_identity = sts_client.get_caller_identity()
            current_account_id = caller_identity['Account']

            if current_account_id != management_account_id:
                raise ValueError(
                    f"Current account ({current_account_id}) is not the organization "
                    f"management account ({management_account_id}). "
                    "Organization scanning requires management account access."
                )

            self.logger.info("Verified management account access for organization: %s",
                           org_info['Organization']['Id'])

            # List all accounts in the organization
            accounts = []
            paginator = org_client.get_paginator('list_accounts')

            for page in paginator.paginate():
                for account in page['Accounts']:
                    if account['Status'] == 'ACTIVE':
                        accounts.append({
                            'Id': account['Id'],
                            'Name': account['Name'],
                            'Email': account['Email'],
                            'Status': account['Status'],
                            'JoinedMethod': account.get('JoinedMethod', 'UNKNOWN'),
                            'JoinedTimestamp': account.get('JoinedTimestamp')
                        })
                        self.logger.debug("Found active account: %s (%s)",
                                        account['Name'], account['Id'])

            self.logger.info("Found %d active accounts in organization", len(accounts))
            return accounts

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AWSOrganizationsNotInUseException':
                raise ValueError(
                    "AWS Organizations is not enabled for this account. "
                    "Enable Organizations or use single-account scanning."
                ) from e
            if error_code == 'AccessDeniedException':
                raise ValueError(
                    "Access denied to AWS Organizations. Ensure the current role/user "
                    "has organizations:DescribeOrganization and organizations:ListAccounts permissions."
                ) from e
            self.logger.error("Error accessing AWS Organizations: %s", e)
            raise

    def create_cross_account_session(self, account_id: str, role_name: str = None) -> boto3.Session:
        """
        Create a cross-account session for the specified account.

        Args:
            account_id: Target AWS account ID
            role_name: IAM role name to assume (optional)

        Returns:
            boto3.Session for the target account
        """
        try:
            # If no role name specified, try to use the account ID as profile
            if not role_name:
                # Try using account ID as profile name first
                try:
                    session = boto3.Session(profile_name=account_id)
                    # Test the session
                    sts_client = session.client('sts', region_name=self.aws_client.default_region)
                    identity = sts_client.get_caller_identity()
                    if identity['Account'] == account_id:
                        self.logger.debug("Using profile %s for account %s", account_id, account_id)
                        return session
                except Exception:
                    # Profile doesn't exist or doesn't work, continue to role assumption
                    pass

            # Fall back to role assumption if profile doesn't work
            if not role_name:
                role_name = "OrganizationAccountAccessRole"  # Default cross-account role

            sts_client = self.aws_client.get_client('sts', self.aws_client.default_region)
            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

            self.logger.debug("Assuming role %s for account %s", role_arn, account_id)

            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"LambdaScanner-{account_id}",
                DurationSeconds=3600  # 1 hour
            )

            credentials = response['Credentials']
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            # Verify the session works
            test_sts = session.client('sts', region_name=self.aws_client.default_region)
            identity = test_sts.get_caller_identity()
            self.logger.info("Successfully assumed role for account %s: %s",
                           account_id, identity.get('Arn', 'Unknown'))

            return session

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                self.logger.warning("Access denied assuming role for account %s. Skipping.", account_id)
                return None
            self.logger.error("Error assuming role for account %s: %s", account_id, e)
            return None
        except Exception as e:
            self.logger.error("Unexpected error creating session for account %s: %s", account_id, e)
            return None

    def validate_organization_access(self) -> bool:
        """
        Validate that the current account has proper Organizations access.

        Returns:
            True if access is valid, False otherwise
        """
        try:
            org_client = self.aws_client.get_organizations_client()
            org_client.describe_organization()
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['AWSOrganizationsNotInUseException', 'AccessDeniedException']:
                return False
            raise
