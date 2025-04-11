import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skip-model", action="store_true", default=False, help="skip tests requiring a model"
    )
    parser.addoption(
        "--only-model", action="store_true", default=False, help="only run tests requiring a model"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "model: mark test as needing model to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-model"):
        skip_model = pytest.mark.skip(reason="skipping model tests with --skip-model option")
        for item in items:
            if "model" in item.keywords:
                item.add_marker(skip_model)

    if config.getoption("--only-model"):
        skip_non_model = pytest.mark.skip(reason="skipping non-model tests with --only-model option")
        for item in items:
            if "model" not in item.keywords:
                item.add_marker(skip_non_model)
