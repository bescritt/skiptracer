"""Full-stack integration test: drive the menu chain (intro -> email submenu
-> plugin dispatch) with mocked input + HTTP, proving the UI and plugin layer
wire together end-to-end.
"""

import builtins as bi

import pytest
import requests
from requests.models import Response

from skiptracer.menus.default_menus import DefaultMenus
from skiptracer.plugins.base import PageGrabber


GENERIC_HTML = (
    "<html><body>"
    "<div class='cname'>Test Name</div>"
    "<a href='https://example.com'>x</a>"
    "<script type='application/ld+json'>"
    '{"@type":"Person","name":"Test","@id":"https://x/1",'
    '"address":[{"@type":"PostalAddress","streetAddress":"1 St",'
    '"addressLocality":"Town","addressRegion":"CA","postalCode":"90001"}]}'
    "</script>"
    "</body></html>"
)


class _StopFlow(Exception):
    """Raised to break the menu's re-display loop after one dispatch."""


def _fake_response(*args, **kwargs):
    r = Response()
    r.status_code = 200
    r._content = GENERIC_HTML.encode('utf-8')
    return r


def test_intro_to_email_to_plugin_dispatch(monkeypatch):
    """Select 'email' (2), then a plugin (1), feed a search string, and
    confirm a plugin's get_info is reached without error."""
    from skiptracer.skiptracer import SkipTracer
    from skiptracer.plugins.base import PageGrabber

    monkeypatch.setattr(requests, 'get', _fake_response)
    monkeypatch.setattr(requests, 'post', _fake_response)
    monkeypatch.setattr(requests.Session, 'get',
                        lambda self, *a, **k: _fake_response())
    monkeypatch.setattr(requests.Session, 'post',
                        lambda self, *a, **k: _fake_response())
    monkeypatch.setattr(PageGrabber, 'get_source',
                        lambda self, url: GENERIC_HTML)

    calls = iter(['2', '1', 'a@b.com'])  # intro=email, submenu=plugin[0], query

    def fake_input(*a, **k):
        try:
            return next(calls)
        except StopIteration:
            # The menu re-displays after dispatch; break the loop.
            raise _StopFlow()

    monkeypatch.setattr(bi, 'input', fake_input)

    # Track that a plugin's get_info actually executes.
    executed = {}

    def spy_get_info(self, value, lookup):
        executed[(self.__class__.__name__, lookup)] = value
        return {}

    from skiptracer.plugins.base import PageGrabber
    plugins = SkipTracer.load_plugins('skiptracer.plugins')
    for cls in plugins.values():
        if hasattr(cls, 'get_info'):
            monkeypatch.setattr(cls, 'get_info', spy_get_info)

    dm = DefaultMenus(SkipTracer.load_plugins('skiptracer.plugins'))
    try:
        dm.intromenu()
    except _StopFlow:
        pass

    assert executed, "no plugin get_info was invoked by the menu chain"
