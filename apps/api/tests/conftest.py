"""Pytest configuration and fixtures.

TODO: Implement the following fixtures:
- async_client: Async HTTP test client
- db_session: Test database session
- test_user: Pre-configured test user
"""

import pytest


@pytest.fixture
def sample_data():
    """Sample data for tests."""
    return {"test": "data"}
