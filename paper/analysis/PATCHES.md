# PATCHES — 論文の数値を生成した実行版からの変更記録

**English summary.** The scripts in `paper/analysis/` are the versions that produced the article,
with four kinds of edits made for publication and none to computation, aggregation or random seeds: (1) four lines containing the author's local path were replaced by
`C:\path\to\data` (§2); (2) the stage scripts were renamed (`stage3_tables.py` → `stage2_tables.py`,
`stage4_figures_v16.py` → `stage3_figures.py`) and 34 references to the undistributed exploratory
script were marked `legacy stage2` (§5); (3) two comments in `config.py` and one log message and one
docstring line in `stage3_figures.py` were reworded (§6); (4) 60 text labels drawn in the figures of
`stage3_figures.py` were changed, in three rounds on 2026-10-19 and 2026-10-20, so that the figures use the terms
of the article (`par` → `PIR-AR`, `NT-AR`, `Empty cage`, axis labels of Figures 1c, 2a, 3a and S4, `QC-pass`/`QC-fail`,
`good-channel criterion`, digit grouping and sentence-case legends) (§7). After each of edits (1)–(3), stage2 and stage3 were
run on `paper/intermediate` with the code before and after the edit; the 9 table CSVs,
`figure_values_good070.csv` and the 46 figure PNGs were byte-identical. After edit (4), the tables and the
caption values were unchanged and only the label text of the figure PNGs changed (checked pixel by pixel;
§7). The current checksums are in `SHA256SUMS.txt`.

公開にあたり `paper/analysis/` のコードに加えた変更は次の 4 種類である。いずれも計算・集約・乱数には手を加えていない。第 1〜3 種は出力も変えておらず、第 4 種は図中の文字だけを変えた。

1. 作者のローカルパス文字列の置換（4 行、§2）
2. stage の改名と、公開しない探索用スクリプトへの言及の明記（34 箇所、§5）
3. コメントとログ文字列の修正（4 箇所、§6）
4. 図中の表記の修正（`stage3_figures.py` の 60 箇所、3 回に分けて実施、§7）

## 1. 変更の理由（第 1 種）
作者の Windows ユーザー名を含むローカルパスが、既定値と使用例（docstring）に書かれていたため。

## 2. 第 1 種の変更内容（全 4 箇所）

ファイル名は現在の名前で記す（第 2 種の改名前は `stage3_tables.py`・`stage4_figures_v16.py`）。

| ファイル | 行 | 変更前 | 変更後 |
|---|---:|---|---|
| `config.py` | 217 | `BASE_DATA_DIR = r"C:\Users\<作者ユーザー名>\..."` | `BASE_DATA_DIR = r"C:\path\to\data"` |
| `config.py` | 244 | `update_paths(os.environ.get("SENSORS_BASE_DATA_DIR", r"C:\Users\<作者ユーザー名>\..."))` | `update_paths(os.environ.get("SENSORS_BASE_DATA_DIR", r"C:\path\to\data"))` |
| `stage2_tables.py` | 28（docstring） | `python stage2_tables.py "C:\\Users\\<作者ユーザー名>\\..."` | `python stage2_tables.py "C:\\path\\to\\data"` |
| `stage3_figures.py` | 43（docstring） | `python stage3_figures.py "C:/Users/<作者ユーザー名>/..."` | `python stage3_figures.py "C:/path/to/data"` |

（この表ではユーザー名以下を伏せて `<作者ユーザー名>\...` と書いている。）
`diff` で上記 4 行以外に差分がないことを確認した。行数・文字コード（UTF-8）・改行コードは変えていない。

## 3. 第 1 種の変更の動作への影響
- **数値への影響はない。** `BASE_DATA_DIR` は入力・出力フォルダの位置を決めるだけで、どのスクリプトもコマンドライン引数（stage1 は `--base-data-dir`）または環境変数 `SENSORS_BASE_DATA_DIR` があればそちらを使う。
- 唯一変わる挙動：引数も環境変数も与えずに実行した場合、既定の読み書き先が `C:\path\to\data` になる。存在しないフォルダなので、stage2・stage3 は「データフォルダを特定できませんでした」と表示して終了する（作者以外の環境では変更前も同じ動作）。
- 変更後のコードで stage2・stage3 を `paper/intermediate` に対して実行した。表 9 本（CSV）は変更前のコードの出力とバイト単位で同一、キャプション値 51 件は `paper/provenance/figure_values_good070.csv` と一致した。

## 4. 第 1 種の変更前後の SHA-256

| ファイル | 実行版 | パス置換後（第 2 種の改名前） | |
|---|---|---|---|
| `config.py` | `1f23468011d7decfdd3ee399141a36b2218d30b3748ac5d40ee292231e969d90` | `3cfe5cc4079570681cd924ff48998ebcb4330def622a38012af889d3311ff0f5` | パス文字列のみ変更 |
| `stage1_compute.py` | `c228eba545133c8e1c8547b6105ad3783eb3f26845547e554ed9b6b118dd5da4` | `c228eba545133c8e1c8547b6105ad3783eb3f26845547e554ed9b6b118dd5da4` | 同一 |
| `stage2_tables.py` | `395e4131b5a72e3f0c43bd851920eb380b9d4849504bd3f731941f79714ce88c` | `c71e7db418085e11aad0eb5a2408d5cdff0e92e9c732dbe7df31ed7e3a1881fa` | パス文字列のみ変更 |
| `stage3_figures.py` | `ad6f37175b8c9c97003e13914f3ff4e8df6c44970e4c7af84878abc4903bf4eb` | `a474c23aa70f71a4be132a7465308f978c13c1187c243d74b4a9e38f58e0f38e` | パス文字列のみ変更 |

これらは途中段階のハッシュで、公開版のハッシュは §7 と `SHA256SUMS.txt` にある。

---

## 5. 第 2 種の変更（2026-09-24）— stage の改名

欠番（旧 stage2 は探索用の図を出力するスクリプトで、論文には使用しておらず公開もしない）を解消するため、ファイル名と識別子を次のとおり改めた。

| 旧 | 新 |
|---|---|
| `stage3_tables.py` | `stage2_tables.py` |
| `stage4_figures_v16.py` | `stage3_figures.py` |

あわせて、コード内の旧 stage2 への言及 34 箇所（`config.py` 7・`stage1_compute.py` 5・`stage3_figures.py` 22）を **`legacy stage2`** と明記した。行番号付きの参照（`legacy stage2:1194-1310` など）は、公開していない探索用スクリプトの行を指す。
34 箇所のうち `stage1_compute.py:3859` はコメントではなくファイル名の文字列で、stage1 が `PAPER_VALUES.md` の監査のために `int_*.csv` への参照を探すファイルの名前である。このファイルは改名の前後とも本リポジトリに存在しない。

### 改名前後の検証（2026-09-24・実行して確認）

改名前のコードと改名後のコードを、同じ `paper/intermediate` に対して実行し、出力を照合した。

| 出力 | 結果 |
|---|---|
| 表の CSV 9 本（Table 1–3・Table S1–S6） | **バイト単位で同一** |
| `figure_values_good070.csv`（キャプション用の実測値） | **バイト単位で同一** |
| 図の PNG 46 点 | **バイト単位で同一** |
| `figure_table_registry_*.csv` | 生成時刻の列を除いて同一 |
| `caption_payload_good070.json` | 生成時刻、スクリプトのハッシュを記録するキー名（`stage4_sha256` → `stage3_sha256`）とその値、および注記中のスクリプト名のみが異なる |
| 図の PDF・表の XLSX | ファイル形式が生成時刻を内部に持つため不一致（PNG と CSV が一致していることで内容の同一性を確認した） |

改名直後のハッシュ：`config.py` `d078fc859ee7d73eba45c4e86a998dae5ae0fbe89efa18edf5e2b1526ac5bac5`、`stage1_compute.py` `0e5ef516aee44181d2c15f89741676eae6848d46c13f524cbc425487d3b023c8`、`stage2_tables.py` `cd39b62bbf79e4878135ee203ca58744382b644bf0d95623aa2c226cf7242f41`、`stage3_figures.py` `cc0f40181138319d219ccd203349aadb2f9b5fd4fc20ed45c8022dd43dc06528`（`config.py` と `stage3_figures.py` は §6 でさらに変わる）。

---

## 6. 第 3 種の変更（2026-09-29）— コメントとログ文字列の修正

次の 4 か所のコメント・ログ文字列を修正した。

| ファイル | 変更前 | 変更後 | 理由 |
|---|---|---|---|
| `stage3_figures.py` | Figure 1 の分散比について、キャプションの更新を促すログ | ログ `[Fig1] variance ratios above are the values used in the caption of the article.` | 実行のたびに「更新が必要」と表示されるのは誤解を招くため |
| `stage3_figures.py` | 診断図の docstring にあった作業時のメモ（1 行） | `It is a diagnostic figure and is not part of the article.` | 公開物の説明として不適切なため |
| `config.py` | 解析対象の記録に関するコメント | `本研究の対象は 30 Hz で記録した 4 セッションのみ。対象外の記録は空固定` | 本研究の範囲をそのまま書くため |
| `config.py` | 同上 | `対象外の記録を完全排除` | 同上 |

### 検証（2026-09-29・実行して確認）

修正前後のコードを同じ中間データに対して実行し、出力を照合した。

| 出力 | 結果 |
|---|---|
| 表の CSV 9 本、`figure_values_good070.csv` ほか 11 本 | **バイト単位で同一** |
| 図の PNG 46 点 | **バイト単位で同一** |
| `figure_table_registry_*.csv` 2 本 | 生成時刻の列のみ相違 |

## 7. 第 4 種の変更（2026-10-19・20）— 図中の表記

共著者（K.K.）の指摘により、論文本文の `par`（PIR active rate）を `PIR-AR`、`nar`（NanoTag-measured active rate）を `NT-AR` に改称した。
図の表記を本文と一致させるため、`stage3_figures.py` のうち**図に描かれる文字列だけ**を、次の 3 回で計 60 箇所変更した。

| 回 | 作者の実行版 | 箇所 | 内容 |
|---|---|---:|---|
| 1 | `stage4_figures_v16_3.py`（2026-10-19） | 21 | 下の表 |
| 2 | `stage4_figures_v16_4.py`（2026-10-19） | 5 | 共著者（J.T.）の指摘：Figure 1(c) の縦軸 `Raw signal (V)` / `1 Hz low-pass filtered (V)`、Figure 2(a)・3(a)・S4 の `NanoTag activity (counts / 10 min)` |
| 3 | `stage4_figures_v16_5.py`（2026-10-20） | 34 | 表記の最終統一：`good-channel criterion (F1 ≥ 0.70)`（S7・S8）、`QC-pass`/`QC-fail`、S8(b) 縦軸 `State F1`、Figure 5(e) の桁区切り `n = 28,168`、「=」の前後の空白、凡例の先頭の大文字。Figure 5(a) の凡例 `Good criterion` は、長くするとデータ点を隠すため変えていない |

第 1 回の内容：
コード内の変数名、`int_*.csv` と表 CSV の列名（`par`・`nar`・`pir_active_rate` など）、ログの文言は変えていない。

| 図 | 変更前 | 変更後 |
|---|---|---|
| Figure 5(a) 横軸 | `PIR active rate (par)` | `PIR active rate (PIR-AR)` |
| Figure S5(a) 凡例 | `par (AUC=…)` | `PIR-AR (AUC=…)` |
| Figure S5(b) 縦軸 / 横軸 | `par (PIR active rate)` / `NanoTag active rate` | `PIR active rate (PIR-AR)` / `NanoTag active rate (NT-AR)` |
| Figure S6(a) 縦軸 | `QC threshold (par), remaining 7 mice` | `QC threshold (PIR-AR), remaining 7 mice` |
| Figure S8(a) 縦軸 | `par (mean ± SD across mice)` | `PIR-AR (mean ± SD across mice)` |
| Figure S8(a)(b) 横軸 | `Cumulative active bins` | `Cumulative Active bins` |
| Figure S1(a) 凡例 | `Empty box` / `Occupied, rest` / `Occupied, active` | `Empty cage` / `Occupied, Rest` / `Occupied, Active` |
| Figure 2(b) 凡例 | `PIR (normalized)` | `PAI (normalized)`（描いているのは PAI） |
| Figure 4(a) 凡例 | `GMM rest/active component`、`GMM-estimated rest μ`、`NanoTag empirical rest μ` | `Rest`・`Active` を大文字に |
| Figure 4(b) 横軸 | `Absolute difference in rest μ (PAI)` | `Absolute difference in Rest μ (PAI)` |
| Figure 5(e) 目盛 | `(missed active)` / `(false active)` | `(missed Active)` / `(false Active)` |
| titled 版のパネル題（論文には使わない） | `par vs F1` など 4 件 | 上と同じ表記に |

### 検証（2026-10-19・実行して確認）

固定したパッケージ（`requirements.txt`）の環境で、変更前後のコードを同じ中間データに対して実行した。

| 出力 | 結果 |
|---|---|
| `figure_values_good070.csv`（キャプション値 51 件） | 変更前後で同一。`paper/provenance/figure_values_good070.csv` とは改行コード（CRLF/LF）のみ相違 |
| 変更前のコードの図 PNG と、それまでの論文の図 | Figure 2–6、S1–S5 はピクセル単位で一致。S6–S8 は、それまでの論文の図が旧版のスクリプトで作られていたため、S6 は凡例付近の 1,927 ピクセル、S7・S8 は個体数の表記（`n=` → `N=`）が異なっていた。今回の差し替えで論文の図はすべて現行コードの出力になった |
| 図 PNG（untitled 版） | Figure 1・3・6、S2・S3・S4・S7 はピクセル単位で同一。Figure 2・4・5、S1・S5・S6・S8 は変わったピクセルがすべて上の文字列の領域（凡例・軸ラベル・目盛）に限られ、データの点・線・軸の位置は 1 ピクセルも動いていない |
| 公開版（本ファイル）と作者の実行版（`stage4_figures_v16_3.py`）の出力 | 図 PNG 46 点がバイト単位で同一 |
| 第 2・3 回（2026-10-19・20） | 各回の前後で、変わったピクセルは変更した文字列の領域だけ。キャプション値 51 件は同一。公開版と作者の実行版（`stage4_figures_v16_5.py`）の出力は図 PNG 46 点がバイト単位で同一 |
| 差し替え後の論文の図（2026-10-20） | Figure 2–6、S1–S8 が公開版の出力とピクセル単位で同一（S6 は凡例付近の約 1,900 ピクセルに描画環境による差）。Figure 1 は写真と生成パネル (c) の合成図で、(c) の縦軸ラベルの領域だけを公開版の出力に置き換えた |

## 8. 公開版のチェックサム

`paper/analysis/SHA256SUMS.txt` に記載（2026-10-20 に再計算。変わったのは `stage3_figures.py` のみ）。

| ファイル | SHA256 |
|---|---|
| `config.py` | `b65fcedcb40a8f499a634bf808ced46126e2d68033dcb4fa4cbee9cc88f8b5bf` |
| `stage1_compute.py` | `0e5ef516aee44181d2c15f89741676eae6848d46c13f524cbc425487d3b023c8` |
| `stage2_tables.py` | `cd39b62bbf79e4878135ee203ca58744382b644bf0d95623aa2c226cf7242f41` |
| `stage3_figures.py` | `f6a2db569a6243b9d13bfd56aacd991ba51c9e3290f46204cdce85e3061725da` |
