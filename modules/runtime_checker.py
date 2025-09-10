"""
Runtime Checker Module

Checks AWS Lambda runtime support status and extracts language information.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup


class RuntimeChecker:
    """Checks Lambda runtime support status and language information."""

    def __init__(self):
        """Initialize runtime checker with current AWS Lambda runtime data."""
        self.logger = logging.getLogger(__name__)

        # AWS Lambda runtime support data (as of 2024)
        # This should be updated periodically or fetched from AWS documentation
        self.runtime_data = {
            # Python runtimes
            'python3.13': {
                'language': 'Python',
                'version': '3.13',
                'supported': True,
                'deprecation_date': '2029-10-31',
                'end_of_support': '2029-10-31'
            },
            'python3.12': {
                'language': 'Python',
                'version': '3.12',
                'supported': True,
                'deprecation_date': '2028-10-31',
                'end_of_support': '2028-10-31'
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
            'nodejs22.x': {
                'language': 'Node.js',
                'version': '22.x',
                'supported': True,
                'deprecation_date': '2027-04-30',
                'end_of_support': '2027-04-30'
            },
            'nodejs20.x': {
                'language': 'Node.js',
                'version': '20.x',
                'supported': True,
                'deprecation_date': '2026-04-30',
                'end_of_support': '2026-04-30'
            },
            'nodejs18.x': {
                'language': 'Node.js',
                'version': '18.x',
                'supported': True,
                'deprecation_date': '2025-04-30',
                'end_of_support': '2025-04-30'
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

    def update_runtime_data_from_aws_docs(self, save_to_file: Optional[str] = None) -> bool:
        """
        Update runtime data by fetching from AWS Lambda documentation.

        Args:
            save_to_file: Optional file path to save the updated runtime data

        Returns:
            True if update was successful, False otherwise
        """
        try:
            self.logger.info("Fetching runtime data from AWS documentation...")

            # Fetch the AWS Lambda runtimes page
            url = "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the runtime tables
            new_runtime_data = {}

            # Parse supported runtimes table
            supported_runtimes = self._parse_supported_runtimes_table(soup)
            new_runtime_data.update(supported_runtimes)

            # Parse deprecated runtimes table
            deprecated_runtimes = self._parse_deprecated_runtimes_table(soup)
            new_runtime_data.update(deprecated_runtimes)

            if new_runtime_data:
                self.runtime_data = new_runtime_data
                self.logger.info("Successfully updated runtime data with %d runtimes", len(new_runtime_data))

                # Save to file if requested
                if save_to_file:
                    self._save_runtime_data_to_file(save_to_file)

                return True

            self.logger.warning("No runtime data found in AWS documentation")
            return False

        except Exception as e:
            self.logger.error("Failed to update runtime data from AWS docs: %s", e)
            return False

    def _parse_supported_runtimes_table(self, soup: BeautifulSoup) -> Dict:  # pylint: disable=too-many-nested-blocks
        """Parse the supported runtimes table from AWS documentation."""
        runtimes = {}

        try:
            # Find all tables and look for runtime data
            tables = soup.find_all('table')
            self.logger.info("Found %d tables in AWS documentation", len(tables))

            for i, table in enumerate(tables):
                # Check if this table contains runtime information
                headers = table.find_all(['th', 'td'])
                header_text = ' '.join([h.get_text().strip().lower() for h in headers[:5]])

                # Look for tables with runtime-related headers
                if any(keyword in header_text for keyword in ['name', 'identifier', 'runtime', 'deprecation']):
                    self.logger.info("Found potential runtime table %d with headers: %s", i, header_text[:100])

                    # Parse table rows
                    rows = table.find_all('tr')
                    if len(rows) > 1:  # Must have header + data rows
                        # Find header row to determine column positions
                        header_row = rows[0]
                        header_cells = header_row.find_all(['th', 'td'])

                        # Map column positions
                        col_map = {}
                        for idx, cell in enumerate(header_cells):
                            text = cell.get_text().strip().lower()
                            if 'name' in text:
                                col_map['name'] = idx
                            elif 'identifier' in text:
                                col_map['identifier'] = idx
                            elif 'deprecation' in text:
                                col_map['deprecation'] = idx

                        # Parse data rows
                        for row in rows[1:]:
                            parsed_runtime = self._parse_table_row(row, col_map)
                            if parsed_runtime:
                                identifier, runtime_info = parsed_runtime
                                runtimes[identifier] = runtime_info
                                self.logger.debug("Parsed runtime: %s", identifier)

        except Exception as e:
            self.logger.error("Error parsing supported runtimes table: %s", e)

        return runtimes

    def _parse_table_row(self, row, col_map):
        """Parse a single table row for runtime information."""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 3:  # Need at least name, identifier, deprecation
            return None

        try:
            name = cells[col_map.get('name', 0)].get_text().strip()
            identifier = cells[col_map.get('identifier', 1)].get_text().strip()
            deprecation_date = cells[col_map.get('deprecation', 3)].get_text().strip()

            if not identifier or identifier == 'Identifier' or '.' not in identifier:
                return None

            # Determine if supported based on deprecation date
            supported = self._is_runtime_supported(deprecation_date)

            runtime_info = self._parse_runtime_from_table_row(
                name, identifier, deprecation_date, supported=supported
            )
            if runtime_info:
                return identifier, runtime_info

        except (IndexError, AttributeError) as e:
            self.logger.debug("Error parsing row: %s", e)

        return None

    def _is_runtime_supported(self, deprecation_date_str: str) -> bool:
        """Determine if a runtime is currently supported based on its deprecation date."""
        if not deprecation_date_str or 'not scheduled' in deprecation_date_str.lower():
            # No deprecation date means it's currently supported
            return True

        # Parse the deprecation date
        parsed_date = self._parse_date_string(deprecation_date_str)
        if not parsed_date:
            # If we can't parse the date, assume it's supported to be conservative
            return True

        try:
            # Convert to datetime for comparison
            deprecation_datetime = datetime.fromisoformat(parsed_date)
            current_datetime = datetime.now()

            # Runtime is supported if current date is BEFORE the deprecation date
            return current_datetime < deprecation_datetime

        except (ValueError, TypeError):
            # If date parsing fails, assume supported to be conservative
            return True

    def _parse_deprecated_runtimes_table(self, soup: BeautifulSoup) -> Dict:  # pylint: disable=unused-argument
        """Parse the deprecated runtimes table from AWS documentation."""
        # The improved parsing logic in _parse_supported_runtimes_table
        # already handles both supported and deprecated runtimes
        # This method is kept for interface compatibility
        return {}

    def _parse_runtime_from_table_row(self, name: str, identifier: str, deprecation_date: str, supported: bool) -> Optional[Dict]:
        """Parse runtime information from a table row."""
        try:
            # Extract language and version from name
            language, version = self._extract_language_version(name, identifier)

            # Parse deprecation date
            parsed_deprecation_date = None
            end_of_support = None

            if deprecation_date and deprecation_date.strip() and 'not scheduled' not in deprecation_date.lower():
                # Try to parse various date formats
                date_text = deprecation_date.strip()
                parsed_deprecation_date = self._parse_date_string(date_text)
                end_of_support = parsed_deprecation_date  # Use same date for end of support

            return {
                'language': language,
                'version': version,
                'supported': supported,
                'deprecation_date': parsed_deprecation_date,
                'end_of_support': end_of_support
            }

        except Exception as e:
            self.logger.error("Error parsing runtime row for %s: %s", identifier, e)
            return None

    def _extract_language_version(self, name: str, identifier: str) -> tuple:
        """Extract language and version from runtime name and identifier."""
        # Map common patterns
        language_map = {
            'node.js': 'Node.js',
            'python': 'Python',
            'java': 'Java',
            '.net': '.NET',
            'ruby': 'Ruby',
            'go': 'Go',
            'os-only': 'Custom Runtime'
        }

        name_lower = name.lower()

        # Find language
        language = 'Unknown'
        for key, value in language_map.items():
            if key in name_lower:
                language = value
                break

        # Extract version from name or identifier
        version = 'Unknown'

        # Try to extract version from name first
        version_patterns = [
            r'(\d+\.?\d*\.?\d*)',  # Version numbers
            r'(\d+\.x)',           # Node.js style
            r'(al\d+)',            # Amazon Linux versions
            r'(container only)',    # Container only runtimes
        ]

        for pattern in version_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                version = match.group(1)
                break

        # If no version found in name, try identifier
        if version == 'Unknown':
            for pattern in version_patterns:
                match = re.search(pattern, identifier, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    break

        return language, version

    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats to ISO format."""
        if not date_str or 'not scheduled' in date_str.lower():
            return None

        try:
            # Common AWS date formats
            date_formats = [
                '%b %d, %Y',    # "Oct 14, 2024"
                '%B %d, %Y',    # "October 14, 2024"
                '%Y-%m-%d',     # "2024-10-14"
                '%m/%d/%Y',     # "10/14/2024"
            ]

            date_str = date_str.strip()

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            self.logger.warning("Could not parse date string: %s", date_str)
            return None

        except Exception as e:
            self.logger.error("Error parsing date string '%s': %s", date_str, e)
            return None

    def _save_runtime_data_to_file(self, file_path: str) -> bool:
        """Save runtime data to a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.runtime_data, f, indent=2, sort_keys=True)
            self.logger.info("Runtime data saved to %s", file_path)
            return True
        except Exception as e:
            self.logger.error("Failed to save runtime data to %s: %s", file_path, e)
            return False
