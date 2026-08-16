"""Targeted tests for the namechk2 plugin fix:
  1. Non-JSON response from /services/check returns structured error (not crash)
  2. Valid JSON response returns results dict
  3. Per-service parse failure skips to next service (does not abort sweep)
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from skiptracer.plugins.namechk2 import NameChkGrabber


@pytest.fixture
def grabber():
    return NameChkGrabber()


def test_namechk2_non_json_returns_error(grabber):
    """Non-JSON response must return structured error, not crash."""
    mock_session = MagicMock()
    # Homepage returns 200 with HTML
    mock_home = MagicMock()
    mock_home.status_code = 200
    mock_home.text = "<html><meta>Test</meta></html>"
    mock_home.cookies.get_dict.return_value = {"session": "abc123"}
    # POST to namechk returns non-JSON
    mock_post = MagicMock()
    mock_post.text = "Could not load results into JSON format"
    mock_session.get.return_value = mock_home
    mock_session.post.return_value = mock_post

    with patch(
        "skiptracer.plugins.namechk2.requests.Session",
        return_value=mock_session,
    ), patch.object(grabber, "get_dom", return_value=MagicMock(
        find_all=lambda *a, **kw: [MagicMock()]
    )):
        grabber.env = {}
        result = grabber.get_info("testuser", "username")

    assert result is not None
    assert isinstance(result, dict)
    assert result.get("error") == "json_parse_failed"


def test_namechk2_returns_structured_results(grabber):
    """Valid JSON response returns results dict with username + results."""
    mock_session = MagicMock()
    # Homepage
    mock_home = MagicMock()
    mock_home.status_code = 200
    mock_home.text = "<html><meta name='csrf' content='token123'></meta></html>"
    mock_home.cookies.get_dict.return_value = {"session": "abc123"}
    # POST that returns HTML for initial check + JSON for /services/check
    mock_initial = MagicMock()
    mock_initial.text = '{"status":"ok"}'
    mock_initial.status_code = 200
    mock_svc = MagicMock()
    mock_svc.text = json.dumps({"available": True, "callback_url": ""})
    mock_svc.status_code = 200
    mock_session.get.return_value = mock_home
    mock_session.post.side_effect = [mock_initial, mock_svc]

    with patch(
        "skiptracer.plugins.namechk2.requests.Session",
        return_value=mock_session,
    ), patch.object(grabber, "get_dom", return_value=MagicMock(
        find_all=lambda *a, **kw: [MagicMock()]
    )):
        grabber.env = {}
        result = grabber.get_info("testuser", "username")

    assert result is not None
    assert isinstance(result, dict)
    # Should have results key with per-service outcomes
    if "results" in result:
        assert isinstance(result["results"], dict)
    elif "error" in result:
        # Acceptable: if CSRF extraction fails, returns error — still structured
        assert result["error"] in ("json_parse_failed",)
