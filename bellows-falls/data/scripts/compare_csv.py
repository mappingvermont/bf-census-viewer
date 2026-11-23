"""Compare a test transcription with a reference one, cell by cell.

Usage: python3 -I scripts/compare_csv.py transcribed/259-43A.csv test_bedrock/259-43A.csv

Rows are matched by line number. The uncertain and notes columns are ignored.
"""
import csv
import sys
from collections import Counter

SKIP = {"uncertain", "notes"}


def load(path):
    with open(path, newline="") as f:
        return {r["line"]: r for r in csv.DictReader(f)}


def main(ref_path, test_path):
    ref, test = load(ref_path), load(test_path)
    cols = [c for c in next(iter(ref.values())) if c not in SKIP]
    diffs, per_col, cells = [], Counter(), 0
    for line in sorted(set(ref) | set(test), key=lambda x: int(x)):
        if line not in test or line not in ref:
            diffs.append(f"  line {line}: only in {'reference' if line in ref else 'test'}")
            continue
        for c in cols:
            cells += 1
            a, b = ref[line][c].strip(), test[line][c].strip()
            if a != b:
                per_col[c] += 1
                flag = " (test flagged row uncertain)" if test[line]["uncertain"] == "1" else ""
                diffs.append(f"  line {line} {c}: ref={a!r} test={b!r}{flag}")
    n = sum(per_col.values())
    print(f"{test_path}: {n} of {cells} cells differ ({100 * (1 - n / max(cells, 1)):.1f}% match)")
    if per_col:
        print("  by column: " + ", ".join(f"{c} {k}" for c, k in per_col.most_common()))
    print("\n".join(diffs))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
