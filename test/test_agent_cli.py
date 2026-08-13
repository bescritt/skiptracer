import os
import sys
import json
from subprocess import run, PIPE

import pytest

def test_enrich_email_stdout(monkeypatch, tmp_path):
    # run module as script
    cmd = [sys.executable, '-m', 'tools.agent_cli', 'enrich-email', '-']
    p = run(cmd, input=b'alice@example.com', stdout=PIPE, stderr=PIPE)
    assert p.returncode == 0
    out = p.stdout.decode()
    assert 'summary' in out or 'matches' in out

def test_map_handle_stdout(monkeypatch):
    cmd = [sys.executable, '-m', 'tools.agent_cli', 'map-screenname', 'doesnotexist', '-']
    p = run(cmd, stdout=PIPE, stderr=PIPE)
    assert p.returncode in (0,2)
