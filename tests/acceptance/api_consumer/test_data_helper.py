"""
Helper functions for working with test data files
"""

from pathlib import Path


def get_test_data_path(filename):
    """
    Get the path to a test data file
    """
    # Go up three directory levels from the test file to reach the project root,
    # then find the test data under features/test_data/
    return (
        Path(__file__).parent.parent.parent.parent / "features" / "test_data" / filename
    )
