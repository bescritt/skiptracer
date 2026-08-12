"""Test entry point.

Run the full suite with:
    python -m pytest test/ -v

This module keeps backward-compatible behaviour for `python -m
skiptracer.test.test_runner` callers while delegating to pytest.
"""
import sys

import pytest


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__.rsplit("/", 1)[0]]))
