from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

Modality = Literal["accelerometer", "audio", "video", "touch", "camera", "derived"]
AnnotationType = Literal["instant", "interval"]
AnnotationSource = Literal["human", "extractor", "imported", "synced_device", "synced-stream"]
TrackKind = Literal[
    "numeric-timeseries",
    "multichannel-timeseries",
    "audio",
    "video",
    "image-sequence",
    "touch-log",
    "event-tier",
    "interval-tier",
    "derived-signal",
    "detector-preview",
    "sync-map",
]
ToolCategory = Literal["edit", "detect", "transform", "sync", "annotate", "export"]
ValueSource = Literal["sample-at-time", "interval-statistic", "other-signal-at-time", "detector-score", "manual"]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class RecordingSession:
    id: str
    name: str
    devices: list[str] = field(default_factory=list)
    started_at: str | None = None
    clock_model: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class Channel:
    name: str
    unit: str | None = None
    axis: str | None = None
    derived_from: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class DataSource:
    id: str
    name: str
    uri: str
    format: str
    modality: Modality
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class Stream:
    id: str
    session_id: str
    source_device_id: str | None
    modality: Modality
    channels: list[Channel]
    sample_rate_hint: float | None
    time_base: str
    raw_uri: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class Track:
    id: str
    session_id: str
    name: str
    kind: TrackKind
    source_stream_id: str | None = None
    channel: str | None = None
    channels: list[str] = field(default_factory=list)
    unit: str | None = None
    visible: bool = True
    editable: bool = False
    parent_track_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class TrackView:
    id: str
    track_id: str
    view_type: str
    height: int = 96
    color: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class AnnotationTier:
    id: str
    session_id: str
    name: str
    track_kind: TrackKind
    labels: list[str]
    editable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class Annotation:
    id: str
    label: str
    type: AnnotationType
    start_time: float
    source: AnnotationSource
    end_time: float | None = None
    stream_id: str | None = None
    session_id: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    event_type_id: str | None = None
    value: float | str | bool | None = None
    value_unit: str | None = None
    value_source: ValueSource | None = None
    attributes: dict[str, str | int | float | bool] = field(default_factory=dict)
    extractor_run_id: str | None = None
    reviewed: bool = False

    def __post_init__(self) -> None:
        if self.type == "instant":
            if self.end_time is None:
                object.__setattr__(self, "end_time", self.start_time)
            if self.end_time != self.start_time:
                raise ValueError("instant annotations must have end_time equal to start_time")
        elif self.type == "interval":
            if self.end_time is None:
                raise ValueError("interval annotations require end_time")
            if self.end_time <= self.start_time:
                raise ValueError("interval annotations require end_time > start_time")
        else:
            raise ValueError(f"unsupported annotation type: {self.type}")

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Annotation":
        return cls(**payload)


@dataclass(frozen=True)
class EventSchema:
    id: str
    name: str
    labels: list[str]
    attributes_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    category: ToolCategory
    accepts: list[TrackKind]
    produces: list[TrackKind]
    parameters_schema: dict[str, Any]
    requires_selection: bool = False
    previewable: bool = True
    destructive: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class ToolPreset:
    id: str
    tool_id: str
    name: str
    parameters: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class ExtractorRun:
    id: str
    extractor_name: str
    version: str
    input_streams: list[str]
    parameters: dict[str, Any]
    output_annotations: list[Annotation] = field(default_factory=list)
    diagnostics_uri: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class DetectorPreview:
    id: str
    extractor_run_id: str
    source_track_id: str
    preview_track_id: str
    annotations: list[Annotation]
    accepted_annotation_ids: list[str] = field(default_factory=list)
    rejected_annotation_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class DerivedSignal:
    id: str
    source_track_ids: list[str]
    output_track_id: str
    transform_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class SyncMap:
    id: str
    source_track_id: str
    target_track_id: str
    model: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)


@dataclass(frozen=True)
class EventExport:
    id: str
    session_id: str
    annotations: list[Annotation]
    format_version: str = "countpp.event_export.v1"
    generated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _to_jsonable(self)
