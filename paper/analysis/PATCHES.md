# PATCHES — 論文の数値を生成した実行版からの変更記録

**English summary.** The scripts in `paper/analysis/` are the versions that produced the article,
with three kinds of edits made for publication and none to computation, aggregation, random seeds
or the content of the outputs: (1) four lines containing the author's local path were replaced by
`C:\path\to\data` (§2); (2) the stage scripts were renamed (`stage3_tables.py` → `stage2_tables.py`,
`stage4_figures_v16.py` → `stage3_figures.py`) and 34 references to the undistributed exploratory
script were marked `legacy stage2` (§5); (3) two comments in `config.py` and one log message and one
docstring line in `stage3_figures.py` were reworded (§6). After each edit, stage2 and stage3 were
run on `paper/intermediate` with the code before and after the edit; the 9 table CSVs,
`figure_values_good070.csv` and the 46 figure PNGs were byte-identical. The current checksums are
in `SHA256SUMS.txt`.

公開にあたり `paper/analysis/` のコードに加えた変更は次の 3 種類である。いずれも計算・集約・乱数・出力の内容には手を加えていない。

1. 作者のローカルパス文字列の置換（4 行、§2）
2. stage の改名と、公開しない探索用スクリプトへの言及の明記（34 箇所、§5）
3. コメントとログ文字列の修正（4 箇所、§6）

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

## 7. 公開版のチェックサム

`paper/analysis/SHA256SUMS.txt` に記載（2026-09-29 に再計算）。

| ファイル | SHA256 |
|---|---|
| `config.py` | `b65fcedcb40a8f499a634bf808ced46126e2d68033dcb4fa4cbee9cc88f8b5bf` |
| `stage1_compute.py` | `0e5ef516aee44181d2c15f89741676eae6848d46c13f524cbc425487d3b023c8` |
| `stage2_tables.py` | `cd39b62bbf79e4878135ee203ca58744382b644bf0d95623aa2c226cf7242f41` |
| `stage3_figures.py` | `a597af474b22d53e76df12d1558695c5dbbfbaa22a5348947c747a2920edecbd` |
