from __future__ import annotations

import argparse
import json
from pathlib import Path

from countpp_extractors import run_peak_detector, run_periodicity_detector, run_start_stop_interval_detector
from countpp_label_studio_bridge import build_task_with_extractor_run, generate_time_series_label_config
from countpp_schemas import EventExport
from countpp_signal_io import import_accelerometer_csv, write_annotations_json, write_event_export, write_stream_parquet


def main() -> None:
    parser = argparse.ArgumentParser(description="Run countpp extractors over an accelerometer CSV.")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/derived/extraction_run"))
    parser.add_argument("--csv-url", default=None, help="URL Label Studio should use for the CSV task.")
    args = parser.parse_args()

    canonical = import_accelerometer_csv(args.csv)
    args.out.mkdir(parents=True, exist_ok=True)

    parquet_path = write_stream_parquet(canonical, args.out / "stream.parquet")
    peak_run = run_peak_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
    interval_run = run_start_stop_interval_detector(canonical, start_delta=2.5, stop_delta=0.7)
    periodic_run = run_periodicity_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1, min_peaks=2)

    annotations = peak_run.output_annotations + interval_run.output_annotations + periodic_run.output_annotations
    annotations_path = write_annotations_json(annotations, args.out / "annotations.json")
    export_path = write_event_export(
        EventExport(
            id=f"export_{canonical.stream.id}",
            session_id=canonical.session.id,
            annotations=annotations,
            metadata={"source_csv": args.csv.as_posix(), "parquet": parquet_path.as_posix()},
        ),
        args.out / "event_export.json",
    )
    config_path = args.out / "label_config.xml"
    config_path.write_text(generate_time_series_label_config(canonical.stream.channels), encoding="utf-8")
    task = build_task_with_extractor_run(
        canonical.stream,
        csv_url=args.csv_url or args.csv.resolve().as_uri(),
        run=peak_run,
    )
    task_path = args.out / "label_studio_task.json"
    task_path.write_text(json.dumps([task], indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "parquet": parquet_path.as_posix(),
                "annotations": annotations_path.as_posix(),
                "event_export": export_path.as_posix(),
                "label_config": config_path.as_posix(),
                "label_studio_task": task_path.as_posix(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
