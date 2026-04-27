from __future__ import annotations

from countpp_schemas import ExtractorRun
from countpp_signal_io import CanonicalStream

from .accelerometer import _run

VERSION = "0.1.0"


def run_sktime_segmentation_detector(
    canonical: CanonicalStream,
    *,
    channel: str = "magnitude",
    label: str = "change_segment",
) -> ExtractorRun:
    try:
        import sktime  # noqa: F401
    except ImportError as exc:
        return _run(
            canonical,
            "sktime_segmentation",
            VERSION,
            {"channel": channel, "label": label},
            [],
            diagnostics={"status": "missing_dependency", "detail": str(exc)},
        )

    return _run(
        canonical,
        "sktime_segmentation",
        VERSION,
        {"channel": channel, "label": label},
        [],
        diagnostics={
            "status": "not_configured",
            "detail": "sktime is installed, but a concrete detector has not been selected for this project yet.",
        },
    )
