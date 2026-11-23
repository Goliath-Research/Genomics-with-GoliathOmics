"""Teaching helpers for Module 5: why bisulfite reads need three-letter alignment.

The reference is synthetic (seeded random bases). No real genome or patient sequence is used.
"""

from __future__ import annotations

import random


def synthetic_reference(length: int = 2000, seed: int = 7, cpg_boost: float = 0.0) -> str:
    rng = random.Random(seed)
    seq = [rng.choice("ACGT") for _ in range(length)]
    for i in range(0, length - 1):
        if cpg_boost and seq[i] == "C" and rng.random() < cpg_boost:
            seq[i + 1] = "G"
    return "".join(seq)


def c_to_t(seq: str) -> str:
    return seq.upper().replace("C", "T")


def mismatches(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def best_hits(read: str, reference: str, three_letter: bool = False) -> list[tuple[int, int]]:
    """All (position, mismatches) ties for the best ungapped placement of ``read``.

    With ``three_letter`` both read and reference are compared in C->T space, the approach used by
    bwa-meth-style aligners (index a C->T converted reference, convert the read the same way).
    """
    ref = c_to_t(reference) if three_letter else reference.upper()
    rd = c_to_t(read) if three_letter else read.upper()
    scores = [(pos, mismatches(rd, ref[pos : pos + len(rd)])) for pos in range(len(ref) - len(rd) + 1)]
    best = min(s for _, s in scores)
    return [(p, s) for p, s in scores if s == best]


def mapq_like(hits: list[tuple[int, int]], second_best: int | None, read_len: int) -> int:
    """A rough MAPQ intuition: 0 when tied, higher when the runner-up is far worse (capped at 60)."""
    if len(hits) > 1:
        return 0
    if second_best is None:
        return 60
    gap = second_best - hits[0][1]
    return max(0, min(60, int(60 * gap / max(read_len // 10, 1))))


def second_best(read: str, reference: str, three_letter: bool, exclude: int) -> int | None:
    ref = c_to_t(reference) if three_letter else reference.upper()
    rd = c_to_t(read) if three_letter else read.upper()
    others = [mismatches(rd, ref[p : p + len(rd)]) for p in range(len(ref) - len(rd) + 1) if p != exclude]
    return min(others) if others else None
