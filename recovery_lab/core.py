from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SIGNATURES: dict[str, tuple[bytes, bytes | None]] = {
    "png": (b"\x89PNG\r\n\x1a\n", b"IEND\xaeB`\x82"),
    "jpg": (b"\xff\xd8\xff", b"\xff\xd9"),
    "pdf": (b"%PDF", b"%%EOF"),
    "zip": (b"PK\x03\x04", None),
}


@dataclass(slots=True)
class RecoveryConfig:
    source: Path
    output: Path
    scan_extensions: tuple[str, ...] = (".img", ".bin", ".raw", ".dd")
    max_file_size_mb: int = 512
    carve_types: tuple[str, ...] = ("png", "jpg", "pdf", "zip")


@dataclass(slots=True)
class RecoveryResult:
    carved_files: list[Path] = field(default_factory=list)
    restored_backups: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def recovered_count(self) -> int:
        return len(self.carved_files) + len(self.restored_backups)


class RecoveryEngine:
    """A pragmatic data recovery engine.

    It does not claim magic recovery; it orchestrates repeatable methods:
    - File carving from raw images using known signatures.
    - Backup restore from shadow directories.
    """

    def __init__(self, config: RecoveryConfig):
        self.config = config

    def run(self) -> RecoveryResult:
        result = RecoveryResult()
        self.config.output.mkdir(parents=True, exist_ok=True)

        for candidate in self._iter_sources():
            if candidate.is_dir():
                result.restored_backups.extend(self._restore_backups(candidate))
                continue

            if candidate.suffix.lower() not in self.config.scan_extensions:
                result.skipped.append(f"unsupported: {candidate}")
                continue

            if candidate.stat().st_size > self.config.max_file_size_mb * 1024 * 1024:
                result.skipped.append(f"too-large: {candidate}")
                continue

            carved = self._carve_file(candidate)
            result.carved_files.extend(carved)

        return result

    def _iter_sources(self) -> Iterable[Path]:
        src = self.config.source
        if src.is_file() or src.is_dir() and src.name == ".snapshots":
            yield src
            return

        if src.is_dir():
            for path in src.rglob("*"):
                if path.is_file() or path.name == ".snapshots":
                    yield path
            return

        raise FileNotFoundError(f"source not found: {src}")

    def _carve_file(self, image_path: Path) -> list[Path]:
        carved_dir = self.config.output / "carved"
        carved_dir.mkdir(parents=True, exist_ok=True)

        blob = image_path.read_bytes()
        recovered: list[Path] = []

        for filetype in self.config.carve_types:
            if filetype not in SIGNATURES:
                continue

            header, footer = SIGNATURES[filetype]
            start = 0
            index = 0
            while True:
                hpos = blob.find(header, start)
                if hpos == -1:
                    break

                if footer is None:
                    data = blob[hpos:]
                    end_pos = len(blob)
                else:
                    fpos = blob.find(footer, hpos + len(header))
                    if fpos == -1:
                        start = hpos + len(header)
                        continue
                    end_pos = fpos + len(footer)
                    data = blob[hpos:end_pos]

                digest = hashlib.sha256(data).hexdigest()[:12]
                out = carved_dir / f"{image_path.stem}_{filetype}_{index}_{digest}.{filetype}"
                out.write_bytes(data)
                recovered.append(out)

                index += 1
                start = end_pos

        return recovered

    def _restore_backups(self, snapshots_dir: Path) -> list[Path]:
        if snapshots_dir.name != ".snapshots" or not snapshots_dir.exists():
            return []

        restored_dir = self.config.output / "restored"
        restored_dir.mkdir(parents=True, exist_ok=True)
        restored: list[Path] = []

        for item in snapshots_dir.rglob("*"):
            if not item.is_file():
                continue
            target = restored_dir / item.name
            counter = 1
            while target.exists():
                target = restored_dir / f"{item.stem}_{counter}{item.suffix}"
                counter += 1
            target.write_bytes(item.read_bytes())
            restored.append(target)

        return restored
