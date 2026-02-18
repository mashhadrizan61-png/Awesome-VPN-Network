from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryStrategy:
    """Represents a high-level recovery strategy."""

    name: str
    description: str


DEFAULT_STRATEGIES: tuple[RecoveryStrategy, ...] = (
    RecoveryStrategy(
        name="signature_scan",
        description="Scan raw chunks for known magic bytes and rebuild file headers.",
    ),
    RecoveryStrategy(
        name="timeline_reassembly",
        description="Reconstruct fragmented pieces using temporal metadata and chunk order.",
    ),
    RecoveryStrategy(
        name="parity_rebuild",
        description="Use parity snapshots/checkpoints to reconstruct missing chunk groups.",
    ),
    RecoveryStrategy(
        name="entropy_guided_search",
        description="Prioritize low-entropy windows to reduce false positives.",
    ),
)
