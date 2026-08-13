# 50 NEW Failure Modes — skiptracer (code-grounded, post-migration)

These are NOT the old F1-F27 (those were theoretical CWE mappings). Each below
is tied to a specific line in the CURRENT source and is exercised by a real test
in `test/test_failure_modes_new.py` (N01..N50). Modes that currently crash or
misbehave are marked [BUG]; modes that are merely fragile traps are [TRAP].

## CLI / __main__.py
- N01 [pass] `--version` prints 4.0.0 and exits 0.
- N02 [pass] `--help` prints usage, exits 0.
- N03 [TRAP] `-n/--no-banner` must suppress the banner; if Banner() prints
  unconditionally the flag is inert. (__main__.py:34)
- N04 [pass] `main()` returns int, never None (None -> sys.exit(None) masks
  failures). (__main__.py:37)
- N05 [pass] unknown flag -> argparse SystemExit non-zero, not swallowed.

## Shared builtins (bi) stowage
- N06 [TRAP] `base.get_source` checks `bi.proxy != ''`; if bi.proxy is ever
  None (not ''), truthiness path differs. (base.py:73)
- N07 [FIXED] DataSaver only sets bi.filename when user answers 'y' to save; if
  'n', writeout() raised AttributeError. Fixed: writeout() returns None (no-op)
  when bi.filename is unset. (datasaver.py; commit b03a231+)
  'n', bi.filename is never set, yet writeout() does open(bi.filename) ->
  AttributeError. (datasaver.py:13-21,26)
- N08 [TRAP] DataSaver.__init__ resets bi.outdata; if skipped (subclass),
  stale results leak across runs. (datasaver.py:11)
- N09 [pass] bi.webproxy=='y' rotates proxy on failure (branch reachable).
- N10 [BUG] DataSaver.writeout's `if bi.debug` and `else` print IDENTICAL
  text -> debug flag is dead/inert. (datasaver.py:32 vs 36)
- N11 [BUG] stowing on `builtins` is process-global; SkipTracer class body
  sets bi.* at import time, silently resetting any prior state. (skiptracer.py:21-24)
- N12 [pass] Ctrl-C -> exit 130 (guarded in __main__).

## PageGrabber.get_source / post_data
- N13 [pass] get_source returns str.
- N14 [BUG] `bi.proxy.split(':')[1]`/`[0]` mis-parses a proxy without a scheme
  ('1.2.3.4:8080' -> proto='1.2.3.4'). (base.py:74-75)
- N15 [pass] no-proxy branch returns content.
- N16 [pass] persistent failure caps at 5 retries, returns ''. (base.py:71,93)
- N17 [pass] non-ASCII survives ascii-'ignore' re-encode (data loss, no crash).
- N18 [BUG] get_source uses verify=False -> TLS validation disabled (MITM/SSRF
  exposure). (base.py:82,91)
- N19 [pass] post_data returns None on failure (bare except swallows).
- N20 [pass] proxy dict built without raising on valid proxy.
- N21 [pass] get_dom -> lxml BeautifulSoup.
- N22 [pass] get_html -> html.parser BeautifulSoup.

## random_line / _package_path
- N23 [FIXED] random_line() does next(afile) unguarded; EMPTY UA DB raised
  StopIteration, crashing PageGrabber init. Fixed: returns "" on empty/missing
  DB and now closes the fd (also closes N25). (base.py)
  StopIteration -> crashes PageGrabber init. (base.py:43)
- N24 [pass] 1-line DB returns that line.
- N25 [BUG] random_line opens the file but never closes it -> fd leak.
  (base.py:43)
- N26 [pass] _package_path resolves via importlib.
- N27 [pass] _package_path os.path fallback works when importlib+pkg_resources
  both fail.

## DataSaver
- N28 [TRAP] __init__ calls input() at construction -> untestable without TTY.
  (datasaver.py:13)
- N29 [pass] save path writes JSON to named file.
- N30 [BUG] debug branch dead (identical output) -> flag inert. (see N10)
- N31 [TRAP] non-serializable outdata (set) -> json.dumps raises, caught, no
  file written (silent data loss). (datasaver.py:27)
- N32 [TRAP] writeout opens 'w' -> silently overwrites existing file.
  (datasaver.py:26)
- N33 [BUG] filename from user input goes straight to open() -> path traversal
  ('../../x.json') writes outside cwd. (datasaver.py:18,26)

## proxygrabber
- N34 [BUG] `7 * 86000` typo for 86400 -> proxy cache expiry ~7x too long,
  proxies effectively never expire. (proxygrabber.py:80)
- N35 [BUG] new_proxy reads `str(cwd)+'/storage/proxies.txt'` while storage_dir
  is repo-relative -> wrong path when cwd != repo root. (proxygrabber.py:20-25,82)
- N36 [FIXED] remove_proxy compares `i != str(remline)` but lines keep their
  newline -> the bad proxy is never removed. Fixed: strip newlines before
  comparing. (proxygrabber.py)
  newline -> the bad proxy is never actually removed. (proxygrabber.py:32-39)
- N37 [TRAP] get_proxies scrapes free-proxy-list markup; markup change ->
  silently empty set. (proxygrabber.py:59-66)
- N38 [pass] missing proxies.txt -> get_proxies + test path returns a proxy.
- N39 [TRAP] write_file appends ('a') -> file grows unbounded across runs.
  (proxygrabber.py:42-49)
- N40 [TRAP] new_proxy builds itertools.cycle but uses random.choice on the
  set -> cycle is dead code. (proxygrabber.py:103)

## default_menus
- N41 [BUG] intromenu does ltypes[selection-1]; input '0' -> ltypes[-1] (last
  item) silently selected instead of rejected. (default_menus.py:78)
- N42 [BUG] negative selection also wraps to a valid (wrong) item.
  (default_menus.py:78)
- N43 [FIXED] grabplugins ast.literal_eval on cfg tuple; malformed value ->
  ValueError/SyntaxError, uncaught, crashing the menu. Fixed: skip malformed
  entries. (default_menus.py)
  ValueError uncaught -> menu crash. (default_menus.py:107)
- N44 [TRAP] grabuserchoice wraps EOFError/KeyboardInterrupt and calls
  sys.exit(0) -> non-interactive run exits the whole process, not just menu.
  (default_menus.py:124-127)
- N45 [pass] selectchoice dispatches; 'exit' -> sys.exit (caught).
- N46 [TRAP] profiler() writes raw user input into bi.* globals with no
  validation -> injection into later report rendering. (default_menus.py:228-246)

## load_plugins / colors / entry points
- N47 [pass] load_plugins on missing group -> {} (not None/crash).
  (skiptracer.py:51-61)
- N48 [FIXED] a registered plugin whose p.load() raises (bad import) kills the
  whole app. Fixed: load_plugins isolates the broken plugin (log + skip).
  (skiptracer.py)
  whole app -> no per-plugin isolation. (skiptracer.py:59-60)
- N49 [pass] colors.use returns CEND for unknown code (graceful).
  (default_colors.py:13-16)
- N50 [TRAP] colors.use does 'C'+code.upper() get/set; adversarial code like
  '__import__' safely falls back to CEND (no eval), but the prefix-concat
  pattern is fragile. (default_colors.py:14-16)

## Summary
Real defects found by NEW tests: N07, N10, N11, N14, N18, N23, N25, N33, N34,
N35, N36, N41, N42, N43, N48 (15 confirmed-defect modes). Of these, 5 are now
FIXED in source (N07, N23, N36, N43, N48 -- plus N25 fd-leak closed via N23):
datasaver.writeout no-op when filename unset; random_line handles empty UA DB;
remove_proxy strips newlines; grabplugins skips malformed config; load_plugins
isolates broken plugins. The remaining 10 (N10, N11, N14, N18, N25-partial,
N33, N34, N35, N41, N42) are documented and pinned by tests but not yet fixed
in source. The rest are fragility traps pinned so they cannot regress silently.
