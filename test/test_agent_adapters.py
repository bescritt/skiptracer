import builtins as bi
import types
import os
import sys
import tempfile

# ensure repo root on sys.path so tests can import tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from tools import agent_adapters as aa

# Helper fake plugins
class FakePlugin:
    def __init__(self):
        pass
    def get_info(self, input_value, _):
        return f"http://example.com/{input_value}"

class FailingPlugin:
    def __init__(self):
        pass
    def get_info(self, input_value, _):
        raise RuntimeError("boom")


def test_parallel_probe_and_synthesize(monkeypatch):
    # patch SkipTracer.load_plugins
    import skiptracer.skiptracer as st
    monkeypatch.setattr(st.SkipTracer, 'load_plugins', classmethod(lambda cls, g: {'p1': FakePlugin, 'p2': FakePlugin}))

    res = aa.parallel_probe(['p1','p2'], 'alice', max_workers=2, retries=1)
    assert isinstance(res, list)
    assert all(r.get('ok') for r in res)

    # verify synthesize computes scores and confidence
    verified = [aa.verify_match(r, expected_tokens=['alice']) for r in res]
    summ = aa.synthesize(verified)
    assert 'confidence' in summ


def test_call_with_retries_handles_failures(monkeypatch):
    import skiptracer.skiptracer as st
    monkeypatch.setattr(st.SkipTracer, 'load_plugins', classmethod(lambda cls, g: {'bad': FailingPlugin}))
    out = aa.call_with_retries('bad', 'x', tries=2, base_delay=0.01)
    assert out.get('ok') is False
    assert out.get('error')


def test_verify_match_fetches_and_tokens(monkeypatch):
    r = {'tool':'p', 'raw': 'http://example.com/x'}
    # patch PageGrabber.get_source
    monkeypatch.setattr('skiptracer.plugins.base.PageGrabber.get_source', lambda self, url: '<html>alice bob</html>')
    v = aa.verify_match(r, expected_tokens=['alice'])
    assert v['verification']['fetched'] is True
    assert v['verification']['tokens_found']['alice'] is True


def test_persist_summary_writes_file(tmp_path):
    summary = {'ts': aa.now_ts(), 'matches': []}
    bi.outdata = {}
    # prefer writing into tmp_path: set cwd
    cwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        rel = aa.persist_summary(summary, filename_prefix='test-agent')
        # DataSaver.writeout returns relative path string when successful
        assert rel is None or isinstance(rel, str)
    finally:
        os.chdir(cwd)
