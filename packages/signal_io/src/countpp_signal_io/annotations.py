from __future__ import annotations

import json
from pathlib import Path

from countpp_schemas import Annotation, EventExport


def write_annotations_json(annotations: list[Annotation], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps([annotation.to_dict() for annotation in annotations], indent=2),
        encoding="utf-8",
    )
    return destination


def read_annotations_json(path: str | Path) -> list[Annotation]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("annotation JSON must contain a list")
    return [Annotation.from_dict(item) for item in payload]


def write_event_export(export: EventExport, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(export.to_dict(), indent=2), encoding="utf-8")
    return destination
