"""Run data validators V1 to V14 (Data Model §13). Exit 1 on any FAIL.

Run: .venv/bin/python mock-data/validate.py [--scale 5]
--scale 5 validates the git-ignored 5,000+ variant benchmark set (build it first).
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from backend.catalogue.validators import GENERATED, load_context, run_all  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=1)
    args = ap.parse_args()
    folder = GENERATED if args.scale == 1 else next(GENERATED.glob("scale_*"))
    print(f"validating {folder.relative_to(GENERATED.parent.parent)} (scale {args.scale})")
    results = run_all(load_context(folder, scale=args.scale))
    for r in results.values():
        print(f"{r.vid:<4} {r.status:<8} {r.title}" + (f"  [{r.note}]" if r.note else ""))
        for e in r.errors[:10]:
            print(f"       - {e}")
        if len(r.errors) > 10:
            print(f"       ... {len(r.errors) - 10} more")
    counts = {s: sum(r.status == s for r in results.values()) for s in ("PASS", "FAIL", "NOT RUN")}
    print("summary: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
