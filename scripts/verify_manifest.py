#!/usr/bin/env python3
"""Verify every file bound by the replication-package SHA-256 manifest."""

from __future__ import annotations

import hashlib
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]


def main() -> None:
    failures = []
    listed = set()
    for line in (PACKAGE / "MANIFEST.sha256").read_text(encoding="ascii").splitlines():
        expected, relative = line.split("  ", 1)
        listed.add(relative)
        path = PACKAGE / relative
        observed = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
        if observed != expected:
            failures.append((relative, expected, observed))
    observed_files = {
        str(path.relative_to(PACKAGE))
        for path in PACKAGE.rglob("*")
        if path.is_file()
        and path.name not in {"MANIFEST.sha256", ".DS_Store"}
        and ".git" not in path.relative_to(PACKAGE).parts
        and "__pycache__" not in path.relative_to(PACKAGE).parts
        and path.suffix not in {".pyc", ".pyo"}
    }
    for relative in sorted(observed_files - listed):
        failures.append((relative, "not listed", "present"))
    for relative in sorted(listed - observed_files):
        if not any(item[0] == relative for item in failures):
            failures.append((relative, "listed", "missing"))
    if failures:
        for relative, expected, observed in failures:
            print(f"FAIL {relative}: expected {expected}, observed {observed}")
        raise SystemExit(1)
    print("PASS: replication-package manifest verified")


if __name__ == "__main__":
    main()
