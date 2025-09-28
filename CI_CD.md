# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) setup for the `drf-recaptcha-enterprise` package.

## 🚀 Workflows Overview

### 1. Main CI Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**

#### `test` Job
- **Matrix Strategy**: Tests across Python 3.10, 3.11, 3.12 and Django 3.2, 4.0, 4.1, 4.2, 5.0
- **Quality Checks**:
  - Code linting with flake8
  - Code formatting with black
  - Import sorting with isort
  - Type checking with mypy
- **Testing**:
  - Unit tests with pytest
  - Coverage reporting (minimum 80%)
  - Custom test runner execution
- **Artifacts**: Test results and coverage reports

#### `unit-tests-only` Job
- **Purpose**: Fast unit test execution without Django matrix
- **Python Versions**: 3.10, 3.11, 3.12
- **Coverage Requirement**: 95% minimum
- **Focus**: Pure unit tests as requested

#### `security` Job
- **Security Checks**:
  - Dependency vulnerability scanning with safety
  - Code security analysis with bandit
- **Artifacts**: Security reports

#### `performance` Job
- **Performance Testing**:
  - Test execution time monitoring
  - Slowest test identification
- **Metrics**: Test duration analysis

#### `build` Job
- **Triggers**: Only on push to `main` branch
- **Dependencies**: All previous jobs must pass
- **Actions**:
  - Package building with build
  - Package validation with twine
  - Artifact upload for distribution

### 2. Pull Request Validation (`.github/workflows/pr-validation.yml`)

**Purpose**: Comprehensive validation for pull requests

**Features:**
- Multi-Python version testing (3.10, 3.11, 3.12)
- Code quality checks
- Unit test execution
- Coverage reporting (95% minimum)
- Automated PR comments with test results
- Security validation

### 3. Release Automation (`.github/workflows/release.yml`)

**Triggers:**
- Git tags (e.g., `v1.0.0`)
- Manual workflow dispatch

**Process:**
1. **Testing**: Full test suite across Python versions
2. **Building**: Package creation and validation
3. **Publishing**: Automatic PyPI upload
4. **Release**: GitHub release creation with detailed changelog

### 4. Dependabot Integration (`.github/workflows/dependabot.yml`)

**Features:**
- Automatic dependency updates
- Auto-merge for patch and minor updates
- Manual review for major updates
- Automated testing for dependency changes

### 5. CodeQL Security Analysis (`.github/workflows/codeql.yml`)

**Purpose**: Static code analysis for security vulnerabilities

**Features:**
- Automated security scanning
- Weekly scheduled runs
- Pull request analysis
- Security alerts and notifications

### 6. Dependency Review (`.github/workflows/dependency-review.yml`)

**Purpose**: Review dependency changes in pull requests

**Features:**
- Vulnerability detection in new dependencies
- License compliance checking
- Security policy enforcement

## 📋 Requirements Files

### `requirements.txt`
Core package dependencies:
- Django >= 3.2
- Django REST Framework >= 3.12
- Google Cloud reCAPTCHA Enterprise >= 1.0.0
- Requests >= 2.25.0

**Note**: This file also includes development dependencies for convenience.

### `requirements-dev.txt`
Development and testing dependencies:
- Includes all core dependencies via `-r requirements.txt`
- Testing tools (pytest, pytest-django, pytest-cov)
- Code quality tools (black, flake8, isort, mypy)
- Security tools (safety, bandit)
- Additional testing utilities (pytest-xdist, pytest-mock)

## 🧪 Test Configuration

### Test Structure
```
drf_recaptcha_enterprise/tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_client.py           # Client module tests
├── test_fields.py           # Fields module tests
├── test_serializers.py      # Serializers module tests
├── test_validators.py       # Validators module tests
├── test_utils.py            # Utility functions tests
└── README.md                # Test documentation
```

### Test Execution
- **Total Tests**: 119 tests (118 passed, 1 skipped)
- **Coverage**: 97% (314 lines, 10 missing)
- **Execution Time**: ~12 seconds
- **Pure Unit Tests**: No Django runtime dependencies

### Test Commands
```bash
# Run all tests
python run_tests.py

# Run with pytest directly
pytest drf_recaptcha_enterprise/tests/ -v

# Run with coverage
pytest drf_recaptcha_enterprise/tests/ --cov=drf_recaptcha_enterprise --cov-report=html
```

## 🔧 Configuration Files

### `pytest.ini`
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = drf_recaptcha_enterprise.tests.conftest
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --cov=drf_recaptcha_enterprise
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
markers =
    integration: marks tests as integration tests
    slow: marks tests as slow running
```

### `.coveragerc`
```ini
[run]
source = drf_recaptcha_enterprise
omit = 
    */tests/*
    */migrations/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## 🚀 Deployment Process

### 1. Development Workflow
1. Create feature branch from `develop`
2. Make changes and write tests
3. Run local tests: `python run_tests.py`
4. Create pull request
5. Automated validation runs
6. Code review and approval
7. Merge to `develop`

### 2. Release Workflow
1. Merge `develop` to `main`
2. Create and push version tag: `git tag v1.0.0 && git push origin v1.0.0`
3. Automated release process:
   - Full test suite execution
   - Package building and validation
   - PyPI publication
   - GitHub release creation

### 3. Dependency Updates
- **Weekly**: Dependabot checks for updates
- **Automatic**: Patch and minor updates auto-merged
- **Manual**: Major updates require review

## 📊 Quality Metrics

### Code Quality
- **Linting**: flake8 with strict rules
- **Formatting**: black with 88-character line length
- **Imports**: isort for consistent import ordering
- **Types**: mypy for static type checking

### Test Quality
- **Coverage**: 97% (exceeds 80% requirement)
- **Test Types**: Pure unit tests (no Django runtime)
- **Mocking**: Comprehensive external service mocking
- **Fixtures**: Reusable test data and mock objects

### Security
- **Dependencies**: Safety vulnerability scanning
- **Code**: Bandit security analysis
- **Static Analysis**: CodeQL security scanning
- **Dependency Review**: Automated dependency change review
- **Updates**: Automated dependency updates

## 🔍 Monitoring and Alerts

### GitHub Actions
- **Status Checks**: Required for all PRs
- **Notifications**: Email alerts for failures
- **Artifacts**: Test results and coverage reports

### Codecov
- **Coverage Tracking**: Historical coverage trends
- **PR Comments**: Coverage change notifications
- **Quality Gates**: Minimum coverage enforcement

## 🛠 Local Development

### Setup
```bash
# Clone repository
git clone <repository-url>
cd drf-recaptcha-enterprise

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python run_tests.py
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 📈 Performance Optimization

### CI/CD Optimizations
- **Parallel Jobs**: Matrix strategy for faster execution
- **Caching**: pip dependency caching
- **Artifacts**: Build artifact reuse
- **Conditional Jobs**: Skip unnecessary steps

### Test Optimizations
- **Pure Unit Tests**: No Django runtime overhead
- **Mocking**: External service mocking for speed
- **Fixtures**: Efficient test data setup
- **Parallel Execution**: pytest-xdist for parallel test runs

## 🔧 Troubleshooting

### Common Issues

#### Test Failures
```bash
# Run specific test file
pytest drf_recaptcha_enterprise/tests/test_client.py -v

# Run with debugging
pytest drf_recaptcha_enterprise/tests/ -v -s --tb=long

# Check coverage
pytest drf_recaptcha_enterprise/tests/ --cov=drf_recaptcha_enterprise --cov-report=term-missing
```

#### CI/CD Failures
1. **Check GitHub Actions logs** for detailed error messages
2. **Verify dependencies** in requirements files
3. **Test locally** with same Python version
4. **Check code quality** tools (black, flake8, isort, mypy)

#### Coverage Issues
```bash
# Generate detailed coverage report
pytest drf_recaptcha_enterprise/tests/ --cov=drf_recaptcha_enterprise --cov-report=html
open htmlcov/index.html
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
