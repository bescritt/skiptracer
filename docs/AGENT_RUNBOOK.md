Agent Runbook — Hermes-brain style usage for skiptracer

Purpose
- Quick reference for autonomous agents using this fork's plugins via tools/agent_adapters.py.

Work pattern
1. Plan: define goal, constraints (public-only), and escalation rules.
2. Normalize input (email/handle/phone).
3. Probe: run 2–4 complementary probes in parallel (parallel_probe).
4. Verify: fetch candidate pages with PageGrabber and check tokens (verify_match).
5. Synthesize: compute simple confidence (synthesize) and persist (persist_summary).
6. Escalate: call human_escalate for PII or high-confidence sensitive results.

Quick commands
- Use tools.agent_adapters.enrich_email("a@b.com") for an example flow.
- Enumerate installed tools with tools.agent_adapters.list_available_tools().
- Install package and use the native CLI: pip install . && agent-cli enrich-email -

Safety
- Public sources only. Respect ToS and robots.txt. Pause and notify human on paywalls or unredacted PII.

HIBP plugin
- The haveibeenpwned plugin now uses the official HIBP v3 API and requires an API key.
- Set HAVEIBEENPWNED_API_KEY or HIBP_API_KEY in the environment (or provide via .env) before using the plugin or the `enrich-email` CLI.
- The plugin no longer depends on cfscrape and parses JSON safely.

HIBP smoke test
- A live smoke test is available at test/test_hibp_smoke.py. It runs only when HAVEIBEENPWNED_API_KEY or HIBP_API_KEY is present in the environment, otherwise it is skipped.
- To run the smoke test locally with your key:

  $ export HAVEIBEENPWNED_API_KEY=\"your_key_here\"
  $ .venv/bin/activate && pytest -q test/test_hibp_smoke.py

Namechk2 resilience
- namechk2 now detects common anti-bot responses (403/429, captcha/cloudflare challenge, "please enable javascript", etc.) and returns {'blocked': True, 'reason': ...} so agents can escalate or fallback.

Namechk2 note
- `namechk2` performs POSTs to namechk.com which may block automated requests; treat it as fragile. Agents should detect blocking, respect rate limits, and escalate to human review if automated access fails.

Files
- skiptracer.tools.agent_adapters: adapter implementation (now programmatic persist control)
- skiptracer.tools.agent_cli: headless CLI
- src/skiptracer/plugins/haveibeenpwned: updated to use HIBP v3 API (API key required)
- test/test_agent_adapters.py: unit tests
- test/test_agent_cli.py: CLI tests

