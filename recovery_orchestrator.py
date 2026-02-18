#!/usr/bin/env python3
"""Recovery Orchestrator

A safety-first forensic recovery assistant for wiped/formatted/purged media.
It does NOT claim guaranteed recovery for overwritten sectors.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


@dataclasses.dataclass(frozen=True)
class Scenario:
    damage: str
    filesystem: str
    medium: str
    encryption: str
    trim: str

    def id(self) -> str:
        payload = f"{self.damage}|{self.filesystem}|{self.medium}|{self.encryption}|{self.trim}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclasses.dataclass
class ToolProbe:
    name: str
    installed: bool
    path: str | None


SUPPORTED_DIMENSIONS: Dict[str, Sequence[str]] = {
    "damage": [
        "wiped-metadata",
        "partition-table-lost",
        "quick-formatted",
        "full-formatted",
        "fdisk-repartitioned",
        "purged-index",
        "low-level-formatted-claim",
        "partial-overwrite",
        "heavy-overwrite",
    ],
    "filesystem": ["unknown", "ntfs", "fat32", "exfat", "ext4", "xfs", "apfs"],
    "medium": ["hdd", "ssd", "nvme", "usb", "sdcard", "raid"],
    "encryption": ["none", "bitlocker", "luks", "filevault", "veracrypt", "unknown"],
    "trim": ["unknown", "enabled", "disabled"],
}

ACTION_MATRIX = {
    "wiped-metadata": ["backup-image", "scan-partitions", "rebuild-fs-metadata", "carve-files"],
    "partition-table-lost": ["backup-image", "scan-partitions", "recover-partition-table"],
    "quick-formatted": ["backup-image", "analyze-fs-journals", "carve-files", "validate-integrity"],
    "full-formatted": ["backup-image", "deep-signature-carve", "entropy-check", "validate-integrity"],
    "fdisk-repartitioned": ["backup-image", "scan-partitions", "old-superblock-search", "carve-files"],
    "purged-index": ["backup-image", "journal-replay", "inode-walk", "carve-files"],
    "low-level-formatted-claim": ["backup-image", "magnetic-residual-check", "deep-signature-carve"],
    "partial-overwrite": ["backup-image", "range-map-overwrite-zones", "recover-unwritten-ranges"],
    "heavy-overwrite": ["backup-image", "salvage-fragments", "content-triage"],
}

DEFAULT_TOOLS = ["ddrescue", "testdisk", "photorec", "sleuthkit", "foremost", "scalpel"]


def probe_tools(tools: Sequence[str]) -> List[ToolProbe]:
    return [ToolProbe(name=t, installed=shutil.which(t) is not None, path=shutil.which(t)) for t in tools]


def scenario_count(dimensions: Dict[str, Sequence[str]]) -> int:
    total = 1
    for values in dimensions.values():
        total *= len(values)
    return total


def generate_scenarios(dimensions: Dict[str, Sequence[str]], limit: int | None = None) -> Iterable[Scenario]:
    keys = ["damage", "filesystem", "medium", "encryption", "trim"]
    combos = product(*(dimensions[k] for k in keys))
    for idx, combo in enumerate(combos):
        if limit is not None and idx >= limit:
            return
        yield Scenario(*combo)


def recommend_actions(s: Scenario) -> List[str]:
    base = ACTION_MATRIX.get(s.damage, ["backup-image", "carve-files"])
    actions = list(base)

    if s.medium in {"ssd", "nvme"}:
        actions.append("check-trim-impact")
    if s.encryption != "none":
        actions.append("recover-keys-or-unlock-first")
    if s.damage in {"heavy-overwrite", "low-level-formatted-claim"}:
        actions.append("set-expectation-low-probability")
    actions.append("write-evidence-log")
    return actions


def build_report(limit: int, include_scenarios: bool = True) -> Dict[str, object]:
    probes = probe_tools(DEFAULT_TOOLS)
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "capability_note": (
            "Overwritten sectors are usually unrecoverable with consumer software. "
            "This orchestrator focuses on maximizing recoverable remnants safely."
        ),
        "scenario_space_total": scenario_count(SUPPORTED_DIMENSIONS),
        "tooling": [dataclasses.asdict(p) for p in probes],
    }

    if include_scenarios:
        scenarios = []
        for s in generate_scenarios(SUPPORTED_DIMENSIONS, limit=limit):
            scenarios.append({
                "id": s.id(),
                "scenario": dataclasses.asdict(s),
                "recommended_actions": recommend_actions(s),
            })
        results["preview_count"] = len(scenarios)
        results["preview"] = scenarios
    return results


def run_cmd(cmd: Sequence[str]) -> int:
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def create_image(device: str, output_image: str) -> int:
    if os.geteuid() != 0:
        print("[!] For block-level imaging, run as root.", file=sys.stderr)
        return 2

    if shutil.which("ddrescue"):
        return run_cmd(["ddrescue", "-f", "-n", device, output_image, output_image + ".log"])

    print("[!] ddrescue not found; fallback to dd (slower/less resilient).", file=sys.stderr)
    return run_cmd(["dd", f"if={device}", f"of={output_image}", "bs=4M", "status=progress", "conv=noerror,sync"])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Forensic recovery orchestrator")
    sub = p.add_subparsers(dest="command", required=True)

    rp = sub.add_parser("report", help="Generate capability and scenario report")
    rp.add_argument("--limit", type=int, default=25, help="Number of scenarios to preview")
    rp.add_argument("--no-scenarios", action="store_true", help="Only print capabilities")

    ip = sub.add_parser("image", help="Create forensic image of a source device")
    ip.add_argument("--device", required=True, help="Block device path e.g. /dev/sdb")
    ip.add_argument("--out", required=True, help="Output image path e.g. /cases/disk1.img")

    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "report":
        report = build_report(limit=args.limit, include_scenarios=not args.no_scenarios)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if args.command == "image":
        return create_image(args.device, args.out)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
