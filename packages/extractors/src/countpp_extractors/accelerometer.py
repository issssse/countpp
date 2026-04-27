from __future__ import annotations

import hashlib
from statistics import median
from typing import Any

from countpp_schemas import Annotation, ExtractorRun
from countpp_signal_io import CanonicalStream

from .table_utils import numeric_column, time_values

PEAK_VERSION = "0.1.0"
INTERVAL_VERSION = "0.1.0"
PERIODIC_VERSION = "0.1.0"


def run_peak_detector(
    canonical: CanonicalStream,
    *,
    channel: str = "magnitude",
    baseline: float | None = None,
    trigger_delta: float = 2.0,
    reset_delta: float = 0.8,
    min_separation_s: float = 0.08,
    label: str = "peak",
    confidence: float = 0.7,
) -> ExtractorRun:
    times = time_values(canonical)
    values = numeric_column(canonical, channel)
    resolved_baseline = _resolve_baseline(values, baseline)
    parameters = {
        "channel": channel,
        "baseline": resolved_baseline,
        "baseline_strategy": "median" if baseline is None else "fixed",
        "trigger_delta": trigger_delta,
        "reset_delta": reset_delta,
        "min_separation_s": min_separation_s,
        "label": label,
    }
    run_id = _run_id(canonical.stream.id, "accelerometer_peak", parameters)
    events = detect_peak_times(
        times,
        values,
        baseline=resolved_baseline,
        trigger_delta=trigger_delta,
        reset_delta=reset_delta,
        min_separation_s=min_separation_s,
    )
    annotations = [
        Annotation(
            id=_annotation_id(canonical.stream.id, label, index, event_time),
            stream_id=canonical.stream.id,
            session_id=canonical.session.id,
            type="instant",
            start_time=event_time,
            label=label,
            source="extractor",
            confidence=confidence,
            metadata={"channel": channel, "extractor": "accelerometer_peak"},
            event_type_id="impact",
            value=_value_at_time(times, values, event_time),
            value_unit=_channel_unit(canonical, channel),
            value_source="sample-at-time",
            attributes={},
            extractor_run_id=run_id,
            reviewed=False,
        )
        for index, event_time in enumerate(events)
    ]
    return _run(
        canonical,
        "accelerometer_peak",
        PEAK_VERSION,
        parameters,
        annotations,
        diagnostics={"event_count": len(annotations)},
    )


def run_start_stop_interval_detector(
    canonical: CanonicalStream,
    *,
    channel: str = "magnitude",
    baseline: float | None = None,
    start_delta: float = 2.0,
    stop_delta: float = 0.8,
    min_duration_s: float = 0.0,
    label: str = "start_stop_interval",
    confidence: float = 0.65,
) -> ExtractorRun:
    times = time_values(canonical)
    values = numeric_column(canonical, channel)
    resolved_baseline = _resolve_baseline(values, baseline)
    parameters = {
        "channel": channel,
        "baseline": resolved_baseline,
        "baseline_strategy": "median" if baseline is None else "fixed",
        "start_delta": start_delta,
        "stop_delta": stop_delta,
        "min_duration_s": min_duration_s,
        "label": label,
    }
    run_id = _run_id(canonical.stream.id, "accelerometer_start_stop", parameters)
    intervals = detect_threshold_intervals(
        times,
        values,
        baseline=resolved_baseline,
        start_delta=start_delta,
        stop_delta=stop_delta,
        min_duration_s=min_duration_s,
    )
    annotations = [
        Annotation(
            id=_annotation_id(canonical.stream.id, label, index, start),
            stream_id=canonical.stream.id,
            session_id=canonical.session.id,
            type="interval",
            start_time=start,
            end_time=end,
            label=label,
            source="extractor",
            confidence=confidence,
            metadata={"channel": channel, "extractor": "accelerometer_start_stop"},
            event_type_id="start_stop",
            value=_max_value_between(times, values, start, end),
            value_unit=_channel_unit(canonical, channel),
            value_source="interval-statistic",
            attributes={"statistic": "max"},
            extractor_run_id=run_id,
            reviewed=False,
        )
        for index, (start, end) in enumerate(intervals)
    ]
    return _run(
        canonical,
        "accelerometer_start_stop",
        INTERVAL_VERSION,
        parameters,
        annotations,
        diagnostics={"interval_count": len(annotations)},
    )


def run_periodicity_detector(
    canonical: CanonicalStream,
    *,
    channel: str = "magnitude",
    baseline: float | None = None,
    trigger_delta: float = 2.0,
    reset_delta: float = 0.8,
    min_separation_s: float = 0.08,
    max_cv: float = 0.25,
    min_peaks: int = 3,
    label: str = "periodic_behavior",
    confidence: float = 0.6,
) -> ExtractorRun:
    times = time_values(canonical)
    values = numeric_column(canonical, channel)
    resolved_baseline = _resolve_baseline(values, baseline)
    parameters = {
        "channel": channel,
        "baseline": resolved_baseline,
        "baseline_strategy": "median" if baseline is None else "fixed",
        "trigger_delta": trigger_delta,
        "reset_delta": reset_delta,
        "min_separation_s": min_separation_s,
        "max_cv": max_cv,
        "min_peaks": min_peaks,
        "label": label,
    }
    run_id = _run_id(canonical.stream.id, "accelerometer_periodicity", parameters)
    events = detect_peak_times(
        times,
        values,
        baseline=resolved_baseline,
        trigger_delta=trigger_delta,
        reset_delta=reset_delta,
        min_separation_s=min_separation_s,
    )
    estimated_period, periodic_interval = infer_periodic_interval(events, max_cv=max_cv, min_peaks=min_peaks)
    annotations: list[Annotation] = []
    if periodic_interval:
        annotations.append(
            Annotation(
                id=_annotation_id(canonical.stream.id, label, 0, periodic_interval[0]),
                stream_id=canonical.stream.id,
                session_id=canonical.session.id,
                type="interval",
                start_time=periodic_interval[0],
                end_time=periodic_interval[1],
                label=label,
                source="extractor",
                confidence=confidence,
                metadata={
                    "channel": channel,
                    "extractor": "accelerometer_periodicity",
                    "estimated_period_s": estimated_period,
                    "event_count": len(events),
                },
                event_type_id="periodic_motion",
                value=(1.0 / estimated_period) if estimated_period else None,
                value_unit="Hz" if estimated_period else None,
                value_source="interval-statistic",
                attributes={"pattern": "periodic"},
                extractor_run_id=run_id,
                reviewed=False,
            )
        )
    return _run(
        canonical,
        "accelerometer_periodicity",
        PERIODIC_VERSION,
        parameters,
        annotations,
        diagnostics={"event_count": len(events), "estimated_period_s": estimated_period},
    )


def detect_peak_times(
    times: list[float],
    values: list[float],
    *,
    baseline: float,
    trigger_delta: float,
    reset_delta: float,
    min_separation_s: float,
) -> list[float]:
    events: list[float] = []
    armed = True
    last_event_t = float("-inf")
    for t, value in zip(times, values, strict=True):
        delta = abs(value - baseline)
        if armed and delta >= trigger_delta and (t - last_event_t) >= min_separation_s:
            events.append(t)
            last_event_t = t
            armed = False
        elif (not armed) and delta <= reset_delta:
            armed = True
    return events


def detect_threshold_intervals(
    times: list[float],
    values: list[float],
    *,
    baseline: float,
    start_delta: float,
    stop_delta: float,
    min_duration_s: float,
) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    active_start: float | None = None
    last_time: float | None = None
    for t, value in zip(times, values, strict=True):
        last_time = t
        delta = abs(value - baseline)
        if active_start is None and delta >= start_delta:
            active_start = t
        elif active_start is not None and delta <= stop_delta:
            if t - active_start >= min_duration_s:
                intervals.append((active_start, t))
            active_start = None

    if active_start is not None and last_time is not None and last_time - active_start >= min_duration_s:
        intervals.append((active_start, last_time))
    return intervals


def infer_periodic_interval(
    events: list[float],
    *,
    max_cv: float,
    min_peaks: int,
) -> tuple[float | None, tuple[float, float] | None]:
    if len(events) < 2:
        return None, None
    deltas = [events[i] - events[i - 1] for i in range(1, len(events))]
    estimated_period = median(deltas)
    if estimated_period <= 0:
        return None, None

    mean = sum(deltas) / len(deltas)
    variance = sum((delta - mean) ** 2 for delta in deltas) / len(deltas)
    cv = (variance**0.5) / mean if mean > 0 else float("inf")
    if cv > max_cv or len(events) < min_peaks:
        return estimated_period, None
    return estimated_period, (events[0], events[-1])


def _run(
    canonical: CanonicalStream,
    name: str,
    version: str,
    parameters: dict[str, Any],
    annotations: list[Annotation],
    *,
    diagnostics: dict[str, Any] | None = None,
) -> ExtractorRun:
    return ExtractorRun(
        id=_run_id(canonical.stream.id, name, parameters),
        extractor_name=name,
        version=version,
        input_streams=[canonical.stream.id],
        parameters=parameters,
        output_annotations=annotations,
        diagnostics=diagnostics or {},
    )


def _resolve_baseline(values: list[float], baseline: float | None) -> float:
    if baseline is not None:
        return baseline
    if not values:
        return 0.0
    return median(values)


def _value_at_time(times: list[float], values: list[float], event_time: float) -> float | None:
    if not times:
        return None
    index = min(range(len(times)), key=lambda i: abs(times[i] - event_time))
    return values[index]


def _max_value_between(times: list[float], values: list[float], start: float, end: float) -> float | None:
    interval_values = [value for t, value in zip(times, values, strict=True) if start <= t <= end]
    return max(interval_values) if interval_values else None


def _channel_unit(canonical: CanonicalStream, channel_name: str) -> str | None:
    for channel in canonical.stream.channels:
        if channel.name == channel_name:
            return channel.unit
    return None


def _run_id(stream_id: str, extractor_name: str, parameters: dict[str, Any]) -> str:
    digest = hashlib.sha1(f"{stream_id}|{extractor_name}|{sorted(parameters.items())}".encode("utf-8")).hexdigest()[:12]
    return f"run_{digest}"


def _annotation_id(stream_id: str, label: str, index: int, t: float) -> str:
    digest = hashlib.sha1(f"{stream_id}|{label}|{index}|{t:.9f}".encode("utf-8")).hexdigest()[:12]
    return f"ann_{digest}"
