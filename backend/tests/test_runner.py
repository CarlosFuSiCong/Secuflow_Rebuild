"""
Custom test runner and utilities for the Secuflow test suite.
"""

import os
import sys
from django.test.runner import DiscoverRunner
from django.conf import settings


class SecuflowTestRunner(DiscoverRunner):
    """Custom test runner for Secuflow with enhanced features."""
    
    def __init__(self, **kwargs):
        """Initialize the test runner."""
        super().__init__(**kwargs)
        
        # Set up test-specific settings
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up the test environment."""
        # Disable logging during tests unless explicitly enabled
        if not os.environ.get('ENABLE_TEST_LOGGING'):
            import logging
            logging.disable(logging.CRITICAL)
        
        # Set test-specific settings
        settings.TNM_OUTPUT_DIR = '/tmp/test_tnm_output'
        settings.TNM_REPOSITORIES_DIR = '/tmp/test_tnm_repositories'
        
        # Ensure test directories exist
        os.makedirs(settings.TNM_OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.TNM_REPOSITORIES_DIR, exist_ok=True)
    
    def run_tests(self, test_labels, **kwargs):
        """Run the test suite."""
        # If no test labels provided, run all tests in the tests package
        if not test_labels:
            test_labels = ['tests']
        
        return super().run_tests(test_labels, **kwargs)
    
    def teardown_test_environment(self, **kwargs):
        """Clean up after tests."""
        super().teardown_test_environment(**kwargs)
        
        # Clean up test directories
        import shutil
        for directory in [settings.TNM_OUTPUT_DIR, settings.TNM_REPOSITORIES_DIR]:
            if os.path.exists(directory):
                shutil.rmtree(directory, ignore_errors=True)


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    try:
        import coverage
    except ImportError:
        print("Coverage package not installed. Install with: pip install coverage")
        sys.exit(1)
    
    # Start coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'test', 'tests'])
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*50)
    print("COVERAGE REPORT")
    print("="*50)
    cov.report()
    
    # Generate HTML report
    cov.html_report(directory='htmlcov')
    print(f"\nHTML coverage report generated in: htmlcov/index.html")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--coverage':
        run_tests_with_coverage()
    else:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'test', 'tests'] + sys.argv[1:])
