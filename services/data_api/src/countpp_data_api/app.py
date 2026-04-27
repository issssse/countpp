from __future__ import annotations

from pathlib import Path
from typing import Any

from countpp_extractors import run_peak_detector, run_periodicity_detector, run_start_stop_interval_detector
from countpp_label_studio_bridge import build_task_with_extractor_run, generate_time_series_label_config
from countpp_schemas import (
    Annotation,
    AnnotationTier,
    DataSource,
    DetectorPreview,
    EventExport,
    EventSchema,
    ToolDefinition,
    Track,
    TrackView,
)
from countpp_signal_io import import_accelerometer_csv
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES_DIR = ROOT / "data" / "examples"


def create_app() -> FastAPI:
    app = FastAPI(title="countpp data API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/files", StaticFiles(directory=EXAMPLES_DIR), name="files")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/datasets")
    def list_datasets() -> list[dict[str, object]]:
        return [
            {
                "id": path.name,
                "name": path.stem.replace("_", " "),
                "path": path.as_posix(),
                "kind": "accelerometer_csv",
            }
            for path in sorted(EXAMPLES_DIR.glob("*.csv"))
        ]

    @app.get("/datasets/{dataset_id}")
    def get_dataset(dataset_id: str) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        return {
            "session": canonical.session.to_dict(),
            "stream": canonical.stream.to_dict(),
            "rows": canonical.table.num_rows,
            "columns": canonical.table.column_names,
        }

    @app.get("/datasets/{dataset_id}/workbench")
    def get_workbench(dataset_id: str, request: Request) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        base_url = str(request.base_url).rstrip("/")
        return {
            "session": canonical.session.to_dict(),
            "data_sources": [_data_source(dataset_id, base_url, canonical).to_dict()],
            "stream": canonical.stream.to_dict(),
            "tracks": [track.to_dict() for track in _tracks(canonical)],
            "track_views": [view.to_dict() for view in _track_views(canonical)],
            "annotation_tiers": [tier.to_dict() for tier in _annotation_tiers(canonical)],
            "event_schemas": [schema.to_dict() for schema in _event_schemas()],
            "tool_definitions": [tool.to_dict() for tool in _tool_definitions()],
            "tool_presets": [],
            "extension_track_kinds": ["audio", "video", "image-sequence", "touch-log", "sync-map"],
            "label_studio": {
                "config_url": f"{base_url}/datasets/{dataset_id}/label-studio/config",
                "task_url": f"{base_url}/datasets/{dataset_id}/label-studio/task",
                "server_url": "http://127.0.0.1:8080",
            },
        }

    @app.get("/datasets/{dataset_id}/tracks/{track_id}/overview")
    def get_track_overview(
        dataset_id: str,
        track_id: str,
        points: int = Query(default=1200, ge=16, le=10000),
    ) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        track = _track_by_id(canonical, track_id)
        channels = _overview_channels(track)
        if not channels:
            return {"track_id": track_id, "channels": [], "time_range": None, "points": [], "stats": {}}
        table = canonical.table
        time_values = [float(v) for v in table.column("time").combine_chunks().to_pylist()]
        if not time_values:
            return {"track_id": track_id, "channels": channels, "time_range": None, "points": [], "stats": {}}

        channel_values = {
            channel: [float(v) for v in table.column(channel).combine_chunks().to_pylist()]
            for channel in channels
            if channel in table.column_names
        }
        indices = _sample_indices(len(time_values), points)
        overview_points = [
            {"time": time_values[i], **{channel: values[i] for channel, values in channel_values.items()}}
            for i in indices
        ]
        stats = {
            channel: {"min": min(values), "max": max(values)}
            for channel, values in channel_values.items()
            if values
        }
        return {
            "track_id": track_id,
            "channels": list(channel_values),
            "time_range": {"start": time_values[0], "end": time_values[-1]},
            "points": overview_points,
            "stats": stats,
            "source_rows": len(time_values),
            "overview_rows": len(overview_points),
        }

    @app.get("/tools")
    def get_tools() -> list[dict[str, object]]:
        return [tool.to_dict() for tool in _tool_definitions()]

    @app.get("/datasets/{dataset_id}/label-studio/config")
    def get_label_studio_config(dataset_id: str) -> dict[str, str]:
        canonical = _load_dataset(dataset_id)
        return {"config": generate_time_series_label_config(canonical.stream.channels)}

    @app.post("/datasets/{dataset_id}/extractors/{extractor_name}")
    def run_extractor(dataset_id: str, extractor_name: str) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        if extractor_name == "peak":
            run = run_peak_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
        elif extractor_name == "start-stop":
            run = run_start_stop_interval_detector(canonical, start_delta=2.5, stop_delta=0.7)
        elif extractor_name == "periodicity":
            run = run_periodicity_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1, min_peaks=2)
        else:
            raise HTTPException(status_code=404, detail=f"unknown extractor {extractor_name!r}")
        return run.to_dict()

    @app.post("/datasets/{dataset_id}/tools/{tool_id}/preview")
    def preview_tool(dataset_id: str, tool_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        track_id = payload.get("track_id")
        if not isinstance(track_id, str):
            raise HTTPException(status_code=400, detail="track_id is required")
        track = _track_by_id(canonical, track_id)
        parameters = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else {}
        run = _run_tool(canonical, track, tool_id, parameters)
        preview_track_id = f"{run.id}:preview"
        preview = DetectorPreview(
            id=f"preview_{run.id}",
            extractor_run_id=run.id,
            source_track_id=track.id,
            preview_track_id=preview_track_id,
            annotations=run.output_annotations,
            metadata={"tool_id": tool_id, "track_name": track.name},
        )
        preview_track = Track(
            id=preview_track_id,
            session_id=canonical.session.id,
            name=f"{run.extractor_name} preview",
            kind="detector-preview",
            source_stream_id=canonical.stream.id,
            parent_track_id=track.id,
            visible=True,
            editable=True,
            metadata={"extractor_run_id": run.id, "tool_id": tool_id},
        )
        return {
            "extractor_run": run.to_dict(),
            "detector_preview": preview.to_dict(),
            "preview_track": preview_track.to_dict(),
        }

    @app.post("/datasets/{dataset_id}/detector-previews/{preview_id}/commit")
    def commit_preview(dataset_id: str, preview_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        raw_annotations = payload.get("annotations")
        if not isinstance(raw_annotations, list):
            raise HTTPException(status_code=400, detail="annotations list is required")
        annotations = [_reviewed_annotation(item) for item in raw_annotations]
        tier = AnnotationTier(
            id=f"tier_{canonical.stream.id}_events",
            session_id=canonical.session.id,
            name="Reviewed events",
            track_kind="event-tier",
            labels=[label for schema in _event_schemas() for label in schema.labels],
        )
        return {
            "preview_id": preview_id,
            "annotation_tier": tier.to_dict(),
            "annotations": [annotation.to_dict() for annotation in annotations],
        }

    @app.get("/datasets/{dataset_id}/label-studio/task")
    def get_label_studio_task(dataset_id: str, request: Request) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        run = run_peak_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
        base_url = str(request.base_url).rstrip("/")
        return build_task_with_extractor_run(
            canonical.stream,
            csv_url=f"{base_url}/files/{dataset_id}",
            run=run,
        )

    @app.get("/datasets/{dataset_id}/exports/events")
    def get_event_export(dataset_id: str) -> dict[str, object]:
        canonical = _load_dataset(dataset_id)
        peak_run = run_peak_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1)
        periodic_run = run_periodicity_detector(canonical, trigger_delta=2.5, reset_delta=0.7, min_separation_s=0.1, min_peaks=2)
        export = EventExport(
            id=f"export_{canonical.stream.id}",
            session_id=canonical.session.id,
            annotations=peak_run.output_annotations + periodic_run.output_annotations,
            metadata={"dataset_id": dataset_id},
        )
        return export.to_dict()

    return app


def _load_dataset(dataset_id: str):
    path = (EXAMPLES_DIR / dataset_id).resolve()
    if not path.is_file() or EXAMPLES_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=404, detail=f"dataset {dataset_id!r} not found")
    return import_accelerometer_csv(path)


def _data_source(dataset_id: str, base_url: str, canonical) -> DataSource:
    return DataSource(
        id=dataset_id,
        name=canonical.session.name,
        uri=f"{base_url}/files/{dataset_id}",
        format="csv",
        modality=canonical.stream.modality,
        metadata={
            "rows": canonical.table.num_rows,
            "columns": canonical.table.column_names,
            "raw_uri": canonical.stream.raw_uri,
        },
    )


def _tracks(canonical) -> list[Track]:
    session_id = canonical.session.id
    stream_id = canonical.stream.id
    raw_channels = [channel.name for channel in canonical.stream.channels if channel.name != "magnitude"]
    tracks = [
        Track(
            id=f"{stream_id}:raw",
            session_id=session_id,
            name="Raw accelerometer",
            kind="multichannel-timeseries",
            source_stream_id=stream_id,
            channels=raw_channels,
            visible=True,
            editable=False,
            metadata={"modality": "accelerometer"},
        )
    ]
    for channel in canonical.stream.channels:
        kind = "derived-signal" if channel.derived_from else "numeric-timeseries"
        tracks.append(
            Track(
                id=f"{stream_id}:{channel.name}",
                session_id=session_id,
                name=channel.name,
                kind=kind,
                source_stream_id=stream_id,
                channel=channel.name,
                channels=[channel.name],
                unit=channel.unit,
                visible=True,
                editable=False,
                parent_track_id=f"{stream_id}:raw" if kind == "derived-signal" else None,
                metadata={"axis": channel.axis, "derived_from": channel.derived_from},
            )
        )
    tracks.extend(
        [
            Track(
                id=f"{stream_id}:events",
                session_id=session_id,
                name="Reviewed event tier",
                kind="event-tier",
                source_stream_id=stream_id,
                visible=True,
                editable=True,
            ),
            Track(
                id=f"{stream_id}:intervals",
                session_id=session_id,
                name="Reviewed interval tier",
                kind="interval-tier",
                source_stream_id=stream_id,
                visible=True,
                editable=True,
            ),
        ]
    )
    return tracks


def _track_views(canonical) -> list[TrackView]:
    colors = {
        "raw": "#38bdf8",
        "ax": "#10b981",
        "ay": "#f59e0b",
        "az": "#d946ef",
        "magnitude": "#06b6d4",
        "events": "#8b5cf6",
        "intervals": "#ef4444",
    }
    views = []
    for track in _tracks(canonical):
        key = track.channel or track.id.rsplit(":", 1)[-1]
        views.append(
            TrackView(
                id=f"view_{track.id}",
                track_id=track.id,
                view_type="timeline-layer",
                height=120 if track.kind in {"multichannel-timeseries", "derived-signal"} else 82,
                color=colors.get(key),
            )
        )
    return views


def _annotation_tiers(canonical) -> list[AnnotationTier]:
    labels = [label for schema in _event_schemas() for label in schema.labels]
    return [
        AnnotationTier(
            id=f"tier_{canonical.stream.id}_events",
            session_id=canonical.session.id,
            name="Events",
            track_kind="event-tier",
            labels=labels,
        ),
        AnnotationTier(
            id=f"tier_{canonical.stream.id}_intervals",
            session_id=canonical.session.id,
            name="Intervals",
            track_kind="interval-tier",
            labels=labels,
        ),
    ]


def _event_schemas() -> list[EventSchema]:
    return [
        EventSchema(
            id="accelerometer_review",
            name="Accelerometer review",
            labels=["Impact", "Start", "Stop", "Invalid Region"],
            attributes_schema={
                "hand": {"type": "string", "enum": ["left", "right", "unknown"]},
                "quality": {"type": "string", "enum": ["clean", "uncertain", "invalid"]},
                "comment": {"type": "string"},
            },
        )
    ]


def _tool_definitions() -> list[ToolDefinition]:
    numeric = ["numeric-timeseries", "derived-signal"]
    annotation = ["event-tier", "interval-tier", "detector-preview"]
    return [
        ToolDefinition(
            id="create-point-event",
            name="Create point event",
            category="annotate",
            accepts=numeric + annotation,
            produces=["event-tier"],
            parameters_schema={"label": {"type": "string"}},
            requires_selection=False,
            previewable=False,
        ),
        ToolDefinition(
            id="create-interval-event",
            name="Create interval event",
            category="annotate",
            accepts=numeric + annotation,
            produces=["interval-tier"],
            parameters_schema={"label": {"type": "string"}},
            requires_selection=True,
            previewable=False,
        ),
        ToolDefinition(
            id="peak-detector",
            name="Peak detector",
            category="detect",
            accepts=numeric,
            produces=["detector-preview"],
            parameters_schema={
                "trigger_delta": {"type": "number", "default": 2.5},
                "reset_delta": {"type": "number", "default": 0.7},
                "min_separation_s": {"type": "number", "default": 0.1},
            },
            previewable=True,
        ),
        ToolDefinition(
            id="threshold-intervals",
            name="Threshold intervals",
            category="detect",
            accepts=numeric,
            produces=["detector-preview"],
            parameters_schema={
                "start_delta": {"type": "number", "default": 2.5},
                "stop_delta": {"type": "number", "default": 0.7},
            },
            previewable=True,
        ),
        ToolDefinition(
            id="periodicity-detector",
            name="Periodicity detector",
            category="detect",
            accepts=numeric,
            produces=["detector-preview"],
            parameters_schema={
                "trigger_delta": {"type": "number", "default": 2.5},
                "reset_delta": {"type": "number", "default": 0.7},
                "min_peaks": {"type": "integer", "default": 2},
            },
            previewable=True,
        ),
        ToolDefinition(
            id="smoothing",
            name="Smoothing",
            category="transform",
            accepts=numeric,
            produces=["derived-signal"],
            parameters_schema={"window_s": {"type": "number", "default": 0.05}},
        ),
        ToolDefinition(
            id="derivative",
            name="Derivative / jerk",
            category="transform",
            accepts=numeric,
            produces=["derived-signal"],
            parameters_schema={},
        ),
        ToolDefinition(
            id="change-point",
            name="Change point",
            category="detect",
            accepts=numeric,
            produces=["detector-preview"],
            parameters_schema={},
        ),
        ToolDefinition(
            id="matrix-profile",
            name="Matrix profile",
            category="detect",
            accepts=numeric,
            produces=["detector-preview"],
            parameters_schema={"window_size": {"type": "integer", "default": 64}},
        ),
        ToolDefinition(
            id="audio-onset",
            name="Audio onset detector",
            category="detect",
            accepts=["audio"],
            produces=["detector-preview"],
            parameters_schema={},
        ),
        ToolDefinition(
            id="video-frame-marker",
            name="Video frame marker",
            category="annotate",
            accepts=["video"],
            produces=["event-tier"],
            parameters_schema={},
        ),
        ToolDefinition(
            id="event-tier-validation",
            name="Validate coding map",
            category="edit",
            accepts=annotation,
            produces=["event-tier"],
            parameters_schema={},
            previewable=False,
        ),
    ]


def _track_by_id(canonical, track_id: str) -> Track:
    for track in _tracks(canonical):
        if track.id == track_id:
            return track
    raise HTTPException(status_code=404, detail=f"track {track_id!r} not found")


def _overview_channels(track: Track) -> list[str]:
    if track.kind in {"numeric-timeseries", "derived-signal", "multichannel-timeseries"}:
        return track.channels or ([track.channel] if track.channel else [])
    return []


def _sample_indices(length: int, target: int) -> list[int]:
    if length <= target:
        return list(range(length))
    if target < 2:
        return [0]
    last = length - 1
    return sorted({round(i * last / (target - 1)) for i in range(target)})


def _run_tool(canonical, track: Track, tool_id: str, parameters: dict[str, Any]):
    channel = track.channel or ("magnitude" if "magnitude" in track.channels else None)
    if not channel:
        raise HTTPException(status_code=400, detail=f"tool {tool_id!r} needs a numeric or derived signal track")
    if tool_id == "peak-detector":
        return run_peak_detector(
            canonical,
            channel=channel,
            trigger_delta=float(parameters.get("trigger_delta", 2.5)),
            reset_delta=float(parameters.get("reset_delta", 0.7)),
            min_separation_s=float(parameters.get("min_separation_s", 0.1)),
            label="Impact",
        )
    if tool_id == "threshold-intervals":
        return run_start_stop_interval_detector(
            canonical,
            channel=channel,
            start_delta=float(parameters.get("start_delta", 2.5)),
            stop_delta=float(parameters.get("stop_delta", 0.7)),
            label="Invalid Region",
        )
    if tool_id == "periodicity-detector":
        return run_periodicity_detector(
            canonical,
            channel=channel,
            trigger_delta=float(parameters.get("trigger_delta", 2.5)),
            reset_delta=float(parameters.get("reset_delta", 0.7)),
            min_peaks=int(parameters.get("min_peaks", 2)),
            label="Repeated motion",
        )
    raise HTTPException(status_code=400, detail=f"tool {tool_id!r} is registered but not executable yet")


def _reviewed_annotation(payload: dict[str, Any]) -> Annotation:
    data = dict(payload)
    data["reviewed"] = True
    return Annotation.from_dict(data)


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("countpp_data_api.app:app", host="127.0.0.1", port=8000, reload=True)
