"""
Lambda Analyzer Module

Analyzes AWS Lambda functions to extract metadata, code complexity, and other metrics.
"""

import logging
from typing import Dict, List

from botocore.exceptions import ClientError

from .aws_client import AWSClientManager


class LambdaAnalyzer:
    """Analyzes AWS Lambda functions for assessment reporting."""

    def __init__(self, aws_client: AWSClientManager):
        """
        Initialize Lambda analyzer.

        Args:
            aws_client: AWS client manager instance
        """
        self.aws_client = aws_client
        self.logger = logging.getLogger(__name__)

    def scan_region(self, region: str) -> List[Dict]:
        """
        Scan all Lambda functions in a specific region.

        Args:
            region: AWS region to scan

        Returns:
            List of Lambda function analysis results
        """
        lambda_client = self.aws_client.get_lambda_client(region)
        functions = []

        try:
            paginator = lambda_client.get_paginator('list_functions')

            for page in paginator.paginate():
                for function in page['Functions']:
                    try:
                        analysis = self._analyze_function(lambda_client, function, region)
                        functions.append(analysis)
                    except Exception as exc:
                        self.logger.error("Error analyzing function %s: %s",
                                        function['FunctionName'], exc)
                        continue

        except ClientError as e:
            self.logger.error("Error listing functions in region %s: %s", region, e)
            raise

        return functions

    def get_function_details(self, function_name: str, region: str) -> Dict:
        """
        Get detailed information about a specific Lambda function.

        Args:
            function_name: Name of the Lambda function
            region: AWS region where the function is located

        Returns:
            Detailed function analysis
        """
        lambda_client = self.aws_client.get_lambda_client(region)

        try:
            # Get function configuration
            response = lambda_client.get_function(FunctionName=function_name)
            function_data = response['Configuration']

            # Analyze the function
            return self._analyze_function(lambda_client, function_data, region)

        except ClientError as exc:
            self.logger.error("Error getting function details for %s: %s", function_name, exc)
            raise

    def _analyze_function(self, lambda_client, function_data: Dict, region: str) -> Dict:
        """
        Analyze a single Lambda function.

        Args:
            lambda_client: Lambda client for the region
            function_data: Function metadata from list_functions
            region: AWS region

        Returns:
            Analysis results for the function
        """
        function_name = function_data['FunctionName']

        # Basic function information
        result = {
            'region': region,
            'function_name': function_name,
            'runtime': function_data['Runtime'],
            'version': function_data['Version'],
            'code_size': function_data['CodeSize'],
            'memory_size': function_data['MemorySize'],
            'timeout': function_data['Timeout'],
            'last_modified': function_data['LastModified'],
            'handler': function_data['Handler'],
            'description': function_data.get('Description', ''),
        }

        # Get additional function configuration
        try:
            config_response = lambda_client.get_function_configuration(
                FunctionName=function_name
            )
            result.update({
                'environment_variables': len(config_response.get('Environment', {}).get('Variables', {})),
                'layers': len(config_response.get('Layers', [])),
                'dead_letter_config': bool(config_response.get('DeadLetterConfig')),
                'vpc_config': bool(config_response.get('VpcConfig', {}).get('VpcId')),
            })
        except ClientError as e:
            self.logger.warning("Could not get configuration for %s: %s", function_name, e)

        # Get function tags
        try:
            # Use the FunctionArn from the function data if available, otherwise construct it
            function_arn = function_data.get('FunctionArn')
            if not function_arn:
                # Construct ARN if not provided
                function_arn = f"arn:aws:lambda:{region}:*:function:{function_name}"

            tags_response = lambda_client.list_tags(Resource=function_arn)
            tags = tags_response.get('Tags', {})
            # Format tags as "key1=value1,key2=value2" for CSV compatibility
            if tags:
                tags_formatted = ','.join([f"{k}={v}" for k, v in tags.items()])
            else:
                tags_formatted = ''
            result['tags'] = tags_formatted
        except ClientError as e:
            self.logger.warning("Could not get tags for %s: %s", function_name, e)
            result['tags'] = ''

        # Analyze code complexity
        try:
            complexity_info = self._analyze_code_complexity(lambda_client, function_name)
            result.update(complexity_info)
        except Exception as exc:
            self.logger.warning("Could not analyze code complexity for %s: %s", function_name, exc)
            result.update({
                'lines_of_code': 0,
                'complexity_score': 'unknown',
                'file_count': 0
            })

        return result

    def _analyze_code_complexity(self, lambda_client, function_name: str) -> Dict:
        """
        Analyze code complexity by downloading and examining the function code.

        Args:
            lambda_client: Lambda client
            function_name: Name of the Lambda function

        Returns:
            Dictionary with complexity metrics
        """
        try:
            # Get function code
            response = lambda_client.get_function(FunctionName=function_name)
            code_location = response['Code']['Location']

            # For now, we'll use a simplified approach
            # In a production environment, you might want to download and analyze the actual code
            code_size = response['Configuration']['CodeSize']

            # Estimate complexity based on code size and runtime
            runtime = response['Configuration']['Runtime']

            # Simple heuristic for lines of code estimation
            if runtime.startswith('python'):
                estimated_loc = max(1, code_size // 50)  # Rough estimate for Python
            elif runtime.startswith('node'):
                estimated_loc = max(1, code_size // 40)  # Rough estimate for Node.js
            elif runtime.startswith('java'):
                estimated_loc = max(1, code_size // 100)  # Rough estimate for Java
            else:
                estimated_loc = max(1, code_size // 60)  # Generic estimate

            # Complexity scoring based on size and estimated LOC
            if estimated_loc < 100:
                complexity = 'low'
            elif estimated_loc < 500:
                complexity = 'medium'
            elif estimated_loc < 1000:
                complexity = 'high'
            else:
                complexity = 'very_high'

            return {
                'lines_of_code': estimated_loc,
                'complexity_score': complexity,
                'file_count': 1,  # Simplified - would need actual code analysis
                'code_location': code_location
            }

        except ClientError as exc:
            self.logger.warning("Could not get function code for %s: %s", function_name, exc)
            return {
                'lines_of_code': 0,
                'complexity_score': 'unknown',
                'file_count': 0
            }
