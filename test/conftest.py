"""Pytest configuration and shared fixtures for skiptracer."""

import builtins as bi
import sys
import os

import pytest


def _reset_builtins_state():
    """Clear the framework's stowed globals on the builtins module."""
    for attr in ('webproxy', 'proxy', 'lookup', 'output', 'outdata',
                 'search_string', 'debug', 'filename'):
        if hasattr(bi, attr):
            delattr(bi, attr)


@pytest.fixture(autouse=True)
def clean_builtins():
    """Each test starts with a clean builtins namespace."""
    _reset_builtins_state()
    bi.webproxy = ''
    bi.proxy = ''
    bi.debug = False
    bi.outdata = {}
    bi.output = ''
    yield
    _reset_builtins_state()


@pytest.fixture
def ua_sample(tmp_path, monkeypatch):
    """Provide a deterministic user-agents db and point the loader at it."""
    import random
    db = tmp_path / "user-agents.db"
    db.write_text("UA-A\nUA-B\nUA-C\n")
    monkeypatch.setattr(
        "skiptracer.plugins.base._package_path",
        lambda *parts: str(db) if parts and parts[0] == "user-agents.db" else str(tmp_path / parts[-1]))
    return db
