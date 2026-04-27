import React from "react";
import {
  NUMERIC_TRACK_KINDS,
  annotationEnd,
  annotationKind,
  annotationStart,
  channelColor,
  formatTime,
  percent,
  scale,
  timeTicks,
} from "./workbench_utils.js";
import { EmptyMessage } from "./workbench_layout.jsx";

export function Timeline({
  tracks,
  views,
  overviews,
  selectedTrackId,
  setSelectedTrackId,
  range,
  fullRange,
  cursorTime,
  selection,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onWheel,
  previewAnnotations,
  committedEvents,
}) {
  if (!tracks.length) {
    return <div className="timeline-empty"><EmptyMessage title="No tracks" message="Select a data source to create typed tracks." /></div>;
  }

  return (
    <main className="timeline" aria-label="Timeline workspace">
      <div className="timeline-frame">
        <TimeRuler
          range={range}
          fullRange={fullRange}
          cursorTime={cursorTime}
          selection={selection}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onWheel={onWheel}
        />
        <div className="track-stack">
          {tracks.map((track) => (
            <TrackRow
              key={track.id}
              track={track}
              view={views.find((item) => item.track_id === track.id)}
              overview={overviews[track.id]}
              range={range}
              cursorTime={cursorTime}
              selection={selection}
              selected={selectedTrackId === track.id}
              onSelect={() => setSelectedTrackId(track.id)}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onWheel={onWheel}
              previewAnnotations={previewAnnotations}
              committedEvents={committedEvents}
            />
          ))}
        </div>
      </div>
    </main>
  );
}

function TimeRuler({ range, fullRange, cursorTime, selection, onPointerDown, onPointerMove, onPointerUp, onWheel }) {
  const ticks = range ? timeTicks(range.start, range.end, 8) : [];
  return (
    <div className="time-ruler">
      <div className="track-header-label">
        <strong>Shared timeline</strong>
        {fullRange ? <small>{formatTime(fullRange.start)} – {formatTime(fullRange.end)}</small> : null}
      </div>
      <div className="ruler-lane" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onWheel={onWheel}>
        {ticks.map((tick) => (
          <span key={tick} style={{ left: `${percent(tick, range.start, range.end)}%` }}>{formatTime(tick)}</span>
        ))}
        <TimelineMarkers range={range} cursorTime={cursorTime} selection={selection} />
      </div>
    </div>
  );
}

function TrackRow({
  track,
  view,
  overview,
  range,
  cursorTime,
  selection,
  selected,
  onSelect,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onWheel,
  previewAnnotations,
  committedEvents,
}) {
  const height = Math.max(72, Math.min(190, view?.height || suggestedHeight(track.kind)));
  const visibleEvents = eventsForTrack(track, previewAnnotations, committedEvents);

  return (
    <div className={`track-row ${selected ? "selected" : ""}`} style={{ height }}>
      <button className="track-label" onClick={onSelect} type="button" title="Select track">
        <span className="track-kind">{track.kind}</span>
        <strong>{track.name}</strong>
        <small>{track.unit || track.channel || track.id}</small>
        <span className="track-flags">
          <b title="Visible">V</b><b title="Unlocked">U</b><b title="Focused">F</b>
        </span>
      </button>
      <div
        className="track-canvas"
        onPointerDown={(event) => { onSelect(); onPointerDown(event); }}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onWheel={onWheel}
      >
        {renderTrackBody(track, overview, range, view, visibleEvents)}
        <TimelineMarkers range={range} cursorTime={cursorTime} selection={selection} />
      </div>
    </div>
  );
}

function renderTrackBody(track, overview, range, view, annotations) {
  if (!range) return <TrackProblem message="No timeline range available." />;
  if (NUMERIC_TRACK_KINDS.has(track.kind)) {
    return overview?.points?.length ? <SignalSvg overview={overview} range={range} color={view?.color} /> : <TrackProblem message="No overview data returned for this signal track." />;
  }
  if (track.kind === "detector-preview") return <AnnotationLayer annotations={annotations} range={range} mode="preview" />;
  if (track.kind === "event-tier" || track.kind === "interval-tier") return <AnnotationLayer annotations={annotations} range={range} mode="committed" />;
  return <TrackProblem message={`Track kind '${track.kind}' is registered but has no viewer yet.`} />;
}

function suggestedHeight(kind) {
  if (kind === "multichannel-timeseries") return 132;
  if (kind === "event-tier" || kind === "interval-tier" || kind === "detector-preview") return 82;
  return 96;
}

function eventsForTrack(track, previewAnnotations, committedEvents) {
  if (track.kind === "detector-preview") return previewAnnotations || [];
  if (track.kind === "event-tier") return (committedEvents || []).filter((annotation) => annotationKind(annotation) !== "interval");
  if (track.kind === "interval-tier") return (committedEvents || []).filter((annotation) => annotationKind(annotation) === "interval");
  return [];
}

function SignalSvg({ overview, range, color }) {
  const width = 1200;
  const height = 120;
  const channels = overview.channels || [];
  const visiblePoints = (overview.points || []).filter((point) => point.time >= range.start && point.time <= range.end);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="signal-svg" aria-hidden="true">
      <GridLines width={width} height={height} />
      {channels.map((channel, index) => {
        const values = visiblePoints.map((point) => point[channel]).filter(Number.isFinite);
        const stats = values.length ? { min: Math.min(...values), max: Math.max(...values) } : overview.stats?.[channel];
        if (!stats) return null;
        const points = visiblePoints.map((point) => {
          const x = scale(point.time, range.start, range.end, 0, width);
          const y = scale(point[channel], stats.min, stats.max, height - 12, 12);
          return `${x},${Number.isFinite(y) ? y : height / 2}`;
        }).join(" ");
        return <polyline key={channel} points={points} fill="none" stroke={channelColor(channel, color, index)} strokeWidth={channels.length > 1 ? 1.2 : 1.8} vectorEffect="non-scaling-stroke" />;
      })}
    </svg>
  );
}

function TimelineMarkers({ range, cursorTime, selection }) {
  if (!range) return null;
  const cursor = Number.isFinite(cursorTime) ? percent(cursorTime, range.start, range.end) : null;
  const normalizedSelection = selection ? { start: Math.min(selection.start, selection.end), end: Math.max(selection.start, selection.end) } : null;
  return (
    <>
      {normalizedSelection ? (
        <div
          className="time-selection"
          style={{
            left: `${percent(normalizedSelection.start, range.start, range.end)}%`,
            width: `${Math.max(0.2, percent(normalizedSelection.end, range.start, range.end) - percent(normalizedSelection.start, range.start, range.end))}%`,
          }}
        />
      ) : null}
      {cursor !== null ? <div className="playhead" style={{ left: `${cursor}%` }} /> : null}
    </>
  );
}

function AnnotationLayer({ annotations, range, mode }) {
  if (!range) return <TrackProblem message="No timeline range available." />;
  if (!annotations.length) return <div className="annotation-empty">No {mode === "preview" ? "preview candidates" : "committed annotations"}.</div>;
  return (
    <div className="annotation-layer">
      {annotations.map((annotation) => {
        const kind = annotationKind(annotation);
        const start = percent(annotationStart(annotation), range.start, range.end);
        const end = percent(annotationEnd(annotation), range.start, range.end);
        const width = Math.max(0.7, end - start);
        return (
          <div
            key={annotation.id}
            className={`annotation-chip ${kind === "interval" ? "interval" : "point"} ${mode}`}
            style={{ left: `${start}%`, width: kind === "interval" ? `${width}%` : undefined }}
            title={`${annotation.label} ${formatTime(annotationStart(annotation))}`}
          >
            <span>{annotation.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function GridLines({ width, height }) {
  return (
    <>
      {[0.25, 0.5, 0.75].map((p) => <line key={`h-${p}`} x1="0" x2={width} y1={height * p} y2={height * p} stroke="rgba(148, 163, 184, .16)" />)}
      {[0.2, 0.4, 0.6, 0.8].map((p) => <line key={`v-${p}`} y1="0" y2={height} x1={width * p} x2={width * p} stroke="rgba(148, 163, 184, .16)" />)}
    </>
  );
}

function TrackProblem({ message }) {
  return <div className="track-problem">{message}</div>;
}
