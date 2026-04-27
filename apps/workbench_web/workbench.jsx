import React, { useEffect, useMemo, useState } from "react";
import { MenuBar, ActivityRail, ProjectPanel, TransportBar } from "./workbench_layout.jsx";
import { Timeline } from "./timeline_workspace.jsx";
import { BottomPanel, ContextInspector } from "./inspector_panels.jsx";
import {
  BOTTOM_TABS,
  NUMERIC_TRACK_KINDS,
  apiGet,
  apiPost,
  candidateState,
  combinedTimeRange,
  defaultParameters,
  editedAnnotation,
  initialApiBase,
  midpoint,
  normalizeSelection,
  panRange,
  timeFromPointer,
  visibleDuration,
  zoomRange,
} from "./workbench_utils.js";

export default function Workbench() {
  const [apiBase, setApiBase] = useState(initialApiBase);
  const [apiDraft, setApiDraft] = useState(initialApiBase);
  const [dataSources, setDataSources] = useState([]);
  const [selectedDataSourceId, setSelectedDataSourceId] = useState("");
  const [workbench, setWorkbench] = useState(null);
  const [selectedTrackId, setSelectedTrackId] = useState("");
  const [trackOverviews, setTrackOverviews] = useState({});
  const [activeActivity, setActiveActivity] = useState("Explorer");
  const [selectedToolId, setSelectedToolId] = useState("");
  const [detectorPreview, setDetectorPreview] = useState(null);
  const [candidateEdits, setCandidateEdits] = useState({});
  const [committedEvents, setCommittedEvents] = useState([]);
  const [timelineView, setTimelineView] = useState(null);
  const [cursorTime, setCursorTime] = useState(null);
  const [timeSelection, setTimeSelection] = useState(null);
  const [draftSelection, setDraftSelection] = useState(null);
  const [toolParameters, setToolParameters] = useState({});
  const [activeBottomTab, setActiveBottomTab] = useState(BOTTOM_TABS[0]);
  const [status, setStatus] = useState({ kind: "idle", message: "Connect to the Data API and select a data source." });

  useEffect(() => {
    loadDataSources();
  }, [apiBase]);

  useEffect(() => {
    if (!selectedDataSourceId) {
      resetSessionState();
      return;
    }
    loadWorkbench(selectedDataSourceId);
  }, [selectedDataSourceId, apiBase]);

  const tracks = workbench?.tracks || [];
  const selectedTrack = tracks.find((track) => track.id === selectedTrackId) || null;
  const tools = workbench?.tool_definitions || [];
  const compatibleTools = useMemo(() => {
    if (!selectedTrack) return [];
    return tools.filter((tool) => (tool.accepts || []).includes(selectedTrack.kind));
  }, [tools, selectedTrack]);
  const selectedTool = compatibleTools.find((tool) => tool.id === selectedToolId) || compatibleTools[0] || null;
  const visibleTracks = useMemo(() => {
    if (!workbench) return [];
    const previewTrack = detectorPreview?.preview_track;
    return previewTrack ? [...tracks, previewTrack] : tracks;
  }, [workbench, tracks, detectorPreview]);
  const timelineRange = useMemo(() => combinedTimeRange(trackOverviews), [trackOverviews]);
  const visibleRange = timelineView || timelineRange;
  const visibleSelection = draftSelection || timeSelection;
  const previewAnnotations = detectorPreview?.detector_preview?.annotations || [];
  const acceptedCandidates = previewAnnotations.filter((annotation) => candidateState(annotation.id, candidateEdits).accepted);
  const selectedToolParameters = selectedTool ? (toolParameters[selectedTool.id] || defaultParameters(selectedTool)) : {};

  function resetSessionState() {
    setWorkbench(null);
    setSelectedTrackId("");
    setTrackOverviews({});
    setDetectorPreview(null);
    setCandidateEdits({});
    setCommittedEvents([]);
    setTimelineView(null);
    setCursorTime(null);
    setTimeSelection(null);
    setDraftSelection(null);
    setSelectedToolId("");
  }

  async function loadDataSources() {
    setStatus({ kind: "loading", message: "Loading data sources from the Data API..." });
    setDataSources([]);
    try {
      const datasets = await apiGet(apiBase, "/datasets");
      setDataSources(Array.isArray(datasets) ? datasets : []);
      setStatus(
        datasets?.length
          ? { kind: "ready", message: "Select a data source from Explorer." }
          : { kind: "empty", message: "The Data API is running, but it returned no data sources." }
      );
    } catch (error) {
      setStatus({ kind: "error", message: `Data API unavailable: ${error.message}` });
      setSelectedDataSourceId("");
    }
  }

  async function loadWorkbench(datasetId) {
    setStatus({ kind: "loading", message: `Loading workbench model for ${datasetId}...` });
    setWorkbench(null);
    setTrackOverviews({});
    setDetectorPreview(null);
    setCandidateEdits({});
    setCommittedEvents([]);
    setTimelineView(null);
    setCursorTime(null);
    setTimeSelection(null);
    setDraftSelection(null);
    setActiveBottomTab(BOTTOM_TABS[0]);
    try {
      const model = await apiGet(apiBase, `/datasets/${encodeURIComponent(datasetId)}/workbench`);
      setWorkbench(model);
      const preferredTrack = model.tracks.find((track) => track.channel === "magnitude") || model.tracks.find((track) => NUMERIC_TRACK_KINDS.has(track.kind)) || model.tracks[0];
      setSelectedTrackId(preferredTrack?.id || "");
      setSelectedToolId("");
      const overviewRange = await loadTrackOverviews(datasetId, model.tracks || []);
      setTimelineView(overviewRange);
      setCursorTime(overviewRange?.start ?? null);
      setStatus({ kind: "ready", message: "Workbench loaded. Select a track, choose a compatible tool, then preview non-destructively." });
    } catch (error) {
      setStatus({ kind: "error", message: `Could not load selected data source: ${error.message}` });
    }
  }

  async function loadTrackOverviews(datasetId, modelTracks) {
    const numericTracks = modelTracks.filter((track) => NUMERIC_TRACK_KINDS.has(track.kind));
    const entries = await Promise.all(
      numericTracks.map(async (track) => {
        try {
          const overview = await apiGet(apiBase, `/datasets/${encodeURIComponent(datasetId)}/tracks/${encodeURIComponent(track.id)}/overview?points=1600`);
          return [track.id, overview];
        } catch (error) {
          return [track.id, { error: error.message, points: [], channels: [], time_range: null }];
        }
      })
    );
    const loadedOverviews = Object.fromEntries(entries);
    setTrackOverviews(loadedOverviews);
    return combinedTimeRange(loadedOverviews);
  }

  async function runPreview() {
    if (!selectedDataSourceId || !selectedTrack || !selectedTool) return;
    if (!selectedTool.previewable) {
      setStatus({ kind: "error", message: `${selectedTool.name} is not a previewable tool yet.` });
      return;
    }
    setStatus({ kind: "loading", message: `Previewing ${selectedTool.name} on ${selectedTrack.name}...` });
    try {
      const result = await apiPost(apiBase, `/datasets/${encodeURIComponent(selectedDataSourceId)}/tools/${selectedTool.id}/preview`, {
        track_id: selectedTrack.id,
        parameters: selectedToolParameters,
        time_selection: timeSelection,
      });
      const annotations = result.detector_preview?.annotations || [];
      setDetectorPreview(result);
      setCandidateEdits(Object.fromEntries(annotations.map((annotation) => [annotation.id, { accepted: true, label: annotation.label, attributes: annotation.attributes || {} }])));
      setActiveBottomTab("Events");
      setStatus({ kind: "ready", message: `${annotations.length} preview candidates returned. Review edge cases before committing.` });
    } catch (error) {
      setStatus({ kind: "error", message: `Tool preview failed: ${error.message}` });
    }
  }

  async function commitAcceptedCandidates() {
    if (!selectedDataSourceId || !detectorPreview) return;
    const annotations = acceptedCandidates.map((annotation) => editedAnnotation(annotation, candidateEdits));
    if (!annotations.length) {
      setStatus({ kind: "error", message: "No accepted candidates to commit." });
      return;
    }
    setStatus({ kind: "loading", message: "Committing accepted candidates into the reviewed event tier..." });
    try {
      const result = await apiPost(apiBase, `/datasets/${encodeURIComponent(selectedDataSourceId)}/detector-previews/${detectorPreview.detector_preview.id}/commit`, { annotations });
      setCommittedEvents(result.annotations || []);
      setDetectorPreview(null);
      setCandidateEdits({});
      setActiveBottomTab("Events");
      setStatus({ kind: "ready", message: `${result.annotations?.length || 0} annotations committed to ${result.annotation_tier?.name || "the event tier"}.` });
    } catch (error) {
      setStatus({ kind: "error", message: `Commit failed: ${error.message}` });
    }
  }

  function applyApiBase(event) {
    event.preventDefault();
    const next = apiDraft.trim().replace(/\/$/, "");
    window.localStorage.setItem("countpp.apiBase", next);
    setApiBase(next);
  }

  function updateCandidate(id, patch) {
    setCandidateEdits((current) => ({ ...current, [id]: { ...candidateState(id, current), ...patch } }));
  }

  function selectTool(toolId) {
    const tool = tools.find((item) => item.id === toolId);
    setSelectedToolId(toolId);
    if (tool) {
      setToolParameters((current) => ({ ...current, [tool.id]: current[tool.id] || defaultParameters(tool) }));
      setStatus({ kind: "ready", message: `${tool.name} selected for ${selectedTrack?.name || "the selected track"}. Adjust options, then preview.` });
    }
  }

  function updateToolParameter(name, value) {
    if (!selectedTool) return;
    setToolParameters((current) => ({
      ...current,
      [selectedTool.id]: {
        ...(current[selectedTool.id] || defaultParameters(selectedTool)),
        [name]: value,
      },
    }));
  }

  function showActionStatus(message, kind = "ready") {
    setStatus({ kind, message });
  }

  function handleMenuAction(item) {
    if (item === "Export") {
      setActiveBottomTab("Export");
      if (committedEvents.length) exportCommittedEvents();
      else setStatus({ kind: "error", message: "No committed annotations are available to export. Use the Export panel to inspect the empty payload." });
      return;
    }
    if (item === "View") {
      fitTimeline();
      return;
    }
    if (item === "Tools") setActiveActivity("Tools");
    if (item === "Annotations") setActiveActivity("Events");
    if (item === "Window") setStatus({ kind: "ready", message: "Window menu selected. Layout presets, reset layout, and panel visibility belong here." });
    else setStatus({ kind: "ready", message: `${item} menu selected. Command palette/submenu wiring can be added without changing the layout.` });
  }

  function handleTimelinePointerDown(event) {
    if (!visibleRange) return;
    const nextTime = timeFromPointer(event, visibleRange);
    setCursorTime(nextTime);
    setDraftSelection({ start: nextTime, end: nextTime });
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }

  function handleTimelinePointerMove(event) {
    if (!visibleRange || !draftSelection || event.buttons !== 1) return;
    const nextTime = timeFromPointer(event, visibleRange);
    setCursorTime(nextTime);
    setDraftSelection({ ...draftSelection, end: nextTime });
  }

  function handleTimelinePointerUp(event) {
    if (!visibleRange || !draftSelection) return;
    const nextTime = timeFromPointer(event, visibleRange);
    const normalized = normalizeSelection(draftSelection.start, nextTime);
    setCursorTime(nextTime);
    setTimeSelection(normalized.end - normalized.start < visibleDuration(visibleRange) * 0.002 ? null : normalized);
    setDraftSelection(null);
  }

  function handleTimelineWheel(event) {
    if (!timelineRange || !visibleRange) return;
    event.preventDefault();
    const anchor = timeFromPointer(event, visibleRange);
    if (event.ctrlKey || event.metaKey) {
      const factor = event.deltaY > 0 ? 1.25 : 0.8;
      setTimelineView(zoomRange(visibleRange, timelineRange, anchor, factor));
    } else {
      const delta = (event.deltaX || event.deltaY) * visibleDuration(visibleRange) / 900;
      setTimelineView(panRange(visibleRange, timelineRange, delta));
    }
  }

  function zoomIn() {
    if (!timelineRange || !visibleRange) return;
    setTimelineView(zoomRange(visibleRange, timelineRange, cursorTime ?? midpoint(visibleRange), 0.72));
  }

  function zoomOut() {
    if (!timelineRange || !visibleRange) return;
    setTimelineView(zoomRange(visibleRange, timelineRange, cursorTime ?? midpoint(visibleRange), 1.35));
  }

  function fitTimeline() {
    setTimelineView(timelineRange);
    setTimeSelection(null);
    setDraftSelection(null);
    setStatus({ kind: "ready", message: "Timeline fit to the full data source range." });
  }

  function clearSelection() {
    setTimeSelection(null);
    setDraftSelection(null);
    setStatus({ kind: "ready", message: "Timeline selection cleared." });
  }

  function exportCommittedEvents() {
    if (!workbench) {
      setStatus({ kind: "error", message: "No workbench session is loaded to export." });
      return;
    }
    if (!committedEvents.length) {
      setStatus({ kind: "error", message: "No committed annotations are available to export." });
      return;
    }
    const payload = {
      format_version: "countpp.event_export.v1",
      session_id: workbench.session?.id,
      annotations: committedEvents,
      generated_at: new Date().toISOString(),
      metadata: { data_source_id: selectedDataSourceId },
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "countpp_event_export.json";
    link.click();
    URL.revokeObjectURL(url);
    setStatus({ kind: "ready", message: `${committedEvents.length} committed annotations exported as JSON.` });
  }

  return (
    <div className="workbench">
      <MenuBar dataSource={selectedDataSourceId} onMenuAction={handleMenuAction} />
      <div className="main-grid">
        <ActivityRail active={activeActivity} setActive={setActiveActivity} />
        <ProjectPanel
          active={activeActivity}
          apiBase={apiBase}
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
        <section className="center">
          <TransportBar
            range={visibleRange}
            fullRange={timelineRange}
            cursorTime={cursorTime}
            selection={visibleSelection}
            status={status}
            zoomIn={zoomIn}
            zoomOut={zoomOut}
            fitTimeline={fitTimeline}
            clearSelection={clearSelection}
          />
          <Timeline
            tracks={visibleTracks}
            views={workbench?.track_views || []}
            overviews={trackOverviews}
            selectedTrackId={selectedTrackId}
            setSelectedTrackId={setSelectedTrackId}
            range={visibleRange}
            fullRange={timelineRange}
            cursorTime={cursorTime}
            selection={visibleSelection}
            onPointerDown={handleTimelinePointerDown}
            onPointerMove={handleTimelinePointerMove}
            onPointerUp={handleTimelinePointerUp}
            onWheel={handleTimelineWheel}
            previewAnnotations={previewAnnotations}
            committedEvents={committedEvents}
          />
          <BottomPanel
            activeTab={activeBottomTab}
            setActiveTab={setActiveBottomTab}
            previewAnnotations={previewAnnotations}
            candidateEdits={candidateEdits}
            updateCandidate={updateCandidate}
            commitAcceptedCandidates={commitAcceptedCandidates}
            committedEvents={committedEvents}
            detectorPreview={detectorPreview}
            selectedTrack={selectedTrack}
            selectedTool={selectedTool}
            selectedToolParameters={selectedToolParameters}
            cursorTime={cursorTime}
            selection={visibleSelection}
            overviews={trackOverviews}
            status={status}
            labelStudio={workbench?.label_studio}
            exportCommittedEvents={exportCommittedEvents}
          />
        </section>
        <ContextInspector
          selectedTrack={selectedTrack}
          tools={compatibleTools}
          selectedTool={selectedTool}
          selectTool={selectTool}
          parameters={selectedToolParameters}
          updateParameter={updateToolParameter}
          runPreview={runPreview}
          commitAcceptedCandidates={commitAcceptedCandidates}
          eventSchemas={workbench?.event_schemas || []}
          extensionTrackKinds={workbench?.extension_track_kinds || ["audio", "video", "image-sequence", "touch-log", "sync-map"]}
          hasPreview={Boolean(previewAnnotations.length)}
          showActionStatus={showActionStatus}
        />
      </div>
    </div>
  );
}
