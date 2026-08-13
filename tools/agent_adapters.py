"""Hermes-brain style agent adapters for skiptracer plugins.
Provides: list_available_tools, parallel_probe, call_with_retries, verify_match,
             synthesize, persist_summary, human_escalate, enrich_email (example).
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import builtins as bi
from typing import List, Dict, Any
import importlib.metadata as imd

from skiptracer.skiptracer import SkipTracer
from skiptracer.plugins.base import PageGrabber
from skiptracer.datasaver import DataSaver

_pg = PageGrabber()

def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def list_available_tools(group: str = "skiptracer.plugins") -> List[str]:
    eps = imd.entry_points()
    if hasattr(eps, "select"):
        sel = eps.select(group=group)
    else:
        sel = eps.get(group, [])
    return [e.name for e in sel]


def call_plugin(plugin_name: str, input_value: str, plugin_group: str = "skiptracer.plugins") -> Dict[str, Any]:
    res = {"tool": plugin_name, "input": input_value, "ts": now_ts(), "ok": False, "raw": None, "parsed": None, "error": None}
    try:
        plugin_map = SkipTracer.load_plugins(plugin_group)
        if plugin_name not in plugin_map:
            res["error"] = "not_installed"
            return res
        PluginCls = plugin_map[plugin_name]
        inst = PluginCls()
        if hasattr(inst, "get_info"):
            raw = inst.get_info(input_value, None)
        elif hasattr(inst, "run"):
            raw = inst.run(input_value)
        else:
            raw = None
        res["raw"] = raw
        res["parsed"] = raw
        res["ok"] = True
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {e}"
    return res


def call_with_retries(tool_name: str, arg: str, tries: int = 3, base_delay: float = 0.5, **kwargs) -> Dict[str, Any]:
    out = None
    for attempt in range(1, tries + 1):
        out = call_plugin(tool_name, arg, **kwargs)
        if out.get("ok") or attempt == tries:
            return out
        sleep = base_delay * (2 ** (attempt - 1)) + random.random() * 0.1
        time.sleep(sleep)
    return out


def parallel_probe(tool_names: List[str], identifier: str, max_workers: int = 4, retries: int = 2) -> List[Dict[str, Any]]:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(call_with_retries, t, identifier, tries=retries): t for t in tool_names}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append({"tool": futures[fut], "ok": False, "error": str(e)})
    return results


def verify_match(m: Dict[str, Any], expected_tokens: List[str] = None) -> Dict[str, Any]:
    m = dict(m)
    m.setdefault("verification", {})
    raw = m.get("raw")
    url = None
    if isinstance(raw, str) and raw.startswith("http"):
        url = raw
    elif isinstance(raw, dict):
        url = raw.get("url")
    if not url:
        m["verification"]["fetched"] = False
        return m
    try:
        src = _pg.get_source(url)
        m["verification"]["fetched"] = True
        if expected_tokens:
            m["verification"]["tokens_found"] = {t: (t in src) for t in expected_tokens}
        m["verification"]["snippet"] = src[:200]
    except Exception as e:
        m["verification"]["fetched"] = False
        m["verification"]["error"] = str(e)
    return m


def synthesize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {"ts": now_ts(), "matches": [], "confidence": 0.0}
    for r in results:
        score = 0.0
        if r.get("ok"):
            score += 0.5
        if r.get("parsed"):
            score += 0.3
        if r.get("verification", {}).get("fetched"):
            score += 0.2
        r["score"] = round(score, 2)
        summary["matches"].append(r)
    if summary["matches"]:
        summary["confidence"] = round(sum(m["score"] for m in summary["matches"]) / len(summary["matches"]), 2)
    return summary


def persist_summary(summary: Dict[str, Any], filename_prefix: str = "agent-out") -> Any:
    bi.outdata = summary
    # programmatic, safe write: set filename and call writeout on a raw instance
    bi.filename = f"{filename_prefix}-{int(time.time())}.json"
    ds = DataSaver.__new__(DataSaver)
    try:
        return ds.writeout()
    except Exception:
        return None


def human_escalate(summary: Dict[str, Any], reason: str = "sensitive"):
    print("HUMAN_ESCALATE:", reason, summary.get("confidence"), len(summary.get("matches", [])))


# example convenience
def enrich_email(email: str):
    email = email.strip().lower()
    tools = ["haveibeenpwned", "whoismind", "linkedin"]
    raw_results = parallel_probe(tools, email, max_workers=3, retries=2)
    verified = [verify_match(r, expected_tokens=[email.split("@")[0]]) for r in raw_results]
    summary = synthesize(verified)
    if any("SSN" in str(m.get("raw", "")) or m.get("score", 0) > 0.9 for m in summary["matches"]):
        human_escalate(summary, "high_confidence_or_sensitive")
    rel = persist_summary(summary, filename_prefix=f"email-{email.replace('@','_')}")
    return {"summary": summary, "saved": rel}
