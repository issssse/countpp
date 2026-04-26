from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path

from .extraction import detect_peak_events


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
    """Backwards-compatible wrapper for peak event detection."""
    return detect_peak_events(
        samples,
        baseline_g=baseline_g,
        trigger_delta=trigger_delta,
        reset_delta=reset_delta,
        min_separation_s=min_separation_s,
    )
