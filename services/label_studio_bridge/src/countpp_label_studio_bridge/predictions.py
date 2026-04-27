from __future__ import annotations

from countpp_schemas import Annotation, ExtractorRun


def annotations_to_prediction(
    annotations: list[Annotation],
    *,
    model_version: str,
    score: float | None = None,
    from_name: str = "label",
    to_name: str = "ts",
) -> dict[str, object]:
    prediction: dict[str, object] = {
        "model_version": model_version,
        "result": [_annotation_to_result(annotation, from_name=from_name, to_name=to_name) for annotation in annotations],
    }
    if score is not None:
        prediction["score"] = score
    return prediction


def extractor_run_to_prediction(
    run: ExtractorRun,
    *,
    from_name: str = "label",
    to_name: str = "ts",
) -> dict[str, object]:
    return annotations_to_prediction(
        run.output_annotations,
        model_version=f"{run.extractor_name}:{run.version}",
        score=_mean_confidence(run.output_annotations),
        from_name=from_name,
        to_name=to_name,
    )


def _annotation_to_result(annotation: Annotation, *, from_name: str, to_name: str) -> dict[str, object]:
    return {
        "id": annotation.id,
        "from_name": from_name,
        "to_name": to_name,
        "type": "timeserieslabels",
        "value": {
            "start": annotation.start_time,
            "end": annotation.end_time if annotation.end_time is not None else annotation.start_time,
            "instant": annotation.type == "instant",
            "timeserieslabels": [annotation.label],
        },
    }


def _mean_confidence(annotations: list[Annotation]) -> float | None:
    confidences = [a.confidence for a in annotations if a.confidence is not None]
    if not confidences:
        return None
    return sum(confidences) / len(confidences)
