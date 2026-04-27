from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from .models import CanonicalStream


def write_stream_parquet(canonical: CanonicalStream, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = dict(canonical.table.schema.metadata or {})
    metadata.update(
        {
            b"countpp.session": json.dumps(canonical.session.to_dict()).encode("utf-8"),
            b"countpp.stream": json.dumps(canonical.stream.to_dict()).encode("utf-8"),
        }
    )
    table = canonical.table.replace_schema_metadata(metadata)
    pq.write_table(table, destination)
    return destination


def read_stream_table(path: str | Path):
    return pq.read_table(path)


def read_stream_metadata(path: str | Path) -> dict[str, object]:
    table = pq.read_table(path)
    metadata = table.schema.metadata or {}
    out: dict[str, object] = {}
    for key, value in metadata.items():
        decoded_key = key.decode("utf-8")
        if decoded_key.startswith("countpp."):
            out[decoded_key] = json.loads(value.decode("utf-8"))
    return out
