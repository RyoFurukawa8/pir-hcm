# Note on `VERSION_DRIFT_CHECK.txt`

```
analysis_payload_hash_match=True
raw_hash_match=False
```

`raw_hash_match` does **not** concern the raw recordings (LabVIEW CSV).
It is written by `paper/analysis/stage1_compute.py` (line 4775) and compares the byte-level SHA-256 of
`int_channel.csv` produced by the good_cut = 0.70 run with that produced by the good_cut = 0.80 run.

`int_channel.csv` contains a `good_cut` column (0.7 vs 0.8), so the two files necessarily differ byte-for-byte:
**`False` is the expected result.** The normalized analysis payload is identical across versions
(`analysis_payload_hash_match=True`). The same interpretation applies to the column
`int_channel_raw_sha256` in `int_version_crosswalk.csv`.

The code (`stage1_compute.py`) and its output (`VERSION_DRIFT_CHECK.txt`) were left unchanged so that the archived code and outputs correspond exactly.
