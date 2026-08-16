"""Persist scraped results to disk as JSON/CSV."""
import json
import builtins as bi
from .colors.default_colors import DefaultBodyColors as bc


class DataSaver:
    """Collects results from plugins and writes them to disk on request."""

    def __init__(self):
        bi.outdata = dict()
        bi.output = ''
        self.webproxy = input(
            "[Do we wish to enable proxy support? (Y/n)]: ")
        bi.output = input(
            "[Do we wish to save returned data to disk? (Y/n)]: ")
        if str(bi.output).lower() == "y":
            raw = input(
                "[Please provide the filename for output? "
                "(somefile.txt|somefile.json)]: ")
            # Guard against path traversal: reject bare filenames that escape
            # the working directory via '..' or absolute paths.
            if raw.startswith("/") or raw.startswith(".."):
                print("[!] Unsafe filename rejected, using default.")
                raw = "output.json"
            bi.filename = raw
        self.writeout()

    def writeout(self):
        """Write collected data to disk and report status to STDOUT."""
        if not getattr(bi, "filename", None):
            # No output filename was chosen (user declined saving) -> no-op.
            return None
        fname = bi.filename
        # Guard against path-traversal: reject filenames that escape
        # the current working directory via ".." or absolute paths.
        if fname.startswith("/") or fname.startswith("..") or fname.startswith("~"):
            print(
                ("  [{}X{}] {} Refusing unsafe filename: {}\n{}").format(
                    bc.CRED, bc.CEND, bc.CYLW, fname, bc.CEND))
            return None
        try:
            with open(fname, "w") as pg:
                pg.write(json.dumps(bi.outdata, indent=2))
            if bi.debug:
                print(
                    ("  [{}X{}] {} Debug: Output written to disk: ./{}\n{}").format(
                        bc.CRED, bc.CEND, bc.CYLW, fname, bc.CEND))
            else:
                print(
                    ("  [{}X{}] {} Output written to disk: ./{}\n{}").format(
                        bc.CRED, bc.CEND, bc.CYLW, fname, bc.CEND))
        except Exception as nowriteJSON:
            if bi.debug:
                print(
                    ("  [{}X{}] {}Debug: Output failed to write to disk {}\n{}").format(
                        bc.CRED, bc.CEND, bc.CYLW, nowriteJSON, bc.CEND))
            else:
                print(
                    ("  [{}X{}] {}Output failed to write to disk {}\n{}").format(
                        bc.CRED, bc.CEND, bc.CYLW, fname, bc.CEND))
