# `PAPER_VALUES.md` についての注記 / Note on `PAPER_VALUES.md`

`PAPER_VALUES.md` の Settings 欄に記載された `QC1_GOOD_F1=0.8` は、0.70 版と 0.80 版を同一プロセスで連続実行した際に、実行時の設定値が最後の状態で印字されたものである。本ファイルの内容自体は good_cut = 0.70 の解析結果であり、論文の数値と対応する。

（経緯：`paper/analysis/stage1_compute.py` の 4736 行が各版の実行時に `config.QC1_GOOD_F1` をその版の値に書き換える。0.80 版の実行後、最終ループで 0.70 版の `PAPER_VALUES.md` も書き出すため、Settings 欄には最後に設定された 0.8 が印字される。`paper/analysis/config.py` の値は `QC1_GOOD_F1 = 0.70` である。公開コードと出力の対応を保つため、コード・本ファイルとも修正していない。）

---

The line `QC1_GOOD_F1=0.8` in the *Settings* section of `PAPER_VALUES.md` is an artefact of running the good_cut 0.70 and 0.80 versions consecutively in one process: the settings block prints the configuration value as last set at run time. The content of the file is the good_cut = 0.70 analysis and corresponds to the values reported in the article.

(`stage1_compute.py`, line 4736, sets `config.QC1_GOOD_F1` to the good_cut of each version; `PAPER_VALUES.md` for both versions is written in a final loop after the 0.80 run. The declared value in `config.py` is `QC1_GOOD_F1 = 0.70`. Neither the code nor this file was edited, so that code and outputs correspond exactly.)

## Files in this folder
| File | Description |
|---|---|
| `PAPER_VALUES.md` | Machine-generated inventory of every intermediate CSV and gate check, written by `stage1_compute.py` (good_cut = 0.70) |
| `VALUE_PROVENANCE.md` | Mapping from each value in the article to its source file, column and aggregation (Japanese; edited for publication, see `NOTE_VALUE_PROVENANCE.md`) |
| `figure_values_good070.csv` | Caption values written by `stage3_figures.py`; use it to check a reproduction |
| `NOTE_VALUE_PROVENANCE.md` | Note on the editing of `VALUE_PROVENANCE.md` |
| `NOTE_LPF_SWEEP.md` | Note on the reused `int_lpf_sweep.csv` |
