# Workbench Interactions

This document is the interaction contract for `apps/workbench_web`. The app should behave like a serious multi-format signal workbench: one shared timeline, typed tracks, context-aware tools, non-destructive previews, rich event annotations, and reproducible exports.

The design borrows proven interaction patterns from:

- Kdenlive: project bin, timeline tracks, effect/tool scopes, customizable workspaces.
- VS Code: activity rail, side views, central editor/workbench area, bottom panel, command-oriented menus.
- Audacity: time ruler, track containers, selection timing, point/region labels.
- Sonic Visualiser: panes/layers, editable annotation layers, time instants, time values, regions, and analysis-derived layers.

## Core Principles

1. **Typed tracks, shared timebase**
   All data is represented on one timeline where possible. Tracks differ by kind, but share cursor, selection, zoom, pan, snapping, overlays, and export behavior.

2. **Tools are context-aware**
   The selected track controls which tools are available. Numeric tracks show numeric detectors and transforms. Audio tracks later show audio tools. Video tracks later show frame/motion tools. Event tiers show annotation tools.

3. **Preview is not commit**
   Detectors and transforms first create non-destructive previews. Users review edge cases, accept/reject candidates, edit labels/attributes, and only then commit results to an annotation tier or derived track.

4. **Events are rich objects**
   Events can be points or intervals. They can have labels, event types, values, units, value sources, attributes, provenance, confidence, notes, and reviewed state.

5. **Menus organize commands; panels organize state**
   A command may be accessible from a menu, context menu, shortcut, or palette, but the state should live in the appropriate panel: Explorer, Tools, Events, Runs, History, Settings, Timeline, Inspector, or Bottom Panel.

---

## Top-Level Layout

```text
Menu Bar
Activity Rail | Explorer Panel | Timeline Workspace | Context Inspector
Bottom Panel below the Timeline Workspace
Status shown in the Transport Bar and Console tab
```

### Layout Regions

| Region | Purpose |
| --- | --- |
| Menu Bar | Global commands grouped by task category. |
| Activity Rail | Switches the left panel between major workbench views. |
| Explorer Panel | Shows sessions, data sources, typed tracks, and annotation tiers. |
| Timeline Workspace | Main editing surface: ruler, tracks, cursor, selection, overlays. |
| Context Inspector | Shows track properties, compatible tools, active tool options, event schemas, and extension points. |
| Bottom Panel | Shows events, diagnostics, values, history, export preview, and console messages. |

---

## Menu Bar

The menu bar should not contain duplicate one-off actions. It should organize global commands that can later be exposed through a command palette and keyboard shortcuts.

| Menu | Contents | Notes |
| --- | --- | --- |
| `File` | New session, import data, open recent, save workspace, session settings, integrations, close session. | Import and project/session lifecycle belong here. |
| `Edit` | Undo, redo, cut/copy/paste annotations, delete selected event, clear selection, split/merge intervals, edit selected event attributes. | Edits apply to selected tracks, annotations, or regions. |
| `View` | Zoom in/out, fit timeline, go to selection, show/hide panels, track height, waveform style, value overlays, grid, snapping, layout visibility. | Replaces the previous `Navigate` menu. |
| `Tracks` | Add derived track, hide/show tracks, reorder tracks, group channels, resample, duplicate view, track properties. | Track management only. |
| `Annotations` | Add point event, add interval event, add exclusion region, edit event schema, validate annotations, bulk relabel, apply attributes. | Replaces the previous `Regions` menu. |
| `Tools` | Select, pan, zoom, region brush, point event, interval event, detector tools, sync tools, transform tools. | Replaces the previous `Detect` menu. Detectors are tools. |
| `Analyze` | Summary statistics, frequency analysis, periodicity report, matrix profile report, event distribution, cross-track comparison. | Reports and diagnostics, not direct annotation edits. |
| `Sync` | Add sync markers, align tracks, cross-correlation sync, inspect clock offset, apply sync map, manage device timebases. | For multi-device and multi-format alignment. |
| `Export` | Export events, annotations, selected region, detector run, Label Studio task, CSV/JSON/Parquet outputs. | Primary export location. Export preview lives in the bottom panel. |
| `Window` | Layout presets, reset layout, show/hide left panel, right inspector, bottom panel, fullscreen timeline. | Workbench layout only. |
| `Help` | Keyboard shortcuts, command palette help, documentation, about, debug info. | Add this as the app grows. |

### Removed Menus

| Removed menu | Replacement |
| --- | --- |
| `Navigate` | `View` menu plus timeline toolbar shortcuts. |
| `Regions` | `Annotations` menu and annotation/event-tier tools. |
| `Detect` | `Tools` menu and context-aware detector tools. |

---

## Activity Rail

The Activity Rail switches the left side panel. It should not expose tiny one-feature panels.

| Activity | Contains | Behavior |
| --- | --- | --- |
| `Explorer` | Project bin, sessions, data sources, raw streams, derived streams, track tree, annotation tiers. | Default view. Load data sources and select tracks. |
| `Tools` | Full tool registry grouped by category and compatible track kind. | Read-only registry at first; later supports pinning/favorites. |
| `Events` | Event schemas, labels, required attributes, annotation tiers, validation rules. | Event schema editing and tier management belong here. |
| `Runs` | Current preview run, past extractor runs, parameters, input tracks, output candidates, diagnostics. | Shows provenance and reproducibility. |
| `History` | Undo/redo stack, imports, previews, commits, exports, parameter changes. | Eventually powers rollback. |
| `Settings` | Data API URL, Label Studio URL, shortcuts, theme, import defaults, rendering/performance settings. | API setup belongs here, not permanently in the project bin. |

---

## Data API and Project Bin

### Connection Status

The current Data API URL should appear as a compact status card in the left panel and/or status bar.

| Control | Behavior |
| --- | --- |
| API status card | Shows current API base URL. No editing inline unless Settings is active. |
| Settings > Data API URL | Editable API base URL. |
| Settings > Connect | Stores the API URL, fetches `/datasets`, and reports success or failure. |

### Project Bin / Explorer

| Control | Behavior |
| --- | --- |
| Data source button | Loads `/datasets/{id}/workbench`, builds typed tracks, fetches numeric track overviews, resets previews and commits. |
| Data source context menu | Future: inspect schema, rename, remove from workspace, import as specific track type. |
| Track tree item | Selects the track and updates the Context Inspector. |
| Track tree context menu | Future: hide/show, rename, duplicate view, derive signal, resample, export track, delete view. |

---

## Timeline and Transport

Transport and timeline controls should focus only on time navigation, cursor, selection, and tool mode. Export and Label Studio are not transport controls.

### Transport Toolbar

| Control | Behavior |
| --- | --- |
| `Select` | Select tracks, events, and regions. |
| `Region` | Paint or edit include/exclude regions. Future: supports brush modes. |
| `Point` | Add a point event at the cursor or click location. |
| `Interval` | Add an interval event from the current selection. |
| `Zoom in` | Zoom around playhead/cursor or visible midpoint. |
| `Zoom out` | Zoom out toward full data range. |
| `Fit` | Reset visible range to full data source range and clear current selection. |
| `Clear` | Clear current time selection without moving cursor. |
| Status text | Shows current status, API errors, preview result summaries, and selected command feedback. |
| Time readout | Shows visible range, cursor, and selection range. |

### Removed From Transport

| Removed control | New location |
| --- | --- |
| `Label Studio` | Bottom Panel > Export or File > Integrations. |
| `Export committed JSON` | Menu Bar > Export and Bottom Panel > Export. |
| Per-track `Select` button | Track header click selects the track. |

### Timeline Interactions

| Interaction | Behavior |
| --- | --- |
| Ruler click | Move cursor/playhead. |
| Ruler drag | Create or replace shared time selection. |
| Shift + drag | Future: extend selection. |
| Track canvas click | Select track and move cursor. |
| Track canvas drag | Select track and create shared time selection. |
| Mouse wheel | Pan visible time window. |
| Ctrl/Cmd + wheel | Zoom around pointer time. |
| Track header click | Select track without changing cursor. |
| Event double click | Future: open event editor. |
| Event edge drag | Future: resize interval event. |
| Event body drag | Future: move unlocked event. |
| Threshold handle drag | Future: update detector threshold parameter interactively. |
| Right click track/event | Future: open context menu. |

### Track Header

Each track header should expose track state compactly.

| Element | Behavior |
| --- | --- |
| Track kind pill | Shows `numeric-timeseries`, `multichannel-timeseries`, `event-tier`, etc. |
| Track name | Main selectable label. |
| Unit/channel/source | Secondary metadata. |
| V/U/F flags | Placeholder for visible, unlocked, focused states. |
| Header click | Selects track. |

---

## Typed Track Kinds

Initial track kinds:

| Track kind | View | Compatible tools |
| --- | --- | --- |
| `numeric-timeseries` | Signal line plot. | Threshold, peak, smoothing, derivative, change point, matrix profile. |
| `multichannel-timeseries` | Multiple signal line plots in one track. | Same numeric tools, with channel selector. |
| `derived-signal` | Signal line plot derived from another source. | Numeric tools and transform provenance. |
| `event-tier` | Point event overlay. | Add point event, relabel, validate, bulk edit. |
| `interval-tier` | Interval overlay. | Add interval, split/merge, trim, validate. |
| `detector-preview` | Non-destructive candidate overlay. | Accept/reject, edit label, commit accepted. |

Future track kinds:

| Track kind | Future view | Future tools |
| --- | --- | --- |
| `audio` | Waveform and spectrogram. | Onset, silence, amplitude threshold, cross-correlation sync. |
| `video` | Frame strip and monitor. | Frame marker, motion-derived signal, scene boundary. |
| `image-sequence` | Frame/image strip. | Frame markers, regions, metadata extraction. |
| `touch-log` | Gesture/touch events over time. | Tap, drag, long-press, gesture segmentation. |
| `sync-map` | Alignment/offset track. | Offset inspection, clock drift correction, marker alignment. |

---

## Context Inspector

The Context Inspector is selection-aware. It should change based on selected track, selected tool, or selected event.

### No Track Selected

Show:

- Session summary.
- Import guidance.
- Available data sources.
- Recent tools.
- Empty-state instructions.

### Numeric or Multichannel Track Selected

Show:

- Track name, kind, unit, channels, sample rate if available, visible range, warnings.
- Compatible tools: threshold, peak, periodicity, smoothing, derivative/jerk, change point, matrix profile.
- Active tool options: target channel, absolute threshold, relative threshold, prominence, minimum distance, smoothing window, detection scope, show rejected candidates.
- Preview/apply controls.

### Audio Track Selected Later

Show:

- Sample rate, channels, duration, waveform/spectrogram mode.
- Compatible tools: onset detector, silence detector, amplitude threshold, spectrogram, cross-correlation sync.

### Video Track Selected Later

Show:

- Frame rate, duration, resolution, current frame.
- Compatible tools: frame marker, scene boundary, motion-derived signal, sync marker.

### Annotation/Event Tier Selected

Show:

- Event schema, allowed labels, point/interval support, required attributes, validation rules.
- Compatible tools: add point event, add interval event, bulk relabel, validate tier, merge/split intervals.

### Active Tool Options

Every active tool should expose:

| Field | Description |
| --- | --- |
| Tool name | Human-readable tool name. |
| Description | Short explanation of what the tool does. |
| Input tracks | Selected track(s) and required track kinds. |
| Output type | Preview, annotation tier, derived signal, report, or sync map. |
| Scope | Full track, selected range, included regions, or custom regions. |
| Preset | Default/custom parameter preset. |
| Parameters | Editable schema-driven controls. |
| Preview | Runs non-destructive backend preview when supported. |
| Commit/apply | Commits accepted preview items or creates a derived output. |
| Diagnostics | Links to diagnostics in the bottom panel. |

---

## Event Schema and Event Objects

Events are not just labels. They should carry values and attributes.

### Event Object

```ts
interface EventAnnotation {
  id: string;
  kind: "point" | "interval";
  start_time: number;
  end_time?: number;
  label: string;
  event_type_id?: string;
  value?: number | string | boolean;
  value_unit?: string;
  value_source?: "sample-at-time" | "interval-statistic" | "other-signal-at-time" | "detector-score" | "manual";
  attributes: Record<string, string | number | boolean>;
  source: "human" | "extractor" | "imported" | "synced-stream";
  extractor_run_id?: string;
  confidence?: number;
  reviewed: boolean;
  notes?: string;
}
```

### Event Schema Editor Future Behavior

| Control | Behavior |
| --- | --- |
| Schema card | Opens schema editor. |
| Label list | Defines controlled labels such as Impact, Start, Stop, Invalid Region, Sync Marker. |
| Attribute fields | Defines required/optional attributes and value types. |
| Validation rules | Prevents committing/exporting invalid events when required fields are missing. |
| Default value source | Configures whether event values are sampled, computed, synced, detector-based, or manual. |

---

## Bottom Panel

The bottom panel shows detailed state and review information. Tabs should be named by function, not implementation details.

| Tab | Contents |
| --- | --- |
| `Events` | Detector candidates when a preview exists; committed annotations otherwise. Editable labels, kind, start/end, values, attributes, source, reviewed state. |
| `Diagnostics` | Extractor run ID, name, version, candidate count, diagnostics JSON, warnings, backend messages. |
| `Values` | Selected track, cursor time, selection, nearest sampled values at cursor, future interval statistics. |
| `History` | Selected tool, current parameters, last preview timestamp, future undo/redo stack. |
| `Export` | Export preview JSON, export button, Label Studio link/import/export integration. |
| `Console` | Current status, API interaction notes, errors, debug messages. |

### Event Table Columns

Default columns:

- Use / reviewed.
- Label.
- Kind: point or interval.
- Start.
- End.
- Duration.
- Value.
- Value source.
- Attributes.
- Source.
- Confidence.
- Provenance.

Future column chooser should allow hiding rarely used fields.

---

## Detector Preview Workflow

1. Select a compatible track.
2. Select a detector or transform tool from the Context Inspector.
3. Edit visible parameters.
4. Optionally select a time range or include/exclude regions.
5. Click `Preview`.
6. Preview results appear as a `detector-preview` track and in the Events table.
7. Review edge cases.
8. Accept/reject candidates.
9. Edit candidate labels and attributes.
10. Click `Commit accepted`.
11. Accepted candidates become committed annotations in an event tier.
12. Export from the Export menu or bottom Export tab.

---

## Error and Empty States

| Situation | Expected behavior |
| --- | --- |
| Data API unavailable | Show status error; no project data. |
| Data API returns no data sources | Show Explorer empty state. |
| Selected data source cannot load | Show status error; no synthetic tracks. |
| Track overview cannot be drawn | Show track-level problem message. |
| Selected track has no compatible tools | Show explanation in Context Inspector. |
| Tool requires selection but none exists | Disable preview and explain requirement. |
| Preview fails | Show backend error in status. |
| Preview returns zero candidates | Show successful empty result with parameter hints. |
| Commit without accepted candidates | Show error in status. |
| Event schema requires missing attributes | Future: prevent commit or mark invalid. |
| Export without committed annotations | Show error and empty export preview. |
| Track has irregular/missing timestamps | Future: show warning and suggest repair/resampling. |
| Backend tool version changes | Future: mark preview stale and require re-preview. |

---

## Implementation Notes

- Keep the current app split into small components:
  - `workbench.jsx`: state/controller and backend calls.
  - `workbench_layout.jsx`: menu bar, activity rail, explorer/settings panel, transport bar, shared UI primitives.
  - `timeline_workspace.jsx`: ruler, typed track rows, signal rendering, annotation overlays.
  - `inspector_panels.jsx`: context inspector, tool parameters, bottom panel tabs, event tables.
  - `workbench_utils.js`: constants, API helpers, time/range/value helpers.
- The transport bar intentionally excludes export and Label Studio. Those are integration/export tasks.
- Track selection is done through the track header, not through a separate per-track `Select` button.
- The timeline frame uses stable grid columns and fixed row heights to avoid overlapping tracks.
- The backend tool registry remains authoritative for available preview/apply tools; the format-aware palette communicates the intended future interaction model.
