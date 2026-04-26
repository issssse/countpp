from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path


@dataclass(frozen=True)
class AccelerometerSample:
    """Single accelerometer sample with timestamp in seconds."""

    t: float
    ax: float
    ay: float
    az: float

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.ax**2 + self.ay**2 + self.az**2)


def parse_csv_samples(path: str | Path) -> list[AccelerometerSample]:
    """Parse samples from CSV with columns: t,ax,ay,az."""
    rows: list[AccelerometerSample] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"t", "ax", "ay", "az"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must include columns {sorted(required)}")
        for row in reader:
            rows.append(
                AccelerometerSample(
                    t=float(row["t"]),
                    ax=float(row["ax"]),
                    ay=float(row["ay"]),
                    az=float(row["az"]),
                )
            )
    rows.sort(key=lambda s: s.t)
    return rows


def detect_events_from_samples(
    samples: list[AccelerometerSample],
    *,
    baseline_g: float = 9.81,
    trigger_delta: float = 2.0,
    reset_delta: float = 0.8,
    min_separation_s: float = 0.08,
) -> list[float]:
    """Detect event timestamps from acceleration magnitude.

    Uses a threshold + hysteresis strategy:
    - Trigger when |mag - baseline| >= trigger_delta.
    - Rearm after |mag - baseline| <= reset_delta.
    - Enforce minimum time separation between events.
    """
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
