"""Teaching helpers for Module 4: FASTQ, SAM flags and CIGAR strings (pure Python)."""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from pathlib import Path

ADAPTER_TRUSEQ = "AGATCGGAAGAGC"  # common prefix of the Illumina TruSeq adapters
FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"


@dataclass(frozen=True)
class FastqRecord:
    name: str
    seq: str
    qual: str

    def phred(self, offset: int = 33) -> list[int]:
        return [ord(c) - offset for c in self.qual]


def read_fastq(path: str | Path, limit: int | None = None) -> list[FastqRecord]:
    opener = gzip.open if str(path).endswith(".gz") else open
    records: list[FastqRecord] = []
    with opener(path, "rt") as handle:
        while limit is None or len(records) < limit:
            header = handle.readline().rstrip("\n")
            if not header:
                break
            seq = handle.readline().rstrip("\n")
            plus = handle.readline().rstrip("\n")
            qual = handle.readline().rstrip("\n")
            if not header.startswith("@") or not plus.startswith("+") or len(seq) != len(qual):
                raise ValueError(f"malformed FASTQ record near {header!r}")
            records.append(FastqRecord(header[1:], seq, qual))
    return records


def base_composition(records: list[FastqRecord]) -> dict[str, float]:
    total = sum(len(r.seq) for r in records) or 1
    return {b: sum(r.seq.count(b) for r in records) / total for b in "ACGTN"}


def q30_percent(records: list[FastqRecord]) -> float:
    quals = [q for r in records for q in r.phred()]
    return 100.0 * sum(q >= 30 for q in quals) / max(len(quals), 1)


def per_cycle_mean_quality(records: list[FastqRecord]) -> list[float]:
    length = max(len(r.seq) for r in records)
    sums = [0] * length
    counts = [0] * length
    for r in records:
        for i, q in enumerate(r.phred()):
            sums[i] += q
            counts[i] += 1
    return [s / c for s, c in zip(sums, counts) if c]


def adapter_fraction(records: list[FastqRecord], adapter: str = ADAPTER_TRUSEQ) -> float:
    return sum(adapter in r.seq for r in records) / max(len(records), 1)


SAM_FLAGS = [
    (0x1, "paired"),
    (0x2, "proper_pair"),
    (0x4, "unmapped"),
    (0x8, "mate_unmapped"),
    (0x10, "reverse"),
    (0x20, "mate_reverse"),
    (0x40, "first_in_pair"),
    (0x80, "second_in_pair"),
    (0x100, "secondary"),
    (0x200, "qc_fail"),
    (0x400, "duplicate"),
    (0x800, "supplementary"),
]


def decode_flag(flag: int) -> list[str]:
    if flag < 0 or flag > 0xFFF:
        raise ValueError("SAM FLAG is a 12-bit value")
    return [name for bit, name in SAM_FLAGS if flag & bit]


CIGAR_RE = re.compile(r"(\d+)([MIDNSHP=X])")
CONSUMES_REF = set("MDN=X")
CONSUMES_READ = set("MIS=X")


def parse_cigar(cigar: str) -> list[tuple[int, str]]:
    ops = [(int(n), op) for n, op in CIGAR_RE.findall(cigar)]
    if "".join(f"{n}{op}" for n, op in ops) != cigar:
        raise ValueError(f"invalid CIGAR {cigar!r}")
    return ops


def cigar_lengths(cigar: str) -> tuple[int, int]:
    """(reference span, read length consumed)"""
    ops = parse_cigar(cigar)
    return (sum(n for n, op in ops if op in CONSUMES_REF), sum(n for n, op in ops if op in CONSUMES_READ))
