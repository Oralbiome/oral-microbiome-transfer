#!/usr/bin/env python3
"""Check omitted inputs before deliberately running the frozen research scripts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.parents[1]
EXPERIMENTS = ["marker_stability", "portability", "sign_adaptation", "ood_detection",
               "marker_properties", "diversity_transfer", "population_vs_study"]


def check_inputs(root=ROOT, package=PACKAGE):
    contract = json.loads((package / "input-contract.json").read_text())
    if not contract.get("required_inputs"):
        raise ValueError("Input contract has no required inputs; refusing to run")
    results = []
    for row in contract["required_inputs"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Input contract contains an unsafe path")
        path = root / relative
        components = [root.joinpath(*relative.parts[:i]) for i in range(1, len(relative.parts) + 1)]
        if any(p.is_symlink() for p in components):
            raise ValueError("Input contract paths must not contain symlinks")
        if not path.is_file():
            status = "missing"
        elif hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            status = "hash_mismatch"
        else:
            status = "present"
        results.append({"path": row["path"], "status": status})
    return {"ready": all(r["status"] == "present" for r in results), "inputs": results,
            "scope": "byte identity only; obtain and use inputs under their applicable terms"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-inputs", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--render-paper", action="store_true")
    args = parser.parse_args()
    if args.render_paper and not args.run:
        parser.error("--render-paper requires --run")
    status = check_inputs()
    print(json.dumps(status, indent=2), flush=True)
    if not status["ready"]:
        return 2
    if not args.run:
        return 0
    if args.render_paper and any(shutil.which(p) is None for p in ("pandoc", "xelatex")):
        parser.error("Paper rendering additionally requires Pandoc and XeLaTeX")
    for path in (ROOT / "data/models", ROOT / "data/processed", ROOT / "reports/figures",
                 PACKAGE / "site/app/data", PACKAGE / "site/public"):
        path.mkdir(parents=True, exist_ok=True)
    steps = [("reconstruct_validation.py", []), ("reconstruct_subgroups.py", [])]
    steps += [(f"experiment_{name}.py", []) for name in EXPERIMENTS]
    steps += [("calibrate.py", ["export"]), ("build_site_data.py", [])]
    if args.render_paper:
        steps += [("render_validation.py", []), ("render_preprint.py", [])]
    for name, extra in steps:
        print("Running " + name, flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / name), *extra], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
