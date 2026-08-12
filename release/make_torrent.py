#!/usr/bin/env python3
"""Generate a public, multi-tracker .torrent for a Skiptracer release file.

Uses the `torf` library (stable, BSD-licensed) for spec-correct bencoding and
piece hashing. Tracker list is sourced from ngosang/trackerslist (GitHub), the
de-facto community list of public trackers.

Usage:
    python3 make_torrent.py <file-or-dir> [output.torrent]
"""
import sys
import urllib.request

import torf

# ngosang/trackerslist — curated public tracker lists (best + all_udp).
TRACKER_SOURCES = [
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_udp.txt",
]

PIECE_LENGTH = 256 * 1024  # 256 KiB pieces — standard for releases < 1 GiB
NAME = "skiptracer-4.0.0"
COMMENT = ("Skiptracer v4.0.0 (Python 3, Mission-Critical) — OSINT "
           "web-scraping framework (Apache-2.0)")
CREATED_BY = "skiptracer-release-tool/1.0 (torf)"


def fetch_trackers():
    seen = []
    for url in TRACKER_SOURCES:
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                text = r.read().decode("utf-8", "replace")
            for line in text.splitlines():
                t = line.strip()
                if t and t not in seen:
                    seen.append(t)
        except Exception as e:
            print("  [warn] tracker source failed: %s (%s)" % (url, e))
    return seen


def main():
    if len(sys.argv) < 2:
        print("usage: make_torrent.py <file-or-dir> [output.torrent]")
        return 2
    target = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else target.rstrip("/") + ".torrent"

    print("Fetching public trackers from ngosang/trackerslist ...")
    trackers = fetch_trackers()
    print("  %d unique trackers" % len(trackers))

    torrent = torf.Torrent(
        path=target,
        name=NAME,
        piece_size=PIECE_LENGTH,
        comment=COMMENT,
        created_by=CREATED_BY,
        trackers=[trackers],  # single tier with all announce URLs
    )
    # Private=0 (default) => public torrent; DHT/PEX enabled by omission.
    torrent.private = False

    # torf.generate() raises on failure; validate() returns None/True on a
    # well-formed torrent, so we treat "no exception" as success.
    try:
        torrent.generate()
    except Exception as e:
        print("  [ERROR] torrent generation failed: %s" % e)
        return 1

    try:
        torrent.write(out, overwrite=True)
    except Exception as e:
        print("  [ERROR] torrent write failed: %s" % e)
        return 1

    print("Wrote %s" % out)
    print("  name      : %s" % torrent.name)
    print("  size      : %d bytes" % torrent.size)
    print("  pieces    : %d" % torrent.pieces)
    print("  files     : %d" % len(torrent.files))
    print("  trackers  : %d" % len(trackers))
    print("  info_hash : %s" % torrent.infohash)
    print("  magnet    : %s" % torrent.magnet())
    return 0


if __name__ == "__main__":
    sys.exit(main())
