from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import RecoveryConfig, RecoveryEngine
from .scenarios import ScenarioMatrix


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recovery-lab",
        description="Advanced data recovery orchestrator with massive scenario planning.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    recover = sub.add_parser("recover", help="Run recovery pipeline on source path")
    recover.add_argument("source", type=Path, help="Raw image file, directory, or .snapshots directory")
    recover.add_argument("output", type=Path, help="Directory to save recovered files")
    recover.add_argument(
        "--types",
        default="png,jpg,pdf,zip",
        help="Comma-separated carve file types",
    )
    recover.add_argument(
        "--extensions",
        default=".img,.bin,.raw,.dd",
        help="Comma-separated image extensions to scan",
    )
    recover.add_argument("--max-size-mb", type=int, default=512)

    scenarios = sub.add_parser("scenarios", help="Plan recovery scenario matrix")
    scenarios.add_argument("--block-sizes", default="512,1024,4096")
    scenarios.add_argument("--pass-counts", default="1,2,3,5")
    scenarios.add_argument("--hashes", default="sha1,sha256,blake2b")
    scenarios.add_argument("--repairs", default="none,parity,reed-solomon")
    scenarios.add_argument("--io-modes", default="sequential,parallel")
    scenarios.add_argument("--sample", type=int, default=5)

    return parser


def _split_csv(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "recover":
        config = RecoveryConfig(
            source=args.source,
            output=args.output,
            carve_types=tuple(_split_csv(args.types)),
            scan_extensions=tuple(_split_csv(args.extensions)),
            max_file_size_mb=args.max_size_mb,
        )
        result = RecoveryEngine(config).run()
        payload = {
            "recovered_count": result.recovered_count,
            "carved": [str(p) for p in result.carved_files],
            "restored_backups": [str(p) for p in result.restored_backups],
            "skipped": result.skipped,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    matrix = ScenarioMatrix(
        block_sizes=tuple(int(x) for x in _split_csv(args.block_sizes)),
        pass_counts=tuple(int(x) for x in _split_csv(args.pass_counts)),
        hash_strategies=_split_csv(args.hashes),
        repair_modes=_split_csv(args.repairs),
        io_modes=_split_csv(args.io_modes),
    )
    print(
        json.dumps(
            {
                "total_scenarios": matrix.total_scenarios(),
                "sample": matrix.sample(args.sample),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
