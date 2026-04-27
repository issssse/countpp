# Data Model

The canonical model is defined in `packages/schemas`.

## RecordingSession

A logical recording run. It can contain streams from one or many devices.

Fields:
- `id`
- `name`
- `devices`
- `started_at`
- `clock_model`
- `metadata`

## Stream

A timestamped signal source inside a recording session.

Fields:
- `id`
- `session_id`
- `source_device_id`
- `modality`: `accelerometer`, `audio`, `video`, `touch`, `camera`, or `derived`
- `channels`
- `sample_rate_hint`
- `time_base`
- `raw_uri`
- `metadata`

## DataSource

An importable project asset such as a CSV, WAV, video file, JSON annotation file, or future remote recording.

Fields:
- `id`
- `name`
- `uri`
- `format`
- `modality`
- `metadata`

## Track

A typed timeline lane. Tracks can represent raw streams, derived signals, annotation tiers, detector previews, media, or sync maps.

Initial track kinds:
- `numeric-timeseries`
- `multichannel-timeseries`
- `event-tier`
- `interval-tier`
- `derived-signal`
- `detector-preview`

Prepared extension kinds:
- `audio`
- `video`
- `image-sequence`
- `touch-log`
- `sync-map`

Fields:
- `id`
- `session_id`
- `name`
- `kind`
- `source_stream_id`
- `channel`
- `channels`
- `unit`
- `visible`
- `editable`
- `parent_track_id`
- `metadata`

## ToolDefinition

The registry entry that decides whether a tool can be shown for the selected track.

Fields:
- `id`
- `name`
- `category`
- `accepts`
- `produces`
- `parameters_schema`
- `requires_selection`
- `previewable`
- `destructive`
- `metadata`

## Channel

A named dimension within a stream.

Examples: `ax`, `ay`, `az`, `magnitude`, `audio_l`, `audio_r`.

Fields:
- `name`
- `unit`
- `axis`
- `derived_from`
- `metadata`

## Annotation

The shared representation for human edits, extractor predictions, imported events, and synced-device markers.

Fields:
- `id`
- `stream_id` or `session_id`
- `type`: `instant` or `interval`
- `start_time`
- `end_time`
- `label`
- `event_type_id`
- `value`
- `value_unit`
- `value_source`
- `attributes`
- `source`: `human`, `extractor`, `imported`, `synced_device`, or `synced-stream`
- `extractor_run_id`
- `confidence`
- `reviewed`
- `metadata`

`value_source` identifies whether the value came from a sample at the event time, an interval statistic, another synchronized signal, a detector score, or manual entry.

## ExtractorRun

The reproducibility record for an algorithm run.

Fields:
- `id`
- `extractor_name`
- `version`
- `input_streams`
- `parameters`
- `output_annotations`
- `diagnostics_uri`
- `diagnostics`
- `created_at`

## EventExport

The cleaned output artifact for downstream timestamp/event use.

Fields:
- `id`
- `session_id`
- `annotations`
- `format_version`
- `generated_at`
- `metadata`
