from __future__ import annotations

import base64
import csv
import io
from pathlib import Path

from dash import Dash, Input, Output, State, callback, dcc, html, dash_table
import plotly.graph_objects as go

from countpp_analysis import (
    AccelerometerSample,
    Interval,
    clamp_intervals,
    detect_peak_events,
    detect_periodic_intervals,
    parse_csv_samples,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT / "data" / "examples" / "accelerometer_fixture.csv"

app = Dash(__name__)
app.title = "countpp data analyzer"


def _decode_upload(contents: str) -> list[dict[str, float]]:
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)
    text = decoded.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [{k: float(v) for k, v in row.items()} for row in reader]


def _load_rows(dataset: str, upload_contents: str | None) -> list[dict[str, float]]:
    if dataset == "upload" and upload_contents:
        return _decode_upload(upload_contents)

    samples = parse_csv_samples(EXAMPLE_PATH)
    return [{"t": s.t, "ax": s.ax, "ay": s.ay, "az": s.az, "mag": s.magnitude} for s in samples]


def _build_figure(rows: list[dict[str, float]], events: list[float], windows: list[Interval]) -> go.Figure:
    t = [r["t"] for r in rows]
    fig = go.Figure()
    for ch in ("ax", "ay", "az", "mag"):
        fig.add_trace(go.Scattergl(x=t, y=[r[ch] for r in rows], mode="lines", name=ch))

    for e in events:
        fig.add_vline(x=e, line_width=1, line_dash="dash", line_color="red")

    for iv in windows:
        fig.add_vrect(x0=iv.start, x1=iv.end, fillcolor="green", opacity=0.12, line_width=0)

    fig.update_layout(
        template="plotly_dark",
        margin={"l": 30, "r": 10, "t": 30, "b": 30},
        xaxis_title="time (s)",
        yaxis_title="signal",
        dragmode="zoom",
        legend={"orientation": "h"},
    )
    return fig


app.layout = html.Div(
    style={"padding": "12px", "fontFamily": "Inter, system-ui, sans-serif"},
    children=[
        html.H2("countpp data analysis app"),
        html.P("Accelerometer-focused MVP with extensible start/stop extraction windows."),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "8px"},
            children=[
                dcc.Dropdown(
                    id="dataset",
                    options=[
                        {"label": "Example accelerometer fixture", "value": "example"},
                        {"label": "Upload CSV", "value": "upload"},
                    ],
                    value="example",
                    clearable=False,
                ),
                dcc.Dropdown(
                    id="method",
                    options=[
                        {"label": "Peak detection", "value": "peak"},
                        {"label": "Periodic behavior", "value": "periodic"},
                    ],
                    value="peak",
                    clearable=False,
                ),
                html.Button("Run extraction", id="run", n_clicks=0),
            ],
        ),
        dcc.Upload(id="upload", children=html.Button("Upload CSV"), multiple=False),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "8px", "marginTop": "8px"},
            children=[
                dcc.Input(id="trigger", type="number", value=2.0, step=0.1, placeholder="trigger delta"),
                dcc.Input(id="reset", type="number", value=0.8, step=0.1, placeholder="reset delta"),
                dcc.Input(id="manual_start", type="number", value=0.0, step=0.01, placeholder="manual start"),
                dcc.Input(id="manual_end", type="number", value=0.2, step=0.01, placeholder="manual end"),
            ],
        ),
        html.Div([
            html.Button("Add manual window", id="add_window", n_clicks=0),
            html.Button("Clear windows", id="clear_windows", n_clicks=0, style={"marginLeft": "8px"}),
        ], style={"marginTop": "8px"}),
        dcc.Store(id="windows_store", data=[]),
        dcc.Graph(id="graph", style={"height": "65vh"}),
        html.H4("Detected windows/events"),
        dash_table.DataTable(id="table", page_size=10),
        html.Div(id="meta"),
    ],
)


@callback(
    Output("windows_store", "data"),
    Input("add_window", "n_clicks"),
    Input("clear_windows", "n_clicks"),
    State("manual_start", "value"),
    State("manual_end", "value"),
    State("windows_store", "data"),
    prevent_initial_call=True,
)
def update_windows(add_clicks: int, clear_clicks: int, start: float, end: float, current: list[dict]) -> list[dict]:
    from dash import ctx

    if ctx.triggered_id == "clear_windows":
        return []
    if start is None or end is None or end <= start:
        return current
    current = current or []
    current.append({"start": start, "end": end, "source": "manual-ui"})
    return current


@callback(
    Output("graph", "figure"),
    Output("table", "data"),
    Output("table", "columns"),
    Output("meta", "children"),
    Input("run", "n_clicks"),
    Input("dataset", "value"),
    Input("method", "value"),
    State("upload", "contents"),
    State("trigger", "value"),
    State("reset", "value"),
    State("windows_store", "data"),
)
def run_analysis(
    _: int,
    dataset: str,
    method: str,
    upload_contents: str | None,
    trigger: float,
    reset: float,
    manual_windows: list[dict],
):
    rows = _load_rows(dataset, upload_contents)
    samples = [AccelerometerSample(t=r["t"], ax=r["ax"], ay=r["ay"], az=r["az"]) for r in rows]
    events = detect_peak_events(samples, trigger_delta=trigger or 2.0, reset_delta=reset or 0.8)

    auto_windows: list[Interval] = []
    period_value = None
    if method == "periodic":
        periodic = detect_periodic_intervals(events, min_peaks=2)
        auto_windows = periodic.intervals
        period_value = periodic.estimated_period_s

    min_t, max_t = rows[0]["t"], rows[-1]["t"]
    merged = auto_windows + [Interval(**w) for w in (manual_windows or [])]
    windows = clamp_intervals(merged, min_t=min_t, max_t=max_t)

    fig = _build_figure(rows, events, windows)

    table_rows = [{"kind": "event", "t": e, "start": None, "end": None, "source": "peak"} for e in events]
    table_rows.extend({"kind": "window", "t": None, "start": w.start, "end": w.end, "source": w.source} for w in windows)
    columns = [{"name": k, "id": k} for k in ["kind", "t", "start", "end", "source"]]
    meta = f"samples={len(rows)} | events={len(events)} | windows={len(windows)}"
    if period_value:
        meta += f" | estimated period={period_value:.4f}s"
    return fig, table_rows, columns, meta


if __name__ == "__main__":
    app.run(debug=True)
