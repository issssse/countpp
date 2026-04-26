from pathlib import Path

from countpp_analysis.accelerometer import detect_events_from_samples, parse_csv_samples


FIXTURE = Path(__file__).resolve().parents[3] / "data" / "examples" / "accelerometer_fixture.csv"


def test_parse_csv_samples():
    samples = parse_csv_samples(FIXTURE)
    assert len(samples) == 9
    assert samples[0].t == 0.0
    assert samples[-1].t == 0.8


def test_detect_events_from_samples():
    samples = parse_csv_samples(FIXTURE)
    events = detect_events_from_samples(samples, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
    assert events == [0.2, 0.6]
