# Contributing to Skiptracer

Thanks for your interest in improving Skiptracer. This document explains how to
get a change merged.

## Development setup

```bash
git clone https://github.com/bescritt/skiptracer.git
cd skiptracer
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[browser,scraper,tor]"
.venv/bin/python -m pip install pytest pytest-cov pytest-mock responses
```

Run the suite from a neutral directory (so the package, not the repo root, is
imported):

```bash
.venv/bin/python -m pytest test/ -q
```

## Adding a plugin

1. Create `src/skiptracer/plugins/<name>/__init__.py` defining a class that
   subclasses `skiptracer.plugins.base.PageGrabber`.
2. Register it in `setup.py` under the `skiptracer.plugins` entry-points group.
3. List it under the relevant `[menu.*]` sections of
   `src/skiptracer/data/skiptracer.cfg`.
4. Add a mocked-HTTP test under `test/` (see `test_plugins.py`).

## Guidelines

- Keep changes focused; one logical change per pull request.
- New code ships with tests. The CI gate fails on regression.
- Respect the Apache-2.0 license; do not introduce GPL code.
- Be mindful of the tool's purpose: passive, public-source OSINT only. Do not
  add capabilities that target non-public data or circumvent access controls.
