from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod
from typing import Iterable, Iterator

from .strategies import DEFAULT_STRATEGIES, RecoveryStrategy


@dataclass(frozen=True)
class RecoveryPlan:
    """A compact plan describing one concrete recovery scenario."""

    strategy: str
    chunk_size: int
    pass_count: int
    heuristic: str


@dataclass(frozen=True)
class RecoveryResult:
    """Output of a recovery run."""

    plan: RecoveryPlan
    recovered_bytes: int
    confidence: float
    notes: str


class RecoveryEngine:
    """Generates and executes large-scale recovery scenario plans lazily.

    The engine is designed for huge combinatorial search spaces. It does not
    materialize all combinations in memory.
    """

    def __init__(self, strategies: Iterable[RecoveryStrategy] | None = None) -> None:
        self._strategies = tuple(strategies or DEFAULT_STRATEGIES)

    def estimate_scenarios(
        self,
        chunk_sizes: Iterable[int],
        pass_counts: Iterable[int],
        heuristics: Iterable[str],
    ) -> int:
        """Return total number of scenario combinations."""
        dimensions = [
            len(self._strategies),
            len(tuple(chunk_sizes)),
            len(tuple(pass_counts)),
            len(tuple(heuristics)),
        ]
        return prod(dimensions)

    def iter_plans(
        self,
        chunk_sizes: Iterable[int],
        pass_counts: Iterable[int],
        heuristics: Iterable[str],
    ) -> Iterator[RecoveryPlan]:
        """Yield plans lazily to support very large scenario spaces."""
        chunk_sizes = tuple(chunk_sizes)
        pass_counts = tuple(pass_counts)
        heuristics = tuple(heuristics)

        for strategy, chunk_size, pass_count, heuristic in product(
            self._strategies,
            chunk_sizes,
            pass_counts,
            heuristics,
        ):
            yield RecoveryPlan(
                strategy=strategy.name,
                chunk_size=chunk_size,
                pass_count=pass_count,
                heuristic=heuristic,
            )

    def run(self, input_size: int, plan: RecoveryPlan) -> RecoveryResult:
        """Simulate one recovery attempt.

        This is a deterministic simulation-friendly scoring model.
        """
        efficiency = {
            "signature_scan": 0.46,
            "timeline_reassembly": 0.63,
            "parity_rebuild": 0.78,
            "entropy_guided_search": 0.58,
        }.get(plan.strategy, 0.40)

        pass_boost = min(1.0, 0.20 + plan.pass_count * 0.12)
        chunk_penalty = 1.0 if plan.chunk_size <= 4096 else 0.92
        heuristic_boost = 1.05 if plan.heuristic == "balanced" else 0.96

        confidence = min(0.99, efficiency * pass_boost * chunk_penalty * heuristic_boost)
        recovered_bytes = int(input_size * confidence)

        return RecoveryResult(
            plan=plan,
            recovered_bytes=recovered_bytes,
            confidence=round(confidence, 4),
            notes="Use plugin backends for real disk/image recovery workflows.",
        )
