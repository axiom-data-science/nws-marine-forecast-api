import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test to run only when integration testing",
    )


def pytest_addoption(parser):
    """Adds --integration option to pytest."""
    parser.addoption(
        '--integration',
        action='store_true',
        default=False,
        help='Run integration tests.',
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skipper = pytest.mark.skip(
            reason="Only run when --integration is given"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skipper)
