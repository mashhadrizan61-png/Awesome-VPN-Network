from __future__ import annotations

import argparse

from .core import RecoveryEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recovery-engine",
        description="Large-scale data recovery scenario explorer",
    )
    parser.add_argument("--input-size", type=int, default=10_000_000)
    parser.add_argument("--chunk-sizes", default="512,1024,2048,4096")
    parser.add_argument("--pass-counts", default="1,2,3,4,5")
    parser.add_argument("--heuristics", default="fast,balanced,deep")
    parser.add_argument("--preview", type=int, default=5, help="Number of plans to preview")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    chunk_sizes = [int(item.strip()) for item in args.chunk_sizes.split(",") if item.strip()]
    pass_counts = [int(item.strip()) for item in args.pass_counts.split(",") if item.strip()]
    heuristics = [item.strip() for item in args.heuristics.split(",") if item.strip()]

    engine = RecoveryEngine()
    total = engine.estimate_scenarios(chunk_sizes, pass_counts, heuristics)

    print(f"Estimated scenarios: {total:,}")
    print("Preview:")

    for index, plan in enumerate(engine.iter_plans(chunk_sizes, pass_counts, heuristics), start=1):
        if index > args.preview:
            break
        result = engine.run(args.input_size, plan)
        print(
            f"{index:02d}. strategy={plan.strategy} chunk={plan.chunk_size} pass={plan.pass_count} "
            f"heuristic={plan.heuristic} => recovered={result.recovered_bytes:,} "
            f"confidence={result.confidence}"
        )


if __name__ == "__main__":
    main()
