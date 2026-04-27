import React from "react";
import { EmptyMessage, InfoRow, PanelSection } from "./workbench_layout.jsx";
import {
  BOTTOM_TABS,
  TOOL_FAMILIES,
  annotationEnd,
  annotationKind,
  annotationStart,
  candidateState,
  formatTime,
  formatValue,
  serializeAttributes,
  valuesAtCursor,
} from "./workbench_utils.js";

export function ContextInspector({
  selectedTrack,
  tools,
  selectedTool,
  selectTool,
  parameters,
  updateParameter,
  runPreview,
  commitAcceptedCandidates,
  eventSchemas,
  extensionTrackKinds,
  hasPreview,
  showActionStatus,
}) {
  return (
    <aside className="context-inspector">
      <PanelSection title="Context inspector" subtitle="Selection-aware">
        {selectedTrack ? (
          <div className="selected-context">
            <span>Selected track</span>
            <strong>{selectedTrack.name}</strong>
            <small>{selectedTrack.kind}{selectedTrack.unit ? ` · ${selectedTrack.unit}` : ""}</small>
          </div>
        ) : (
          <EmptyMessage title="No selected track" message="Select a typed track to see compatible tools." />
        )}
      </PanelSection>

      <PanelSection title="Format-aware tools" subtitle="Palette">
        <ToolFamilies selectedKind={selectedTrack?.kind} showActionStatus={showActionStatus} />
      </PanelSection>

      <PanelSection title="Compatible backend tools" subtitle="Registry">
        {tools.length ? (
          <div className="tool-list">
            {tools.map((tool) => (
              <button key={tool.id} className={selectedTool?.id === tool.id ? "selected" : ""} onClick={() => selectTool(tool.id)} type="button">
                <span>{tool.name}</span>
                <small>{tool.category || "tool"} → {(tool.produces || []).join(", ") || "output"}</small>
              </button>
            ))}
          </div>
        ) : (
          <EmptyMessage title="No compatible backend tools" message="This track kind has no registered preview/apply tools yet." />
        )}
      </PanelSection>

      <PanelSection title="Active tool options" subtitle={selectedTool?.name || "No tool"}>
        {selectedTool ? <ToolParameters tool={selectedTool} parameters={parameters} updateParameter={updateParameter} /> : <EmptyMessage title="No tool selected" message="Choose a compatible tool to inspect its parameters." />}
        <div className="button-row">
          <button onClick={runPreview} disabled={!selectedTool || !selectedTool.previewable} type="button">Preview</button>
          <button onClick={commitAcceptedCandidates} disabled={!hasPreview} type="button">Commit accepted</button>
        </div>
        <div className="inspector-note">Preview is non-destructive. Commit writes accepted candidates to an annotation tier.</div>
      </PanelSection>

      <PanelSection title="Event schemas" subtitle="Labels and attributes">
        {eventSchemas.length ? eventSchemas.map((schema) => (
          <button className="schema-card" key={schema.id} onClick={() => showActionStatus(`${schema.name} schema selected. Schema editing and persistence should open from here next.`)} type="button">
            <strong>{schema.name}</strong>
            <div>{(schema.labels || []).join(", ") || "No labels"}</div>
            {schema.attributes?.length ? <small>Attributes: {schema.attributes.join(", ")}</small> : null}
          </button>
        )) : <EmptyMessage title="No schemas" message="Event schema creation belongs here once persistence is wired." />}
      </PanelSection>

      <PanelSection title="Extension points" subtitle="Future formats">
        <div className="tag-list">
          {(extensionTrackKinds || []).map((kind) => (
            <button key={kind} onClick={() => showActionStatus(`${kind} tracks are registered as extension points, but no importer/viewer is implemented yet.`)} type="button">{kind}</button>
          ))}
        </div>
      </PanelSection>
    </aside>
  );
}

function ToolFamilies({ selectedKind, showActionStatus }) {
  return (
    <div className="tool-family-list">
      {TOOL_FAMILIES.map((group) => {
        const active = group.kind === "common" || group.kind === selectedKind || (selectedKind === "multichannel-timeseries" && group.kind === "numeric-timeseries");
        return (
          <div key={group.title} className={active ? "tool-family active" : "tool-family"}>
            <strong>{group.title}</strong>
            <div className="tag-list">
              {group.tools.map((tool) => (
                <button key={tool} type="button" onClick={() => showActionStatus(`${tool} is a ${group.title.toLowerCase()} command. Backend wiring can attach it to the registry.`)}>
                  {tool}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ToolParameters({ tool, parameters, updateParameter }) {
  const entries = Object.entries(tool.parameters_schema || {});
  if (!entries.length) return <EmptyMessage title="No parameters" message="This tool has no visible parameters yet." />;
  return (
    <div className="parameter-list">
      {entries.map(([name, schema]) => (
        <div key={name}>
          <label>{schema.title || name}</label>
          <ParameterInput name={name} schema={schema} value={parameters[name]} updateParameter={updateParameter} />
          {schema.description ? <small>{schema.description}</small> : null}
        </div>
      ))}
    </div>
  );
}

function ParameterInput({ name, schema, value, updateParameter }) {
  if (Array.isArray(schema.enum)) {
    return (
      <select aria-label={name} value={value ?? schema.default ?? ""} onChange={(event) => updateParameter(name, event.target.value)}>
        {schema.enum.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    );
  }
  if (schema.type === "boolean") {
    return <input aria-label={name} type="checkbox" checked={Boolean(value ?? schema.default)} onChange={(event) => updateParameter(name, event.target.checked)} />;
  }
  if (schema.type === "number" || schema.type === "integer") {
    return (
      <input
        type="number"
        aria-label={name}
        step={schema.type === "integer" ? 1 : 0.01}
        value={value ?? schema.default ?? 0}
        onChange={(event) => updateParameter(name, schema.type === "integer" ? Number.parseInt(event.target.value || "0", 10) : Number.parseFloat(event.target.value || "0"))}
      />
    );
  }
  return <input aria-label={name} value={value ?? schema.default ?? ""} onChange={(event) => updateParameter(name, event.target.value)} />;
}

export function BottomPanel({
  activeTab,
  setActiveTab,
  previewAnnotations,
  candidateEdits,
  updateCandidate,
  commitAcceptedCandidates,
  committedEvents,
  detectorPreview,
  selectedTrack,
  selectedTool,
  selectedToolParameters,
  cursorTime,
  selection,
  overviews,
  status,
  labelStudio,
  exportCommittedEvents,
}) {
  return (
    <section className="bottom-panel">
      <div className="bottom-tabs">
        {BOTTOM_TABS.map((tab) => (
          <button key={tab} className={activeTab === tab ? "active" : ""} onClick={() => setActiveTab(tab)} type="button">{tab}</button>
        ))}
      </div>
      <div className="bottom-content">
        <BottomTabContent
          activeTab={activeTab}
          previewAnnotations={previewAnnotations}
          candidateEdits={candidateEdits}
          updateCandidate={updateCandidate}
          committedEvents={committedEvents}
          detectorPreview={detectorPreview}
          selectedTrack={selectedTrack}
          selectedTool={selectedTool}
          selectedToolParameters={selectedToolParameters}
          cursorTime={cursorTime}
          selection={selection}
          overviews={overviews}
          status={status}
          labelStudio={labelStudio}
          exportCommittedEvents={exportCommittedEvents}
        />
        <div className="diagnostics">
          <strong>Run summary</strong>
          {detectorPreview ? (
            <>
              <span>{detectorPreview.extractor_run?.extractor_name || "Extractor"}</span>
              <span>{previewAnnotations.length} candidates</span>
              <span>{previewAnnotations.filter((annotation) => candidateState(annotation.id, candidateEdits).accepted).length} accepted</span>
              <button onClick={commitAcceptedCandidates} type="button">Commit accepted candidates</button>
            </>
          ) : (
            <p>No detector preview has been created for the selected track.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function BottomTabContent({ activeTab, previewAnnotations, candidateEdits, updateCandidate, committedEvents, detectorPreview, selectedTrack, selectedTool, selectedToolParameters, cursorTime, selection, overviews, status, labelStudio, exportCommittedEvents }) {
  if (activeTab === "Events") {
    return (
      <div className="table-wrap">
        {previewAnnotations.length ? (
          <>
            <h3>Preview candidates</h3>
            <CandidateTable annotations={previewAnnotations} edits={candidateEdits} updateCandidate={updateCandidate} />
          </>
        ) : committedEvents.length ? (
          <>
            <h3>Committed events</h3>
            <CommittedTable annotations={committedEvents} />
          </>
        ) : (
          <EmptyMessage title="No events" message="Preview a compatible detector, accept/reject candidates, then commit them to an event tier." />
        )}
      </div>
    );
  }

  if (activeTab === "Diagnostics") {
    return (
      <div className="tab-panel">
        {detectorPreview ? (
          <>
            <InfoRow label="Run" value={detectorPreview.extractor_run?.id} />
            <InfoRow label="Extractor" value={detectorPreview.extractor_run?.extractor_name} />
            <InfoRow label="Version" value={detectorPreview.extractor_run?.version} />
            <InfoRow label="Candidates" value={String(previewAnnotations.length)} />
            <pre>{JSON.stringify(detectorPreview.extractor_run?.diagnostics || {}, null, 2)}</pre>
          </>
        ) : (
          <EmptyMessage title="No diagnostics" message="Run a previewable detector to inspect diagnostics." />
        )}
      </div>
    );
  }

  if (activeTab === "Values") {
    const values = selectedTrack && cursorTime !== null ? valuesAtCursor(selectedTrack, overviews[selectedTrack.id], cursorTime) : [];
    return (
      <div className="tab-panel">
        <InfoRow label="Selected track" value={selectedTrack ? `${selectedTrack.name} (${selectedTrack.kind})` : "None"} />
        <InfoRow label="Cursor" value={formatTime(cursorTime)} />
        <InfoRow label="Selection" value={selection ? `${formatTime(selection.start)} – ${formatTime(selection.end)}` : "None"} />
        {values.length ? values.map(([key, value]) => <InfoRow key={key} label={key} value={formatValue(value, selectedTrack?.unit)} />) : <EmptyMessage title="No sampled value" message="Select a numeric track and click on the timeline." />}
      </div>
    );
  }

  if (activeTab === "History") {
    return (
      <div className="tab-panel">
        <InfoRow label="Selected tool" value={selectedTool?.name || "None"} />
        <InfoRow label="Current parameters" value={JSON.stringify(selectedToolParameters)} />
        <InfoRow label="Last preview" value={detectorPreview?.extractor_run?.created_at || "None"} />
        <InfoRow label="Undo / redo" value="Reserved for non-destructive edit history." />
      </div>
    );
  }

  if (activeTab === "Export") {
    return (
      <div className="tab-panel export-panel">
        <div className="export-actions">
          <button onClick={exportCommittedEvents} disabled={!committedEvents.length} type="button">Export committed JSON</button>
          {labelStudio?.server_url ? <a href={labelStudio.server_url} target="_blank" rel="noreferrer">Open Label Studio</a> : <button disabled type="button">Label Studio unavailable</button>}
        </div>
        <pre>{JSON.stringify({ format_version: "countpp.event_export.v1", annotations: committedEvents }, null, 2)}</pre>
      </div>
    );
  }

  return (
    <div className="tab-panel">
      <InfoRow label="Status" value={`${status.kind}: ${status.message}`} />
      <InfoRow label="API interactions" value="Shown in the browser network panel and Data API terminal." />
    </div>
  );
}

function CandidateTable({ annotations, edits, updateCandidate }) {
  return (
    <table className="candidate-table">
      <thead>
        <tr>
          <th>Use</th><th>Label</th><th>Kind</th><th>Start</th><th>End</th><th>Duration</th><th>Value</th><th>Value source</th><th>Attributes</th><th>Source</th><th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        {annotations.map((annotation) => {
          const state = candidateState(annotation.id, edits);
          const kind = annotationKind(annotation);
          const start = annotationStart(annotation);
          const end = annotationEnd(annotation);
          return (
            <tr key={annotation.id}>
              <td><input type="checkbox" checked={state.accepted} onChange={(event) => updateCandidate(annotation.id, { accepted: event.target.checked })} /></td>
              <td><input value={state.label || annotation.label || ""} onChange={(event) => updateCandidate(annotation.id, { label: event.target.value })} /></td>
              <td>{kind}</td>
              <td>{formatTime(start)}</td>
              <td>{kind === "interval" ? formatTime(end) : "—"}</td>
              <td>{kind === "interval" ? formatTime(end - start) : "—"}</td>
              <td>{formatValue(annotation.value, annotation.value_unit)}</td>
              <td>{annotation.value_source || "—"}</td>
              <td>{serializeAttributes(state.attributes || annotation.attributes)}</td>
              <td>{annotation.source || "preview"}</td>
              <td>{annotation.confidence ?? "—"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function CommittedTable({ annotations }) {
  return (
    <table className="committed-table">
      <thead>
        <tr><th>Label</th><th>Kind</th><th>Start</th><th>End</th><th>Duration</th><th>Value</th><th>Value source</th><th>Attributes</th><th>Reviewed</th><th>Provenance</th></tr>
      </thead>
      <tbody>
        {annotations.map((annotation) => {
          const kind = annotationKind(annotation);
          const start = annotationStart(annotation);
          const end = annotationEnd(annotation);
          return (
            <tr key={annotation.id}>
              <td>{annotation.label}</td>
              <td>{kind}</td>
              <td>{formatTime(start)}</td>
              <td>{kind === "interval" ? formatTime(end) : "—"}</td>
              <td>{kind === "interval" ? formatTime(end - start) : "—"}</td>
              <td>{formatValue(annotation.value, annotation.value_unit)}</td>
              <td>{annotation.value_source || "—"}</td>
              <td>{serializeAttributes(annotation.attributes)}</td>
              <td>{annotation.reviewed ? "yes" : "no"}</td>
              <td>{annotation.extractor_run_id || annotation.source || "—"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
