# Numbering of the supplementary figures and tables / 補足図表の番号について

`stage3_figures.py` and `stage2_tables.py` emit the supplementary figures and tables under the numbering that
was in use while the analysis was run. During the final revision of the article, the supplementary items were
renumbered so that they appear in ascending order of first citation in the main text, as the journal requires.
**The frozen code was not modified for this**, so the file names produced by the code (`FigS5.png`,
`TableS1.csv`, …) do not always match the numbers printed in the article.

論文の最終改訂で、補足図表を本文での初出順に採番し直した。**凍結コードはそのために改変していない**ため、
コードが出力するファイル名（`FigS5.png`、`TableS1.csv` など）と、論文中の番号が一部食い違う。
対応は下表のとおり。

## Figures

| Output of the code | Number in the article | Contents |
|---|---|---|
| `FigS1` | Figure S1 | Separation and computation of the PAI |
| `FigS2` | Figure S2 | Bin width |
| `FigS3` | Figure S3 | GMM settings and errors |
| `FigS4` | Figure S4 | Per-mouse intensity relationships |
| **`FigS5`** | **Figure S6** | Discriminative performance of the QC metrics, algebraically attainable region |
| **`FigS6`** | **Figure S5** | Robustness and applicability of the QC (leave-one-mouse-out) |
| `FigS7` | Figure S7 | Independence of the QC |
| `FigS8` | Figure S8 | Stability of par and F1 against cumulative recording length |

## Tables

| Output of the code | Number in the article | Contents |
|---|---|---|
| **`TableS1`** | **Table S6** | Sensitivity to the definition of a good channel |
| **`TableS2`** | **Table S1** | Sensitivity to the definition of the reference label |
| **`TableS3`** | **Table S5** | Reference-free temporal guard complementing the par gate |
| `TableS4` | Table S4 | Detection ratio by record and dark-phase block |
| **`TableS5`** | **Table S3** | Leave-one-mouse-out fold-by-fold breakdown |
| **`TableS6`** | **Table S2** | Point estimates of the main outcomes and their 95% confidence intervals |

Tables 1–3 and Figures 1–6 of the main text are unaffected.
本文の Table 1–3 と Figure 1–6 は影響を受けない。

The contents of each item are unchanged; only the label differs.
各項目の内容は変わっておらず、違うのは番号だけである。
