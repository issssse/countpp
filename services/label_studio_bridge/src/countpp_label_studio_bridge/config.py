from __future__ import annotations

from html import escape

from countpp_schemas import Channel

DEFAULT_LABELS = {
    "peak": "#d4380d",
    "start_stop_interval": "#237804",
    "periodic_behavior": "#096dd9",
    "matrix_profile_discord": "#722ed1",
    "change_segment": "#ad6800",
}


def generate_time_series_label_config(
    channels: list[Channel],
    *,
    labels: dict[str, str] | None = None,
    data_key: str = "csv",
    object_name: str = "ts",
    label_name: str = "label",
    time_column: str = "time",
) -> str:
    label_map = labels or DEFAULT_LABELS
    label_lines = "\n".join(
        f'    <Label value="{escape(label)}" background="{escape(color)}"/>'
        for label, color in label_map.items()
    )
    channel_lines = "\n".join(
        f'      <Channel column="{escape(channel.name)}" legend="{escape(channel.name)}"{_unit_attr(channel)}/>'
        for channel in channels
    )
    if len(channels) > 1:
        channel_block = f"    <MultiChannel>\n{channel_lines}\n    </MultiChannel>"
    else:
        channel_block = channel_lines

    return f"""<View>
  <TimeSeriesLabels name="{escape(label_name)}" toName="{escape(object_name)}">
{label_lines}
  </TimeSeriesLabels>
  <TimeSeries name="{escape(object_name)}" value="${escape(data_key)}" valueType="url" sep="," timeColumn="{escape(time_column)}">
{channel_block}
  </TimeSeries>
</View>"""


def _unit_attr(channel: Channel) -> str:
    if not channel.unit:
        return ""
    return f' units="{escape(channel.unit)}"'
