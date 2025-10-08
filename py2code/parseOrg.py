"""
Very small Org-mode table/header parser.

Improvements over the original:
- Class is now `ParserOrg` and supports passing either a filename or a file-like object.
- Context manager support (use `with ParserOrg(...) as p:`).
- Safer parsing of headers, tables and variables.
- Returns parsed items from `parse()` and stores vars on `vars`.
- Backwards-compatible alias `ParseOrg` preserved.
"""

import logging
import re
from typing import IO, List, Sequence, Tuple, Union, Optional
import os

clock_re = re.compile(r"CLOCK: \[(\d{4}-\d{2}-\d{2}) [^\]]+\]--\[.*?\] =>\s+([\d:]+)")
header_re = re.compile(r"^(\*+)\s+(?:TODO\s+|DONE\s+)?(.*)")

class OrgHeader:
    """Represents an org-mode header (a line starting with one or more '*')."""
    def __init__(self, level: int, name: str) -> None:
        self.level = level
        self.name = name.strip()
        self.items: List[object] = []

    def add(self, child: object) -> None:
        self.items.append(child)

    def __repr__(self) -> str:
        return f"<H{self.level} {self.name!r} childs={len(self.items)}>"

class OrgClock:
    """Represents a CLOCK entry."""
    def __init__(self, line: str) -> None:
        m = clock_re.match(line)
        if not m:
            raise ValueError(f"Invalid CLOCK line: {line}")
        self.start = m.groups(1)[0]  # YYYY-MM-DD
        self.duration = m.groups(1)[1]  # HH:MM

    def __repr__(self) -> str:
        return f"<Clock {self.start} {self.duration}>"

class OrgTable:
    """Simple container for table rows. Rows are lists of cell strings."""
    def __init__(self) -> None:
        self.rows: List[List[str]] = []

    def add_row(self, row: Sequence[str]) -> None:
        self.rows.append(list(row))

    def __repr__(self) -> str:
        return f"<Table rows={len(self.rows)}>"


class ParserOrg:
    """Parser for a tiny subset of Emacs org-mode used by this project.

    Usage:
      p = ParserOrg(path_or_file)
      p.parse()
      items = p.items

    or as a context manager:
      with ParserOrg(path) as p:
          items = p.parse()

    The parser focuses on headers (lines starting with '*'), tables (lines
    beginning with '|') and file-local variables (lines starting with '#+').
    """

    def __init__(self, source: Union[str, os.PathLike, IO[str]]) -> None:
        if isinstance(source, (str, os.PathLike)):
            # open file ourselves
            self._f = open(str(source), "rt", encoding="utf-8")
            self._own_file = True
        else:
            # assume file-like object
            self._f = source
            self._own_file = False

        self.items: List[object] = []
        self.vars: dict = {}

    def __enter__(self) -> "ParserOrg":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if getattr(self, "_own_file", False):
            try:
                self._f.close()
            except Exception:
                logging.exception("Failed to close org file")

    # keep backwards-compatible name
    ParseOrg = None

    def parse_table(self, line: str) -> OrgTable:
        """Parse consecutive table lines starting from `line` (which should
        start with '|'). Returns an OrgTable object. The file pointer will be
        left at the first non-table line.
        """
        tbl = OrgTable()
        # line may have trailing newline
        while line is not None and line.lstrip().startswith("|"):
            text = line.strip()
            if not text.startswith("|-") and len(text) > 1:
                # remove leading and trailing pipe if present
                if text.endswith("|"):
                    core = text[1:-1]
                else:
                    core = text[1:]
                cells = [c.strip() for c in core.split("|")]
                tbl.add_row(cells)
            # read next line
            line = self._f.readline()

            if line == "":
                # EOF - break and return
                break

        # If we stopped on a non-empty non-table line, move the file cursor
        # back so the outer loop can process it. We can approximate by using
        # tell/seek only for real files; for other file-likes we keep the
        # leftover line in a small attribute.
        if line and not line.lstrip().startswith("|"):
            # store leftover line for next parse step
            self._last_line = line
        else:
            self._last_line = None

        return tbl

    def parse_header(self, line: str) -> OrgHeader:
        """Parse a header line like "*** Heading text" into an OrgHeader."""
        m = re.match(r"^(\*+)(?:\s+(.+))?", line)
        if m:
            level = len(m.group(1))
            name = m.group(2) or ""
            return OrgHeader(level, name)
        # fallback: treat whole line as name with level 0
        return OrgHeader(0, line.strip())

    def parse(self) -> List[object]:
        """Parse the opened file and return a list of top-level items.

        Items are instances of OrgHeader (which has .items) or OrgTable.
        File-local variables are stored in `self.vars`.
        """
        # Reset state
        self.items = []
        self.vars = {}
        cur_header: Optional[OrgHeader] = None
        self._last_line = None

        while True:
            if self._last_line is not None:
                raw = self._last_line
                self._last_line = None
            else:
                raw = self._f.readline()

            if raw == "":
                break

            # keep the original for pattern checks
            line = raw.rstrip("\n")
            if line.strip() == "":
                # empty line
                continue

            if line.lstrip().startswith("|"):
                # table
                if cur_header is None:
                    # create a root header so existing callers that expect
                    # tables to be under headers still work
                    cur_header = OrgHeader(0, "")
                    self.items.append(cur_header)

                table = self.parse_table(line)
                cur_header.add(table)

            elif line.startswith("*"):
                # header
                cur_header = self.parse_header(line)
                self.items.append(cur_header)

            elif line.startswith("CLOCK:"):
                self.items.append(OrgClock(line))

            elif line.startswith("#+"):
                # file variable - split at first ':' for safety
                tail = line[2:]
                if ":" in tail:
                    name, value = tail.split(":", 1)
                    self.vars[name.strip().lower()] = value.strip()
                else:
                    logging.debug("Unrecognized variable line: %r", line)

            else:
                logging.debug("Invalid org item: %r", line)

        # close the file if we opened it
        self.close()
        return self.items


# Backwards compatibility: old name ParseOrg
ParseOrg = ParserOrg
