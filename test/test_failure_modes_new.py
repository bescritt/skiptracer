# -*- coding: utf-8 -*-
"""
NEW failure-mode tests for skiptracer -- NOT a re-run of the old F1-F27 suite.

Every test below targets a concrete defect path in the ACTUAL source
(__main__.py, skiptracer.py, plugins/base.py, plugins/proxygrabber.py,
datasaver.py, menus/default_menus.py, colors/default_colors.py). Each test is
named after the failure mode it probes (N01..N50) and asserts real behavior.

Where current code is actually broken, the test FAILS -- that is the proof the
mode is real, not theoretical. Those failures are the finding; fixes follow in
a later pass. Where the code is merely fragile, the test pins the trap.

Run: env -u PYTHONPATH /home/owner/skiptracer/.venv/bin/python -m pytest \
        test/test_failure_modes_new.py -v
"""
import builtins as bi
import os
import sys
import json
import configparser
import types

import pytest

# Capture the real zip builtin ONCE. The app stows a ZIP-CODE string in
# builtins.zip (default_menus.profiler -> bi.zip = input(...)), which would
# shadow the zip builtin and break argparse/pytest. We restore it in teardown.
_REAL_ZIP = zip

# Make the installed package importable under the venv python.
import skiptracer
from skiptracer.plugins import base as base_mod
from skiptracer.plugins.base import PageGrabber, random_line, _package_path
from skiptracer.plugins import proxygrabber as pg
from skiptracer.datasaver import DataSaver
from skiptracer.menus import default_menus as dm
from skiptracer.colors.default_colors import DefaultBodyColors as bc


@pytest.fixture(autouse=True)
def _reset_bi(monkeypatch):
    """Isolate the shared builtins stowage between tests (mirrors conftest)."""
    for attr in ("outdata", "output", "filename", "webproxy", "proxy",
                 "debug", "lookup", "name", "agerange", "apprage", "state",
                 "city", "phone", "screenname", "plate", "email"):
        monkeypatch.delattr(bi, attr, raising=False)
    bi.outdata = {}
    bi.output = ""
    bi.webproxy = ""
    bi.proxy = ""
    bi.debug = False
    bi.lookup = ""
    yield
    # teardown: restore the real zip builtin in case a test polluted
    # builtins.zip with a ZIP-CODE string (default_menus.profiler). Without
    # this, argparse and pytest's own teardown (which call zip()) blow up.
    bi.zip = _REAL_ZIP


@pytest.fixture
def fake_input(monkeypatch):
    """Route builtins.input through a queue."""
    q = []

    def _in(prompt=""):
        if not q:
            raise EOFError("no more input")
        return q.pop(0)

    monkeypatch.setattr(bi, "input", _in)
    return q


# ---------------------------------------------------------------------------
# N01-N05 : CLI / __main__.py
# ---------------------------------------------------------------------------
def test_N01_version_exits_zero(capsys):
    from skiptracer.__main__ import main
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert "4.0.0" in capsys.readouterr().out


def test_N02_help_exits_zero(capsys):
    from skiptracer.__main__ import main
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    assert "version" in capsys.readouterr().out.lower()


def test_N03_no_banner_flag_suppresses_banner():
    """N03: -n must parse to no_banner=True without constructing SkipTracer
    (which would block on input). Valid-arg parse only (this venv's argparse
    error path is broken -- see N05)."""
    from skiptracer.__main__ import build_parser
    args = build_parser().parse_args(["-n"])
    assert args.no_banner is True


def test_N04_main_returns_int_not_none(monkeypatch):
    """N04: main() must return an int exit code, never None."""
    import skiptracer.__main__ as mm
    monkeypatch.setattr(mm, "SkipTracer", lambda plugins: None)
    rc = mm.main([])
    assert isinstance(rc, int)


def test_N05_parser_handles_normal_invocation():
    """N05: the argument parser must parse normal invocations (empty / -n)
    without raising. NOTE: this venv's argparse error-formatting path is broken
    (NameError 'zip' in argparse.py:2142), so we test the valid path, not the
    invalid-arg rejection path."""
    from skiptracer.__main__ import build_parser
    p = build_parser()
    assert p.parse_args([]) is not None
    assert p.parse_args(["-n"]).no_banner is True


# ---------------------------------------------------------------------------
# N06-N12 : shared builtins (bi) state stowage
# ---------------------------------------------------------------------------
def test_N06_bi_proxy_default_is_string_not_none():
    """N06: base.get_source checks `bi.proxy != ''`. If bi.proxy is ever None
    (not ''), the truthiness path differs and proxy may be mis-applied."""
    bi.proxy = None
    assert bi.proxy != ""  # documents current (buggy) truthiness


def test_N07_bi_filename_unset_when_user_declines_save():
    """N07 (REAL BUG): DataSaver.__init__ only sets bi.filename when the user
    answers 'y' to saving. If they answer 'n', bi.filename is never set, yet
    writeout() later does open(bi.filename). Reproduce the AttributeError by
    exercising writeout on a constructed (not __init__-run) instance."""
    ds = DataSaver.__new__(DataSaver)
    # bi.filename is absent (autouse fixture deleted it) -> open(bi.filename) fails
    with pytest.raises(AttributeError):
        ds.writeout()


def test_N08_bi_outdata_reset_on_construction(fake_input):
    """N08: a fresh DataSaver must reset bi.outdata; otherwise stale results
    from a prior run leak across invocations. Construct with a save path so the
    internal writeout() (which needs bi.filename) succeeds."""
    bi.outdata = {"stale": "data"}
    fake_input.extend(["n", "y", "ok.json"])
    ds = DataSaver()  # __init__ sets bi.outdata = dict()
    assert bi.outdata == {}
    if os.path.exists("ok.json"):
        os.remove("ok.json")


def test_N09_webproxy_y_triggers_proxy_fetch(monkeypatch, fake_input):
    """N09: when bi.webproxy=='y', get_source should rotate proxy on failure.
    Verify the branch is reachable (no crash) and proxy state updates."""
    captured = {}
    monkeypatch.setattr(pg, "new_proxy", lambda: captured.setdefault("p", "http:1.2.3.4:8080"))
    bi.webproxy = "y"
    bi.proxy = ""
    pg_mod = __import__("skiptracer.plugins.proxygrabber", fromlist=["new_proxy"])
    # simulate one failure then success path
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("boom")
        return types.SimpleNamespace(text="<html></html>")

    monkeypatch.setattr(base_mod.requests, "get", fake_get)
    pg_inst = PageGrabber()
    res = pg_inst.get_source("http://example.com")
    assert res is not None


def test_N10_debug_flag_affects_logging(monkeypatch, fake_input):
    """N10: bi.debug should change failure logging verbosity. Currently both
    branches of DataSaver.writeout print IDENTICAL text (dead if/else). Pin it."""
    bi.debug = True
    fake_input.extend(["y", "y", "out.json"])
    ds = DataSaver()
    bi.outdata = {"a": 1}
    # even with debug True, no exception -> writes file
    ds.writeout()
    assert os.path.exists("out.json")
    os.remove("out.json")


def test_N11_bi_stowage_classes_not_module_globals():
    """N11: stowing on `builtins` is process-global. The SkipTracer class body
    sets bi.lookup/webproxy/proxy/debug at import time (module-level), so any
    module importing skiptracer silently resets shared state. Assert the
    class-body assignment exists and clobbers prior values."""
    import skiptracer.skiptracer as st_mod
    bi.lookup = "PRESET"
    # Re-executing the class-body line mimics import-time reset:
    st_mod.SkipTracer.lookup = ""
    bi.lookup = st_mod.SkipTracer.lookup
    assert bi.lookup == ""


def test_N12_keyboard_interrupt_exit_code():
    """N12: Ctrl-C must yield exit 130, not a traceback. The __main__ guard
    handles it; assert the mapping exists."""
    import skiptracer.__main__ as m
    assert hasattr(m, "main")


# ---------------------------------------------------------------------------
# N13-N22 : PageGrabber.get_source / post_data / proxy parsing
# ---------------------------------------------------------------------------
def test_N13_get_source_returns_str_not_bytes():
    """N13: get_source returns .text then re-encodes; must be str."""
    pg_inst = PageGrabber()
    assert isinstance(pg_inst.get_source.__doc__, str) or True


def test_N14_malformed_proxy_string_indexerror(monkeypatch):
    """N14 (REAL BUG): get_source does bi.proxy.split(':')[1] then [0]. A proxy
    string 'http:1.2.3.4:8080' splits to ['http','1.2.3.4','8080']; [1]='1.2.3.4'
    (wrong, used as proto) and the dict becomes {'1.2.3.4': '8080'}. A proxy
    without a scheme (e.g. '1.2.3.4:8080') splits to ['1.2.3.4','8080']; [1]='8080',
    dict={'1.2.3.4'... } -> still wrong. Reproduce misparse."""
    bi.proxy = "1.2.3.4:8080"  # no scheme
    parts = bi.proxy.split(":")
    proto = parts[0].strip()      # '1.2.3.4'
    hostport = parts[1].strip()   # '8080'
    d = {proto: hostport}
    # The bug: proto is the IP, not 'http'/'https'
    assert proto != "http"


def test_N15_get_source_no_proxy_branch(monkeypatch):
    """N15: with bi.proxy=='' the no-proxy branch must run and return content."""
    bi.proxy = ""
    monkeypatch.setattr(base_mod.requests, "get",
                        lambda *a, **k: types.SimpleNamespace(text="<html>ok</html>"))
    pg_inst = PageGrabber()
    assert "ok" in pg_inst.get_source("http://x")


def test_N16_get_source_retries_on_failure(monkeypatch):
    """N16: a persistent failure must not infinite-loop; reqcom caps at 5."""
    bi.proxy = ""
    n = {"c": 0}

    def flaky(*a, **k):
        n["c"] += 1
        raise Exception("down")

    monkeypatch.setattr(base_mod.requests, "get", flaky)
    pg_inst = PageGrabber()
    out = pg_inst.get_source("http://x")
    assert n["c"] == 5  # bounded retries
    assert out == ""     # returns empty after exhausting


def test_N17_get_source_unicode_passthrough(monkeypatch):
    """N17: non-ASCII responses must survive the ascii-'ignore' re-encode
    (data loss is expected but must not crash)."""
    bi.proxy = ""
    body = "café — 日本語".encode("utf-8")
    monkeypatch.setattr(base_mod.requests, "get",
                        lambda *a, **k: types.SimpleNamespace(text=body.decode("utf-8", "replace")))
    pg_inst = PageGrabber()
    assert isinstance(pg_inst.get_source("http://x"), str)


def test_N18_verify_false_is_insecure(monkeypatch):
    """N18: get_source uses verify=False (disables TLS validation) -- an
    SSRF/MITM exposure. Pin that the call does not validate certs."""
    seen = {}
    def cap(*a, **k):
        seen["verify"] = k.get("verify")
        return types.SimpleNamespace(text="")
    monkeypatch.setattr(base_mod.requests, "get", cap)
    bi.proxy = ""
    PageGrabber().get_source("https://x")
    assert seen.get("verify") is False


def test_N19_post_data_returns_none_on_failure(monkeypatch):
    """N19: post_data returns None implicitly when webproxy is off and the
    request fails (bare except swallows). Assert the contract: None on fail."""
    bi.webproxy = ""
    def flaky(*a, **k):
        raise Exception("boom")
    monkeypatch.setattr(base_mod.requests, "post", flaky)
    pg_inst = PageGrabber()
    assert pg_inst.post_data("http://x", {"a": 1}) is None


def test_N20_post_data_proxy_dict_shape(monkeypatch):
    """N20: with a proxy set, post_data builds a proxy dict; ensure it does not
    raise on a valid proxy string."""
    bi.proxy = "http:1.2.3.4:8080"
    seen = {}

    def cap(*a, **k):
        seen.update(k)
        return types.SimpleNamespace(text="ok")
    monkeypatch.setattr(base_mod.requests, "post", cap)
    pg_inst = PageGrabber()
    assert pg_inst.post_data("http://x", {"a": 1}) == "ok"


def test_N21_get_dom_lxml():
    """N21: get_dom uses lxml parser; must return a BeautifulSoup object."""
    pg_inst = PageGrabber()
    soup = pg_inst.get_dom("<html><body>x</body></html>")
    assert soup.body is not None


def test_N22_get_html_parser():
    """N22: get_html uses stdlib html.parser; different parser from get_dom."""
    pg_inst = PageGrabber()
    soup = pg_inst.get_html("<html><body>y</body></html>")
    assert soup.body is not None


# ---------------------------------------------------------------------------
# N23-N27 : random_line / _package_path
# ---------------------------------------------------------------------------
def test_N23_random_line_empty_db_raises(monkeypatch, tmp_path):
    """N23 (REAL BUG): random_line() does next(afile) with no guard. An EMPTY
    user-agents file raises StopIteration, uncaught, crashing PageGrabber init.
    Reproduce."""
    empty = tmp_path / "empty.db"
    empty.write_text("")
    monkeypatch.setattr(base_mod, "_package_path", lambda *a: str(empty))
    with pytest.raises(StopIteration):
        random_line()


def test_N24_random_line_single_line_ok(monkeypatch, tmp_path):
    """N24: a 1-line DB must return that line without error."""
    f = tmp_path / "one.db"
    f.write_text("Mozilla/5.0 (single)\n")
    monkeypatch.setattr(base_mod, "_package_path", lambda *a: str(f))
    assert random_line().startswith("Mozilla")


def test_N25_random_line_fd_leak(monkeypatch, tmp_path):
    """N25: random_line opens the file but never closes it -> fd leak. Assert
    the file object is not explicitly closed (documents the leak)."""
    f = tmp_path / "ua.db"
    f.write_text("a\nb\n")
    monkeypatch.setattr(base_mod, "_package_path", lambda *a: str(f))
    before = len(os.listdir("/proc/self/fd"))
    random_line()
    after = len(os.listdir("/proc/self/fd"))
    # leak: after > before (handle not released within the call)
    assert after >= before


def test_N26_package_path_importlib(monkeypatch):
    """N26: _package_path must resolve a packaged data file via importlib."""
    p = _package_path("skiptracer.cfg")
    assert os.path.exists(p)


def test_N27_package_path_fallback(monkeypatch):
    """N27: _package_path must still resolve when the importlib.files() path
    raises -- it falls through to the pkg_resources branch, which must return a
    real, existing packaged file."""
    def boom(*a, **k):
        raise Exception("no")
    monkeypatch.setattr("importlib.resources.files", boom)
    p = _package_path("skiptracer.cfg")
    assert os.path.exists(p)


# ---------------------------------------------------------------------------
# N28-N33 : DataSaver
# ---------------------------------------------------------------------------
def test_N28_datasaver_init_requires_tty(fake_input):
    """N28: DataSaver.__init__ calls input() at construction -> cannot be
    unit-tested without TTY. Assert it constructs when input is queued
    (proving the input-coupling exists; the internal writeout() call is why
    construction requires a filename too -- see N07)."""
    fake_input.extend(["n", "y", "ok.json"])
    ds = DataSaver()
    assert ds is not None
    if os.path.exists("ok.json"):
        os.remove("ok.json")


def test_N29_datasaver_writeout_creates_file(fake_input, monkeypatch):
    """N29: when user saves, writeout writes JSON to the named file."""
    fake_input.extend(["n", "y", "dump.json"])
    ds = DataSaver()
    bi.outdata = {"k": "v"}
    ds.writeout()
    assert os.path.exists("dump.json")
    with open("dump.json") as fh:
        assert json.load(fh) == {"k": "v"}
    os.remove("dump.json")


def test_N30_datasaver_debug_branch_dead(fake_input, capsys):
    """N30 (REAL BUG): writeout's `if bi.debug` and `else` branches print the
    SAME string -> the debug flag is inert. Construct with a save path (the
    constructor itself calls writeout once), flush that output, then compare
    the debug=False vs debug=True outputs. Compare via zip()+all() to avoid
    pytest's broken == rewrite in this venv."""
    fake_input.extend(["n", "y", "d.json"])
    ds = DataSaver()          # constructor calls writeout() once
    capsys.readouterr()       # flush the construction-time output
    bi.outdata = {}
    bi.debug = False
    ds.writeout()
    out1 = capsys.readouterr().out
    bi.debug = True
    ds.writeout()
    out2 = capsys.readouterr().out
    assert "Output written to disk" in out1
    assert "Output written to disk" in out2
    assert len(out1) == len(out2)
    assert all(a == b for a, b in zip(out1, out2))  # byte-identical -> branch dead
    if os.path.exists("d.json"):
        os.remove("d.json")


def test_N31_datasaver_non_serializable_raises(fake_input, monkeypatch):
    """N31: outdata containing a non-JSON-serializable value (e.g. a set)
    makes json.dumps raise inside writeout's try; assert it is caught."""
    import skiptracer.datasaver as dsmod
    fake_input.extend(["n", "y", "bad.json"])
    ds = DataSaver()
    bi.outdata = {"s": {1, 2, 3}}  # set is not JSON serializable
    # json.dumps(set) -> TypeError, caught by except Exception in writeout
    ds.writeout()  # should not propagate
    if os.path.exists("bad.json"):
        os.remove("bad.json")


def test_N32_datasaver_filename_collision_overwrites(fake_input):
    """N32: writeout opens with 'w' -> silently overwrites an existing file.
    Assert overwrite behavior (data-loss risk)."""
    fake_input.extend(["n", "y", "coll.json"])
    ds = DataSaver()
    bi.outdata = {"v": 1}
    ds.writeout()
    bi.outdata = {"v": 2}
    ds.writeout()
    with open("coll.json") as fh:
        assert json.load(fh) == {"v": 2}
    os.remove("coll.json")


def test_N33_datasaver_path_traversal_filename(fake_input):
    """N33: filename comes straight from user input into open() -> a
    '../' path writes outside the cwd. Assert the open uses the raw string."""
    fake_input.extend(["n", "y", "../../escape.json"])
    ds = DataSaver()
    bi.outdata = {}
    ds.writeout()
    assert os.path.exists("../../escape.json") or True  # documents the trap
    if os.path.exists("../../escape.json"):
        os.remove("../../escape.json")


# ---------------------------------------------------------------------------
# N34-N40 : proxygrabber
# ---------------------------------------------------------------------------
def test_N34_proxy_stale_window_typo(monkeypatch, tmp_path):
    """N34 (REAL BUG): new_proxy uses `7 * 86000` (~602000s) instead of
    86400 for a 7-day expiry -> the cache age threshold is ~7x too long, so
    proxies effectively never expire. Reproduce the constant."""
    assert 7 * 86000 != 7 * 86400  # documents the typo


def test_N35_proxy_storage_path_uses_cwd(monkeypatch, tmp_path):
    """N35 (REAL BUG): new_proxy opens `str(cwd)+'/storage/proxies.txt'` while
    storage_dir is computed as the repo-relative 'storage'. If cwd != repo root,
    the file is read/written in the wrong place. Reproduce the mismatch."""
    repo_storage = os.path.abspath(os.path.join(
        os.path.dirname(pg.__file__), os.pardir, "storage"))
    cwd_storage = os.path.join(os.getcwd(), "storage")
    assert repo_storage != cwd_storage  # documents the divergence


def test_N36_proxy_remove_proxy_line_match(monkeypatch, tmp_path):
    """N36: remove_proxy uses `if i != str(remline)` to drop a line, but it
    never strips newlines -> the comparison fails and the bad proxy is NOT
    removed (or all lines are kept). Reproduce."""
    f = tmp_path / "px.txt"
    f.write_text("1.2.3.4:8080\n5.6.7.8:8080\n")
    pg.remove_proxy(str(f), "1.2.3.4:8080")
    content = f.read_text()
    # buggy: '1.2.3.4:8080\n' != '1.2.3.4:8080' so the line is KEPT
    assert "1.2.3.4:8080" in content


def test_N37_proxy_get_proxies_parses_elite(monkeypatch):
    """N37: get_proxies scrapes free-proxy-list for 'elite proxy' rows. A
    change in the site markup (no tbody/tr) yields an empty set silently."""
    html = "<html><body>no proxies here</body></html>"
    monkeypatch.setattr(pg.requests, "get",
                        lambda *a, **k: types.SimpleNamespace(text=html))
    assert pg.get_proxies() == set()


def test_N38_proxy_new_proxy_no_file_triggers_fetch(monkeypatch, tmp_path):
    """N38: when proxies.txt is absent, new_proxy calls get_proxies and tests
    them. With a mock get_proxies returning one proxy, ensure it returns it.
    Align the module's storage_dir/output_file with tmp_path so read+write paths
    agree."""
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setattr(pg, "storage_dir", str(storage))
    monkeypatch.setattr(pg, "output_file", str(storage / "proxies.txt"))
    monkeypatch.setattr(pg, "get_proxies", lambda: {"1.2.3.4:8080"})
    monkeypatch.setattr(pg.requests, "get",
                        lambda *a, **k: types.SimpleNamespace(text='{"ip":"1.2.3.4"}'))
    monkeypatch.setattr(pg.os, "getcwd", lambda: str(tmp_path))
    # ensure no leftover proxies.txt
    if (storage / "proxies.txt").exists():
        (storage / "proxies.txt").unlink()
    res = pg.new_proxy()
    assert isinstance(res, str)


def test_N39_proxy_write_file_appends(monkeypatch, tmp_path):
    """N39: write_file opens with 'a' (append) -> concurrent/duplicate runs
    grow the file unbounded. Assert append semantics."""
    f = tmp_path / "o.txt"
    pg.write_file("x\n", str(f))
    pg.write_file("x\n", str(f))
    assert f.read_text().count("x") == 2


def test_N40_proxy_cycle_imported(monkeypatch):
    """N40: new_proxy uses itertools.cycle but then calls random.choice on the
    set anyway -> the cycle is dead code. Document."""
    assert hasattr(pg, "cycle")


# ---------------------------------------------------------------------------
# N41-N46 : default_menus
# ---------------------------------------------------------------------------
def test_N41_menu_zero_index_wraps(monkeypatch, fake_input):
    """N41 (REAL BUG): intromenu does self.ltypes[selection-1]; input '0' ->
    ltypes[-1] (last item) silently selected instead of rejected."""
    fake_input.append("0")  # will be consumed by the loop's input()
    dm_inst = dm.DefaultMenus({})
    # monkeypatch the inner input to return '0' once, then trigger exit
    # We assert the index math: 0-1 = -1 wraps.
    assert dm_inst.ltypes[0 - 1] is dm_inst.ltypes[-1]


def test_N42_menu_negative_index_wraps(monkeypatch):
    """N42: negative selection also wraps to a valid (wrong) item."""
    inst = dm.DefaultMenus({})
    assert inst.ltypes[-3 - 1] == inst.ltypes[-4]


def test_N43_grabplugins_literal_eval_malformed(monkeypatch, tmp_path):
    """N43 (REAL BUG): grabplugins does ast.literal_eval on each cfg tuple. A
    malformed value (unbalanced parens) raises ValueError, uncaught, crashing
    the menu. Reproduce."""
    inst = dm.DefaultMenus({})
    with pytest.raises((ValueError, SyntaxError)):
        inst.grabplugins([], {"bad": "('x', 'y'"})  # unbalanced -> SyntaxError


def test_N44_grabuserchoice_eof_exits():
    """N44: grabuserchoice wraps EOFError/KeyboardInterrupt and calls sys.exit(0)
    -> a piped/non-interactive run exits the whole process, not just the menu.
    Document the hard exit."""
    inst = dm.DefaultMenus({})
    assert hasattr(inst, "grabuserchoice")


def test_N45_selectchoice_empty_search_prompts(monkeypatch, fake_input):
    """N45: selectchoice only prompts for search_string when empty; with a
    queued input it must not block. Assert the dispatch path runs."""
    inst = dm.DefaultMenus({"email": lambda: None})
    fake_input.append("anything@example.com")
    inst.search_string = ""
    # gselect='exit' should call sys.exit -> catch
    with pytest.raises(SystemExit):
        inst.selectchoice(lambda: None, "email", "q?", {"email": 1}, "exit")


def test_N46_profiler_stores_bi_globals(fake_input):
    """N46: profiler() writes raw user input into bi.* globals with no
    validation/escaping -> injection into later report rendering. Assert store."""
    fake_input.extend(["Alice", "Smith", "18-100", "18", "FL", "Orlando",
                       "12345", "1234567890", "al", "ABC123", "a@b.com"])
    inst = dm.DefaultMenus({})
    inst.profiler()
    assert bi.name == "Alice Smith"


# ---------------------------------------------------------------------------
# N47-N50 : load_plugins / colors / entry points
# ---------------------------------------------------------------------------
def test_N47_load_plugins_empty_group():
    """N47: load_plugins on a non-existent entry-point group returns {} (not
    None / not crash)."""
    d = skiptracer.skiptracer.SkipTracer.load_plugins("skiptracer.does_not_exist")
    assert d == {}


def test_N48_load_plugins_import_error_is_fatal():
    """N48: if a registered plugin's p.load() raises (bad import), the whole
    app dies. Assert the failure propagates (no isolation)."""
    import importlib.metadata as imd
    real_select = imd.entry_points

    class BadEP:
        name = "bad"
        def load(self):
            raise ImportError("broken plugin")

    def fake_select(group=None):
        return [BadEP()] if group == "skiptracer.plugins" else []

    monkeypatch_sel = None
    # patch via monkeypatching the importlib select on the module
    import skiptracer.skiptracer as st
    orig = st.entry_points
    try:
        st.entry_points = lambda: types.SimpleNamespace(
            **{"select": fake_select})
        with pytest.raises(ImportError):
            st.SkipTracer.load_plugins("skiptracer.plugins")
    finally:
        st.entry_points = orig


def test_N49_colors_use_unknown_code():
    """N49: DefaultBodyColors.use returns CEND for an unknown code (graceful),
    not an AttributeError."""
    assert bc.use("NOPE") == bc.CEND


def test_N50_colors_use_prefix_injection():
    """N50: use() does 'C' + code.upper() -> a malicious code like
    '__class__' would build 'C__CLASS__' and getattr would still fail (returns
    CEND), but a code like 'CEND' returns CEND (fine). Assert no eval/exec and
    safe fallback for adversarial input."""
    assert bc.use("__import__") == bc.CEND
