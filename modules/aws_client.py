"""
AWS Client Manager

Handles AWS session management and client creation for different regions.
"""

import logging
from typing import Dict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound


class AWSClientManager:
    """Manages AWS clients for different regions and services."""

    def __init__(self, profile: str, default_region: str):
        """
        Initialize AWS client manager.

        Args:
            profile: AWS profile name to use
            default_region: Default AWS region
        """
        self.profile = profile
        self.default_region = default_region
        self.logger = logging.getLogger(__name__)
        self._session = None
        self._clients: Dict[str, Dict[str, object]] = {}

        self._initialize_session()

    def _initialize_session(self) -> None:
        """Initialize AWS session with the specified profile."""
        try:
            self._session = boto3.Session(profile_name=self.profile)
            self.logger.info("Initialized AWS session with profile: %s", self.profile)

            # Test credentials by making a simple call
            sts_client = self._session.client('sts', region_name=self.default_region)
            identity = sts_client.get_caller_identity()
            self.logger.info("AWS Identity: %s", identity.get('Arn', 'Unknown'))

        except ProfileNotFound:
            self.logger.error("AWS profile '%s' not found", self.profile)
            raise
        except NoCredentialsError:
            self.logger.error("No AWS credentials found for profile '%s'", self.profile)
            raise
        except ClientError as e:
            self.logger.error("Error initializing AWS session: %s", e)
            raise

    def get_client(self, service: str, region: str) -> object:
        """
        Get AWS client for specified service and region.

        Args:
            service: AWS service name (e.g., 'lambda', 's3')
            region: AWS region name

        Returns:
            AWS service client
        """
        if region not in self._clients:
            self._clients[region] = {}

        if service not in self._clients[region]:
            try:
                client = self._session.client(service, region_name=region)
                self._clients[region][service] = client
                self.logger.debug("Created %s client for region %s", service, region)
            except (ClientError, Exception) as exc:
                self.logger.error("Error creating %s client for region %s: %s", service, region, exc)
                raise

        return self._clients[region][service]

    def get_lambda_client(self, region: str):
        """Get Lambda client for specified region."""
        return self.get_client('lambda', region)

    def list_regions(self) -> list:
        """List all available AWS regions."""
        try:
            ec2_client = self.get_client('ec2', self.default_region)
            response = ec2_client.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except (ClientError, Exception) as exc:
            self.logger.error("Error listing regions: %s", exc)
            return []
