# countpp workbench web

This is the first typed-track workbench shell for reviewing data sources, selecting tracks, previewing compatible tools, committing detector candidates to annotation tiers, preparing Label Studio review tasks, and inspecting event exports.

Run the Data API first:

```bash
python -m uvicorn countpp_data_api.app:app --host 127.0.0.1 --port 8000
```

Then run the React workbench:

```bash
cd apps/workbench_web
npm install
npm run dev
```

Open `http://127.0.0.1:8081`.

If the Data API is unavailable or a selected data source cannot be loaded, the workbench shows an error state.
