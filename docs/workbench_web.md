# Workbench Web

`apps/workbench_web` is the first product shell. It is intentionally not a custom time-series annotation editor.

Responsibilities:
- list data sources from `services/data_api`
- show selected recording/session metadata
- present typed tracks on one shared timeline
- filter tools by selected track kind
- preview detector candidates non-destructively
- accept/reject/edit candidates
- commit accepted candidates into annotation tiers
- link to Label Studio task/config endpoints for review
- inspect and export committed events

Run the API:

```bash
python -m pip install -e packages/schemas -e packages/signal_io -e packages/extractors -e services/label_studio_bridge -e services/data_api
python -m uvicorn countpp_data_api.app:app --host 127.0.0.1 --port 8000
```

Run the React app:

```bash
cd apps/workbench_web
npm install
npm run dev
```

Then open `http://127.0.0.1:8081`.

The frontend does not contain substitute signal data. Missing API, missing data sources, failed track overviews, and unsupported track views are shown as explicit messages.

The expected behavior for each clickable/editable control is listed in `docs/workbench_interactions.md`.
