from __future__ import annotations

from countpp_signal_io import CanonicalStream


def numeric_column(canonical: CanonicalStream, name: str) -> list[float]:
    if name not in canonical.table.column_names:
        raise ValueError(f"stream {canonical.stream.id} has no column {name!r}")
    return [float(value) for value in canonical.table.column(name).combine_chunks().to_pylist()]


def time_values(canonical: CanonicalStream) -> list[float]:
    return numeric_column(canonical, canonical.time_column)
