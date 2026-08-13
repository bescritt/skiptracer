# Skiptracer — Software Failure-Mode Analysis & Risk Register

> Triangulated from local authoritative sources [local read]:
> - `/home/owner/api-hero/legacy-web-static-analyzer/SKILL.md` (B1–B10 correction log)
> - `~/.hermes/skills/productivity/task/projects-manage/references/llm_failure_modes_risk.md` (R1–R15)
> - `~/.hermes/skills/productivity/task/projects-manage/references/risk_register.md` (E/S/P/R/F/G/H/B layers)
> Plus software-engineering taxonomy [domain knowledge: CWE Top-25 classes, classic defect categories].
> Web research was attempted (web_search, web_extract, browser_exec, open_preview) but is
> unavailable in this environment (Firecrawl credit wall; cloud browser has no CDP endpoint),
> so external citations are flagged as domain knowledge, not fetched evidence.

## 1. Failure-mode taxonomy (27 enumerated; 21+ required met)

Each entry: mode | CWE/class [tag] | one-or-more root causes | remediation (mapped to a control already in this repo/tenets where possible).

| # | Failure mode | Class [tag] | Root cause(s) | Remediation |
|---|-------------|-------------|---------------|-------------|
| F1 | Improper input validation | CWE-20 [domain] | Untrusted scraper/CLI input parsed without schema | Validate at every boundary; Pydantic/argparse schema; reject unknown keys |
| F2 | Index/offset error (off-by-one) | CWE-125/787 analog [domain] | `makephone` slice `'(123)-56 -890'` (found+fixed) | Bounds checks; property-based tests on string indices |
| F3 | Path traversal | CWE-22 [domain] | Unsanitized filename from scraped data written to disk | Canonicalize + directory containment check |
| F4 | SSRF | CWE-918 [domain] | User-supplied URL fetched by plugin | Scheme+host allowlist; block private ranges |
| F5 | Secret / credential leakage | CWE-798/547 [domain] | `.env` committed to public repo (found+untracked) | Secret scanning pre-commit + deny-by-default .gitignore (B1/B2) |
| F6 | Dependency confusion / unpinned deps | CWE-829 [domain] | `requirements.txt` listed dead Py2 deps (found+regen) | Lockfile + hash pins; review additions |
| F7 | Silent failure / swallowed exception | CWE-n/a [local] | Bare `except Exception` in `menus` (found+fixed) | Narrow except + structured logging; fail loud |
| F8 | Non-determinism / flaky tests | [local] R12 | Network calls inside tests (fixed w/ `responses`) | Deterministic mocks; hermetic suite |
| F9 | Resource leak (socket/file) | CWE-404 [domain] | IPv4 socket monkey-patch in `base.py` (guarded) | Context managers; `with` for sockets/responses |
| F10 | Race / shared mutable state | CWE-362 [domain] | Global `bi` builtins stowage across plugins | Lock or per-run isolation; fresh init in conftest |
| F11 | Integer overflow / huge input | CWE-190 [domain] | Unbounded pagination from a site | Hard caps on pages/items |
| F12 | Encoding errors | CWE-176 [domain] | UTF-8 assumption on scraped bytes (JSON-LD fix) | `errors='replace'`; detect encoding |
| F13 | Dead code / stale duplicate tree | [local] | Two parallel trees (legacy-py2 shadowed import) | Single source of truth; delete duplicates |
| F14 | API/HTML contract drift | [domain] | Site markup changed under a plugin | Contract monitors + alert on parse failure |
| F15 | Config drift / magic strings | [local] | Hardcoded menu lists (externalized to cfg) | Externalized config; schema-checked |
| F16 | Privilege/permission misuse | CWE-269/732 [domain] | Writing outside the data dir | Path containment; deny writes outside root |
| F17 | Catastrophic regex (ReDoS) | CWE-1333 [domain] | Regex on untrusted input (raw-string fixes) | Linear-time patterns; timeout |
| F18 | Archive/decompression bomb | CWE-409 [domain] | Untrusted zip/tar from release/tracker | Size + entry-count caps before extract |
| F19 | TOCTOU | CWE-367 [domain] | `exists()`-then-open on user path | Atomic open; `os.open` with O_EXCL |
| F20 | Stale state across runs | CWE-416 analog [local] | Cached `bi` state bled between tests | Fresh init per session (conftest fixture) |
| F21 | Broken auth/cookie handling | CWE-287 [local] | Inline cookie in command string (analyzer B2) | Temp header file; redact from logs |
| F22 | Supply-chain / malicious dep | CWE-506 [domain] | `cfscrape`/`selenium` optional (made lazy) | Lockfile; review; lazy/optional import |
| F23 | Runaway loop / non-termination | CWE-835 [domain] | Menu recursion on bad input (fixed w/ bounded loop) | Bounded retries; circuit breaker (T2) |
| F24 | Info exposure via logs | CWE-532 [domain] | Printing secrets to stdout | Redact; structured logging |
| F25 | Unclean crash / no graceful exit | [local] | CLI traceback on EOF (fixed w/ handler) | Signal/EOF handlers; clean exit codes |
| F26 | Test-environment coupling | [local] | Hardcoded `/home/owner/.../.venv/bin/python` (CI caught) | `sys.executable`; portable paths |
| F27 | Version skew (Py2/Py3) | [domain] | Incomplete 2to3 migration | Single Py3 target; CI matrix 3.11–3.13 |

## 2. Root-cause clusters (consolidated)

- **RC-A Boundary trust**: F1,F3,F4,F12,F14,F17,F21 — all stem from trusting
  untrusted external data without validation/encoding. Fix: validate-encode-contain at
  every I/O boundary (skill `osint-input-harden`).
- **RC-B State hygiene**: F7,F10,F20,F25 — global mutable state + silent failures.
  Fix: isolation + loud failure + fresh init.
- **RC-C Supply & deps**: F5,F6,F22 — secrets/deps leaked or unpinned. Fix:
  secret scanning + lockfile + lazy optional deps.
- **RC-D Determinism & tests**: F8,F26 — non-hermetic tests. Fix: mocks + portable paths + CI.
- **RC-E Resource & loop bounds**: F9,F11,F18,F23 — unbounded or leaked resources.
  Fix: caps + context managers + bounded loops.
- **RC-F Duplication/drift**: F13,F15,F27 — parallel trees / magic strings / version skew.
  Fix: single source of truth + externalized config + CI matrix.

## 3. Project risk register (consolidated dispositions)

Carried from RAID (R1–R5) and the failure modes above. Status: Closed / Mitigated / Open.

| ID | Risk | Root cause cluster | Status | Control |
|----|------|--------------------|--------|---------|
| PR-1 | Secret leak to public repo | RC-C | Closed | `.env` untracked + gitignored; secret_gate-style deny-list |
| PR-2 | Import shadow from legacy tree | RC-F | Closed | legacy-py2 deleted; single `src/` tree |
| PR-3 | Silent menu crash on bad input | RC-B | Closed | bounded re-prompt loop + EOF/Interrupt handler |
| PR-4 | Non-hermetic / flaky tests | RC-D | Closed | `responses` mocks; `sys.executable` (CI green) |
| PR-5 | Unpinned/stale deps | RC-C | Mitigated | `requirements.txt` regenerated from setup.py; extras |
| PR-6 | SSRF via user URL | RC-A | Mitigated (new skill) | `osint-input-harden` skill enforces allowlist |
| PR-7 | ReDoS on untrusted regex | RC-A | Mitigated | raw-string fixes; linear patterns |
| PR-8 | Archive bomb in release | RC-E | Mitigated (new skill) | size/entry caps in `release/make_torrent.py` review |
| PR-9 | Stale `bi` state bleed | RC-B | Mitigated | conftest fresh-init fixture |
| PR-10 | Contract drift vs sites | RC-F | Open (monitored) | contract monitors recommended; alert on parse fail |
| PR-11 | Supply-chain malicious dep | RC-C | Mitigated | lazy optional deps; lockfile review |
| PR-12 | Runaway loop | RC-E | Mitigated | bounded loops (T2 circuit breaker) |

## 4. How the 12 new OSINT skills address these

Each new skill encodes a control for one-or-more clusters:
- `osint-input-harden` → RC-A (F1,F3,F4,F17)
- `osint-secret-hygiene` → RC-C (F5,F24)
- `osint-dependency-audit` → RC-C (F6,F22)
- `contract-monitor` (general reliability control, not OSINT-specific) → RC-F/PR-10 (F14)
- `osint-deterministic-test` → RC-D (F8,F26)
- `osint-state-isolation` → RC-B (F7,F10,F20,F25)
- `osint-resource-bounds` → RC-E (F9,F11,F18,F23)
- `osint-config-single-source` → RC-F (F13,F15,F27)
- (domain skills below are orthogonal data-source capabilities, each with the
  hardening controls baked in)
