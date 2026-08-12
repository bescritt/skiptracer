"""Tests for the menu system, packaged configuration, and offline formatting logic."""

import configparser

import pytest

from skiptracer.menus.default_menus import DefaultMenus
from skiptracer.plugins.base import _package_path
from skiptracer.plugins.advance_background_checks import AdvanceBackgroundGrabber
from skiptracer.plugins.true_people import TruePeopleGrabber
from skiptracer.plugins.truthfinder import TruthFinderGrabber


# --------------------------------------------------------------------------
# Packaged configuration
# --------------------------------------------------------------------------
def _load_cfg():
    cfg = configparser.ConfigParser()
    cfg.read(_package_path('skiptracer.cfg'))
    return cfg


def test_packaged_cfg_defines_all_menus():
    cfg = _load_cfg()
    for section in ('menu.email', 'menu.name', 'menu.phone',
                   'menu.screenname', 'menu.plate'):
        assert cfg.has_section(section)


def test_packaged_cfg_menu_entries_parse_as_tuples():
    cfg = _load_cfg()
    import ast
    for key in cfg['menu.email']:
        val = ast.literal_eval(cfg['menu.email'][key])
        assert isinstance(val, list) and len(val) == 2


def test_linkedin_plugin_config_section_present():
    cfg = _load_cfg()
    assert cfg.has_section('plugin.linkedin')
    assert cfg['plugin.linkedin']['homepageurl'].startswith('https://')


# --------------------------------------------------------------------------
# DefaultMenus wiring
# --------------------------------------------------------------------------
def test_default_menus_loads_with_empty_plugin_dict():
    m = DefaultMenus({})
    assert m.config.has_section('menu.email')
    assert m.plugin_list == {}


def test_default_menus_grabplugins_builds_list_with_defaults():
    m = DefaultMenus({})
    result = m.grabplugins([], m.config['menu.email'])
    # 5 email plugins + 3 default items (all/back/exit)
    assert len(result) == 5 + 3
    keys = [r['key'] for r in result]
    assert 'all' in keys and 'back' in keys and 'exit' in keys


# --------------------------------------------------------------------------
# Offline phone/name URL formatting (no network)
# --------------------------------------------------------------------------
def test_abc_makephone_dash_format():
    g = AdvanceBackgroundGrabber()
    out = g.makephone('123-456-7890')
    assert out == '123-456-7890'


def test_abc_makephone_space_format():
    g = AdvanceBackgroundGrabber()
    out = g.makephone('123 456 7890')
    assert out == '(123)-456-7890'


def test_abc_makephone_ten_digit_format():
    g = AdvanceBackgroundGrabber()
    out = g.makephone('1234567890')
    assert out == '123-456-7890'


def test_abc_makephone_bad_length_returns_none():
    g = AdvanceBackgroundGrabber()
    assert g.makephone('123') is None


def test_abc_grab_email_builds_b64_url():
    g = AdvanceBackgroundGrabber()
    g.grab_email('alice@example.com')
    assert g.url.startswith('https://www.advancedbackgroundchecks.com/emails/')
    assert 'alice' not in g.url  # must be encoded


def test_abc_grab_name_builds_hyphenated_url():
    g = AdvanceBackgroundGrabber()
    g.grab_name('Alice Smith')
    assert g.url == 'https://www.advancedbackgroundchecks.com/name/Alice-Smith'


def test_abc_grab_phone_builds_url():
    g = AdvanceBackgroundGrabber()
    g.grab_phone('1234567890')
    assert g.url == 'https://www.advancedbackgroundchecks.com/123-456-7890'


def test_truepeople_makephone_returns_parenthesised():
    g = TruePeopleGrabber()
    assert g.makephone('1234567890') == '(123)-456-7890'


def test_truthfinder_split_name_two_parts():
    g = TruthFinderGrabber()
    g.split_name('Alice Smith')
    assert g.fname == 'Alice'
    assert g.lname == 'Smith'


def test_truthfinder_split_name_three_parts_takes_first_and_last():
    g = TruthFinderGrabber()
    g.split_name('Alice B Smith')
    assert g.fname == 'Alice'
    assert g.lname == 'Smith'
