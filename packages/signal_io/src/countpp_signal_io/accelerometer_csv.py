from __future__ import annotations

import csv
import hashlib
import math
import re
from io import StringIO
from pathlib import Path
from typing import Any

import pyarrow as pa

from countpp_schemas import Channel, RecordingSession, Stream

from .models import CanonicalStream

_UNIT_RE = re.compile(r"^(?P<name>.*?)\s*\((?P<unit>.*?)\)\s*$")


def import_accelerometer_csv(
    path: str | Path,
    *,
    session_id: str | None = None,
    session_name: str | None = None,
    stream_id: str | None = None,
    source_device_id: str | None = None,
    raw_uri: str | None = None,
) -> CanonicalStream:
    """Import accelerometer CSV into the canonical stream/table shape.

    Supported inputs include the small `t,ax,ay,az` fixture and exported
    phone-sensor CSVs that begin with `#` metadata and unit-bearing headers.
    """
    source = Path(path)
    metadata, csv_text = _split_metadata_and_csv(source)
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError(f"{source} does not contain a CSV header")

    header_map, units = _build_header_map(reader.fieldnames)
    if "time" not in header_map.values():
        raise ValueError("accelerometer CSV must include a time or t column")

    columns: dict[str, list[float]] = {name: [] for name in header_map.values()}
    for row in reader:
        if not row:
            continue
        for original, canonical in header_map.items():
            raw_value = row.get(original)
            if raw_value is None or raw_value == "":
                continue
            columns[canonical].append(float(raw_value))

    for required in ("ax", "ay", "az"):
        if required not in columns:
            raise ValueError(f"accelerometer CSV must include {required}")

    row_count = len(columns["time"])
    _validate_equal_lengths(columns, row_count)

    if "magnitude" not in columns:
        columns["magnitude"] = [
            math.sqrt(ax**2 + ay**2 + az**2)
            for ax, ay, az in zip(columns["ax"], columns["ay"], columns["az"], strict=True)
        ]
        units["magnitude"] = units.get("ax")

    ordered_names = ["time"] + [name for name in ("ax", "ay", "az", "magnitude") if name in columns]
    table = pa.table({name: pa.array(columns[name], type=pa.float64()) for name in ordered_names})

    resolved_session_id = session_id or _stable_id("session", source.name)
    resolved_stream_id = stream_id or _stable_id("stream", str(source.resolve()), resolved_session_id)
    session = RecordingSession(
        id=resolved_session_id,
        name=session_name or source.stem.replace("_", " "),
        devices=[source_device_id] if source_device_id else [],
        started_at=_metadata_value(metadata, "recording started at"),
        metadata={"source_metadata": metadata},
    )
    stream = Stream(
        id=resolved_stream_id,
        session_id=session.id,
        source_device_id=source_device_id,
        modality="accelerometer",
        channels=[
            Channel(
                name=name,
                unit=units.get(name),
                axis={"ax": "x", "ay": "y", "az": "z"}.get(name),
                derived_from=["ax", "ay", "az"] if name == "magnitude" else None,
            )
            for name in ordered_names
            if name != "time"
        ],
        sample_rate_hint=_parse_sample_rate(metadata),
        time_base="seconds_since_recording_start",
        raw_uri=raw_uri or source.as_posix(),
        metadata={
            "source_format": "csv",
            "original_columns": reader.fieldnames,
            "source_metadata": metadata,
        },
    )
    return CanonicalStream(session=session, stream=stream, table=table, metadata={"rows": row_count})


def _split_metadata_and_csv(path: Path) -> tuple[dict[str, str], str]:
    metadata: dict[str, str] = {}
    csv_lines: list[str] = []
    with path.open(encoding="utf-8", newline="") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                key, value = _parse_comment(stripped)
                metadata[key] = value
            else:
                csv_lines.append(line)
    if not csv_lines:
        raise ValueError(f"{path} does not contain CSV rows")
    return metadata, "".join(csv_lines)


def _parse_comment(line: str) -> tuple[str, str]:
    body = line.lstrip("#").strip()
    if ":" not in body:
        return body.lower(), ""
    key, value = body.split(":", 1)
    return key.strip().lower(), value.strip()


def _build_header_map(headers: list[str]) -> tuple[dict[str, str], dict[str, str | None]]:
    header_map: dict[str, str] = {}
    units: dict[str, str | None] = {}
    for header in headers:
        canonical, unit = _normalize_column(header)
        header_map[header] = canonical
        units[canonical] = unit
    return header_map, units


def _normalize_column(header: str) -> tuple[str, str | None]:
    raw = header.strip()
    match = _UNIT_RE.match(raw)
    unit = None
    if match:
        raw = match.group("name").strip()
        unit = match.group("unit").strip()
    key = raw.lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "t": "time",
        "timestamp": "time",
        "elapsed_time": "time",
        "a_t": "magnitude",
        "at": "magnitude",
        "total_acceleration": "magnitude",
        "mag": "magnitude",
    }
    return aliases.get(key, key), unit


def _validate_equal_lengths(columns: dict[str, list[float]], expected: int) -> None:
    lengths = {name: len(values) for name, values in columns.items()}
    bad = {name: length for name, length in lengths.items() if length != expected}
    if bad:
        raise ValueError(f"CSV columns have uneven lengths: {bad}")


def _parse_sample_rate(metadata: dict[str, str]) -> float | None:
    value = _metadata_value(metadata, "target sample rate") or _metadata_value(metadata, "sample rate")
    if value is None:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", value)
    return float(match.group(0)) if match else None


def _metadata_value(metadata: dict[str, str], key: str) -> str | None:
    return metadata.get(key.lower())


def _stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"
