"""
Global pytest configuration for the document matching project.
"""

import pytest  # noqa: F401 - used in pytest hooks below


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-wip",
        action="store_true",
        default=False,
        help="run work-in-progress tests (skipped by default)",
    )


def pytest_configure(config):
    """Configure pytest based on command line options."""
    # If --run-wip is specified, remove the default marker expression that skips WIP tests
    if config.getoption("--run-wip"):
        # Clear the default addopts that skip WIP tests
        markexpr = getattr(config.option, "markexpr", None)
        if markexpr == "not wip":
            config.option.markexpr = None
