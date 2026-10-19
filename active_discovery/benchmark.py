"""Run: python -m active_discovery.benchmark --budget 4 --seeds 0 1"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy

from .environment import Protocol
from .environment import make_experiment_api
from .evaluation import evaluate
from .runner import discover

SYSTEMS = {
    "linear": [1.3, 0.25, 0.0, 0.0],
    "nonlinear_spring": [1.3, 0.25, 0.9, 0.0],
    "quadratic_drag": [1.3, 0.25, 0.0, 0.7],
    "combined": [1.3, 0.25, 0.9, 0.7],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=4)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--systems", nargs="+", choices=SYSTEMS, default=["nonlinear_spring"])
    parser.add_argument("--strategies", nargs="+", choices=["random", "systematic", "active", "active_local"],
                        default=["random", "systematic", "active"])
    parser.add_argument("--starts", type=int, default=2)
    parser.add_argument("--noise", type=float, default=0.015)
    parser.add_argument("--control-limit", type=float, default=1.0)
    parser.add_argument("--out", type=Path, default=Path("results/pilot"))
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("Output directory is not empty. Choose a fresh --out to preserve results.")
    protocol = Protocol(noise_std=args.noise, control_limit=args.control_limit)
    args.out.mkdir(parents=True, exist_ok=True)
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in Path(__file__).parent.glob("*.py")}
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(),
                "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                "protocol": asdict(protocol), "budget": args.budget, "starts": args.starts,
                "seeds": args.seeds, "systems": {name: SYSTEMS[name] for name in args.systems},
                "strategies": args.strategies, "source_sha256": source_hashes,
                "status": "DEVELOPMENT PILOT - not final held-out research evidence",
                "test_seed": 9381, "test_count": 12, "runs": []}
    for name in args.systems:
        for seed in args.seeds:
            for strategy in args.strategies:
                started = time.perf_counter()
                api = make_experiment_api(SYSTEMS[name], protocol, seed+10000)
                run = discover(api, protocol, strategy, args.budget, seed, args.starts)
                run["learning_seconds"] = time.perf_counter()-started
                # Metrics cannot feed back into this completed discovery run.
                run["metrics"] = evaluate(run, SYSTEMS[name], protocol)
                run["system"] = name
                filename = f"{name}_{seed}_{strategy}.json"
                (args.out/filename).write_text(json.dumps(run, indent=2), encoding="utf-8")
                manifest["runs"].append(filename)
                (args.out/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                print(f"{name} seed={seed} {strategy}: NRMSE={run['metrics'][-1]['normalised_rmse']:.4f}, "
                      f"learning={run['learning_seconds']:.1f}s", flush=True)
    from .report import write_report
    write_report(args.out)
    print(f"Report: {(args.out/'report.html').resolve()}", flush=True)


if __name__ == "__main__":
    main()
