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
    ap.add_argument("--post-hoc", dest="post_hoc", default="",
                    help="reason for a rerun after a change (Evaluation Plan §2.8): marks the result and writes it to results/post-hoc/")
    return ap


def rows(dataset: str, split: str, smoke: bool) -> list[dict]:
    data = [json.loads(line) for line in (ROOT / "eval" / "datasets" / dataset).read_text().splitlines() if line.strip()]
    if smoke:
        return [r for r in data if r.get("split") == "dev"][:3]
    return data if split == "all" else [r for r in data if r.get("split") == split]


def save(result: dict, out: pathlib.Path, post_hoc: str = "") -> None:
    if post_hoc:  # the first result stays where it is; this one is marked and kept beside it
        result["notes"] = f"POST-HOC rerun: {post_hoc}; first result kept in eval/results/. " + result.get("notes", "")
        out = out / "post-hoc" if out == RESULTS else out
    path = write_result(result, out)
    print(f"{result['id']} {result['system']}: {result['status']} -> {path}")
