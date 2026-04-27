# Architecture

`countpp` is organized around an event extraction loop, not a single plotting app:

```text
raw stream
  -> normalized stream
  -> derived channels
  -> extractor suggestions
  -> human correction
  -> final event log
  -> reproducible export
```

Raw data is immutable. Users and extractors create annotations, derived channels, extractor runs, and exports.

## Current repo layout

- `apps/workbench_web/` — React workbench for data sources, typed tracks, context tools, detector previews, Label Studio handoff, and export inspection.
- `services/data_api/` — FastAPI boundary for datasets, Label Studio tasks, extractor runs, and event exports.
- `services/extraction_worker/` — batch CLI for canonicalizing CSVs, running extractors, and writing review/export artifacts.
- `services/label_studio_bridge/` — Label Studio label config, task, prediction, and annotation conversion.
- `services/analysis_engine/` — compatibility package for the earlier accelerometer parser/detector API.
- `packages/schemas/` — shared `RecordingSession`, `Stream`, `Channel`, `Annotation`, `ExtractorRun`, and `EventExport` models.
- `packages/signal_io/` — CSV accelerometer import, Parquet stream export, and JSON annotation export.
- `packages/extractors/` — extractor plugin implementations.
- `data/examples/` — committed examples used by tests.
- `data/derived/` — local generated artifacts; not the raw source of truth.

## Interaction layer

Label Studio is the first serious editor/review layer. The workbench owns datasets, extraction runs, exports, and domain workflows. Label Studio receives time-series tasks plus extractor predictions and returns reviewed annotations that are parsed back into `Annotation` objects.

This keeps the project from turning into a custom clone of audio/video editors before the data model and extraction workflow are stable.

## Service boundaries

- `signal_io` normalizes raw uploads into canonical stream tables and metadata.
- `extractors` consume canonical streams and return `ExtractorRun` objects with annotations.
- `label_studio_bridge` converts internal annotations into Label Studio predictions and Label Studio exports back into internal annotations.
- `data_api` exposes the current local workflow to the workbench shell, including typed tracks, downsampled full-range track overviews, tool definitions, detector previews, and commit/export operations.

## Storage direction

- Raw upload: CSV now, JSON/WAV later.
- Canonical local stream: Parquet.
- Annotation and event metadata: JSON now, database later.
- Local query direction: DuckDB over Parquet.
- Large multidimensional future: Zarr.

## Design rule

Every feature must preserve provenance: which raw stream, derived channel, extractor version, parameters, human edit, and export created a timestamp.
