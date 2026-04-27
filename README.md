# countpp

`countpp` is a time-series event extraction workbench: raw multimodal recordings in, human/editable annotations plus algorithmic predictions in the middle, clean event logs and timestamps out.

This repository is organized to support:
- Immutable raw recordings with normalized stream metadata.
- Human annotations and extractor predictions over the same event model.
- Label Studio-backed time-series review before custom editors are built.
- Plugin-style extractors for peaks, intervals, periodicity, and later STUMPY/sktime.
- Exportable, reproducible event logs.

## Start here
- High-level architecture: `docs/architecture.md`
- Data model: `docs/data_model.md`
- Extractor contract: `docs/extractor_contract.md`
- Workbench interaction inventory: `docs/workbench_interactions.md`
- Phased build plan: `docs/roadmap.md`
- Workbench shell: `apps/workbench_web`
- Data API: `services/data_api`
- Label Studio bridge: `services/label_studio_bridge`
- Batch extraction worker: `services/extraction_worker`

## What runs today

The current runnable system has two parts:

- **Data API**: a local FastAPI service that lists example datasets, runs extractors, serves CSV files, and returns Label Studio task JSON.
- **Workbench web**: a React UI that talks to the Data API. It is the outer shell for typed-track review, detector previews, Label Studio handoff, and event export inspection.

Label Studio itself is optional at this stage. The repo can generate Label Studio configs/tasks now; full project creation/import automation comes next.

## Current loop
```text
raw stream
  -> normalized stream
  -> derived channels
  -> extractor suggestions
  -> human correction
  -> final event log
  -> reproducible export
```

## Setup From A Fresh Clone

Prerequisites:

- Python 3.10 or newer.
- Node.js 20 or newer for the React workbench.
- A shell with `git`.
- A browser.

Clone and enter the repo:

```bash
git clone <repo-url> countpp
cd countpp
```

Create a virtual environment.

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install the local packages and test tools:

```bash
python -m pip install \
  -e packages/schemas \
  -e packages/signal_io \
  -e packages/extractors \
  -e services/label_studio_bridge \
  -e services/data_api \
  -e services/extraction_worker \
  pytest
```

On Windows PowerShell, use backticks instead of backslashes:

```powershell
python -m pip install `
  -e packages/schemas `
  -e packages/signal_io `
  -e packages/extractors `
  -e services/label_studio_bridge `
  -e services/data_api `
  -e services/extraction_worker `
  pytest
```

## Run The Workbench

Use two terminals with the virtual environment activated in both.

Terminal 1: start the Data API.

```bash
python -m uvicorn countpp_data_api.app:app --host 127.0.0.1 --port 8000
```

Check it:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/datasets
```

Terminal 2: run the React workbench.

```bash
cd apps/workbench_web
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:8081
```

Expected first use:

1. The Project bin lists available data sources from the Data API.
2. Select a data source.
3. The timeline shows typed tracks built from the API: raw multichannel stream, numeric channels, derived magnitude, event tier, and interval tier.
4. Select a numeric or derived-signal track.
5. The Context inspector shows only tools compatible with that track kind.
6. Choose **Peak detector**, click **Preview**, then accept/reject/edit candidates in the bottom event table.
7. Click **Commit accepted** to create reviewed event-tier annotations.

If the API is not on port `8000`, change the API field in the left sidebar to the URL you used.

## Useful API Endpoints

```bash
curl http://127.0.0.1:8000/datasets
curl http://127.0.0.1:8000/datasets/accelerometer_fixture.csv
curl http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/workbench
curl http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/tracks/<track-id>/overview
curl -X POST http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/extractors/peak
curl http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/label-studio/config
curl http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/label-studio/task
curl http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/exports/events
```

## Run The Batch Worker

The worker generates canonical and review/export artifacts without opening the web UI:

```bash
countpp-extract data/examples/accelerometer_fixture.csv --out data/derived/fixture_run
```

It writes:

- `stream.parquet`
- `annotations.json`
- `event_export.json`
- `label_config.xml`
- `label_studio_task.json`

`data/derived/` is for local generated output and is ignored by git except for its README.

## Optional Label Studio Review

Install and start Label Studio separately:

```bash
python -m pip install label-studio
label-studio start --port 8080
```

Then:

1. Create a Label Studio project.
2. Use the XML from `http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/label-studio/config` as the labeling config.
3. Import the task JSON from `http://127.0.0.1:8000/datasets/accelerometer_fixture.csv/label-studio/task`.

The task JSON points Label Studio at the CSV served by the Data API, so keep the Data API running while reviewing.

## Run Tests

```bash
python -m pytest -q
```

Current expected result:

```text
12 passed
```

## Development Notes

- Do not build new annotation/editing behavior into the old Dash app. It has been removed.
- Do not add frontend-owned signal data. A missing API or failed data load must be visible as an error or empty state.
- Keep raw data immutable. Add annotations, derived channels, extractor runs, and exports around it.
- Optional research extractors such as STUMPY and sktime should degrade cleanly when those dependencies are not installed.
