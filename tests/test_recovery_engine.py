from recovery_engine.core import RecoveryEngine


def test_estimate_scenarios_counts_cartesian_product() -> None:
    engine = RecoveryEngine()
    total = engine.estimate_scenarios([512, 1024], [1, 2, 3], ["fast", "balanced"])
    assert total == 4 * 2 * 3 * 2


def test_iter_plans_is_lazy_and_generates_expected_shape() -> None:
    engine = RecoveryEngine()
    plans = engine.iter_plans([1024], [1], ["fast"])
    first = next(plans)

    assert first.chunk_size == 1024
    assert first.pass_count == 1
    assert first.heuristic == "fast"
