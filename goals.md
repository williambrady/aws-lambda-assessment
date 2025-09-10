**Script Goals**

For each AWS region, scan all lambdas and return the following information:
- lambda name
- lambda runtime
    - language name
    - language version
    - currently supported by aws?
- lambda version
- lambda size
- lambda complexity (number of lines of code)

**Coding Goals**

- Configuration driven script that reads values from `config.yaml` and also accepts all the same values from CLI for portability to CICD.
- Configuration will support aws_profile of `sbx` and aws_default_region of `us-east-1`.
- If the script becomes too complex, break it into modules under a modules/ directory.
- Create a .pylintrc file to exclude C0301 for long lines.
- All scripts and modules should be tested with pylint and any warnings should be resolved.
- Create a .editorconfig file to enforce 120 character line length, 2 space tabs, UTF-8 encoding, and LF line endings.
- Create a github workflow to run pylint and unit tests on every push request.
- Create a pre-commit hook to run pylint and unit tests before every commit.
- Update .gitignore to include:
    - all build and python environment files
    - all generated report files
- once all testing is complete, update documentation.
