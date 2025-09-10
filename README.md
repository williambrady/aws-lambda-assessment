# AWS Lambda Assessment Scanner

A comprehensive tool to scan AWS Lambda functions across regions and generate detailed reports on runtime information, versions, sizes, and code complexity.

## Features

- **Multi-region scanning**: Scan Lambda functions across multiple AWS regions
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
```

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

## Report Format

The generated report includes:

### Function-level Information
- **Basic metadata**: Name, runtime, version, size, memory, timeout
- **Runtime analysis**: Language name/version, AWS support status
- **Code complexity**: Estimated lines of code, complexity score
- **Configuration**: Environment variables, layers, VPC config
- **Location**: S3 download URL for function code

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
