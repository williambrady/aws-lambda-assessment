"""
Tests for the main lambda_scanner module
"""

import logging
import re
from unittest.mock import patch
from io import StringIO

from lambda_scanner import calculate_statistics, print_summary, export_deprecated_runtimes_csv, generate_timestamped_filename


class TestLambdaScanner:
    """Test cases for lambda_scanner functions."""

    def test_calculate_statistics(self):
        """Test statistics calculation from Lambda results."""
        sample_results = [
            {
                'runtime': 'python3.9',
                'language_name': 'Python',
                'support_status': 'supported',
                'complexity_score': 'low',
                'code_size': 1000,
                'lines_of_code': 50
            },
            {
                'runtime': 'nodejs18.x',
                'language_name': 'Node.js',
                'support_status': 'supported',
                'complexity_score': 'medium',
                'code_size': 2000,
                'lines_of_code': 100
            },
            {
                'runtime': 'python3.7',
                'language_name': 'Python',
                'support_status': 'deprecated',
                'complexity_score': 'high',
                'code_size': 500,
                'lines_of_code': 25
            }
        ]

        stats = calculate_statistics(sample_results)

        # Check runtime stats
        assert stats['runtime_stats']['python3.9'] == 1
        assert stats['runtime_stats']['nodejs18.x'] == 1
        assert stats['runtime_stats']['python3.7'] == 1

        # Check language stats
        assert stats['language_stats']['Python'] == 2
        assert stats['language_stats']['Node.js'] == 1

        # Check support stats
        assert stats['support_stats']['supported'] == 2
        assert stats['support_stats']['deprecated'] == 1

        # Check complexity stats
        assert stats['complexity_stats']['low'] == 1
        assert stats['complexity_stats']['medium'] == 1
        assert stats['complexity_stats']['high'] == 1

        # Check totals
        assert stats['total_code_size'] == 3500
        assert stats['total_lines_of_code'] == 175

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_summary_with_functions(self, mock_stdout):
        """Test summary printing with sample functions."""
        sample_results = [
            {
                'runtime': 'python3.9',
                'language_name': 'Python',
                'support_status': 'supported',
                'complexity_score': 'low',
                'code_size': 1000,
                'lines_of_code': 50,
                'function_name': 'TestFunction1',
                'region': 'us-east-1'
            }
        ]
        regions = ['us-east-1']

        print_summary(sample_results, regions)

        output = mock_stdout.getvalue()
        assert "AWS LAMBDA ASSESSMENT SUMMARY" in output
        assert "Total Functions Found: 1" in output
        assert "python3.9: 1 functions (100.0%)" in output
        assert "Python: 1 functions (100.0%)" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_summary_no_functions(self, mock_stdout):
        """Test summary printing with no functions."""
        sample_results = []
        regions = ['us-east-1']

        print_summary(sample_results, regions)

        output = mock_stdout.getvalue()
        assert "AWS LAMBDA ASSESSMENT SUMMARY" in output
        assert "Total Functions Found: 0" in output
        assert "No Lambda functions found" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_summary_with_deprecated_runtimes_org_mode(self, mock_stdout):
        """Test summary printing with deprecated runtimes in organization mode."""
        sample_results = [
            {
                'runtime': 'python3.7',
                'language_name': 'Python',
                'support_status': 'deprecated',
                'complexity_score': 'low',
                'code_size': 1000,
                'lines_of_code': 50,
                'function_name': 'DeprecatedFunction',
                'region': 'us-east-1',
                'account_id': '123456789012'
            }
        ]
        regions = ['us-east-1']

        print_summary(sample_results, regions, is_org_scan=True)

        output = mock_stdout.getvalue()
        assert "DEPRECATED RUNTIMES DETECTED" in output
        assert "DeprecatedFunction (python3.7) in us-east-1 of 123456789012" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_summary_with_deprecated_runtimes_single_account(self, mock_stdout):
        """Test summary printing with deprecated runtimes in single account mode."""
        sample_results = [
            {
                'runtime': 'python3.7',
                'language_name': 'Python',
                'support_status': 'deprecated',
                'complexity_score': 'low',
                'code_size': 1000,
                'lines_of_code': 50,
                'function_name': 'DeprecatedFunction',
                'region': 'us-east-1'
                # No account_id for single account mode
            }
        ]
        regions = ['us-east-1']

        print_summary(sample_results, regions, is_org_scan=False)

        output = mock_stdout.getvalue()
        assert "DEPRECATED RUNTIMES DETECTED" in output
        assert "DeprecatedFunction (python3.7) in us-east-1" in output
        assert "123456789012" not in output  # Should not contain account ID

    def test_export_deprecated_runtimes_csv(self, tmp_path):
        """Test CSV export of deprecated runtimes."""
        logger = logging.getLogger(__name__)

        sample_results = [
            {
                'runtime': 'python3.7',
                'language_name': 'Python',
                'language_version': '3.7',
                'support_status': 'deprecated',
                'function_name': 'DeprecatedFunction1',
                'region': 'us-east-1',
                'account_id': '123456789012',
                'description': 'Test deprecated function',
                'tags': 'Environment=test,Owner=team1'
            },
            {
                'runtime': 'python3.9',
                'language_name': 'Python',
                'language_version': '3.9',
                'support_status': 'supported',
                'function_name': 'SupportedFunction',
                'region': 'us-east-1',
                'account_id': '123456789012',
                'description': 'Test supported function',
                'tags': 'Environment=prod'
            },
            {
                'runtime': 'nodejs14.x',
                'language_name': 'Node.js',
                'language_version': '14.x',
                'support_status': 'deprecated',
                'function_name': 'DeprecatedFunction2',
                'region': 'us-west-2',
                'account_id': '987654321098',
                'description': '',
                'tags': ''
            }
        ]

        csv_file = tmp_path / "deprecated_runtimes.csv"
        export_deprecated_runtimes_csv(sample_results, str(csv_file), logger)

        # Verify CSV file was created and contains correct data
        assert csv_file.exists()

        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check header includes new columns
        assert "account_number,region,language,language_version,name,ARN,description,tags" in content

        # Check deprecated functions are included with description and tags
        assert "123456789012,us-east-1,Python,3.7,DeprecatedFunction1" in content
        assert "987654321098,us-west-2,Node.js,14.x,DeprecatedFunction2" in content
        assert "Test deprecated function" in content
        assert "Environment=test,Owner=team1" in content

        # Check ARNs are correctly formatted
        assert "arn:aws:lambda:us-east-1:123456789012:function:DeprecatedFunction1" in content
        assert "arn:aws:lambda:us-west-2:987654321098:function:DeprecatedFunction2" in content

        # Check supported function is NOT included
        assert "SupportedFunction" not in content

    def test_export_deprecated_runtimes_csv_no_deprecated(self, tmp_path):
        """Test CSV export when no deprecated runtimes exist."""
        logger = logging.getLogger(__name__)

        sample_results = [
            {
                'runtime': 'python3.9',
                'language_name': 'Python',
                'language_version': '3.9',
                'support_status': 'supported',
                'function_name': 'SupportedFunction',
                'region': 'us-east-1',
                'account_id': '123456789012'
            }
        ]

        csv_file = tmp_path / "deprecated_runtimes.csv"
        export_deprecated_runtimes_csv(sample_results, str(csv_file), logger)

        # Verify CSV file was NOT created
        assert not csv_file.exists()

    def test_generate_timestamped_filename(self):
        """Test timestamped filename generation."""

        # Test with JSON file (no account ID)
        result = generate_timestamped_filename('report.json')

        # Should match pattern: YYYYMMDD-HHMMSS_report.json
        pattern = r'^\d{8}-\d{6}_report\.json$'
        assert re.match(pattern, result), f"Filename '{result}' doesn't match expected pattern"

        # Test with CSV file and account ID
        result = generate_timestamped_filename('deprecated.csv', '123456789012')
        pattern = r'^\d{8}-\d{6}-123456789012_deprecated\.csv$'
        assert re.match(pattern, result), f"Filename '{result}' doesn't match expected pattern"

        # Test with JSON file and account ID
        result = generate_timestamped_filename('report.json', '987654321098')
        pattern = r'^\d{8}-\d{6}-987654321098_report\.json$'
        assert re.match(pattern, result), f"Filename '{result}' doesn't match expected pattern"

        # Test with path and account ID
        result = generate_timestamped_filename('reports/analysis.json', '555666777888')
        pattern = r'^\d{8}-\d{6}-555666777888_reports/analysis\.json$'
        assert re.match(pattern, result), f"Filename '{result}' doesn't match expected pattern"
