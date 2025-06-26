"""
Test configuration module to handle paths and environment-specific settings.
"""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
FEATURES_DIR = os.environ.get("BDD_FEATURES_DIR", str(PROJECT_ROOT / "features"))
TEST_DATA_DIR = os.environ.get(
    "BDD_TEST_DATA_DIR", str(PROJECT_ROOT / "features" / "test_data")
)


def get_feature_path(feature_file):
    """
    Get the path to a feature file, respecting environment configuration.

    Args:
        feature_file: The name of the feature file or relative path within the features directory

    Returns:
        Path: The full path to the feature file
    """
    return Path(FEATURES_DIR) / feature_file


def get_test_data_path(filename):
    """
    Get the path to a test data file, respecting environment configuration.

    Args:
        filename: The name of the test data file

    Returns:
        Path: The full path to the test data file
    """
    return Path(TEST_DATA_DIR) / filename
