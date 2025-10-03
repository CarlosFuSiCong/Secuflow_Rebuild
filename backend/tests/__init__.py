"""
Secuflow Backend Test Suite

This package contains all tests for the Secuflow backend application.
Tests are organized by module and functionality for better maintainability.

Test Structure:
- unit/: Unit tests for individual components
- integration/: Integration tests for module interactions
- api/: API endpoint tests
- fixtures/: Test data and fixtures
- utils/: Test utilities and helpers

Usage:
    # Run all tests
    python manage.py test tests

    # Run specific test module
    python manage.py test tests.unit.test_accounts

    # Run with coverage
    coverage run --source='.' manage.py test tests
    coverage report
"""
