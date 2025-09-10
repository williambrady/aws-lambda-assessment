#!/usr/bin/env python3
"""
AWS Lambda Assessment Scanner

Scans AWS Lambda functions across regions and generates a comprehensive report
including runtime information, versions, sizes, and code complexity.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict

import click
import yaml

from modules.aws_client import AWSClientManager
from modules.lambda_analyzer import LambdaAnalyzer
from modules.runtime_checker import RuntimeChecker


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error("Configuration file not found: %s", config_path)
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error("Error parsing configuration file: %s", e)
        sys.exit(1)


def process_cli_overrides(config_data: Dict, **kwargs) -> None:
    """Process CLI argument overrides for configuration."""
    if kwargs.get('profile'):
        config_data['aws']['profile'] = kwargs['profile']
    if kwargs.get('region'):
        config_data['aws']['regions'] = [kwargs['region']]
    if kwargs.get('output'):
        config_data['output']['file'] = kwargs['output']
    if kwargs.get('output_format'):
        config_data['output']['format'] = kwargs['output_format']


def calculate_statistics(all_results: list) -> Dict:
    """Calculate statistics from Lambda function results."""
    stats = {
        'runtime_stats': {},
        'language_stats': {},
        'support_stats': {"supported": 0, "deprecated": 0, "unknown": 0},
        'complexity_stats': {"low": 0, "medium": 0, "high": 0, "very_high": 0, "unknown": 0},
        'total_code_size': 0,
        'total_lines_of_code': 0
    }

    for func in all_results:
        # Runtime statistics
        runtime = func['runtime']
        stats['runtime_stats'][runtime] = stats['runtime_stats'].get(runtime, 0) + 1

        # Language statistics
        language = func['language_name']
        stats['language_stats'][language] = stats['language_stats'].get(language, 0) + 1

        # Support status
        status = func['support_status']
        if status in stats['support_stats']:
            stats['support_stats'][status] += 1
        else:
            stats['support_stats']['unknown'] += 1

        # Complexity
        complexity = func['complexity_score']
        if complexity in stats['complexity_stats']:
            stats['complexity_stats'][complexity] += 1
        else:
            stats['complexity_stats']['unknown'] += 1

        # Size metrics
        stats['total_code_size'] += func['code_size']
        stats['total_lines_of_code'] += func['lines_of_code']

    return stats


def print_summary(all_results: list, regions: list) -> None:
    """Print a comprehensive summary of Lambda findings to STDOUT."""
    print("\n" + "="*80)
    print("AWS LAMBDA ASSESSMENT SUMMARY")
    print("="*80)

    # Overall statistics
    total_functions = len(all_results)
    print("\n📊 SCAN OVERVIEW:")
    print(f"   • Total Functions Found: {total_functions}")
    print(f"   • Regions Scanned: {len(regions)} ({', '.join(regions)})")

    if total_functions == 0:
        print("\n   No Lambda functions found in the specified regions.")
        return

    # Calculate statistics
    stats = calculate_statistics(all_results)

    # Print runtime breakdown
    print("\n🔧 RUNTIME BREAKDOWN:")
    for runtime, count in sorted(stats['runtime_stats'].items()):
        percentage = (count / total_functions) * 100
        print(f"   • {runtime}: {count} functions ({percentage:.1f}%)")

    # Print language breakdown
    print("\n💻 LANGUAGE BREAKDOWN:")
    for language, count in sorted(stats['language_stats'].items()):
        percentage = (count / total_functions) * 100
        print(f"   • {language}: {count} functions ({percentage:.1f}%)")

    # Print support status
    print("\n✅ AWS SUPPORT STATUS:")
    for status, count in stats['support_stats'].items():
        if count > 0:
            percentage = (count / total_functions) * 100
            status_icon = "✅" if status == "supported" else "⚠️" if status == "deprecated" else "❓"
            print(f"   • {status_icon} {status.title()}: {count} functions ({percentage:.1f}%)")

    # Print complexity breakdown
    print("\n📈 COMPLEXITY ANALYSIS:")
    complexity_icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "very_high": "🔴", "unknown": "⚪"}
    for complexity, count in stats['complexity_stats'].items():
        if count > 0:
            percentage = (count / total_functions) * 100
            icon = complexity_icons.get(complexity, "⚪")
            print(f"   • {icon} {complexity.replace('_', ' ').title()}: {count} functions ({percentage:.1f}%)")

    # Print size metrics
    avg_code_size = stats['total_code_size'] / total_functions
    avg_lines_of_code = stats['total_lines_of_code'] / total_functions
    print("\n📏 SIZE METRICS:")
    print(f"   • Total Code Size: {stats['total_code_size']:,} bytes")
    print(f"   • Average Code Size: {avg_code_size:,.0f} bytes")
    print(f"   • Total Lines of Code: {stats['total_lines_of_code']:,}")
    print(f"   • Average Lines of Code: {avg_lines_of_code:.0f}")

    # Highlight any deprecated runtimes
    deprecated_functions = [f for f in all_results if f['support_status'] == 'deprecated']
    if deprecated_functions:
        print("\n⚠️  DEPRECATED RUNTIMES DETECTED:")
        for func in deprecated_functions:
            print(f"   • {func['function_name']} ({func['runtime']}) in {func['region']}")
        print(f"   → Consider upgrading these {len(deprecated_functions)} function(s) to supported runtimes")

    # Show largest functions
    largest_functions = sorted(all_results, key=lambda x: x['lines_of_code'], reverse=True)[:3]
    if largest_functions:
        print("\n🔍 LARGEST FUNCTIONS (by estimated LOC):")
        for i, func in enumerate(largest_functions, 1):
            print(f"   {i}. {func['function_name']}: {func['lines_of_code']} lines ({func['complexity_score']} complexity)")

    print("\n" + "="*80)


def scan_regions(lambda_analyzer, runtime_checker, regions: list, logger) -> list:
    """Scan Lambda functions across multiple regions."""
    all_results = []

    logger.info("Scanning %d regions: %s", len(regions), ', '.join(regions))

    for region_name in regions:
        logger.info("Scanning region: %s", region_name)
        try:
            region_results = lambda_analyzer.scan_region(region_name)

            # Enhance results with runtime information
            for result in region_results:
                runtime_info = runtime_checker.get_runtime_info(result['runtime'])
                result.update(runtime_info)

            all_results.extend(region_results)
            logger.info("Found %d Lambda functions in %s", len(region_results), region_name)

        except Exception as exc:
            logger.error("Error scanning region %s: %s", region_name, exc)
            continue

    return all_results


@click.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--profile', '-p', help='AWS profile to use')
@click.option('--region', '-r', help='AWS region to scan (overrides config)')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', 'output_format', type=click.Choice(['json', 'csv']), help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(**kwargs) -> None:
    """AWS Lambda Assessment Scanner - Analyze Lambda functions across regions."""

    # Setup logging
    log_level = "DEBUG" if kwargs.get('verbose') else "INFO"
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting AWS Lambda Assessment Scanner")

    # Load configuration
    config_data = load_config(kwargs.get('config', 'config.yaml'))

    # Override config with CLI arguments
    process_cli_overrides(config_data, **kwargs)

    # Initialize components
    aws_client = AWSClientManager(
        profile=config_data['aws']['profile'],
        default_region=config_data['aws']['default_region']
    )

    lambda_analyzer = LambdaAnalyzer(aws_client)
    runtime_checker = RuntimeChecker()

    # Scan all regions
    regions = config_data['aws']['regions']
    all_results = scan_regions(lambda_analyzer, runtime_checker, regions, logger)

    # Generate report
    report = {
        'scan_timestamp': datetime.utcnow().isoformat(),
        'total_functions': len(all_results),
        'regions_scanned': regions,
        'functions': all_results
    }

    # Save results
    output_file = config_data['output']['file']
    report_format = config_data['output']['format']

    if report_format == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

    # Print summary to STDOUT
    print_summary(all_results, regions)

    logger.info("Scan complete. Found %d Lambda functions across %d regions",
                len(all_results), len(regions))
    logger.info("Report saved to: %s", output_file)


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter
