"""
Helper functions for working with test data files
"""

from tests.config import get_test_data_path as _get_test_data_path


def get_test_data_path(filename):
    """
    Get the path to a test data file using centralized configuration
    """
    return _get_test_data_path(filename)
