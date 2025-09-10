# AWS Lambda Assessment Scanner

A comprehensive tool to scan AWS Lambda functions across regions and generate detailed reports on runtime information, versions, sizes, and code complexity.

## Features

- **Multi-region scanning**: Scan Lambda functions across multiple AWS regions
- **Organization support**: Scan all accounts in AWS Organizations with `--org` flag
- **Runtime analysis**: Detect language, version, and AWS support status
- **Complexity assessment**: Estimate lines of code and complexity scores
- **Interactive summary**: Beautiful STDOUT summary with statistics and insights
- **Configuration driven**: Use YAML config files or CLI arguments
- **CI/CD ready**: Supports command-line arguments for automation
- **Perfect code quality**: 10.00/10 pylint score with comprehensive testing

## Quick Start

### Prerequisites

- Python 3.9 or higher
- AWS CLI configured with appropriate credentials
- Required Python packages (see `requirements.txt`)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd aws-lambda-assessment

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Basic Usage

```bash
# Scan using default configuration (sbx profile, us-east-1)
python lambda_scanner.py

# Scan specific profile and region
python lambda_scanner.py --profile my-profile --region us-west-2

# Verbose output
python lambda_scanner.py --verbose

# Custom output file
python lambda_scanner.py --output my-report.json

# Organization scanning (requires management account access)
python lambda_scanner.py --org --profile management-account
```

## Organization Scanning

The `--org` flag enables scanning across all active accounts in an AWS Organization:

### Prerequisites for Organization Scanning
- Must be run from the **AWS Organizations management account**
- Requires the following permissions:
  - `organizations:DescribeOrganization`
  - `organizations:ListAccounts`
- Cross-account access via one of:
  - AWS profiles named with account IDs (e.g., profile `123456789012`)
  - IAM roles for cross-account access (default: `OrganizationAccountAccessRole`)

### Organization Scanning Examples

```bash
# Scan all organization accounts
python lambda_scanner.py --org

# Organization scan with specific profile and region
python lambda_scanner.py --org --profile management-account --region us-east-1

# Verbose organization scanning
python lambda_scanner.py --org --verbose

# Export deprecated runtimes to CSV
python lambda_scanner.py --org --csv deprecated_runtimes.csv
```

### Cross-Account Access Methods

The scanner attempts cross-account access in this order:

1. **Profile-based**: Looks for AWS profiles named with the account ID
2. **Role assumption**: Falls back to assuming `OrganizationAccountAccessRole`

If neither method works, the account is skipped with a warning.

### Organization Scanning Output

When using `--org`, the summary includes additional organization-specific information:

- **Account count**: Total number of organization accounts scanned
- **Account attribution**: Deprecated runtime findings include account numbers for easy identification

Example deprecated runtime output:
```
⚠️  DEPRECATED RUNTIMES DETECTED:
   • aws-controltower-NotificationForwarder (python3.13) in us-east-1 of 018194650040
   • tf-sample-aws-dev-web-app (python3.13) in us-east-1 of 514869215994
   → Consider upgrading these 2 function(s) to supported runtimes
```

## CSV Export for Deprecated Runtimes

The `--csv` option creates a CSV file containing only Lambda functions with deprecated runtimes, making it easy to track and remediate outdated functions across your organization.

### CSV Format

The CSV file includes the following columns:
- **account_number**: AWS account ID
- **region**: AWS region
- **language**: Programming language (e.g., Python, Node.js)
- **language_version**: Language version (e.g., 3.13, 14.x)
- **name**: Lambda function name
- **ARN**: Complete Lambda function ARN

### CSV Export Examples

```bash
# Export deprecated runtimes from single account (auto-generated filename)
python lambda_scanner.py --csv

# Export deprecated runtimes from organization (auto-generated filename)
python lambda_scanner.py --org --csv

# Combine with other options
python lambda_scanner.py --org --region us-east-1 --csv deprecated_runtimes.csv --verbose
```

### Sample CSV Output

```csv
account_number,region,language,language_version,name,ARN
018194650040,us-east-1,Python,3.13,aws-controltower-NotificationForwarder,arn:aws:lambda:us-east-1:018194650040:function:aws-controltower-NotificationForwarder
514869215994,us-east-1,Python,3.13,tf-sample-aws-dev-web-app,arn:aws:lambda:us-east-1:514869215994:function:tf-sample-aws-dev-web-app
```

**Note**: If no deprecated runtimes are found, the CSV file will not be created and a message will be logged.

## Timestamped Output Files

All output files (JSON reports and CSV exports) are automatically prefixed with timestamps and AWS account numbers in the format `YYYYMMDD-HHMMSS-ACCOUNT_ID` to prevent overwrites and enable historical tracking.

### Filename Format Examples

```bash
# Single account scanning
20250910-103547-992382657570_lambda_assessment_report.json
20250910-103547-992382657570_deprecated_runtimes.csv

# Organization scanning (uses management account ID)
20250910-103606-992382657570_lambda_assessment_report.json
20250910-103606-992382657570_deprecated_runtimes.csv

# Custom JSON output filename (CSV uses auto-generated name)
20250910-142530-123456789012_custom_report.json
20250910-142530-123456789012_deprecated_runtimes.csv
```

### Benefits

- **No overwrites**: Each scan creates a unique file with timestamp and account ID
- **Account identification**: Immediately know which AWS account the report belongs to
- **Historical tracking**: Easy to compare scans over time for specific accounts
- **Organization clarity**: When scanning organizations, files are tagged with management account
- **Automation friendly**: Predictable filename patterns for scripts and processing
- **Compliance auditing**: Timestamped and account-tagged evidence of security assessments

## Configuration

### YAML Configuration (`config.yaml`)

```yaml
aws:
  profile: sbx
  default_region: us-east-1
  regions:
    - us-east-1
    - us-west-2
    - eu-west-1

output:
  format: json
  file: lambda_assessment_report.json
  include_timestamp: true

scanning:
  include_code_analysis: true
  max_concurrent_requests: 10
  timeout_seconds: 30
```

### CLI Arguments

All configuration options can be overridden via command line:

```bash
python lambda_scanner.py --help
```

Options:
- `-c, --config`: Configuration file path (default: config.yaml)
- `-p, --profile`: AWS profile to use
- `-r, --region`: AWS region to scan (overrides config)
- `-o, --output`: Output file path
- `-f, --format`: Output format (json|csv)
- `-v, --verbose`: Enable verbose logging
- `--org`: Scan all accounts in AWS Organization (requires management account access)
- `--csv`: Export deprecated runtimes to CSV file (e.g., deprecated_runtimes.csv)

## Report Format

The generated report includes:

### Function-level Information
- **Basic metadata**: Name, runtime, version, size, memory, timeout
- **Runtime analysis**: Language name/version, AWS support status
- **Code complexity**: Estimated lines of code, complexity score
- **Configuration**: Environment variables, layers, VPC config
- **Location**: S3 download URL for function code
- **Organization data**: Account ID and name (when using `--org` flag)

### Report Structure
```json
{
  "scan_timestamp": "2025-09-10T13:53:31.457758",
  "total_functions": 2,
  "regions_scanned": ["us-east-1"],
  "functions": [
    {
      "region": "us-east-1",
      "function_name": "MyFunction",
      "runtime": "python3.9",
      "language_name": "Python",
      "language_version": "3.9",
      "aws_supported": true,
      "support_status": "supported",
      "code_size": 3800,
      "lines_of_code": 76,
      "complexity_score": "low",
      // ... additional fields
    }
  ]
}
```

## Architecture

### Project Structure
```
aws-lambda-assessment/
├── lambda_scanner.py          # Main CLI application
├── config.yaml               # Default configuration
├── modules/                  # Core modules
│   ├── aws_client.py         # AWS session management
│   ├── lambda_analyzer.py    # Lambda function analysis
│   └── runtime_checker.py    # Runtime support checking
├── tests/                    # Unit tests
├── .github/workflows/        # CI/CD workflows
├── .pylintrc                 # Code quality configuration
├── .editorconfig            # Editor configuration
└── requirements.txt         # Python dependencies
```

### Key Components

1. **AWSClientManager**: Handles AWS authentication and client creation
2. **LambdaAnalyzer**: Scans and analyzes Lambda functions
3. **RuntimeChecker**: Determines runtime support status and language info

## Development

### Code Quality

This project maintains high code quality standards:
- **Pylint score**: 10.00/10 (perfect score!)
- **Test coverage**: Comprehensive unit tests (17 tests)
- **Pre-commit hooks**: Automated quality checks
- **CI/CD**: GitHub Actions for testing

### Running Tests

```bash
# Run unit tests
pytest tests/ -v

# Run pylint
pylint lambda_scanner.py modules/ tests/

# Run pre-commit checks
pre-commit run --all-files
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure pylint score remains high
5. Submit a pull request

## Supported Runtimes

The scanner recognizes and analyzes:
- **Python**: 2.7, 3.7-3.12
- **Node.js**: 12.x-20.x
- **Java**: 8, 11, 17, 21
- **.NET**: 6, 8
- **Go**: Custom runtimes
- **Ruby**: 3.2
- **Custom runtimes**: provided, provided.al2, provided.al2023

## License

[Add your license information here]

## Support

For issues and questions:
1. Check the [Issues](../../issues) page
2. Review the documentation
3. Submit a new issue with detailed information
