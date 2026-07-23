"""Test fixtures for the identity platform."""

import uuid

import pytest


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "password": "TestPass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_workspace_data():
    """Sample workspace creation data."""
    return {
        "name": "Test Workspace",
        "description": "A test workspace",
    }


@pytest.fixture
def sample_project_data():
    """Sample project creation data."""
    return {
        "name": "Test Project",
        "description": "A test project",
        "color": "#6366f1",
    }
