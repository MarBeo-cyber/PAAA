"""Baseline, scoring and confidence tests.

Tests marked REGRESSION pin a bug found in the audit.
"""

import pytest

from paaa_core.baseline import FEATURE_MIN_STD, FEATURES, BaselineBuilder, effective_std
from paaa_core.config import PAAAConfig, load_config
from paaa_core.deviation import FEATURE_WEIGHTS, DeviationDetector
from paaa_core.longitudinal import deviation_level
from paaa_core.models import PhysiologicalSample, SignalQuality


def varied_samples(n=12):
    """A baseline with real session-to-session jitter on every feature."""
    return [
        PhysiologicalSample(
            tremor_amplitude=0.10 + (i % 5) * 0.008,
            tremor_frequency_hz=4.0 + (i % 4) * 0.30,
            motor_smoothness=0.86 + (i % 3) * 0.025,
            reaction_latency_ms=250 + (i % 6) * 12,
            grip_stability=0.88 + (i % 4) * 0.020,
            voice_stability=0.87 + (i % 3) * 0.030,
            stress_proxy=0.15 + (i % 4) * 0.030,
        )
        for i in range(n)
    ]


def flat_samples(n=12):
    """A baseline of literal constants: zero variance on every feature."""
    return [
        PhysiologicalSample(
            tremor_amplitude=0.10,
            tremor_frequency_hz=4.2,
            motor_smoothness=0.88,
            reaction_latency_ms=260,
            grip_stability=0.91,
            voice_stability=0.90,
            stress_proxy=0.18,
        )
        for _ in range(n)
    ]


def sample(**overrides):
    values = dict(
        tremor_amplitude=0.10,
        tremor_frequency_hz=4.2,
        motor_smoothness=0.88,
        reaction_latency_ms=260,
        grip_stability=0.91,
        voice_stability=0.90,
        stress_proxy=0.18,
    )
    values.update(overrides)
    return PhysiologicalSample(**values)


# ── BaselineBuilder ───────────────────────────────────────────────────

class TestBaselineBuilder:

    def test_requires_minimum_samples(self):
        with pytest.raises(ValueError, match="At least"):
            BaselineBuilder().build("x", [PhysiologicalSample() for _ in range(3)])

    def test_rejects_insufficient_good_quality_samples(self):
        samples = varied_samples(8)
        for s in samples[:5]:
            s.signal_quality = SignalQuality.DEGRADED
        with pytest.raises(ValueError, match="good-quality"):
            BaselineBuilder().build("x", samples)

    def test_builds_mean_and_std_per_feature(self):
        profile = BaselineBuilder().build("x", varied_samples())
        assert set(profile.means) == set(FEATURES)
        assert set(profile.stds) == set(FEATURES)
        assert profile.sample_count == 12

    def test_varied_baseline_has_no_degenerate_features(self):
        assert BaselineBuilder().build("x", varied_samples()).degenerate_features == []


class TestStdFloor:
    """REGRESSION: std was floored at 1e-6, so a constant baseline feature
    turned any difference into a z-score of ~10^5, clipped to the ceiling.
    Perturbing tremor frequency by 0.0001 Hz produced exactly the same
    deviation score as perturbing it by 0.9 Hz."""

    def test_constant_feature_is_flagged_degenerate_not_floored_to_epsilon(self):
        profile = BaselineBuilder().build("x", flat_samples())
        assert set(profile.degenerate_features) == set(FEATURES)
        for feature in FEATURES:
            assert profile.stds[feature] == pytest.approx(FEATURE_MIN_STD[feature])
            assert profile.stds[feature] > 1e-6

    def test_zero_variance_feature_does_not_saturate_on_a_tiny_perturbation(self):
        profile = BaselineBuilder().build("x", flat_samples())
        state = DeviationDetector().score(profile, sample(tremor_frequency_hz=4.2001))
        assert abs(state.z_scores["tremor_frequency_hz"]) < 0.01
        assert state.deviation_score < 0.01

    def test_tiny_and_large_perturbations_give_different_scores(self):
        profile = BaselineBuilder().build("x", flat_samples())
        detector = DeviationDetector()
        tiny = detector.score(profile, sample(tremor_frequency_hz=4.2001)).deviation_score
        large = detector.score(profile, sample(tremor_frequency_hz=5.1)).deviation_score
        assert tiny != large
        assert large > tiny

    def test_effective_std_never_returns_below_the_floor(self):
        for feature, floor in FEATURE_MIN_STD.items():
            assert effective_std(feature, 0.0) == floor
            assert effective_std(feature, floor * 10) == floor * 10


# ── Scoring ───────────────────────────────────────────────────────────

class TestFeatureWeights:
    """REGRESSION: stress_proxy was appended to `drivers` but omitted from the
    weighted sum, so it could be reported as a driver while contributing 0.00.
    voice_stability could contribute at most 2%."""

    def test_weights_cover_every_feature_and_sum_to_one(self):
        assert set(FEATURE_WEIGHTS) == set(FEATURES)
        assert sum(FEATURE_WEIGHTS.values()) == pytest.approx(1.0)
        for feature, weight in FEATURE_WEIGHTS.items():
            assert weight > 0.0, feature

    def test_stress_proxy_changes_the_score(self):
        profile = BaselineBuilder().build("x", varied_samples())
        detector = DeviationDetector()
        low = detector.score(profile, sample(stress_proxy=0.0)).deviation_score
        high = detector.score(profile, sample(stress_proxy=1.0)).deviation_score
        assert high > low

    def test_voice_stability_changes_the_score(self):
        profile = BaselineBuilder().build("x", varied_samples())
        detector = DeviationDetector()
        good = detector.score(profile, sample(voice_stability=1.0)).deviation_score
        poor = detector.score(profile, sample(voice_stability=0.10)).deviation_score
        assert poor > good

    def test_every_reported_driver_can_move_the_score(self):
        profile = BaselineBuilder().build("x", varied_samples())
        detector = DeviationDetector()
        state = detector.score(profile, sample(
            tremor_amplitude=0.9, tremor_frequency_hz=6.5, motor_smoothness=0.2,
            reaction_latency_ms=600, grip_stability=0.2, voice_stability=0.2,
            stress_proxy=0.95,
        ))
        assert state.drivers
        for driver in state.drivers:
            assert FEATURE_WEIGHTS[driver] > 0.0

    def test_lower_is_worse_direction_is_preserved(self):
        # The direction inversion for smoothness/grip/voice is load-bearing.
        profile = BaselineBuilder().build("x", varied_samples())
        detector = DeviationDetector()
        state = detector.score(profile, sample(motor_smoothness=0.20, grip_stability=0.20))
        assert state.z_scores["motor_smoothness"] > 0
        assert state.z_scores["grip_stability"] > 0


class TestDerivedFeatureScores:
    """REGRESSION: tremor_band_score and latency_penalty were computed and
    never consumed by anything."""

    def test_all_extractor_outputs_are_reported(self):
        profile = BaselineBuilder().build("x", varied_samples())
        state = DeviationDetector().score(profile, sample(tremor_frequency_hz=5.0, tremor_amplitude=0.4))
        assert set(state.feature_scores) == {
            "tremor_band_score", "stability_loss", "latency_penalty", "stress_proxy",
        }

    def test_tremor_band_score_reflects_the_3_5_to_7_hz_band(self):
        profile = BaselineBuilder().build("x", varied_samples())
        detector = DeviationDetector()
        in_band = detector.score(profile, sample(tremor_frequency_hz=5.0, tremor_amplitude=0.4))
        out_of_band = detector.score(profile, sample(tremor_frequency_hz=12.0, tremor_amplitude=0.4))
        assert in_band.feature_scores["tremor_band_score"] == pytest.approx(0.4)
        assert out_of_band.feature_scores["tremor_band_score"] == 0.0

    def test_latency_penalty_is_reported(self):
        profile = BaselineBuilder().build("x", varied_samples())
        state = DeviationDetector().score(profile, sample(reaction_latency_ms=1000))
        assert state.feature_scores["latency_penalty"] == pytest.approx(1.0)


class TestConfidence:
    """REGRESSION: confidence was `0.92 if signal_quality == "good" else 0.55`,
    a constant surfaced as a model confidence."""

    def test_confidence_rises_with_baseline_evidence(self):
        detector = DeviationDetector()
        short = BaselineBuilder().build("x", varied_samples(6))
        long = BaselineBuilder().build("x", varied_samples(30))
        assert (detector.score(long, sample()).confidence
                > detector.score(short, sample()).confidence)

    def test_confidence_drops_when_baseline_has_no_usable_variance(self):
        detector = DeviationDetector()
        measured = BaselineBuilder().build("x", varied_samples())
        degenerate = BaselineBuilder().build("x", flat_samples())
        assert (detector.score(degenerate, sample()).confidence
                < detector.score(measured, sample()).confidence)

    def test_confidence_drops_with_signal_quality(self):
        detector = DeviationDetector()
        profile = BaselineBuilder().build("x", varied_samples())
        good = detector.score(profile, sample())
        degraded = detector.score(profile, sample(signal_quality=SignalQuality.DEGRADED))
        assert degraded.confidence < good.confidence

    def test_confidence_is_not_one_of_two_constants(self):
        detector = DeviationDetector()
        values = {
            detector.score(BaselineBuilder().build("x", varied_samples(n)), sample()).confidence
            for n in (6, 12, 24, 30)
        }
        assert len(values) > 2


# ── Deviation levels ──────────────────────────────────────────────────

class TestDeviationLevel:
    """Hardened: the old test asserted the level was in the complete set of
    possible values, which cannot fail, and never compared its own `cases`."""

    CASES = [
        (0.0, "normal"),
        (1.49, "normal"),
        (-1.49, "normal"),
        (1.5, "mild"),
        (2.49, "mild"),
        (-2.0, "mild"),
        (2.5, "moderate"),
        (3.49, "moderate"),
        (3.5, "significant"),
        (12.8, "significant"),
    ]

    @pytest.mark.parametrize("z,expected", CASES)
    def test_expected_level_for_z(self, z, expected):
        assert deviation_level(z) == expected

    def test_level_matches_the_score_computed_by_the_detector(self):
        profile = BaselineBuilder().build("x", flat_samples())
        state = DeviationDetector().score(profile, sample(tremor_frequency_hz=4.2 + 0.15 * 2.0))
        # 2.0 floors above the mean on a feature whose std is the 0.15 Hz floor.
        assert state.z_scores["tremor_frequency_hz"] == pytest.approx(2.0, abs=1e-3)
        assert deviation_level(state.z_scores["tremor_frequency_hz"]) == "mild"


# ── Config ────────────────────────────────────────────────────────────

class TestConfig:
    """REGRESSION: config/default.yaml was never read and its thresholds were
    duplicated as literals in deviation.py and baseline.py."""

    def test_default_config_file_is_loaded(self):
        config = load_config()
        assert config.review_threshold == 0.72
        assert config.escalation_min_sessions == 5

    def test_detector_uses_config_thresholds(self):
        detector = DeviationDetector(PAAAConfig(review_threshold=0.10, high_threshold=0.05,
                                                medium_threshold=0.01))
        assert detector.review_threshold == 0.10

    def test_builder_uses_config_minimum_samples(self):
        builder = BaselineBuilder(PAAAConfig(minimum_samples=8))
        with pytest.raises(ValueError, match="At least 8"):
            builder.build("x", varied_samples(6))

    def test_missing_config_file_falls_back_to_defaults(self, tmp_path):
        assert load_config(tmp_path / "nope.json") == PAAAConfig()
