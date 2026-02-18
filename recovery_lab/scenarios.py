from __future__ import annotations

from dataclasses import dataclass
from itertools import islice, product
from math import prod
from typing import Iterator


@dataclass(slots=True)
class ScenarioMatrix:
    """Lazy scenario combinator for very large search spaces."""

    block_sizes: tuple[int, ...] = (512, 1024, 4096)
    pass_counts: tuple[int, ...] = (1, 2, 3, 5)
    hash_strategies: tuple[str, ...] = ("sha1", "sha256", "blake2b")
    repair_modes: tuple[str, ...] = ("none", "parity", "reed-solomon")
    io_modes: tuple[str, ...] = ("sequential", "parallel")

    def total_scenarios(self) -> int:
        return prod(
            [
                len(self.block_sizes),
                len(self.pass_counts),
                len(self.hash_strategies),
                len(self.repair_modes),
                len(self.io_modes),
            ]
        )

    def iter_scenarios(self) -> Iterator[dict[str, str | int]]:
        for block_size, pass_count, h, repair, io_mode in product(
            self.block_sizes,
            self.pass_counts,
            self.hash_strategies,
            self.repair_modes,
            self.io_modes,
        ):
            yield {
                "block_size": block_size,
                "pass_count": pass_count,
                "hash": h,
                "repair": repair,
                "io_mode": io_mode,
            }

    def sample(self, n: int = 10) -> list[dict[str, str | int]]:
        return list(islice(self.iter_scenarios(), n))
