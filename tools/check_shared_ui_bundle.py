#!/usr/bin/env python3
"""Check a vendored herdr_shared_ui directory against the canonical bundle."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "herdr_shared_ui"

def package_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "PIN" and "__pycache__" not in p.parts):
        relative = path.relative_to(directory).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", nargs="*", type=Path, help="plugin herdr_shared_ui directories")
    parser.add_argument("--sync", action="store_true", help="copy canonical package files into the listed bundles before checking")
    args = parser.parse_args()
    version = (CANONICAL / "VERSION").read_text(encoding="utf-8").strip()
    digest = package_digest(CANONICAL)
    pin = (CANONICAL / "PIN").read_text(encoding="utf-8").split()
    if pin != [version, f"sha256:{digest}"]:
        print(f"canonical PIN mismatch: expected {version} sha256:{digest}")
        return 1
    if args.sync and not args.bundles:
        parser.error("--sync requires one or more bundle paths")
    ok = True
    for bundle in args.bundles:
        bundle = bundle.resolve()
        if args.sync:
            bundle.mkdir(parents=True, exist_ok=True)
            for source in CANONICAL.rglob("*"):
                if not source.is_file() or "__pycache__" in source.parts:
                    continue
                destination = bundle / source.relative_to(CANONICAL)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        if not bundle.is_dir() or package_digest(bundle) != digest:
            print(f"stale or divergent bundle: {bundle}")
            ok = False
        else:
            print(f"{bundle}: {version} sha256:{digest} OK")
    if not args.bundles:
        print(f"canonical: {version} sha256:{digest} OK")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
