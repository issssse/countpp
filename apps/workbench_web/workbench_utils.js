export const NUMERIC_TRACK_KINDS = new Set(["numeric-timeseries", "multichannel-timeseries", "derived-signal"]);
export const ANNOTATION_TRACK_KINDS = new Set(["event-tier", "interval-tier", "detector-preview"]);

export const MENU_ITEMS = [
  "File",
  "Edit",
  "View",
  "Tracks",
  "Annotations",
  "Tools",
  "Analyze",
  "Sync",
  "Export",
  "Window",
  "Help",
];

export const ACTIVITY_ITEMS = [
  { id: "Explorer", label: "Explorer", short: "Ex" },
  { id: "Tools", label: "Tools", short: "To" },
  { id: "Events", label: "Events", short: "Ev" },
  { id: "Runs", label: "Runs", short: "Ru" },
  { id: "History", label: "History", short: "Hi" },
  { id: "Settings", label: "Settings", short: "Se" },
];

export const BOTTOM_TABS = ["Events", "Diagnostics", "Values", "History", "Export", "Console"];

export const TOOL_FAMILIES = [
  {
    title: "Common timeline tools",
    kind: "common",
    tools: ["Select", "Pan", "Zoom", "Point event", "Interval event", "Region brush", "Snap to sample"],
  },
  {
    title: "Numeric / sensor tools",
    kind: "numeric-timeseries",
    tools: ["Threshold", "Peak / prominence", "Periodicity", "Derivative / jerk", "Smoothing", "Change point", "Matrix profile"],
  },
  {
    title: "Audio tools",
    kind: "audio",
    tools: ["Waveform", "Spectrogram", "Onset", "Silence", "Cross-correlation sync"],
  },
  {
    title: "Video tools",
    kind: "video",
    tools: ["Frame marker", "Motion-derived signal", "Scene boundary", "Sync marker"],
  },
  {
    title: "Annotation tools",
    kind: "event-tier",
    tools: ["Controlled labels", "Bulk relabel", "Validate required attributes", "Split / merge intervals"],
  },
];

export function initialApiBase() {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  return window.localStorage.getItem("countpp.apiBase") || "http://127.0.0.1:8000";
}

export async function apiGet(apiBase, path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

export async function apiPost(apiBase, path, payload) {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP error detail.
    }
    throw new Error(detail);
  }
  return response.json();
}

export function defaultParameters(tool) {
  return Object.fromEntries(
    Object.entries(tool?.parameters_schema || {})
      .map(([name, schema]) => [name, schema.default])
      .filter(([, value]) => value !== undefined)
  );
}

export function timeFromPointer(event, range) {
  const rect = event.currentTarget.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (event.clientX - rect.left) / Math.max(1, rect.width)));
  return range.start + ratio * visibleDuration(range);
}

export function visibleDuration(range) {
  return Math.max(0, (range?.end ?? 0) - (range?.start ?? 0));
}

export function midpoint(range) {
  return range.start + visibleDuration(range) / 2;
}

export function normalizeSelection(start, end) {
  return { start: Math.min(start, end), end: Math.max(start, end) };
}

export function zoomRange(current, full, anchor, factor) {
  if (!current || !full) return current;
  const fullDuration = visibleDuration(full);
  const nextDuration = Math.max(fullDuration / 500, Math.min(fullDuration, visibleDuration(current) * factor));
  const anchorRatio = visibleDuration(current) > 0 ? (anchor - current.start) / visibleDuration(current) : 0.5;
  let start = anchor - nextDuration * anchorRatio;
  let end = start + nextDuration;
  if (start < full.start) {
    start = full.start;
    end = start + nextDuration;
  }
  if (end > full.end) {
    end = full.end;
    start = end - nextDuration;
  }
  return { start, end };
}

export function panRange(current, full, delta) {
  if (!current || !full) return current;
  const duration = visibleDuration(current);
  let start = current.start + delta;
  let end = current.end + delta;
  if (start < full.start) {
    start = full.start;
    end = start + duration;
  }
  if (end > full.end) {
    end = full.end;
    start = end - duration;
  }
  return { start, end };
}

export function rangesEqual(left, right) {
  if (!left || !right) return false;
  return Math.abs(left.start - right.start) < 1e-9 && Math.abs(left.end - right.end) < 1e-9;
}

export function valuesAtCursor(track, overview, cursorTime) {
  if (!overview?.points?.length || !Number.isFinite(cursorTime)) return [];
  const nearest = overview.points.reduce(
    (best, point) => (Math.abs(point.time - cursorTime) < Math.abs(best.time - cursorTime) ? point : best),
    overview.points[0]
  );
  const channels = overview.channels?.length ? overview.channels : track.channels || [];
  return channels.filter((channel) => Number.isFinite(nearest[channel])).map((channel) => [channel, nearest[channel]]);
}

export function candidateState(id, edits) {
  return edits[id] || { accepted: false, label: "", attributes: {} };
}

export function editedAnnotation(annotation, edits) {
  const edit = candidateState(annotation.id, edits);
  return {
    ...annotation,
    label: edit.label || annotation.label,
    attributes: edit.attributes || annotation.attributes || {},
    reviewed: true,
  };
}

export function combinedTimeRange(overviews) {
  const ranges = Object.values(overviews || {}).map((overview) => overview.time_range).filter(Boolean);
  if (!ranges.length) return null;
  return { start: Math.min(...ranges.map((range) => range.start)), end: Math.max(...ranges.map((range) => range.end)) };
}

export function timeTicks(start, end, count) {
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return [];
  return Array.from({ length: count }, (_, index) => start + ((end - start) * index) / Math.max(1, count - 1));
}

export function percent(value, start, end) {
  if (!Number.isFinite(value) || end <= start) return 0;
  return Math.max(0, Math.min(100, ((value - start) / (end - start)) * 100));
}

export function scale(value, inMin, inMax, outMin, outMax) {
  if (!Number.isFinite(value) || inMax <= inMin) return (outMin + outMax) / 2;
  return outMin + ((value - inMin) / (inMax - inMin)) * (outMax - outMin);
}

export function channelColor(channel, providedColor, index) {
  const colors = { ax: "#10b981", ay: "#f59e0b", az: "#d946ef", magnitude: "#06b6d4" };
  return colors[channel] || providedColor || ["#38bdf8", "#a78bfa", "#fb7185"][index % 3];
}

export function formatTime(value) {
  if (!Number.isFinite(value)) return "—";
  return `${value.toFixed(3)}s`;
}

export function formatValue(value, unit) {
  if (value === null || value === undefined || value === "") return "—";
  const rendered = typeof value === "number" ? Number(value).toFixed(3) : String(value);
  return unit ? `${rendered} ${unit}` : rendered;
}

export function annotationKind(annotation) {
  return annotation.kind || annotation.type || "point";
}

export function annotationStart(annotation) {
  return annotation.start_time ?? annotation.startTime ?? annotation.start ?? 0;
}

export function annotationEnd(annotation) {
  return annotation.end_time ?? annotation.endTime ?? annotation.end ?? annotationStart(annotation);
}

export function serializeAttributes(attributes) {
  if (!attributes || !Object.keys(attributes).length) return "";
  return Object.entries(attributes).map(([key, value]) => `${key}=${value}`).join(", ");
}
