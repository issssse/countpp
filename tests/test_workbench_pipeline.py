from __future__ import annotations

import json
from pathlib import Path

from countpp_extractors import (
    run_peak_detector,
    run_periodicity_detector,
    run_sktime_segmentation_detector,
    run_start_stop_interval_detector,
    run_stumpy_matrix_profile_detector,
)
from countpp_label_studio_bridge import (
    build_task_with_extractor_run,
    extractor_run_to_prediction,
    generate_time_series_label_config,
    parse_label_studio_annotations,
)
from countpp_signal_io import (
    import_accelerometer_csv,
    read_annotations_json,
    read_stream_metadata,
    read_stream_table,
    write_annotations_json,
    write_stream_parquet,
)
from fastapi.testclient import TestClient

from countpp_data_api import create_app

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "examples" / "accelerometer_fixture.csv"
LINEAR = ROOT / "data" / "examples" / "linear_acceleration_example.csv"


def test_accelerometer_csv_to_canonical_stream_and_parquet(tmp_path):
    canonical = import_accelerometer_csv(LINEAR)

    assert canonical.stream.modality == "accelerometer"
    assert canonical.stream.sample_rate_hint == 100.0
    assert canonical.table.num_rows == 90008
    assert canonical.table.column_names == ["time", "ax", "ay", "az", "magnitude"]
    assert [channel.name for channel in canonical.stream.channels] == ["ax", "ay", "az", "magnitude"]

    parquet_path = write_stream_parquet(canonical, tmp_path / "stream.parquet")
    table = read_stream_table(parquet_path)
    metadata = read_stream_metadata(parquet_path)

    assert table.num_rows == canonical.table.num_rows
    assert metadata["countpp.stream"]["id"] == canonical.stream.id
    assert metadata["countpp.session"]["id"] == canonical.session.id


def test_extractors_detect_expected_events_from_fixture():
    canonical = import_accelerometer_csv(FIXTURE)

    peak_run = run_peak_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
    assert [annotation.start_time for annotation in peak_run.output_annotations] == [0.2, 0.6]

    interval_run = run_start_stop_interval_detector(canonical, start_delta=2.5, stop_delta=0.7)
    assert [(a.start_time, a.end_time) for a in interval_run.output_annotations] == [(0.2, 0.3), (0.6, 0.7)]

    periodic_run = run_periodicity_detector(
        canonical,
        trigger_delta=2.5,
        reset_delta=0.7,
        min_separation_s=0.1,
        min_peaks=2,
    )
    assert len(periodic_run.output_annotations) == 1
    assert periodic_run.output_annotations[0].start_time == 0.2
    assert periodic_run.output_annotations[0].end_time == 0.6


def test_linear_acceleration_example_produces_many_peak_candidates():
    canonical = import_accelerometer_csv(LINEAR)
    run = run_peak_detector(canonical, trigger_delta=10.0, reset_delta=3.0, min_separation_s=0.1)

    assert len(run.output_annotations) > 400
    assert run.output_annotations[0].start_time == 2.573093
    assert run.output_annotations[0].source == "extractor"


def test_label_studio_config_task_prediction_and_export_round_trip(tmp_path):
    canonical = import_accelerometer_csv(FIXTURE)
    peak_run = run_peak_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)

    config = generate_time_series_label_config(canonical.stream.channels)
    assert '<TimeSeries name="ts"' in config
    assert '<MultiChannel>' in config
    assert '<Channel column="ax"' in config

    task = build_task_with_extractor_run(canonical.stream, csv_url="http://localhost/files/accelerometer_fixture.csv", run=peak_run)
    prediction = extractor_run_to_prediction(peak_run)
    assert task["predictions"][0]["result"][0]["value"]["instant"] is True
    assert prediction["model_version"] == "accelerometer_peak:0.1.0"

    exported_task = {
        **task,
        "annotations": [
            {
                "result": [
                    {
                        "id": "manual_interval_1",
                        "from_name": "label",
                        "to_name": "ts",
                        "type": "timeserieslabels",
                        "value": {
                            "start": 0.2,
                            "end": 0.6,
                            "instant": False,
                            "timeserieslabels": ["reviewed_interval"],
                        },
                    }
                ]
            }
        ],
    }
    parsed = parse_label_studio_annotations(exported_task)
    assert parsed[0].label == "reviewed_interval"
    assert parsed[0].type == "interval"
    assert parsed[0].session_id == canonical.session.id

    annotations_path = write_annotations_json(parsed, tmp_path / "annotations.json")
    assert read_annotations_json(annotations_path) == parsed
    assert json.loads(annotations_path.read_text(encoding="utf-8"))[0]["source"] == "human"


def test_optional_research_extractors_report_missing_dependencies_when_unavailable():
    canonical = import_accelerometer_csv(FIXTURE)
    stumpy_run = run_stumpy_matrix_profile_detector(canonical, window_size=4)
    sktime_run = run_sktime_segmentation_detector(canonical)

    assert stumpy_run.extractor_name == "stumpy_matrix_profile"
    assert sktime_run.extractor_name == "sktime_segmentation"
    assert stumpy_run.diagnostics["status"] in {"missing_dependency", "ok"}
    assert sktime_run.diagnostics["status"] in {"missing_dependency", "not_configured"}


def test_data_api_serves_workbench_and_label_studio_contracts():
    client = TestClient(create_app())

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    datasets = client.get("/datasets").json()
    assert {dataset["id"] for dataset in datasets} >= {"accelerometer_fixture.csv", "linear_acceleration_example.csv"}

    peak_run = client.post("/datasets/accelerometer_fixture.csv/extractors/peak").json()
    assert [annotation["start_time"] for annotation in peak_run["output_annotations"]] == [0.2, 0.6]

    task = client.get("/datasets/accelerometer_fixture.csv/label-studio/task").json()
    assert task["data"]["csv"].startswith("http://testserver/files/")
    assert task["predictions"][0]["model_version"] == "accelerometer_peak:0.1.0"


def test_data_api_serves_typed_tracks_overviews_previews_and_commits():
    client = TestClient(create_app())

    model = client.get("/datasets/accelerometer_fixture.csv/workbench").json()
    track_kinds = {track["kind"] for track in model["tracks"]}
    assert {"multichannel-timeseries", "numeric-timeseries", "derived-signal", "event-tier", "interval-tier"} <= track_kinds
    assert {schema["id"] for schema in model["event_schemas"]} == {"accelerometer_review"}

    magnitude_track = next(track for track in model["tracks"] if track["channel"] == "magnitude")
    compatible_tool_ids = {
        tool["id"]
        for tool in model["tool_definitions"]
        if magnitude_track["kind"] in tool["accepts"]
    }
    assert {"peak-detector", "threshold-intervals", "periodicity-detector"} <= compatible_tool_ids

    overview = client.get(f"/datasets/accelerometer_fixture.csv/tracks/{magnitude_track['id']}/overview").json()
    assert overview["time_range"] == {"start": 0.0, "end": 0.8}
    assert len(overview["points"]) == 9
    assert overview["points"][2]["magnitude"] == 13.2

    preview = client.post(
        "/datasets/accelerometer_fixture.csv/tools/peak-detector/preview",
        json={"track_id": magnitude_track["id"], "parameters": {"trigger_delta": 2.5, "reset_delta": 0.7}},
    ).json()
    annotations = preview["detector_preview"]["annotations"]
    assert [annotation["start_time"] for annotation in annotations] == [0.2, 0.6]
    assert annotations[0]["value_source"] == "sample-at-time"
    assert annotations[0]["reviewed"] is False

    committed = client.post(
        f"/datasets/accelerometer_fixture.csv/detector-previews/{preview['detector_preview']['id']}/commit",
        json={"annotations": annotations[:1]},
    ).json()
    assert committed["annotation_tier"]["track_kind"] == "event-tier"
    assert committed["annotations"][0]["reviewed"] is True
