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
            bi.filename = input(
                "[Please provide the filename for output? "
                "(somefile.txt|somefile.json)]: ")
        self.writeout()

    def writeout(self):
        """Write collected data to disk and report status to STDOUT."""
        if not getattr(bi, "filename", None):
            # No output filename was chosen (user declined saving) -> no-op.
            return None
        try:
            with open(bi.filename, "w") as pg:
                pg.write(json.dumps(bi.outdata, indent=2))
            print(
                ("  [{}X{}] {} Output written to disk: ./{}\n{}").format(
                    bc.CRED, bc.CEND, bc.CYLW, bi.filename, bc.CEND))
        except Exception as nowriteJSON:
            if bi.debug:
                print(
                    ("  [{}X{}] {}Output failed to write to disk {}\n{}").format(
                        bc.CRED, bc.CEND, bc.CYLW, nowriteJSON, bc.CEND))
            else:
                print(
                    ("  [{}X{}] {}Output failed to write to disk {}\n{}").format(
                        bc.CRED, bc.CEND, bc.CYLW, bi.filename, bc.CEND))
