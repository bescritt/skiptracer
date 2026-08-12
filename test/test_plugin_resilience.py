"""Resilience integration tests: every registered plugin must either run
end-to-end against deterministic HTML, or fail in a clean, catchable way
(interactive prompts belong to that second category).

Mission-Critical guarantee: a single plugin must never produce an
*unhandled* crash (TypeError/AttributeError/IndexError/NameError) when a
site's markup changes. Interactive input prompts (OSError on a closed
stdin) are an accepted, expected boundary.
"""

import builtins as bi

import pytest
import requests
from requests.models import Response

from skiptracer.skiptracer import SkipTracer
from skiptracer.plugins.base import PageGrabber


PLUGINS = [
    'fouroneone_info', 'haveibeenpwned', 'knowem', 'linkedin',
    'myspace', 'namechk2', 'plate', 'tinder', 'true_people',
    'truthfinder', 'twitter', 'who_call_id', 'whoismind',
    'advance_background_checks',
]

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

# Acceptable, expected failure modes for a headless run
ACCEPTED = (OSError, NotImplementedError)


@pytest.fixture
def plugins(monkeypatch):
    def fake_response(*args, **kwargs):
        r = Response()
        r.status_code = 200
        r._content = GENERIC_HTML.encode('utf-8')
        return r

    # Patch every requests entry point the plugins might use, plus the
    # framework's get_source, so the suite never touches the network.
    monkeypatch.setattr(requests, 'get', fake_response)
    monkeypatch.setattr(requests, 'post', fake_response)
    monkeypatch.setattr(requests.Session, 'get', lambda self, *a, **k: fake_response())
    monkeypatch.setattr(requests.Session, 'post', lambda self, *a, **k: fake_response())
    monkeypatch.setattr(PageGrabber, 'get_source',
                        lambda self, url: GENERIC_HTML)
    st = SkipTracer.__new__(SkipTracer)
    return st.load_plugins('skiptracer.plugins')


def test_all_expected_plugins_registered(plugins):
    assert set(PLUGINS).issubset(set(plugins.keys()))


@pytest.mark.parametrize("name", PLUGINS)
def test_plugin_constructs(plugins, name):
    """Every plugin must instantiate without error."""
    inst = plugins[name]()
    assert hasattr(inst, 'get_info')


@pytest.mark.parametrize("name", PLUGINS)
def test_plugin_no_unhandled_crash(plugins, name):
    """A plugin must not raise an *unhandled* error on deterministic HTML.

    Interactive plugins (which prompt via input) may raise OSError when no
    TTY is present -- that is an accepted boundary, not a defect.
    """
    cls = plugins[name]
    bi.webproxy = ''
    bi.proxy = ''
    inst = cls()
    for lookup, value in [('email', 'a@b.com'), ('name', 'Alice Smith'),
                          ('phone', '1234567890'), ('screenname', 'tester'),
                          ('plate', 'ABC123')]:
        try:
            result = inst.get_info(value, lookup)
        except ACCEPTED:
            # Interactive-by-design: prompting for input with no TTY.
            continue
        except (TypeError, ValueError, AttributeError, IndexError,
                NameError, KeyError) as crash:
            pytest.fail(
                "{} crashed on lookup={!r} with {}: {}".format(
                    name, lookup, type(crash).__name__, crash))
        # A clean run must return None or a mapping/list.
        assert result is None or isinstance(result, (dict, list))
