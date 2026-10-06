# Numbering of the supplementary figures and tables / 補足図表の番号について

`stage3_figures.py` and `stage2_tables.py` emit the supplementary figures and tables under the numbering that
was in use while the analysis was run. During the final revision of the article, the supplementary items were
renumbered so that they appear in ascending order of first citation in the main text.
**The frozen code was not modified for this**, so the file names produced by the code (`FigS5.png`,
`TableS1.csv`, …) do not always match the numbers printed in the article.

論文の最終改訂で、補足図表を本文での初出順に採番し直した。**凍結コードはそのために改変していない**ため、
コードが出力するファイル名（`FigS5.png`、`TableS1.csv` など）と、論文中の番号が一部食い違う。
対応は下表のとおり。

## Figures

| Output of the code | Number in the article | Contents |
|---|---|---|
| `FigS1` | Figure S1 | Separation and computation of the PAI |
| `FigS2` | Figure S2 | Sensitivity of state F1 and the intensity r to the analysis bin width |
| `FigS3` | Figure S3 | GMM settings and errors |
| `FigS4` | Figure S4 | Per-mouse intensity relationships |
| `FigS5` | Figure S5 | Discriminative performance of the QC metrics, algebraically attainable region |
| `FigS6` | Figure S6 | Robustness and applicability of the QC (leave-one-mouse-out) |
| `FigS7` | Figure S7 | Intensity correlation by QC group and per-mouse state F1 |
| `FigS8` | Figure S8 | Stability against the cumulative number of Active bins |

## Tables

| Output of the code | Number in the article | Contents |
|---|---|---|
| **`TableS1`** | **Table S6** | Sensitivity to the definition of a good channel |
| **`TableS2`** | **Table S1** | Sensitivity to the definition of the reference label |
| **`TableS3`** | **Table S5** | Reference-free temporal guard complementing the par gate |
| `TableS4` | Table S4 | Detection ratio by record and dark-phase block |
| **`TableS5`** | **Table S3** | Leave-one-mouse-out fold-by-fold breakdown |
| **`TableS6`** | **Table S2** | Point estimates of the main outcomes and their 95% confidence intervals |

All supplementary figures now carry the same number as the file produced by the code (the earlier exchange of Figures S5 and S6 was reverted on 2026-10-05). Tables 1–3 and Figures 1–6 of the main text are unaffected.
補足図は、2026-10-05 に Figure S5 と S6 の入れ替えを元に戻したため、すべてコードの出力ファイル名と同じ番号になった。本文の Table 1–3 と Figure 1–6 は影響を受けない。

The contents of each item are unchanged; only the label differs.
各項目の内容は変わっておらず、違うのは番号だけである。

## Other numbering in the code and its outputs

* `outputs/captions/figure_number_old2new.csv`, written by `stage3_figures.py`, maps an earlier internal numbering
  to the code's numbering. It is not a mapping to the article.
* The docstring of `stage3_figures.py` calls the generated panel of Figure 1 "(d)"; in the article it is Figure 1c.

`outputs/captions/figure_number_old2new.csv` は、それ以前の作業用の番号からコードの番号への対応で、論文の番号への対応ではない。
`stage3_figures.py` の docstring が Figure 1 の「(d)」と呼ぶパネルは、論文の Figure 1c である。
