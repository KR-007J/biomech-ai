"""
Test configuration and fixtures - Phase 3 Testing Framework

Provides common fixtures and configuration for all pytest tests.
"""

import asyncio
import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from async_tasks import TaskManager
from cache import CacheManager
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test to prevent cross-test contamination"""
    from main import limiter

    # Clear the rate limiter state before the test
    limiter.reset()
    yield
    # Also reset after the test
    limiter.reset()


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch("main.supabase") as mock:
        mock.table.return_value.insert.return_value.execute.return_value = None
        mock.table.return_value.upsert.return_value.execute.return_value = None
        mock.table.return_value.select.return_value.execute.return_value = {"data": []}
        yield mock


@pytest.fixture
def mock_cache():
    """Mock cache manager"""
    cache = CacheManager()
    cache.redis_enabled = False  # Force in-memory mode for testing
    return cache


@pytest.fixture
def mock_task_manager():
    """Mock task manager"""
    return TaskManager(max_workers=2)


@pytest.fixture
def sample_metrics_data():
    """Sample biomechanical metrics"""
    return {
        "angles": {"knee": 85.3, "hip": 92.1, "ankle": 88.5, "elbow": 120.2},
        "deviations": {"knee": 5.2, "hip": 2.1, "ankle": 3.8, "elbow": 8.9},
        "pose_confidence": 0.95,
        "ideal_ranges": {"knee": {"min": 80, "max": 90}, "hip": {"min": 85, "max": 95}},
    }


@pytest.fixture
def sample_feedback_request(sample_metrics_data):
    """Sample feedback request"""
    return {
        "metrics": sample_metrics_data,
        "exercise_type": "squat",
        "user_id": "test-user-123",
        "session_id": "session-456",
    }


@pytest.fixture
def sample_profile():
    """Sample user profile"""
    return {
        "id": "user-123",
        "name": "John Doe",
        "email": "john@example.com",
        "picture": "https://example.com/pic.jpg",
        "stats": {"workouts": 42, "time_invested": 3600},
    }


@pytest.fixture
def sample_session():
    """Sample workout session"""
    return {
        "user_id": "user-123",
        "exercise": "squat",
        "reps": 20,
        "score": 87.5,
        "duration": 45.3,
    }


# Markers for organization
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "async_test: async tests")
