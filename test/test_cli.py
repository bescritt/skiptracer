"""End-to-end smoke tests for the command-line entry point."""

import subprocess
import sys

import pytest


VENV_PY = "/home/owner/skiptracer/.venv/bin/python"


def _run_cli(stdin="", timeout=30):
    """Invoke `python -m skiptracer` with given stdin; return (rc, out)."""
    env = dict(__import__('os').environ)
    env.pop('PYTHONPATH', None)
    proc = subprocess.run(
        [VENV_PY, '-m', 'skiptracer'],
        input=stdin, capture_output=True, text=True,
        timeout=timeout, env=env, cwd='/tmp')
    return proc.returncode, proc.stdout + proc.stderr


def test_cli_launches_and_prints_banner():
    rc, out = _run_cli(stdin="9\n")
    # banner contains the ASCII art signature marker
    assert 'illmob.org' in out
    # menu options render from packaged config
    assert 'Email - Search targets by email address' in out


def test_cli_exposes_all_menu_categories():
    rc, out = _run_cli(stdin="9\n")
    for label in ('Proxy', 'Email', 'Name', 'Phone', 'Screen Name',
                  'License Plate', 'Profiler', 'Help', 'Exit'):
        assert label in out
