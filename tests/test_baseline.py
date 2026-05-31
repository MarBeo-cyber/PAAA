from paaa.baseline import BaselineEngine


def test_baseline_engine_runs():
    engine = BaselineEngine()
    result = engine.compare([1, 1, 1, 1, 1, 1], 1.2)
    assert result.value == 1.2
