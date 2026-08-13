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

Safety
- Public sources only. Respect ToS and robots.txt. Pause and notify human on paywalls or unredacted PII.

Files
- tools/agent_adapters.py: adapter implementation
- test/test_agent_adapters.py: unit tests

