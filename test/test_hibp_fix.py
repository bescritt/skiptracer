"""Targeted tests for the HIBP plugin fix:
  1. HTTP 401 returns structured auth_error result (not crash)
  2. HTTP 404 returns no_breaches result
  3. HTTP 200 with valid JSON returns breach data
  4. The backward-compatible class alias works
  5. _make_scraper returns a Session (not cfscrape crash)
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from skiptracer.plugins.haveibeenpwned import (
    HaveIBeenPwnedGrabber,
    HaveIBeenPwwnedGrabber,  # backward-compatible alias
    _make_scraper,
)


@pytest.fixture
def grabber():
    g = HaveIBeenPwnedGrabber()
    g.env = {"HAVEIBEENPWNED_API_KEY": "test-key"}
    g.info_dict = {}
    return g


def test_backward_compatible_alias():
    """The old misspelled class name must still resolve to the new one."""
    assert HaveIBeenPwwnedGrabber is HaveIBeenPwnedGrabber


def test_make_scraper_returns_session():
    """_make_scraper must return a requests.Session (not crash on cfscrape)."""
    session = _make_scraper()
    assert session is not None
    assert session.__class__.__name__ == "Session"


def test_hibp_401_returns_auth_error(grabber):
    """HTTP 401 must return structured auth_error, not crash."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Bad API key"
    mock_session.get.return_value = mock_response

    with patch(
        "skiptracer.plugins.haveibeenpwned._make_scraper",
        return_value=mock_session,
    ):
        result = grabber.get_info("test@example.com", None)

    assert result is not None
    assert result.get("hibp", {}).get("status") == "auth_error"
    assert result["hibp"]["http_status"] == 401


def test_hibp_404_returns_no_breaches(grabber):
    """HTTP 404 must return no_breaches status."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    with patch(
        "skiptracer.plugins.haveibeenpwned._make_scraper",
        return_value=mock_session,
    ):
        result = grabber.get_info("test@example.com", None)

    assert result is not None
    assert result.get("hibp", {}).get("status") == "no_breaches"


def test_hibp_200_parses_breaches(grabber):
    """HTTP 200 must parse JSON and return breach data."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "Title": "TestBreach",
            "Domain": "example.com",
            "BreachDate": "2023-01-01",
            "DataClasses": ["email", "password"],
        }
    ]
    mock_session.get.return_value = mock_response

    with patch(
        "skiptracer.plugins.haveibeenpwned._make_scraper",
        return_value=mock_session,
    ):
        result = grabber.get_info("test@example.com", None)

    assert result is not None
    assert "BreachDate" in result
    assert result["Title"] == "TestBreach"
    assert result["Domain"] == "example.com"


def test_hibp_403_returns_rate_limited(grabber):
    """HTTP 403 must return rate_limited status."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_session.get.return_value = mock_response

    with patch(
        "skiptracer.plugins.haveibeenpwned._make_scraper",
        return_value=mock_session,
    ):
        result = grabber.get_info("test@example.com", None)

    assert result is not None
    assert result.get("hibp", {}).get("status") == "rate_limited"
