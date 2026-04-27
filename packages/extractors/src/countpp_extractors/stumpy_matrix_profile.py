from __future__ import annotations

from countpp_schemas import Annotation, ExtractorRun
from countpp_signal_io import CanonicalStream

from .accelerometer import _run
from .table_utils import numeric_column, time_values

VERSION = "0.1.0"


def run_stumpy_matrix_profile_detector(
    canonical: CanonicalStream,
    *,
    channel: str = "magnitude",
    window_size: int = 64,
    top_k: int = 3,
    label: str = "matrix_profile_discord",
) -> ExtractorRun:
    try:
        import numpy as np
        import stumpy
    except ImportError as exc:
        return _run(
            canonical,
            "stumpy_matrix_profile",
            VERSION,
            {"channel": channel, "window_size": window_size, "top_k": top_k, "label": label},
            [],
            diagnostics={"status": "missing_dependency", "detail": str(exc)},
        )

    times = time_values(canonical)
    values = np.asarray(numeric_column(canonical, channel), dtype=float)
    if window_size < 4 or window_size >= len(values):
        raise ValueError("window_size must be at least 4 and smaller than the stream length")

    profile = stumpy.stump(values, m=window_size)[:, 0].astype(float)
    candidate_indices = np.argsort(profile)[-top_k:][::-1]
    annotations: list[Annotation] = []
    for rank, index in enumerate(candidate_indices):
        start = times[int(index)]
        end = times[min(int(index) + window_size - 1, len(times) - 1)]
        annotations.append(
            Annotation(
                id=f"ann_stumpy_{canonical.stream.id}_{rank}_{int(index)}",
                stream_id=canonical.stream.id,
                session_id=canonical.session.id,
                type="interval",
                start_time=start,
                end_time=end,
                label=label,
                source="extractor",
                confidence=None,
                metadata={"channel": channel, "matrix_profile": float(profile[int(index)]), "rank": rank},
            )
        )

    return _run(
        canonical,
        "stumpy_matrix_profile",
        VERSION,
        {"channel": channel, "window_size": window_size, "top_k": top_k, "label": label},
        annotations,
        diagnostics={"status": "ok", "profile_length": int(len(profile))},
    )
