# Build roadmap

## Phase 0: Foundations (now)
- Define architecture and repository conventions.
- Implement first analyzer: accelerometer parser/event detector.
- Add fixture data and tests.

## Phase 1: Local analysis MVP
- Add robust input adapters (CSV/JSON).
- Add parameterized detection pipeline.
- Export events to JSONL/CSV and summary stats.

## Phase 2: Recording clients
- Android recorder prototype (accelerometer + touch).
- Browser recorder prototype using DeviceMotion API.
- Unified session/device identifiers.

## Phase 3: Backend integration
- Ingest service for multi-device event streams.
- Session synchronization and drift correction.
- Store raw + derived data with query APIs.

## Phase 4: Multi-modal expansion
- Audio/camera-assisted event detection.
- Fusion strategies across sensors.
- Confidence scoring and provenance tracking.

## Phase 5: Productization
- Dashboard for run review and comparisons.
- User/workspace management.
- Deployment, monitoring, and reproducibility workflows.
