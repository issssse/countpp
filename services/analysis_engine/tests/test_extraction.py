from pathlib import Path

from countpp_analysis import (
    Interval,
    clamp_intervals,
    detect_peak_events,
    detect_periodic_intervals,
    parse_csv_samples,
)

FIXTURE = Path(__file__).resolve().parents[3] / "data" / "examples" / "accelerometer_fixture.csv"


def test_peak_events_detected_from_example_fixture():
    samples = parse_csv_samples(FIXTURE)
    events = detect_peak_events(samples, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
    assert events == [0.2, 0.6]


def test_periodic_interval_estimate_from_peak_events():
    periodic = detect_periodic_intervals([0.2, 0.6, 1.0], min_peaks=3)
    assert periodic.estimated_period_s == 0.4
    assert periodic.intervals[0].start == 0.2
    assert periodic.intervals[0].end == 1.0


def test_clamp_intervals():
    intervals = [Interval(start=-1, end=0.5, source="x"), Interval(start=0.7, end=2.0, source="y")]
    clamped = clamp_intervals(intervals, min_t=0.0, max_t=1.0)
    assert clamped == [
        Interval(start=0.0, end=0.5, source="x"),
        Interval(start=0.7, end=1.0, source="y"),
    ]
