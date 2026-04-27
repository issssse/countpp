import React from "react";
import { ACTIVITY_ITEMS, MENU_ITEMS, NUMERIC_TRACK_KINDS, rangesEqual, formatTime } from "./workbench_utils.js";

export function MenuBar({ dataSource, onMenuAction }) {
  return (
    <header className="menu-bar">
      <div className="brand" title="countpp event extraction workbench">
        <span>c++</span>
        <strong>countpp</strong>
      </div>
      <nav aria-label="Workbench menu">
        {MENU_ITEMS.map((item) => (
          <button key={item} onClick={() => onMenuAction(item)} type="button">
            {item}
          </button>
        ))}
      </nav>
      <div className="project-state">{dataSource || "No data source selected"}</div>
    </header>
  );
}

export function ActivityRail({ active, setActive }) {
  return (
    <aside className="activity-rail" aria-label="Workbench views">
      {ACTIVITY_ITEMS.map((item) => (
        <button
          key={item.id}
          className={active === item.id ? "active" : ""}
          onClick={() => setActive(item.id)}
          title={item.label}
          type="button"
        >
          {item.short}
        </button>
      ))}
    </aside>
  );
}

export function ProjectPanel({
  active,
  apiBase,
  apiDraft,
  setApiDraft,
  applyApiBase,
  dataSources,
  selectedDataSourceId,
  setSelectedDataSourceId,
  workbench,
  selectedTrackId,
  setSelectedTrackId,
  detectorPreview,
  committedEvents,
  status,
}) {
  return (
    <aside className="project-panel">
      <div className="panel-status-card">
        <span>Data API</span>
        <strong title={apiBase}>{apiBase}</strong>
      </div>
      <ProjectPanelContent
        active={active}
        apiDraft={apiDraft}
        setApiDraft={setApiDraft}
        applyApiBase={applyApiBase}
        dataSources={dataSources}
        selectedDataSourceId={selectedDataSourceId}
        setSelectedDataSourceId={setSelectedDataSourceId}
        workbench={workbench}
        selectedTrackId={selectedTrackId}
        setSelectedTrackId={setSelectedTrackId}
        detectorPreview={detectorPreview}
        committedEvents={committedEvents}
        status={status}
      />
    </aside>
  );
}

function ProjectPanelContent({
  active,
  apiDraft,
  setApiDraft,
  applyApiBase,
  dataSources,
  selectedDataSourceId,
  setSelectedDataSourceId,
  workbench,
  selectedTrackId,
  setSelectedTrackId,
  detectorPreview,
  committedEvents,
  status,
}) {
  if (active === "Tools") {
    return (
      <PanelSection title="Tool registry" subtitle="All registered tools">
        {workbench?.tool_definitions?.length ? (
          <div className="compact-list">
            {workbench.tool_definitions.map((tool) => (
              <div key={tool.id}>
                <strong>{tool.name}</strong>
                <span>{tool.category || "tool"} · accepts {(tool.accepts || []).join(", ") || "no track kinds"}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyMessage title="No tool registry" message="Load a data source to inspect registered tools." />
        )}
      </PanelSection>
    );
  }

  if (active === "Events") {
    return (
      <PanelSection title="Events" subtitle="Schemas and tiers">
        {workbench?.event_schemas?.length ? (
          <div className="compact-list">
            {workbench.event_schemas.map((schema) => (
              <div key={schema.id}>
                <strong>{schema.name}</strong>
                <span>{(schema.labels || []).join(", ") || "No labels"}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyMessage title="No event schemas" message="Load a data source to inspect event schemas and annotation tiers." />
        )}
      </PanelSection>
    );
  }

  if (active === "Runs") {
    return (
      <PanelSection title="Runs" subtitle="Previews and provenance">
        {detectorPreview ? (
          <div className="compact-list">
            <div>
              <strong>{detectorPreview.extractor_run?.extractor_name || "Extractor run"}</strong>
              <span>{detectorPreview.detector_preview?.annotations?.length || 0} candidates · version {detectorPreview.extractor_run?.version || "unknown"}</span>
            </div>
          </div>
        ) : (
          <EmptyMessage title="No runs yet" message="Preview a compatible tool to create a non-destructive detector run." />
        )}
      </PanelSection>
    );
  }

  if (active === "History") {
    return (
      <PanelSection title="History" subtitle="Session actions">
        <div className="compact-list">
          <div><strong>Status</strong><span>{status.message}</span></div>
          <div><strong>Committed annotations</strong><span>{committedEvents.length}</span></div>
          <div><strong>Undo stack</strong><span>Reserved for edit history and reversible commits.</span></div>
        </div>
      </PanelSection>
    );
  }

  if (active === "Settings") {
    return (
      <PanelSection title="Settings" subtitle="Connections">
        <form className="api-form" onSubmit={applyApiBase}>
          <label htmlFor="apiBase">Data API base URL</label>
          <div>
            <input id="apiBase" value={apiDraft} onChange={(event) => setApiDraft(event.target.value)} />
            <button type="submit">Connect</button>
          </div>
        </form>
        <EmptyMessage title="Runtime configuration" message="Label Studio URL, shortcuts, performance settings, and import defaults belong here as the app grows." />
      </PanelSection>
    );
  }

  return (
    <>
      <PanelSection title="Project bin" subtitle="Sessions and assets">
        {dataSources.length ? (
          <div className="source-list">
            {dataSources.map((source) => (
              <button key={source.id} className={selectedDataSourceId === source.id ? "selected" : ""} onClick={() => setSelectedDataSourceId(source.id)} type="button">
                <span>{source.name || source.id}</span>
                <small>{source.kind || source.format || "data source"}</small>
              </button>
            ))}
          </div>
        ) : (
          <EmptyMessage title="No data sources" message="Open Settings to confirm the Data API URL, then connect to a running backend." />
        )}
      </PanelSection>
      <PanelSection title="Track tree" subtitle="Typed tracks">
        <TrackList workbench={workbench} selectedTrackId={selectedTrackId} setSelectedTrackId={setSelectedTrackId} />
      </PanelSection>
    </>
  );
}

export function TrackList({ workbench, selectedTrackId, setSelectedTrackId }) {
  if (!workbench) return <EmptyMessage title="No session loaded" message="Select a data source to build typed tracks." />;
  return (
    <div className="track-list">
      {workbench.tracks.map((track) => (
        <button key={track.id} className={selectedTrackId === track.id ? "selected" : ""} onClick={() => setSelectedTrackId(track.id)} type="button">
          <span>{track.name}</span>
          <small>{track.kind}{track.unit ? ` · ${track.unit}` : ""}</small>
        </button>
      ))}
    </div>
  );
}

export function TransportBar({ range, fullRange, cursorTime, selection, status, zoomIn, zoomOut, fitTimeline, clearSelection }) {
  return (
    <div className="transport-bar">
      <div className="transport-actions primary-tools" aria-label="Timeline tools">
        <button type="button" title="Selection tool">Select</button>
        <button type="button" title="Region brush">Region</button>
        <button type="button" title="Point event tool">Point</button>
        <button type="button" title="Interval event tool">Interval</button>
      </div>
      <div className={`status-pill ${status.kind}`}>{status.message}</div>
      <div className="time-cluster">
        <div className="time-readout">{range ? `${formatTime(range.start)} – ${formatTime(range.end)}` : "No timeline"}</div>
        <div className="mini-readout">Cursor {formatTime(cursorTime)}{selection ? ` · Selection ${formatTime(selection.start)} – ${formatTime(selection.end)}` : ""}</div>
      </div>
      <div className="transport-actions" aria-label="Timeline navigation">
        <button onClick={zoomIn} disabled={!range} type="button">Zoom in</button>
        <button onClick={zoomOut} disabled={!range || rangesEqual(range, fullRange)} type="button">Zoom out</button>
        <button onClick={fitTimeline} disabled={!range || rangesEqual(range, fullRange)} type="button">Fit</button>
        <button onClick={clearSelection} disabled={!selection} type="button">Clear</button>
      </div>
    </div>
  );
}

export function PanelSection({ title, subtitle, children }) {
  return (
    <section className="panel-section">
      <div className="section-heading">
        <h2>{title}</h2>
        {subtitle ? <span>{subtitle}</span> : null}
      </div>
      {children}
    </section>
  );
}

export function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
    </div>
  );
}

export function EmptyMessage({ title, message }) {
  return (
    <div className="empty-message">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
