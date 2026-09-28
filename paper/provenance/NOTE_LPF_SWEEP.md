# `int_lpf_sweep.csv` についての注記 / Note on `int_lpf_sweep.csv`

`int_lpf_sweep.csv` は本リリースの実行では再計算されておらず（`RUN_LPF_SWEEP=False`）、既存ファイルを流用している。カットオフ 1.0 Hz の行は、本リリースのパイプラインが出力する `int_channel.csv` と 32 チャンネルすべてで一致することを確認した。0.5 / 2.0 / 5.0 Hz の行については、生成時のコード版の記録が残っていない。

`int_lpf_sweep.csv` was not recomputed in the run that produced this release (`RUN_LPF_SWEEP=False` in `config.py`); an existing file was reused. The rows for the 1.0 Hz cutoff were confirmed to agree with `int_channel.csv` produced by this release's pipeline for all 32 channels. No record remains of the code version that generated the rows for 0.5, 2.0 and 5.0 Hz.

(In `PAPER_VALUES.md` this file is marked `[PRE-EXISTING]`. The aggregate `int_lpf_sweep_agg.csv` was rebuilt from it by the released `stage1_compute.py`.)
