# Architecture (v0)

## Design goals
1. **Device flexibility**: Android app + browser app for low-friction recording.
2. **Analysis-first**: process raw streams into event timestamps in real time and batch modes.
3. **Sync and collaboration**: aggregate multiple device streams into shared sessions.
4. **Modular UI**: independent front-end apps over stable APIs.
5. **Extensibility**: add new sensor modalities without rewriting core services.

## Proposed monorepo layout

- `apps/mobile-android/` — native Android recording app.
- `apps/web-recorder/` — browser-based recorder (PWA style).
- `apps/web-dashboard/` — review + analysis UI.
- `services/gateway/` — auth, routing, API composition.
- `services/ingest/` — stream ingestion, session tracking.
- `services/analysis_engine/` — signal/event processing (real-time + batch).
- `services/storage/` — persistence adapters and schemas.
- `packages/protocols/` — shared event schemas (OpenAPI/JSON Schema/Protobuf).
- `packages/ui-components/` — shared visual components.
- `infra/` — deployment manifests, IaC, observability configs.

## Data model (core entities)
- **Session**: one logical recording run across devices.
- **DeviceStream**: one sensor stream from one device (accelerometer/audio/etc).
- **RawSample**: timestamped sensor payload (never discarded).
- **DerivedEvent**: computed event with confidence and provenance.
- **AnalysisRun**: algorithm version + parameters + outputs.

## API boundaries
- Recording apps submit raw samples to `ingest` with clock metadata.
- `ingest` writes immutable raw data and publishes to analysis pipeline.
- `analysis_engine` emits `DerivedEvent` objects with model/algorithm version tags.
- UI apps only talk to `gateway` APIs, never directly to analysis internals.

## Why this scales
- New sensors = new analyzers and schemas, not a platform rewrite.
- Real-time and batch share the same analysis primitives.
- Front-end can evolve independently because APIs are explicit and versioned.
