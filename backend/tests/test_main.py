import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app

client = TestClient(app)


def test_get_health():
    """
    Tests the /health endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_stats():
    """
    Tests the /stats endpoint.
    """
    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json() == {"cloned_repos_count": 0}


def test_post_analyze_invalid_url(mocker):
    """
    Tests the /analyze endpoint with a URL that will fail to clone.
    We mock the cloner to raise an exception.
    """
    # Mock the clone_repo function to simulate a GitCommandError
    mocker.patch(
        "app.services.analysis_service.clone_repo",
        side_effect=HTTPException(status_code=400, detail="Failed to clone")
    )

    response = client.post("/analyze", json={"url": "invalid-url"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to clone"}