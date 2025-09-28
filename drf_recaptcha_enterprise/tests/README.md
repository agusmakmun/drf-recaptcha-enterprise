# Unit Tests for drf_recaptcha_enterprise

This directory contains comprehensive unit tests for the `drf_recaptcha_enterprise` package. The tests are designed to run without Django dependencies and focus on testing the core functionality of the package.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and fixtures
├── test_client.py           # Tests for client.py module
├── test_fields.py           # Tests for fields.py module
├── test_serializers.py      # Tests for serializers.py module
├── test_validators.py       # Tests for validators.py module
├── test_utils.py            # Tests for utility functions
└── README.md               # This file
```

## Running Tests

### Using the test runner script (recommended)

```bash
# From the project root
python run_tests.py
```

### Using pytest directly

```bash
# From the project root
pytest drf_recaptcha_enterprise/tests/ -v

# With coverage
pytest drf_recaptcha_enterprise/tests/ -v --cov=drf_recaptcha_enterprise --cov-report=html

# Run only unit tests (skip integration tests)
pytest drf_recaptcha_enterprise/tests/ -v -m "not integration"

# Run specific test file
pytest drf_recaptcha_enterprise/tests/test_client.py -v
```

### Using virtual environment

```bash
# Activate virtual environment first
source ../bin/activate

# Then run tests
python run_tests.py
```

## Test Coverage

The tests aim for comprehensive coverage of:

- **Client Module (`test_client.py`)**:
  - Credentials loading and validation
  - Project ID extraction from various sources
  - Google Cloud authentication checking
  - reCAPTCHA Enterprise client initialization
  - Assessment creation and token verification
  - Error handling and edge cases

- **Fields Module (`test_fields.py`)**:
  - Field initialization with various parameters
  - Token validation with different scenarios
  - Request context handling (IP, user agent)
  - Error message generation
  - Verification result storage and retrieval

- **Serializers Module (`test_serializers.py`)**:
  - Serializer initialization and configuration
  - Mixin functionality
  - Field addition and customization
  - Verification result retrieval
  - Inheritance and composition patterns

- **Validators Module (`test_validators.py`)**:
  - Validator initialization and configuration
  - Token validation with various scenarios
  - Request context handling
  - Error message generation
  - Integration with DRF field validators

- **Utility Functions (`test_utils.py`)**:
  - Mock object creation helpers
  - Test data generation utilities
  - Request and field mocking utilities

## Test Fixtures

The `conftest.py` file provides comprehensive fixtures for:

- **Mock Objects**: Google Cloud credentials, reCAPTCHA assessments, Django requests
- **Test Data**: Valid/invalid tokens, verification results, credentials files
- **Environment Setup**: Mock environment variables, temporary files
- **Utility Functions**: Helper functions for creating test data

## Mocking Strategy

The tests use extensive mocking to isolate the code under test:

- **Google Cloud APIs**: All external API calls are mocked
- **Django Components**: Request objects, settings, and DRF components are mocked
- **File System**: Temporary files are used for credentials testing
- **Environment Variables**: Environment variables are mocked for testing

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests (default)
- `@pytest.mark.integration`: Integration tests (skipped by default)
- `@pytest.mark.slow`: Slow tests
- `@pytest.mark.requires_credentials`: Tests requiring real credentials

## Coverage Requirements

- **Minimum Coverage**: 80%
- **Branch Coverage**: Enabled
- **Coverage Reports**: Terminal, HTML, and XML formats
- **Excluded**: Test files, migrations, and third-party code

## Continuous Integration

The tests are designed to run in CI environments without external dependencies:

- No real Google Cloud credentials required
- No Django database setup required
- All external services are mocked
- Tests run in isolated environments

## Adding New Tests

When adding new tests:

1. **Follow naming conventions**: `test_*.py` for test files, `test_*` for test functions
2. **Use appropriate fixtures**: Leverage existing fixtures from `conftest.py`
3. **Mock external dependencies**: Don't make real API calls in unit tests
4. **Add appropriate markers**: Mark tests with `@pytest.mark.unit` or other relevant markers
5. **Maintain coverage**: Ensure new code is covered by tests
6. **Document complex tests**: Add docstrings for complex test scenarios

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in the Python path
2. **Mock Failures**: Check that mocks are properly configured and called
3. **Coverage Issues**: Verify that all code paths are tested
4. **Environment Issues**: Use the virtual environment activation command

### Debug Mode

Run tests with verbose output for debugging:

```bash
pytest drf_recaptcha_enterprise/tests/ -v -s --tb=long
```

### Test Specific Functionality

```bash
# Test only client functionality
pytest drf_recaptcha_enterprise/tests/test_client.py -v

# Test specific test method
pytest drf_recaptcha_enterprise/tests/test_client.py::TestReCaptchaEnterpriseClient::test_init_with_all_parameters -v
```
