# APEX Testing Directory Structure

This directory contains all APEX JWT authentication related files, tests, and documentation for Apache Superset.

## Directory Organization

```
tests/integration_tests/apex-testing/
├── docs/                              # English documentation
│   ├── README.md                      # Main documentation
│   └── IMPLEMENTATION_SUMMARY.md     # Technical implementation details
├── tests/                             # Test suites
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   └── test_jwt_auth.py          # JWT authentication unit tests
│   └── integration/                   # Integration tests
│       ├── __init__.py
│       ├── test_comprehensive_api.py  # Comprehensive API tests
│       └── test_real_api.py          # Real-world API tests
├── notes/                             # Learning notes and documentation
│   ├── README.md                      # Notes overview
│   ├── technical-implementation-details.md
│   ├── superset-initialization-process.md
│   ├── troubleshooting-guide.md
│   └── initialization-script.sh      # Setup script
├── comprehensive_test_suite.py        # Complete test suite (43 tests)
├── comprehensive_test_report.json     # Latest test results
├── run_tests.py                       # Test runner
├── conftest.py                        # Pytest configuration
├── demo_apex_jwt_auth.py             # Demo script
├── APEX_IMPLEMENTATION_SUMMARY.md    # Original implementation summary
├── PROJECT_SUMMARY.md                # Final project summary
└── DIRECTORY_STRUCTURE.md           # This file
```

## Test Execution

Run tests from this directory:
```bash
# Run all tests
python run_tests.py

# Run comprehensive test suite
python comprehensive_test_suite.py

# Run specific test files
python -m pytest tests/unit/test_jwt_auth.py
python -m pytest tests/integration/test_comprehensive_api.py
```

## Features Covered

- JWT header authentication implementation
- Swagger UI anonymous access
- Comprehensive API testing (Charts, Dashboards, Datasets, etc.)
- Unit tests with 97.7% success rate
- Integration tests for real-world scenarios
- Performance and error handling tests

## Location

This directory is located in the standard Superset integration tests directory:
`tests/integration_tests/apex-testing/`

This follows Superset's testing conventions and makes it easy to find and run APEX-related tests alongside other integration tests. 