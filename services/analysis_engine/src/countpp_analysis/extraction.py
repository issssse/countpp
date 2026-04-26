from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Protocol


class _AccelSample(Protocol):
    t: float
    magnitude: float


@dataclass(frozen=True)
class Interval:
    start: float
    end: float
    source: str


@dataclass(frozen=True)
class PeriodicityResult:
    estimated_period_s: float | None
    intervals: list[Interval]


def detect_peak_events(
    samples: list[_AccelSample],
    *,
    baseline_g: float = 9.81,
    trigger_delta: float = 2.0,
    reset_delta: float = 0.8,
    min_separation_s: float = 0.08,
) -> list[float]:
    """Detect candidate event timestamps via threshold + hysteresis."""
    if not samples:
        return []

    events: list[float] = []
    armed = True
    last_event_t = float("-inf")

    for s in samples:
        delta = abs(s.magnitude - baseline_g)
        if armed and delta >= trigger_delta and (s.t - last_event_t) >= min_separation_s:
            events.append(s.t)
            last_event_t = s.t
            armed = False
        elif (not armed) and delta <= reset_delta:
            armed = True

    return events


def detect_periodic_intervals(
    events: list[float],
    *,
    max_cv: float = 0.25,
    min_peaks: int = 3,
) -> PeriodicityResult:
    """Infer periodic runs from event timestamps.

    A run is considered periodic when successive event intervals have a
    coefficient of variation <= max_cv.
    """
    if len(events) < 2:
        return PeriodicityResult(estimated_period_s=None, intervals=[])

    deltas = [events[i] - events[i - 1] for i in range(1, len(events))]
    med = median(deltas)
    if med <= 0:
        return PeriodicityResult(estimated_period_s=None, intervals=[])

    mean = sum(deltas) / len(deltas)
    var = sum((d - mean) ** 2 for d in deltas) / len(deltas)
    std = var**0.5
    cv = std / mean if mean > 0 else float("inf")

    if cv > max_cv:
        return PeriodicityResult(estimated_period_s=med, intervals=[])

    intervals: list[Interval] = []
    if len(events) >= min_peaks:
        intervals.append(Interval(start=events[0], end=events[-1], source="periodic-detector"))

    return PeriodicityResult(estimated_period_s=med, intervals=intervals)


def clamp_intervals(intervals: list[Interval], min_t: float, max_t: float) -> list[Interval]:
    out: list[Interval] = []
    for iv in intervals:
        start = max(min_t, iv.start)
        end = min(max_t, iv.end)
        if end > start:
            out.append(Interval(start=start, end=end, source=iv.source))
    return out
