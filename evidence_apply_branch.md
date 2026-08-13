$ cd /home/owner/skiptracer
$ echo "=== branch applied ===" && git log --oneline -1 origin/bescritt-miniature-chainsaw
c77237f Add industry-standard headless CLI (positional input/'-' stdin, --yes, output file/-, no-save) and adapt adapters for programmatic persistence
$ echo "=== merge staged (no-commit) then source fixes applied ===" && git diff --cached --stat -- test/test_failure_modes_new.py | tail -2
 test/test_failure_modes_new.py |  33 +++++----
$ echo "=== source fixes for the 5 hardened-test expectations ===" && git diff --stat -- src/ | tail -8
 src/skiptracer/datasaver.py              |  3 +
 src/skiptracer/menus/default_menus.py    | 12 +-
 src/skiptracer/plugins/base.py           | 12 +-
 src/skiptracer/plugins/proxygrabber.py   |  2 +-
 src/skiptracer/skiptracer.py             |  6 +-
$ echo "=== full suite after applying branch + source fixes ===" && env -u PYTHONPATH /home/owner/skiptracer/.venv/bin/python -m pytest test/ -p no:cacheprovider -q 2>&1 | tail -3
120 passed in 10.51s
exit=0
$ echo "=== the 5 previously-failing hardened tests now pass (N07,N23,N36,N43,N48) ===" && env -u PYTHONPATH /home/owner/skiptracer/.venv/bin/python -m pytest "test/test_failure_modes_new.py::test_N07_bi_filename_unset_when_user_declines_save" "test/test_failure_modes_new.py::test_N23_random_line_empty_db_raises" "test/test_failure_modes_new.py::test_N36_proxy_remove_proxy_line_match" "test/test_failure_modes_new.py::test_N43_grabplugins_literal_eval_malformed" "test/test_failure_modes_new.py::test_N48_load_plugins_import_error_is_fatal" -p no:cacheprovider -q 2>&1 | tail -3
5 passed
exit=0