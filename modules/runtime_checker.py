"""
Runtime Checker Module

Checks AWS Lambda runtime support status and extracts language information.
"""

import logging
import re
from datetime import datetime
from typing import Dict


class RuntimeChecker:
    """Checks Lambda runtime support status and language information."""

    def __init__(self):
        """Initialize runtime checker with current AWS Lambda runtime data."""
        self.logger = logging.getLogger(__name__)

        # AWS Lambda runtime support data (as of 2024)
        # This should be updated periodically or fetched from AWS documentation
        self.runtime_data = {
            # Python runtimes
            'python3.12': {
                'language': 'Python',
                'version': '3.12',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'python3.11': {
                'language': 'Python',
                'version': '3.11',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'python3.10': {
                'language': 'Python',
                'version': '3.10',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'python3.9': {
                'language': 'Python',
                'version': '3.9',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'python3.8': {
                'language': 'Python',
                'version': '3.8',
                'supported': True,
                'deprecation_date': '2024-10-14',
                'end_of_support': '2024-10-14'
            },

            # Node.js runtimes
            'nodejs20.x': {
                'language': 'Node.js',
                'version': '20.x',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'nodejs18.x': {
                'language': 'Node.js',
                'version': '18.x',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'nodejs16.x': {
                'language': 'Node.js',
                'version': '16.x',
                'supported': True,
                'deprecation_date': '2024-06-12',
                'end_of_support': '2024-06-12'
            },

            # Java runtimes
            'java21': {
                'language': 'Java',
                'version': '21',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'java17': {
                'language': 'Java',
                'version': '17',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'java11': {
                'language': 'Java',
                'version': '11',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'java8.al2': {
                'language': 'Java',
                'version': '8 (Amazon Linux 2)',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },

            # .NET runtimes
            'dotnet8': {
                'language': '.NET',
                'version': '8',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'dotnet6': {
                'language': '.NET',
                'version': '6',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },

            # Go runtimes
            'provided.al2023': {
                'language': 'Go',
                'version': 'Custom Runtime (AL2023)',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },
            'provided.al2': {
                'language': 'Go',
                'version': 'Custom Runtime (AL2)',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },

            # Ruby runtimes
            'ruby3.2': {
                'language': 'Ruby',
                'version': '3.2',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },

            # Custom runtimes
            'provided': {
                'language': 'Custom Runtime',
                'version': 'Amazon Linux',
                'supported': True,
                'deprecation_date': None,
                'end_of_support': None
            },

            # Deprecated runtimes (examples)
            'python3.7': {
                'language': 'Python',
                'version': '3.7',
                'supported': False,
                'deprecation_date': '2022-11-27',
                'end_of_support': '2022-12-05'
            },
            'python2.7': {
                'language': 'Python',
                'version': '2.7',
                'supported': False,
                'deprecation_date': '2021-05-30',
                'end_of_support': '2021-07-15'
            },
            'nodejs14.x': {
                'language': 'Node.js',
                'version': '14.x',
                'supported': False,
                'deprecation_date': '2023-11-27',
                'end_of_support': '2023-12-04'
            },
            'nodejs12.x': {
                'language': 'Node.js',
                'version': '12.x',
                'supported': False,
                'deprecation_date': '2023-03-31',
                'end_of_support': '2023-04-30'
            }
        }

    def get_runtime_info(self, runtime: str) -> Dict:
        """
        Get comprehensive runtime information.

        Args:
            runtime: AWS Lambda runtime identifier

        Returns:
            Dictionary with runtime analysis
        """
        # Check if runtime is in our known data
        if runtime in self.runtime_data:
            runtime_info = self.runtime_data[runtime].copy()
        else:
            # Try to parse unknown runtime
            runtime_info = self._parse_unknown_runtime(runtime)

        # Add analysis fields
        runtime_info.update({
            'runtime_identifier': runtime,
            'aws_supported': runtime_info['supported'],
            'support_status': self._get_support_status(runtime_info),
            'language_name': runtime_info['language'],
            'language_version': runtime_info['version']
        })

        return runtime_info

    def _parse_unknown_runtime(self, runtime: str) -> Dict:
        """
        Parse unknown runtime identifier to extract language and version.

        Args:
            runtime: Runtime identifier

        Returns:
            Parsed runtime information
        """
        # Default values
        result = {
            'language': 'Unknown',
            'version': 'Unknown',
            'supported': False,
            'deprecation_date': None,
            'end_of_support': None
        }

        # Try to extract language and version using patterns
        patterns = [
            (r'^python(\d+\.\d+)', 'Python'),
            (r'^nodejs(\d+\.x)', 'Node.js'),
            (r'^java(\d+)', 'Java'),
            (r'^dotnet(\d+)', '.NET'),
            (r'^ruby(\d+\.\d+)', 'Ruby'),
            (r'^go(\d+\.\d+)', 'Go'),
            (r'^provided', 'Custom Runtime')
        ]

        for pattern, language in patterns:
            match = re.match(pattern, runtime)
            if match:
                result['language'] = language
                if match.groups():
                    result['version'] = match.group(1)
                break

        self.logger.warning("Unknown runtime detected: %s", runtime)
        return result

    def _get_support_status(self, runtime_info: Dict) -> str:
        """
        Determine the support status of a runtime.

        Args:
            runtime_info: Runtime information dictionary

        Returns:
            Support status string
        """
        if not runtime_info['supported']:
            return 'deprecated'

        if runtime_info['deprecation_date']:
            try:
                deprecation_date = datetime.fromisoformat(runtime_info['deprecation_date'])
                if deprecation_date <= datetime.now():
                    return 'deprecated'
                return 'deprecation_scheduled'
            except (ValueError, TypeError):
                pass

        return 'supported'

    def check_runtime_support(self, runtime: str) -> bool:
        """
        Check if a runtime is currently supported by AWS.

        Args:
            runtime: Runtime identifier

        Returns:
            True if supported, False otherwise
        """
        runtime_info = self.get_runtime_info(runtime)
        return runtime_info['aws_supported']

    def get_language_summary(self, runtimes: list) -> Dict:
        """
        Generate a summary of languages and their support status.

        Args:
            runtimes: List of runtime identifiers

        Returns:
            Summary dictionary
        """
        summary = {
            'total_runtimes': len(runtimes),
            'supported_count': 0,
            'deprecated_count': 0,
            'languages': {},
            'support_status': {}
        }

        for runtime in runtimes:
            info = self.get_runtime_info(runtime)
            language = info['language_name']
            status = info['support_status']

            # Count by support status
            if status == 'supported':
                summary['supported_count'] += 1
            elif status in ['deprecated', 'deprecation_scheduled']:
                summary['deprecated_count'] += 1

            # Count by language
            if language not in summary['languages']:
                summary['languages'][language] = 0
            summary['languages'][language] += 1

            # Count by status
            if status not in summary['support_status']:
                summary['support_status'][status] = 0
            summary['support_status'][status] += 1

        return summary
