"""
Tests for the main lambda_scanner module
"""

from unittest.mock import patch
from io import StringIO

from lambda_scanner import calculate_statistics, print_summary


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
