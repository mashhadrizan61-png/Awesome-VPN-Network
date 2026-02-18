from pathlib import Path

from recovery_lab.core import RecoveryConfig, RecoveryEngine
from recovery_lab.scenarios import ScenarioMatrix


def test_scenario_matrix_count_and_sample() -> None:
    matrix = ScenarioMatrix(
        block_sizes=(512, 1024),
        pass_counts=(1, 2),
        hash_strategies=("sha1",),
        repair_modes=("none", "parity"),
        io_modes=("sequential", "parallel"),
    )
    assert matrix.total_scenarios() == 16
    sample = matrix.sample(3)
    assert len(sample) == 3
    assert sample[0]["block_size"] == 512


def test_carve_png_from_raw_image(tmp_path: Path) -> None:
    header = b"\x89PNG\r\n\x1a\n"
    footer = b"IEND\xaeB`\x82"
    fake_png = header + b"demo-bytes" + footer
    raw = b"noise" + fake_png + b"tail"

    src = tmp_path / "disk.raw"
    src.write_bytes(raw)

    config = RecoveryConfig(source=src, output=tmp_path / "out", carve_types=("png",))
    result = RecoveryEngine(config).run()

    assert result.recovered_count == 1
    carved = result.carved_files[0]
    assert carved.exists()
    assert carved.read_bytes() == fake_png


def test_restore_snapshots(tmp_path: Path) -> None:
    snapshots = tmp_path / ".snapshots" / "daily"
    snapshots.mkdir(parents=True)
    original = snapshots / "db.sqlite"
    original.write_text("backup-data", encoding="utf-8")

    config = RecoveryConfig(source=tmp_path / ".snapshots", output=tmp_path / "restored")
    result = RecoveryEngine(config).run()

    assert result.recovered_count == 1
    restored = result.restored_backups[0]
    assert restored.read_text(encoding="utf-8") == "backup-data"
