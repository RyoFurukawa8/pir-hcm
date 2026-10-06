# Notes on this folder and on the frozen code / 本フォルダと凍結コードについての注記

The analysis code in `paper/analysis/` is frozen: it was not edited after the run that produced the
intermediate data, so that the code and its outputs correspond exactly. The points below explain the few
places where the code or its outputs, read on their own, could be misunderstood.

`paper/analysis/` の解析コードは凍結しており、中間データを生成した実行の後は改変していない。
コードと出力の対応を厳密に保つためである。以下は、コードや出力だけを見ると誤解されうる箇所の説明である。

## Files in this folder / 本フォルダのファイル

| File | Description |
|---|---|
| `VALUE_PROVENANCE.md` | Mapping from each value in the article to its source file, column and aggregation (Japanese, with an English summary) |
| `PAPER_VALUES.md` | Machine-generated inventory of every intermediate CSV and gate check, written by `stage1_compute.py` (good_cut = 0.70) |
| `figure_values_good070.csv` | Caption values written by `stage3_figures.py`; use it to check a reproduction |
| `NOTES.md` | This file |
| `SHA256SUMS.txt` | SHA-256 checksums of the other files in this folder |

## 1. Numbering of the supplementary figures and tables / 補足図表の番号

`stage2_tables.py` and `stage3_figures.py` name their outputs under the numbering in use when the analysis was
run. In the article, the supplementary tables were renumbered in ascending order of first citation in the main
text. The contents are unchanged; only the label differs. The supplementary figures, Tables 1–3 and Figures
1–6 carry the same numbers as the files produced by the code.

コードが出力する補足表のファイル名と、論文中の番号が一部異なる。論文では本文での初出順に採番し直した。
内容は同じで、違うのは番号だけである。補足図、本文の Table 1–3 と Figure 1–6 は、コードの出力と同じ番号である。

| Output of the code | Number in the article | Contents |
|---|---|---|
| `TableS1` | **Table S6** | Sensitivity to the definition of a good channel |
| `TableS2` | **Table S1** | Sensitivity to the definition of the reference label |
| `TableS3` | **Table S5** | Reference-free temporal guard complementing the par gate |
| `TableS4` | Table S4 | Detection ratio by record and dark-phase block |
| `TableS5` | **Table S3** | Leave-one-mouse-out fold-by-fold breakdown |
| `TableS6` | **Table S2** | Point estimates of the main outcomes and their 95% confidence intervals |

* `outputs/captions/figure_number_old2new.csv`, written by `stage3_figures.py`, maps an earlier internal numbering
  to the code's numbering; it is not a mapping to the article.
  （作業用の古い番号からコードの番号への対応であり、論文の番号への対応ではない。）
* The docstring of `stage3_figures.py` calls the generated panel of Figure 1 "(d)"; in the article it is Figure 1c.
  （docstring の Figure 1「(d)」は、論文の Figure 1c である。）

## 2. `QC1_GOOD_F1=0.8` printed in `PAPER_VALUES.md` / `PAPER_VALUES.md` の「0.8」

The *Settings* section of `PAPER_VALUES.md` prints `QC1_GOOD_F1=0.8`. This is a run-time artefact: the
good_cut 0.70 and 0.80 versions are run consecutively in one process (`stage1_compute.py`, line 4736, sets
`config.QC1_GOOD_F1` for each version), and `PAPER_VALUES.md` for both versions is written in a final loop, so
the settings block shows the value as last set. The content of the file is the good_cut = 0.70 analysis and
corresponds to the article. The declared value in `config.py` is `QC1_GOOD_F1 = 0.70`.

Settings 欄の `QC1_GOOD_F1=0.8` は、0.70 版と 0.80 版を同じ実行で続けて計算したために、最後に設定された値が
印字されたものである。本ファイルの内容は good_cut = 0.70 の解析で、論文の数値と対応する。
`config.py` の値は `QC1_GOOD_F1 = 0.70` である。

## 3. `int_lpf_sweep.csv` / ローパス掃引のデータ

`int_lpf_sweep.csv` (low-pass cutoff sweep; Figure S1f) was not recomputed in the run that produced this release
(`RUN_LPF_SWEEP=False` in `config.py`); an existing file was reused. Its 1.0 Hz rows agree with `int_channel.csv`
produced by the released pipeline for all 32 channels. No record remains of the code version that generated
the rows for 0.5, 2.0 and 5.0 Hz. In `PAPER_VALUES.md` this file is marked `[PRE-EXISTING]`; the aggregate
`int_lpf_sweep_agg.csv` was rebuilt from it by the released `stage1_compute.py`. The same is stated in the Data
Availability Statement of the article.

`int_lpf_sweep.csv` は本リリースの実行では再計算せず、既存のファイルを用いた。1.0 Hz の行は、公開パイプラインの
`int_channel.csv` と 32 チャンネルすべてで一致する。0.5、2.0、5.0 Hz の行を生成したコードの版の記録は残っていない。

## 4. Two comments in `config.py` / `config.py` の 2 つのコメント

**The `【要確認】` comment about a recording "260709" (config.py lines 101–105).** This working note is stale.
"7/9" was a typographical error for "7/6", and the correction was applied at the time: the list immediately
below the comment reads `FIG4_FORCE_CH = ["260702_ch3", "260706_ch3", "260706_ch6"]`. `FIG4_FORCE_CH` is not
read by any of the distributed scripts. Figure 4(a) of the article shows only `FIG4_MAIN_CH` (`260626_ch6`,
Record 1 ch6). The recordings analysed are `260626`, `260629`, `260702` and `260706` (Records 1–4 of the
article); no recording was excluded.

この注記は古い。「7/9」は「7/6」の誤記で、修正はコメント直下の `FIG4_FORCE_CH` に適用済みである。
`FIG4_FORCE_CH` は公開するスクリプトのどれからも読まれない。解析した記録は 4 回で、除外した記録はない。

**`RECORDS_OLD` and the `age_group` column.** `config.py` fixes `RECORDS_OLD` to an empty list, and
`stage1_compute.py` prints an inventory check for it at start-up; the intermediate data carry an `age_group`
column whose value is `Young` for every row. These exist so that the set of recordings entering the analysis is
fixed in the configuration and verified at run time. No data outside the four recordings of the article are
contained in this repository.

`RECORDS_OLD` と `age_group` 列は、解析に入る記録の集合を設定ファイルで固定し、実行時に検査するためのものである。
本リポジトリには、論文の 4 記録以外のデータは含まれていない。

## 5. `VALUE_PROVENANCE.md`

This table was edited for publication and checked against the final version of the article (2026-10-06).
本表は公開用に編集し、論文の最終版（2026-10-06）と照合した。
