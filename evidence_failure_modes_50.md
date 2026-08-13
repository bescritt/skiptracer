$ cd /home/owner/skiptracer
$ env -u PYTHONPATH /home/owner/skiptracer/.venv/bin/python -m pytest test/test_failure_modes_new.py -p no:cacheprovider -q 2>&1 | tail -3
50 passed in 0.24s
exit=0
$ env -u PYTHONPATH /home/owner/skiptracer/.venv/bin/python -m pytest test/ -p no:cacheprovider -q 2>&1 | tail -2
114 passed in 5.57s
exit=0
$ echo "=== real bug found + fixed: post_data infinite loop (N19) ==="
$ grep -n "while reqcom < 5" src/skiptracer/plugins/base.py
    while reqcom < 5:
$ grep -n "while reqcom == 0" src/skiptracer/plugins/base.py || echo "OLD BUGGY 'while reqcom == 0' GONE (fixed)"
OLD BUGGY 'while reqcom == 0' GONE (fixed)
$ echo "=== confirm N19 no longer hangs: bounded retries ==="
$ env -u PYTHONPATH /home/owner/skiptracer/.venv/bin/python - <<'PY'
import builtins as bi
from skiptracer.plugins.base import PageGrabber
bi.webproxy=""; bi.proxy=""
def flaky(*a,**k): raise Exception("boom")
import skiptracer.plugins.base as b
b.requests.post = flaky
pg=PageGrabber()
print("post_data returns:", pg.post_data("http://x",{"a":1}), "(None = bounded, no hang)")
PY
post_data returns: None (None = bounded, no hang)
exit=0