import os
import pytest

from skiptracer.plugins.haveibeenpwned import HaveIBeenPwnedGrabber


@pytest.mark.skipif(not (os.environ.get('HAVEIBEENPWNED_API_KEY') or os.environ.get('HIBP_API_KEY')),
                    reason="No HIBP API key in environment; smoke test skipped")
def test_hibp_smoke_live():
    """Live smoke test for the HIBP plugin. Runs only when API key present."""
    key = os.environ.get('HAVEIBEENPWNED_API_KEY') or os.environ.get('HIBP_API_KEY')
    grabber = HaveIBeenPwnedGrabber()
    # perform a harmless query; caller must ensure the key has access
    res = grabber.get_info('example@example.com', 'email')
    # Expect either a mapping (breach info), list, or a dict indicating 'no_data' or similar
    assert res is None or isinstance(res, (dict, list))
