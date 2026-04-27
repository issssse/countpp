from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from countpp_schemas import ExtractorRun
from countpp_signal_io import CanonicalStream


@dataclass(frozen=True)
class ExtractorSpec:
    name: str
    version: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


class ExtractorPlugin(Protocol):
    spec: ExtractorSpec

    def run(self, canonical: CanonicalStream, **parameters: Any) -> ExtractorRun:
        ...
