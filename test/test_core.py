"""Unit tests for core framework modules (colors, base, config, entry points)."""

import builtins as bi
import configparser

import pytest

from skiptracer.colors.default_colors import DefaultBodyColors as bc
from skiptracer.plugins.base import PageGrabber, random_line, _package_path
from skiptracer.skiptracer import SkipTracer


# --------------------------------------------------------------------------
# Colors
# --------------------------------------------------------------------------
def test_colors_have_expected_escape_codes():
    assert bc.CRED.startswith('\033[')
    assert bc.CEND == '\033[0m'


def test_colors_use_returns_code_or_end():
    assert bc.use('RED') == bc.CRED
    assert bc.use('unknown') == bc.CEND


# --------------------------------------------------------------------------
# Package data resolution
# --------------------------------------------------------------------------
def test_package_path_resolves_user_agents_db():
    p = _package_path('user-agents.db')
    assert p.endswith('user-agents.db')
    # The file shipped in the wheel/source must exist
    import os
    assert os.path.exists(p), "user-agents.db missing from package data"


def test_package_path_resolves_skiptracer_cfg():
    p = _package_path('skiptracer.cfg')
    assert p.endswith('skiptracer.cfg')
    import os
    assert os.path.exists(p), "skiptracer.cfg missing from package data"


# --------------------------------------------------------------------------
# Random user-agent selection
# --------------------------------------------------------------------------
def test_random_line_returns_a_string(ua_sample):
    val = random_line()
    assert isinstance(val, str)
    assert val in ('UA-A', 'UA-B', 'UA-C')


def test_random_line_never_raises_on_valid_db(ua_sample):
    for _ in range(20):
        assert random_line()


# --------------------------------------------------------------------------
# PageGrabber base behaviour
# --------------------------------------------------------------------------
def test_pagegrabber_init_populates_ua_and_dicts(ua_sample):
    pg = PageGrabber()
    assert isinstance(pg.ua, str) and pg.ua
    assert pg.info_dict == {}
    assert pg.info_list == []
    assert pg.proxy == {}


def test_get_dom_returns_beautifulsoup(ua_sample):
    pg = PageGrabber()
    soup = pg.get_dom("<html><body><p id='x'>hi</p></body></html>")
    assert soup.find('p', attrs={'id': 'x'}).text == 'hi'


def test_get_html_uses_html_parser(ua_sample):
    pg = PageGrabber()
    soup = pg.get_html("<html><body><div class='a'>z</div></body></html>")
    assert soup.find('div', attrs={'class': 'a'}).text == 'z'


# --------------------------------------------------------------------------
# Entry-point loading (the framework's plugin discovery)
# --------------------------------------------------------------------------
def test_load_plugins_finds_all_registered():
    st = SkipTracer.__new__(SkipTracer)
    plugins = st.load_plugins('skiptracer.plugins')
    expected = {
        'fouroneone_info', 'haveibeenpwned', 'knowem', 'linkedin',
        'myspace', 'namechk2', 'plate', 'tinder', 'true_people',
        'truthfinder', 'twitter', 'who_call_id', 'whoismind',
        'advance_background_checks',
    }
    assert expected.issubset(set(plugins.keys()))
    # Every loaded entry point is callable to construct an instance
    for name, cls in plugins.items():
        inst = cls()
        assert hasattr(inst, 'get_info')


def test_load_menus_finds_default_menus():
    st = SkipTracer.__new__(SkipTracer)
    menus = st.load_plugins('skiptracer.menus')
    assert 'default_menus' in menus
