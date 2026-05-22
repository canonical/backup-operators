# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm tests."""


def pytest_addoption(parser):
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption("--charm-file", action="append")
    parser.addoption("--base", action="store", default="ubuntu@24.04")
    parser.addoption("--model", action="store")
    parser.addoption("--use-existing", action="store_true")
    parser.addoption("--keep-models", action="store_true")
