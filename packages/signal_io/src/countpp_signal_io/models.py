from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyarrow as pa

from countpp_schemas import RecordingSession, Stream


@dataclass(frozen=True)
class CanonicalStream:
    session: RecordingSession
    stream: Stream
    table: pa.Table
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def time_column(self) -> str:
        return "time"

    def channel_names(self) -> list[str]:
        return [channel.name for channel in self.stream.channels]
