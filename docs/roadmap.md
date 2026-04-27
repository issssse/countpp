# Roadmap

## Phase 0: Workbench foundations
- Define shared session, stream, channel, annotation, extractor run, and export schemas.
- Normalize accelerometer CSV examples into canonical stream tables.
- Export canonical streams to Parquet.
- Convert extractor annotations into Label Studio predictions.
- Parse reviewed Label Studio annotations back into internal annotations.
- Keep the old accelerometer analysis package only as compatibility code.

## Phase 1: Label Studio-backed accelerometer workflow
- Run peak, start/stop interval, and periodicity extractors from `data_api`.
- Create Label Studio projects/tasks from uploaded or example CSV files.
- Import extractor outputs as pre-annotations.
- Pull reviewed annotations into the countpp annotation store.
- Export final event logs as JSON and CSV.

## Phase 2: Extraction system
- Add configurable transform steps: resampling, smoothing, gravity removal, magnitude, jerk.
- Add stronger event candidates: threshold crossings, hysteresis, peak grouping, and template matching.
- Add STUMPY matrix-profile workflows for motifs, discords, and segmentation prototypes.
- Add sktime/catch22/tsfresh feature pipelines where dependencies and task definitions are stable.

## Phase 3: Workbench product surface
- Expand the React workbench with server-backed persistence.
- Add dataset import history, extractor run history, annotation diffs, and export review.
- Add authentication/storage only after the local workflow is solid.
- Build custom high-performance React viewers only for workflows Label Studio cannot handle well.

## Phase 4: Recorders and sync
- Browser recorder for low-friction capture and sharing.
- Android recorder for authoritative sensor timestamps.
- Session sync service for multi-device ingestion, clock alignment, and websocket ingest.

## Phase 5: Multimodal expansion
- Audio start/stop and clap/sync markers.
- Video/camera-derived events.
- Touch and external trigger streams.
- Cross-stream event fusion with provenance and confidence.
