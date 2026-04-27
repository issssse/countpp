from __future__ import annotations

from countpp_schemas import ExtractorRun, Stream

from .predictions import extractor_run_to_prediction


def build_time_series_task(
    stream: Stream,
    *,
    csv_url: str,
    predictions: list[dict[str, object]] | None = None,
    data_key: str = "csv",
) -> dict[str, object]:
    task: dict[str, object] = {
        "data": {data_key: csv_url},
        "meta": {
            "countpp_stream_id": stream.id,
            "countpp_session_id": stream.session_id,
            "modality": stream.modality,
            "channels": [channel.to_dict() for channel in stream.channels],
        },
    }
    if predictions:
        task["predictions"] = predictions
    return task


def build_task_with_extractor_run(
    stream: Stream,
    *,
    csv_url: str,
    run: ExtractorRun,
    data_key: str = "csv",
) -> dict[str, object]:
    return build_time_series_task(
        stream,
        csv_url=csv_url,
        predictions=[extractor_run_to_prediction(run)],
        data_key=data_key,
    )
