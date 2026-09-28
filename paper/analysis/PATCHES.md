# PATCHES — 論文の数値を生成した実行版からの変更記録

公開にあたり `paper/analysis/` のコードに加えた変更は、**作者のローカルパス文字列の置換のみ**である。
計算・集約・乱数・出力の処理には一切手を加えていない。

## 1. 変更の理由
作者の Windows ユーザー名を含むローカルパスが、既定値と使用例（docstring）に書かれていたため。

## 2. 変更内容（全 4 箇所）

| ファイル | 行 | 変更前 | 変更後 |
|---|---:|---|---|
| `config.py` | 217 | `BASE_DATA_DIR = r"C:\Users\<作者ユーザー名>\ドキュメント\最新データ"` | `BASE_DATA_DIR = r"C:\path\to\data"` |
| `config.py` | 244 | `update_paths(os.environ.get("SENSORS_BASE_DATA_DIR", r"C:\Users\<作者ユーザー名>\ドキュメント\最新データ"))` | `update_paths(os.environ.get("SENSORS_BASE_DATA_DIR", r"C:\path\to\data"))` |
| `stage2_tables.py` | 28（docstring） | `python stage2_tables.py "C:\\Users\\<作者ユーザー名>\\ドキュメント\\最新データ"` | `python stage2_tables.py "C:\\path\\to\\data"` |
| `stage3_figures.py` | 43（docstring） | `python stage3_figures.py "C:/Users/<作者ユーザー名>/ドキュメント/最新データ"` | `python stage3_figures.py "C:/path/to/data"` |

（この表ではユーザー名自体を伏せて `<作者ユーザー名>` と書いている。）
`diff` で上記 4 行以外に差分がないことを確認した。行数・文字コード（UTF-8）・改行コードは変えていない。

## 3. 動作への影響
- **数値への影響はない。** `BASE_DATA_DIR` は入力・出力フォルダの位置を決めるだけで、どのスクリプトもコマンドライン引数（stage1 は `--base-data-dir`）または環境変数 `SENSORS_BASE_DATA_DIR` があればそちらを使う。
- 唯一変わる挙動：引数も環境変数も与えずに実行した場合、既定の読み書き先が作者の手元フォルダから `C:\path\to\data` になる。存在しないフォルダなので、stage2・stage3 は「データフォルダを特定できませんでした」と表示して終了する（作者以外の環境では変更前も同じ動作）。
- 変更後のコードで stage2・stage3 を `paper/intermediate` に対して実行した。表 9 本（CSV）は変更前のコードの出力とバイト単位で同一、キャプション値 51 件は `paper/provenance/figure_values_good070.csv` と一致した。

## 4. SHA-256（変更前＝実行版 / 変更後＝公開版）

| ファイル | 実行版 | 公開版 | |
|---|---|---|---|
| `config.py` | `1f23468011d7decfdd3ee399141a36b2218d30b3748ac5d40ee292231e969d90` | `3cfe5cc4079570681cd924ff48998ebcb4330def622a38012af889d3311ff0f5` | パス文字列のみ変更 |
| `stage1_compute.py` | `c228eba545133c8e1c8547b6105ad3783eb3f26845547e554ed9b6b118dd5da4` | `c228eba545133c8e1c8547b6105ad3783eb3f26845547e554ed9b6b118dd5da4` | 同一 |
| `stage2_tables.py` | `395e4131b5a72e3f0c43bd851920eb380b9d4849504bd3f731941f79714ce88c` | `c71e7db418085e11aad0eb5a2408d5cdff0e92e9c732dbe7df31ed7e3a1881fa` | パス文字列のみ変更 |
| `stage3_figures.py` | `ad6f37175b8c9c97003e13914f3ff4e8df6c44970e4c7af84878abc4903bf4eb` | `a474c23aa70f71a4be132a7465308f978c13c1187c243d74b4a9e38f58e0f38e` | パス文字列のみ変更 |

実行版の受領時のファイル名は `stage1_compute__3_.py`、`stage3_figures_2_.py`（アップロード時に付いた接尾辞）。ファイル名の変更は内容に影響しない。

---

## 3. 第 2 種の変更（2026-09-24）— stage の改名

公開にあたり、**欠番（旧 stage2 は探索用の図を出力するスクリプトで、論文には使用しておらず公開もしない）を解消するため**、ファイル名と識別子を次のとおり改めた。**計算・集約・乱数・出力の処理には一切手を加えていない。**

| 旧 | 新 |
|---|---|
| `stage3_tables.py` | `stage2_tables.py` |
| `stage4_figures_v16.py` | `stage3_figures.py` |

あわせて、コード内の旧 stage2 への言及 34 箇所（`config.py` 7・`stage1_compute.py` 5・`stage3_figures.py` 22）を **`legacy stage2`** と明記した。行番号付きの参照（`legacy stage2:1194-1310` など）は、公開していない探索用スクリプトの行を指す。

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

### 改名後のチェックサム

| ファイル | SHA256 |
|---|---|
| `config.py` | `d078fc859ee7d73eba45c4e86a998dae5ae0fbe89efa18edf5e2b1526ac5bac5` |
| `stage1_compute.py` | `0e5ef516aee44181d2c15f89741676eae6848d46c13f524cbc425487d3b023c8` |
| `stage2_tables.py` | `cd39b62bbf79e4878135ee203ca58744382b644bf0d95623aa2c226cf7242f41` |
| `stage3_figures.py` | `cc0f40181138319d219ccd203349aadb2f9b5fd4fc20ed45c8022dd43dc06528` |

上の §2 の表に記載したハッシュは、改名前（パス置換のみを行った版）のものである。

