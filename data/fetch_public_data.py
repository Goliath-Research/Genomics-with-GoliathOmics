"""Fetch the public course data from ENA. Nothing here is patient or customer data.

    python data/fetch_public_data.py --verify          # check the committed fixtures
    python data/fetch_public_data.py --pairs 100000    # stream a larger subset into data/downloads/

SRR28293403 is a public whole-genome bisulfite sequencing run of the 1000 Genomes lymphoblastoid
cell line HG00621 (GEO GSE261315, BioProject PRJNA1086543). ENA serves the FASTQs without access
restrictions. The full run is about 21 GB, so the course only ever streams the first N read pairs.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "fixtures" / "manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> int:
    manifest = json.loads(MANIFEST.read_text())
    bad = 0
    for item in manifest["files"]:
        path = HERE / "fixtures" / item["file"]
        actual = sha256(path)
        ok = actual == item["sha256"]
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {item['file']} {actual[:12]}")
    return 1 if bad else 0


def stream_pairs(pairs: int, out_dir: Path) -> None:
    manifest = json.loads(MANIFEST.read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    for item in manifest["files"]:
        url = item["source_url"]
        target = out_dir / item["file"].replace(".first1000.", f".first{pairs}.")
        print(f"streaming {pairs} reads from {url}")
        with urllib.request.urlopen(url, timeout=120) as resp, gzip.open(resp) as fq, gzip.open(target, "wb") as out:
            for i, line in enumerate(fq):
                if i >= pairs * 4:
                    break
                out.write(line)
        print(f"wrote {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--pairs", type=int, default=0)
    args = parser.parse_args(argv)
    if args.verify or not args.pairs:
        return verify()
    stream_pairs(args.pairs, HERE / "downloads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
