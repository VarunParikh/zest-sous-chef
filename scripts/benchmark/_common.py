"""Shared CLI plumbing for the Day-1 benchmarks (Evaluation Plan §6)."""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from backend.evaluation.results import RESULTS, write_result  # noqa: E402


def parser(desc: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--split", choices=["dev", "test", "all"], default="test")
    ap.add_argument("--smoke", action="store_true", help="plumbing check: dev split, first 3 rows, results to --out only")
    ap.add_argument("--out", type=pathlib.Path, default=RESULTS)
    return ap


def rows(dataset: str, split: str, smoke: bool) -> list[dict]:
    data = [json.loads(line) for line in (ROOT / "eval" / "datasets" / dataset).read_text().splitlines() if line.strip()]
    if smoke:
        return [r for r in data if r.get("split") == "dev"][:3]
    return data if split == "all" else [r for r in data if r.get("split") == split]


def save(result: dict, out: pathlib.Path) -> None:
    path = write_result(result, out)
    print(f"{result['id']} {result['system']}: {result['status']} -> {path}")
