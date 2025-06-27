"""
Test configuration module to handle paths and environment-specific settings.
"""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
FEATURES_DIR = os.environ.get("BDD_FEATURES_DIR", str(PROJECT_ROOT / "features"))
# Legacy: Only used when BDD_TEST_DATA_DIR environment variable is set
TEST_DATA_DIR = os.environ.get("BDD_TEST_DATA_DIR")


def get_feature_path(feature_file):
    """
    Get the path to a feature file, respecting environment configuration.

    Args:
        feature_file: The name of the feature file or relative path within the features directory

    Returns:
        Path: The full path to the feature file
    """
    return Path(FEATURES_DIR) / feature_file


def get_test_data_path(filename, feature_category=None):
    """
    Get the path to a test data file, supporting multiple feature categories.

    Args:
        filename: The name of the test data file
        feature_category: Optional category (api-consumer, evaluation, developer, operational)

    Returns:
        Path: The full path to the test data file
    """
    # If category specified, use it directly
    if feature_category:
        return Path(FEATURES_DIR) / feature_category / "test_data" / filename
    
    # Check environment variable first for backward compatibility
    if TEST_DATA_DIR:
        return Path(TEST_DATA_DIR) / filename
    
    # Search all feature categories for the file
    categories = ["api-consumer", "evaluation", "developer", "operational"]
    for category in categories:
        path = Path(FEATURES_DIR) / category / "test_data" / filename
        if path.exists():
            return path
    
    # Fallback to api-consumer for backward compatibility
    return Path(FEATURES_DIR) / "api-consumer" / "test_data" / filename
