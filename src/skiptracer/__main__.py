import sys
import argparse

from .skiptracer import SkipTracer
from .banner import Banner
from . import __version__ as VERSION


def build_parser():
    """POSIX-ish argument parser for the skiptracer CLI."""
    p = argparse.ArgumentParser(
        prog="skiptracer",
        description="Skiptracer - OSINT web-scraping framework (Python 3).",
    )
    p.add_argument(
        "-V", "--version",
        action="version",
        version="skiptracer %s" % VERSION,
    )
    p.add_argument(
        "-n", "--no-banner",
        action="store_true",
        help="skip the ASCII banner on startup",
    )
    return p


def main(argv=None):
    """Start skip tracer. Returns a process exit code (int)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    plugins = 'all'
    if not args.no_banner:
        Banner().banner()
    SkipTracer(plugins)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n [!] Interrupted -- exiting.")
        sys.exit(130)
