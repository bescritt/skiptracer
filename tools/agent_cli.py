"""Headless CLI wrapper for agent adapters.
Usage examples:
  python -m tools.agent_cli enrich-email --email alice@example.com --output out.json
  echo alice@example.com | python -m tools.agent_cli enrich-email --stdin --output -
"""
import sys
import argparse
import json
from typing import Optional
from . import agent_adapters as aa


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="agent-cli", description="Headless agent adapter CLI")
    p.add_argument("--version", action="version", version="agent-cli 1.0")
    p.add_argument("--yes", "-y", action="store_true", help="Assume yes for interactive confirmations")
    sp = p.add_subparsers(dest="cmd", required=True)

    # common options
    def add_common(sub):
        sub.add_argument("output", nargs="?", help="Write JSON output to file (use '-' for stdout). If omitted prints to stdout.")
        sub.add_argument("--no-save", action="store_true", help="Do not persist results via DataSaver")
        sub.add_argument("--format", choices=["json"], default="json", help="Output format")
        sub.add_argument("--quiet", "-q", action="store_true", help="Minimal terminal noise")

    # enrich-email
    e = sp.add_parser("enrich-email", help="Enrich an email address")
    add_common(e)
    e.add_argument("identifier", nargs="?", help="Email address to enrich, or '-' to read stdin")

    # map-screenname
    m = sp.add_parser("map-screenname", help="Map a handle/screenname across platforms")
    add_common(m)
    m.add_argument("identifier", nargs="?", help="Screenname/handle, or '-' to read stdin")

    # reverse-phone
    r = sp.add_parser("reverse-phone", help="Reverse-lookup a phone number")
    add_common(r)
    r.add_argument("identifier", nargs="?", help="Phone number, or '-' to read stdin")

    # plate-lookup
    pl = sp.add_parser("plate-lookup", help="Lookup a license plate/VIN")
    add_common(pl)
    pl.add_argument("identifier", nargs="?", help="Plate/VIN, or '-' to read stdin")

    return p.parse_args(argv)


def read_stdin_value() -> Optional[str]:
    data = sys.stdin.read()
    if not data:
        return None
    return data.strip()


def resolve_identifier(arg_val: Optional[str]) -> Optional[str]:
    if arg_val is None:
        return None
    if arg_val == '-':
        return read_stdin_value()
    return arg_val


def run_action(args) -> dict:
    cmd = args.cmd
    ident = None

    if cmd == "enrich-email":
        ident = resolve_identifier(args.identifier)
        if not ident:
            # fallback: if stdin contains data, use it
            ident = read_stdin_value()
        if not ident:
            raise SystemExit("email required (positional arg or '-' for stdin)")
        out = aa.enrich_email(ident)
    elif cmd == "map-screenname":
        handle = resolve_identifier(args.identifier)
        if not handle:
            raise SystemExit("handle required (positional arg or '-' for stdin)")
        tools = ["twitter", "knowem", "namechk2", "tinder"]
        raw = aa.parallel_probe(tools, handle, max_workers=4, retries=2)
        verified = [aa.verify_match(r, expected_tokens=[handle]) for r in raw]
        out = aa.synthesize(verified)
        if not args.no_save:
            aa.persist_summary(out, filename_prefix=f"handle-{handle}")
    elif cmd == "reverse-phone":
        phone = resolve_identifier(args.identifier)
        if not phone:
            raise SystemExit("phone required (positional arg or '-' for stdin)")
        tools = ["true_people", "who_call_id", "fouroneone_info"]
        raw = aa.parallel_probe(tools, phone, max_workers=3, retries=2)
        verified = [aa.verify_match(r, expected_tokens=[phone]) for r in raw]
        out = aa.synthesize(verified)
        if not args.no_save:
            aa.persist_summary(out, filename_prefix=f"phone-{phone}")
    elif cmd == "plate-lookup":
        plate = resolve_identifier(args.identifier)
        if not plate:
            raise SystemExit("plate required (positional arg or '-' for stdin)")
        tools = ["plate", "advance_background_checks"]
        raw = aa.parallel_probe(tools, plate, max_workers=2, retries=2)
        verified = [aa.verify_match(r, expected_tokens=[plate]) for r in raw]
        out = aa.synthesize(verified)
        if not args.no_save:
            aa.persist_summary(out, filename_prefix=f"plate-{plate}")
    else:
        raise SystemExit("unknown command")
    return out

def main(argv=None):
    args = parse_args(argv)
    try:
        out = run_action(args)
    except SystemExit as e:
        # argparse/SystemExit path
        print(e, file=sys.stderr)
        return 2

    # output
    # handle output writing: positional 'output' arg (file or '-')
    outfile = getattr(args, 'output', None)
    if outfile == '-' or outfile is None:
        print(json.dumps(out, indent=2))
    else:
        try:
            with open(outfile, 'w', encoding='utf-8') as fh:
                json.dump(out, fh, indent=2)
        except Exception as e:
            print(f"Failed to write output file: {e}", file=sys.stderr)
            return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
