# Data Analyzer App (web MVP)

## Why Dash + Plotly
For this phase, we adapt a mature open-source analytics stack rather than building custom charting from scratch:
- **Dash** provides a reactive web application framework.
- **Plotly** gives performant interactive time-series rendering and annotation overlays.

This is a good fit for future multi-format and multi-signal workflows (accelerometer/audio/video-derived channels).

## Implemented MVP capabilities
- Load accelerometer CSV (example data or upload).
- Display all channels (`ax`, `ay`, `az`) plus magnitude.
- Detect events using peak detection (threshold+hysteresis).
- Detect periodic behavior from detected events.
- Add manual extraction windows (start/stop) from the UI.
- Merge detector-driven and manual windows into one extraction view.

## Run locally
From repository root:

```bash
pip install -e services/analysis_engine
pip install -e apps/data_analyzer_web
python apps/data_analyzer_web/app.py
```

Then open `http://127.0.0.1:8050`.

## Next iterations
- Add additional parsers (JSONL, parquet, WAV-derived events).
- Add synchronized timelines from external sources (audio triggers, camera markers).
- Add user-friendly drag-to-create windows directly on chart regions.
- Add server-backed session storage and collaboration.
