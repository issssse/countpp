from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from countpp_schemas import Annotation


def parse_label_studio_annotations(
    exported: dict[str, Any] | list[dict[str, Any]],
    *,
    session_id: str | None = None,
    stream_id: str | None = None,
    source: str = "human",
) -> list[Annotation]:
    tasks = exported if isinstance(exported, list) else [exported]
    annotations: list[Annotation] = []
    for task in tasks:
        meta = task.get("meta") or {}
        resolved_session_id = session_id or meta.get("countpp_session_id")
        resolved_stream_id = stream_id or meta.get("countpp_stream_id")
        for annotation in task.get("annotations", []):
            for result in annotation.get("result", []):
                parsed = _parse_result(
                    result,
                    session_id=resolved_session_id,
                    stream_id=resolved_stream_id,
                    source=source,
                )
                if parsed is not None:
                    annotations.append(parsed)
    return annotations


def _parse_result(
    result: dict[str, Any],
    *,
    session_id: str | None,
    stream_id: str | None,
    source: str,
) -> Annotation | None:
    if result.get("type") != "timeserieslabels":
        return None
    value = result.get("value") or {}
    labels = value.get("timeserieslabels") or []
    if not labels:
        return None
    start = float(value["start"])
    end = float(value.get("end", start))
    instant = bool(value.get("instant", start == end))
    return Annotation(
        id=str(result.get("id") or f"ls_{start:g}_{end:g}_{labels[0]}"),
        stream_id=stream_id,
        session_id=session_id,
        type="instant" if instant else "interval",
        start_time=start,
        end_time=start if instant else end,
        label=str(labels[0]),
        source=source,  # type: ignore[arg-type]
        metadata={
            "label_studio": {
                "from_name": result.get("from_name"),
                "to_name": result.get("to_name"),
            }
        },
    )


def prediction_results_to_annotations(
    prediction_results: Iterable[dict[str, Any]],
    *,
    session_id: str | None = None,
    stream_id: str | None = None,
) -> list[Annotation]:
    task = {"meta": {"countpp_session_id": session_id, "countpp_stream_id": stream_id}, "annotations": [{"result": list(prediction_results)}]}
    return parse_label_studio_annotations(task, source="extractor")
