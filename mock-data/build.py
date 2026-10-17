"""Generate the mock catalogue (variants and SKUs) from the taxonomy and lexicon.

Run: .venv/bin/python mock-data/build.py [--scale N]
Writes mock-data/generated/{variants,skus}.json (the committed 1,000+ set), or with
--scale 5 the git-ignored 5,000+ benchmark set in mock-data/generated/scale_5000/.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from backend.catalogue.generator import SEED, build_catalogue, write_catalogue  # noqa: E402
from backend.catalogue.seed import MOCK, load_lexicon, load_taxonomy  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    cat = build_catalogue(load_taxonomy(), load_lexicon(), seed=args.seed, scale=args.scale)
    out = MOCK / "generated" / ("" if args.scale == 1 else f"scale_{len(cat.variants) // 1000 * 1000}")
    for p in write_catalogue(cat, out):
        print(f"wrote {p.relative_to(MOCK.parent)}")
    print(f"variants: {len(cat.variants)}  skus: {len(cat.skus)}  seed: {args.seed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
