# Extractor Contract

Extractors consume canonical streams and produce `ExtractorRun` objects.

```text
CanonicalStream
  -> extractor(parameters)
  -> ExtractorRun(output_annotations, diagnostics)
```

## Inputs

An extractor should receive:
- a `CanonicalStream` from `countpp_signal_io`
- explicit parameters
- no mutable raw-data side effects

The stream table must contain `time` plus one or more channel columns.

## Outputs

An extractor returns:
- `extractor_name`
- `version`
- `input_streams`
- `parameters`
- `output_annotations`
- `diagnostics`

Output annotations must use the shared `Annotation` schema and set `source="extractor"`. When the extractor can compute it, annotations should also include:

- `event_type_id`
- `value`
- `value_unit`
- `value_source`
- `attributes`
- `extractor_run_id`
- `confidence`
- `reviewed=false`

Detector tools should first return a `DetectorPreview`. Accepted candidates are committed into an event or interval tier only after review.

## Current plugins

- `accelerometer_peak`: point-event candidates from threshold plus hysteresis.
- `accelerometer_start_stop`: interval candidates where a channel leaves and returns to baseline.
- `accelerometer_periodicity`: interval candidates from peak spacing.
- `stumpy_matrix_profile`: optional prototype for matrix-profile discord intervals.
- `sktime_segmentation`: optional placeholder for future sktime detectors.

## Baselines

Accelerometer extractors default to a median baseline for the selected channel. Pass a fixed `baseline` when the signal has a known reference, such as gravity near `9.81`.

## Label Studio bridge

Extractor annotations become Label Studio predictions with:
- `type="timeserieslabels"`
- `value.start`
- `value.end`
- `value.instant`
- `value.timeserieslabels`

Reviewed Label Studio exports are parsed back into internal `Annotation` objects.
