# Note on two comments in `config.py`

## 1. The `【要確認】` comment about a recording "260709" (config.py lines 101–105)

`config.py` carries a working note that reads, in Japanese, that a label "7/9" could not be
resolved to a recording, that a recording `260709` is not in `RECORDS_YOUNG`, and that the label
should be rewritten if it is a typographical error for "7/6".

**This note is stale.** "7/9" was a typographical error for "7/6". The correction was applied at the
time: the list immediately below the comment already reads
`FIG4_FORCE_CH = ["260702_ch3", "260706_ch3", "260706_ch6"]`.

The recordings analysed in the article are `260626`, `260629`, `260702` and `260706` — four in
total, as stated in Section 2.5 (Records 1–4 of the article). **No recording was excluded from the analysis.**
`FIG4_FORCE_CH` is not read by any of the distributed scripts; it listed channels that the undistributed
exploratory script (`legacy stage2`) always drew as candidates for Figure 4(a). Figure 4(a) of the article shows only `FIG4_MAIN_CH`
(`260626_ch6`, Record 1 ch6).

この注記は古い。「7/9」は「7/6」の誤記であり、修正はコメント直下の `FIG4_FORCE_CH` に適用済みである。
解析対象の記録は 260626・260629・260702・260706 の 4 回で、解析から除外した記録はない。
`FIG4_FORCE_CH` は公開するスクリプトのどれからも読まれない（公開しない探索用スクリプトが Figure 4(a) の候補として必ず描くチャンネルの指定）。
論文の Figure 4(a) は `FIG4_MAIN_CH`（260626_ch6）のみを示す。

## 2. `RECORDS_OLD` and the `age_group` column

`config.py` fixes `RECORDS_OLD` to an empty list and `stage1_compute.py` prints an inventory check
for it at start-up; the intermediate data carry an `age_group` column whose value is `Young` for
every row. These exist so that the set of recordings entering the analysis is fixed in the
configuration and verified at run time, not chosen afterwards. No data outside the four recordings
of the article are contained in this repository.

`RECORDS_OLD` と `age_group` 列は、解析に入る記録の集合を設定ファイルで固定し、実行時に検査する
ためのものである。本リポジトリには、論文の 4 記録以外のデータは含まれていない。
