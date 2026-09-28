"""
stage2_tables.py — 投稿用の表を生成する（v5 番号体系）

生成する表:
    Table 1   システム構成と 1 チャンネルあたりの仕様
    Table 2   個体別の結果（個体別 Spearman r の列を含む）
    Table 3   par 単独の QC が誤分類したチャンネルの内訳（FP + FN）
    Table S1  「good」の定義に対する感度（threshold_source / n_fold_used 必須）
    Table S2  参照ラベル定義 (nb >= 1/2/3) に対する感度            ★新規
    Table S3  par ゲートを補完する参照不要の時間分解ガード          ★新規
    Table S4  セッション別・暗期ブロック別の検出比                 ★新規
    Table S5  LOMO fold 別の内訳（hold-out F1 と LOSO F1 は別量）  ★新規
    Table S6  主要結果と 95% 信頼区間、およびその出典

出力:
    outputs/tables/TableN.csv / TableN.xlsx（1表1ファイル）
    outputs/tables/all_tables.xlsx（全表をシート分け）
    outputs/captions/figure_table_registry.csv（表の部分）

設計上の約束:
  ・測定値をコードに書かない。数値はすべて int_*.csv から読むか、その場で計算する。
  ・Excel に数式を入れない。論文の表に数式は不要で、Word に貼るときに壊れる。
    数値は数値型のまま書き込み、桁は表示形式で指定する（後から桁を変えられる）。
  ・各シート末尾にデータ源の CSV 名と生成日時を注記する。
  ・読めなかった入力があれば空表を出さず、[要実行] としてログに残す。

使い方:
    python stage2_tables.py "C:\\path\\to\\data"
    python stage2_tables.py "<BASE>" --good-cut 0.80
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter

ENC = "utf-8-sig"
FONT = "Arial"

_LOG: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)
    _LOG.append(msg)


# ====================================================================== 入出力
class Paths:
    def __init__(self, base: str, good_cut: float):
        tag = f"{int(round(good_cut * 100)):03d}"
        self.root = os.path.join(base, "paper_pipeline_outputs")
        self.inter = os.path.join(self.root, f"intermediate__good{tag}")
        self.out = os.path.join(self.root, "outputs")
        self.tables = os.path.join(self.out, "tables")
        self.captions = os.path.join(self.out, "captions")
        for d in (self.tables, self.captions):
            os.makedirs(d, exist_ok=True)


def load(paths: Paths, name: str) -> pd.DataFrame | None:
    p = os.path.join(paths.inter, name)
    if not os.path.exists(p):
        return None
    try:
        d = pd.read_csv(p, encoding=ENC)
        return d if len(d) else None
    except Exception as e:  # noqa: BLE001
        log(f"  [読込失敗] {name}: {e}")
        return None


# ====================================================================== 計算補助
def auc_ranked(score: np.ndarray, positive: np.ndarray) -> float:
    """同順位を正しく扱う AUC（Mann-Whitney U の順位表現）。sklearn と一致する。"""
    s = np.asarray(score, dtype=float)
    y = np.asarray(positive).astype(int)
    ok = np.isfinite(s)
    s, y = s[ok], y[ok]
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(s).rank(method="average").to_numpy()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def youden_threshold(score: np.ndarray, positive: np.ndarray) -> float:
    """感度 + 特異度 - 1 を最大化する閾値（候補は観測値そのもの）。"""
    s = np.asarray(score, dtype=float)
    y = np.asarray(positive).astype(int)
    ok = np.isfinite(s)
    s, y = s[ok], y[ok]
    if len(s) == 0 or y.sum() == 0 or (1 - y).sum() == 0:
        return float("nan")
    best_t, best_j = float("nan"), -np.inf
    for t in np.unique(s):
        pred = (s >= t).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        tn = int(((pred == 0) & (y == 0)).sum())
        sens = tp / (tp + fn) if (tp + fn) else np.nan
        spec = tn / (tn + fp) if (tn + fp) else np.nan
        j = (sens + spec - 1.0) if np.isfinite(sens) and np.isfinite(spec) else -np.inf
        if j > best_j:
            best_j, best_t = j, float(t)
    return best_t


def confusion(score: np.ndarray, positive: np.ndarray, thr: float) -> dict:
    s = np.asarray(score, dtype=float)
    y = np.asarray(positive).astype(int)
    pred = (s >= thr).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "PPV": tp / (tp + fp) if (tp + fp) else np.nan,
        "sensitivity": tp / (tp + fn) if (tp + fn) else np.nan,
        "specificity": tn / (tn + fp) if (tn + fp) else np.nan,
    }


def mean_of_means(df: pd.DataFrame, value: str, by: str = "mouse_id") -> float:
    v = df[[by, value]].dropna()
    if not len(v):
        return float("nan")
    return float(v.groupby(by)[value].mean().mean())


# ====================================================================== 表の器
class Table:
    def __init__(self, label: str, title: str, df: pd.DataFrame,
                 notes: list[str], source: str, formats: dict | None = None):
        self.label = label            # "Table 2" / "Table S3"
        self.title = title
        self.df = df
        self.notes = notes
        self.source = source
        self.formats = formats or {}  # 列名 -> Excel 表示形式

    @property
    def stem(self) -> str:
        return self.label.replace(" ", "")   # "Table2" / "TableS3"

    @property
    def sheet(self) -> str:
        return self.stem[:31]


# ====================================================================== 各表
def build_table1(paths: Paths) -> Table | None:
    """システム構成と 1ch あたりの仕様。記録条件は実データから、機材仕様は著者記入。"""
    chan = load(paths, "int_channel.csv")
    rows: list[dict] = []

    def add(item, value, unit="", src=""):
        rows.append({"Item": item, "Value": value, "Unit": unit, "Source": src})

    # --- 著者が記入する行（推測で埋めない）---
    for item in ["PIR module", "Modification point", "DAQ device", "Acquisition software",
                 "Wiring / signal conditioning", "Cage type", "Cost per channel"]:
        add(item, "[要記入]", "", "author")

    # --- 実データから決まる行 ---
    if chan is not None:
        n_ch = int(chan["ch"].nunique())
        n_mouse = int(chan["mouse_id"].nunique())
        n_rec = int(chan["record_id"].nunique()) if "record_id" in chan.columns else np.nan
        add("Channels analysed", n_ch, "n", "int_channel.csv")
        add("Animals", n_mouse, "n", "int_channel.csv")
        add("Recordings", n_rec, "n", "int_channel.csv")
        if "n_hours" in chan.columns:
            add("Recording length (median)", round(float(chan["n_hours"].median()), 1),
                "h", "int_channel.csv")
        if "adc_range" in chan.columns:
            add("ADC range (median)", round(float(chan["adc_range"].median()), 2),
                "V", "int_channel.csv")
    else:
        log("  [Table 1] int_channel.csv が読めない → 実データ由来の行は [要実行]")
        add("Channels analysed", "[要実行]", "n", "int_channel.csv")

    # --- config 由来（設定値であって測定値ではない）---
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import config as _cfg  # noqa: PLC0415
        add("Sampling rate (nominal)", float(_cfg.FS), "Hz", "config.py")
        add("Low-pass cutoff", float(_cfg.LOWPASS_CUTOFF_HZ), "Hz", "config.py")
        add("Low-pass order (Butterworth)", int(_cfg.LOWPASS_ORDER), "", "config.py")
        add("Bin width, state classification", int(_cfg.BIN_STATE_SEC), "s", "config.py")
        add("Bin width, intensity correlation", int(_cfg.BIN_INTENSITY_SEC), "s", "config.py")
        add("Dark phase", f"{_cfg.DARK_HOURS[0]:02d}:00-{_cfg.DARK_HOURS[1]:02d}:00",
            "", "config.py")
        add("Reference logger resolution", int(_cfg.NANOTAG_RESOLUTION_SEC), "s", "config.py")
    except Exception as e:  # noqa: BLE001
        log(f"  [Table 1] config.py を読めなかった: {e}")

    df = pd.DataFrame(rows)
    notes = [
        "Rows marked [要記入] are hardware/cost specifications supplied by the authors; "
        "they are not derived from the recorded data.",
        "Rows sourced from config.py are declared inputs (settings), not measured results.",
        "Recording resolution of 0.01 V is achievable with a 10-bit ADC on a 5 V range.",
    ]
    return Table("Table 1", "System configuration and per-channel specification",
                 df, notes, "int_channel.csv + config.py")


def build_table2(paths: Paths) -> Table | None:
    """個体別の結果。個体別 Spearman r を明示列として持たせる（Figure S3 の引き取り先）。"""
    chan = load(paths, "int_channel.csv")
    if chan is None:
        log("  [Table 2] int_channel.csv が無い → [要実行]")
        return None
    need = ["mouse_id", "intensity_r", "F1_state", "qc1_pass", "nanotag_active_rate"]
    miss = [c for c in need if c not in chan.columns]
    if miss:
        log(f"  [Table 2] 列が足りない {miss} → [要実行]")
        return None

    rows = []
    for mid, g in chan.groupby("mouse_id"):
        qc = g[g["qc1_pass"] == 1]
        rows.append({
            "Animal": mid,
            "Channels analysed": int(len(g)),
            "NanoTag active rate (mean of channels)": float(g["nanotag_active_rate"].mean()),
            "Intensity r (mean of channels)": float(g["intensity_r"].mean()),
            "Intensity r (min)": float(g["intensity_r"].min()),
            "Intensity r (max)": float(g["intensity_r"].max()),
            "State F1 (all channels)": float(g["F1_state"].mean()),
            "State F1 (QC-passing channels)": float(qc["F1_state"].mean()) if len(qc) else np.nan,
            "QC-passing channels": int(len(qc)),
        })
    df = pd.DataFrame(rows).sort_values("Animal").reset_index(drop=True)

    rmin = float(df["Intensity r (mean of channels)"].min())
    rmax = float(df["Intensity r (mean of channels)"].max())
    no_pass = df.loc[df["QC-passing channels"] == 0, "Animal"].tolist()

    notes = [
        "All statistics are computed per animal to avoid pseudo-replication.",
        f"Per-animal intensity r ranges from {rmin:.4f} to {rmax:.4f} "
        "(mean of the channel-wise Spearman correlations within each animal).",
    ]
    if no_pass:
        notes.append("State F1 for QC-passing channels cannot be computed for "
                     + ", ".join(map(str, no_pass)) + " (no channel passed QC).")
    fmt = {c: "0.0000" for c in df.columns if c.startswith(("Intensity", "State", "NanoTag"))}
    return Table("Table 2", "Per-animal results", df, notes, "int_channel.csv", fmt)


def build_table3(paths: Paths) -> Table | None:
    """par 単独QCをすり抜けたチャンネル。時間分解QCの列を追加する。"""
    anat = load(paths, "int_qc_anatomy.csv")
    chan = load(paths, "int_channel.csv")
    lomo = load(paths, "int_loso_thr.csv")
    temporal = load(paths, "int_qc_temporal_compare.csv")
    if anat is None or chan is None or lomo is None:
        log("  [Table 3] int_qc_anatomy.csv / int_channel.csv / int_loso_thr.csv が無い → [要実行]")
        return None

    good_cut = float(chan["good_cut"].dropna().iloc[0])
    fp = anat.copy()
    fp["error_type"] = "FP"

    fn_src = chan[
        (chan["F1_state"].astype(float) >= good_cut) & (chan["qc1_pass"].astype(int) == 0)
    ].copy()
    fn = fn_src.copy().rename(columns={"pir_active_rate": "par"})
    fn["par_minus_true"] = (
        fn["par"].astype(float) - fn["nanotag_active_rate"].astype(float)
    )
    fn["captured_by"] = "not applicable"
    fn["error_type"] = "FN"

    df = pd.concat([fp, fn], ignore_index=True, sort=False)

    ren = {
        "ch": "Channel", "mouse_id": "Animal", "error_type": "Error type",
        "F1_state": "State F1", "par": "par",
        "nanotag_active_rate": "nar (reference)",
        "par_minus_true": "par - nar", "gmm_separation": "GMM separation",
        "snr": "SNR", "bimodality_coef": "Bimodality",
        "captured_by": "Captured by reference-based guard",
    }
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    order = [
        "Channel", "Animal", "Error type", "State F1", "par",
        "nar (reference)", "par - nar", "GMM separation", "SNR",
        "Bimodality", "Captured by reference-based guard",
    ]
    df = df[order]

    notes = [
        "FP = passed the par-only QC rule but fell below the state-F1 criterion; "
        "FN = met the state-F1 criterion but failed the par-only QC rule.",
        "'Captured by reference-based guard' lists the auxiliary rules (SNR, GMM separation) "
        "that would have rejected an FP channel; FN is reported as not applicable.",
    ]

    if temporal is None:
        log("  [Table 3] int_qc_temporal_compare.csv が読めないため時間分解ガード注記は追加しない")
    else:
        temporal_need = ["ch", "flag_saturated", "flag_floor_shift"]
        temporal_miss = [c for c in temporal_need if c not in temporal.columns]
        if temporal_miss:
            log(f"  [Table 3] int_qc_temporal_compare.csv に必要列が無い {temporal_miss} "
                "→ 時間分解ガード注記は追加しない")
        else:
            table3_channels = df["Channel"].astype(str)
            temporal_hit = temporal[
                temporal["ch"].astype(str).isin(table3_channels)
                & (
                    temporal["flag_saturated"].astype(float).eq(1)
                    | temporal["flag_floor_shift"].astype(float).eq(1)
                )
            ]
            temporal_hit_channels = (
                temporal_hit["ch"].astype(str).drop_duplicates().tolist()
            )
            if temporal_hit_channels:
                notes.append(
                    f"{', '.join(temporal_hit_channels)} は参照を要さない時間分解ガード"
                    "（par 飽和または rest 成分のフロアシフト）でも検出される（Table S3）。"
                    "SNR および GMM 分離度は参照ラベルを必要とするが、"
                    "時間分解ガードは PIR 信号のみから算出される。"
                )
            else:
                log("  [Table 3] 時間分解ガードで捕捉される誤分類チャンネルは無い")

    if len(fn_src) == 1:
        fn_par = float(fn_src["pir_active_rate"].iloc[0])
        same = np.isclose(
            lomo["qc1_threshold"].astype(float).to_numpy(), fn_par
        )
        if "threshold_source_ch" in lomo.columns:
            same &= lomo["threshold_source_ch"].astype(str).eq(
                str(fn_src["ch"].iloc[0])
            ).to_numpy()
        n_same = int(same.sum())
        if n_same:
            notes.append(
                f"偽陰性チャンネルの par は、{len(lomo)} fold 中 {n_same} fold の "
                "leave-one-mouse-out 閾値と同値である。すなわちこのチャンネルは各 fold "
                "自身の閾値では通過し、不合格となるのは運用閾値が fold 閾値の平均であることによる。"
            )
        else:
            log("  [Table 3] FN par と LOMO 閾値が一致しない")
    else:
        log("  [Table 3] FN par と LOMO 閾値が一致しない")

    fmt = {c: "0.0000" for c in ["State F1", "par", "nar (reference)", "par - nar",
                                 "GMM separation", "SNR", "Bimodality"] if c in df.columns}
    return Table("Table 3", "Channels misclassified by the par-only QC rule",
                 df, notes,
                 "int_qc_anatomy.csv + int_channel.csv + int_loso_thr.csv + "
                 "int_qc_temporal_compare.csv", fmt)


def build_table_s1(paths: Paths) -> Table | None:
    """good 定義への感度。good_cut の全グリッドを出す。

    優先して int_good_sensitivity_grid.csv（stage1 が全グリッドで計算した表）を読む。
    無い場合のみ、従来どおり版ごとの int_good_sensitivity.csv を走査して結合する。
    """
    grid_frames: list[pd.DataFrame] = []
    ver_frames: list[pd.DataFrame] = []
    for d in sorted(os.listdir(paths.root)):
        if not d.startswith("intermediate__good"):
            continue
        for fn, bucket in (("int_good_sensitivity_grid.csv", grid_frames),
                           ("int_good_sensitivity.csv", ver_frames)):
            p = os.path.join(paths.root, d, fn)
            if not os.path.exists(p):
                continue
            try:
                bucket.append(pd.read_csv(p, encoding=ENC))
            except Exception as e:  # noqa: BLE001
                log(f"  [Table S1] {d}/{fn} を読めない: {e}")
    frames = grid_frames or ver_frames
    if grid_frames:
        source = "int_good_sensitivity_grid.csv (full good_cut grid)"
    else:
        log("  [Table S1] int_good_sensitivity_grid.csv が無い → 版ごとの1行ファイルで代替")
        source = "int_good_sensitivity.csv (all versions)"
    if not frames:
        log("  [Table S1] int_good_sensitivity.csv が見つからない → [要実行]")
        return None
    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["good_cut"])
    df = df.sort_values("good_cut").reset_index(drop=True)

    # 退化条件（片側クラスが 5 未満）を脚注で明示するために、改名前に拾っておく。
    degenerate = []
    if {"n_good_ch", "n_bad_ch"}.issubset(df.columns):
        for _, r in df.iterrows():
            if pd.isna(r["n_good_ch"]) or pd.isna(r["n_bad_ch"]):
                continue
            n_small = min(int(r["n_good_ch"]), int(r["n_bad_ch"]))
            if n_small < 5:
                degenerate.append((float(r["good_cut"]), n_small))
    log(f"  [Table S1] {len(df)} 行（good_cut={[round(float(x), 2) for x in df['good_cut']]}）")

    for c in ["threshold_source", "n_fold_used"]:
        if c not in df.columns:
            log(f"  [Table S1] 必須列 {c} が無い → [要実行] を入れる")
            df[c] = "[要実行]"

    ren = {
        "good_cut": "good definition (state F1 >=)", "lomo_threshold": "LOMO threshold (par)",
        "threshold_source": "threshold_source", "n_fold_used": "n_fold_used",
        "n_good_ch": "good channels (n)", "n_bad_ch": "bad channels (n)",
        "n_pass_ch": "QC-passing channels (n)", "n_pass_mice": "QC-passing animals (n)",
        "PPV": "PPV", "sensitivity": "Sensitivity", "specificity": "Specificity",
        "par_auc": "AUC (par)", "f1_qc_post": "State F1 after QC",
    }
    order = [ren[k] for k in ren if k in df.columns]
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})[order]

    notes = [
        "threshold_source and n_fold_used are reported so that the reader can verify that "
        "the leave-one-mouse-out derivation did not fall back at any criterion.",
        "A stricter criterion raises the post-QC state F1, but only because channels that "
        "fail the criterion are removed; the number of usable channels and animals falls at "
        "the same time.",
        "Conditions in which either group holds fewer than 5 channels are not interpreted.",
    ]
    for cut, n_small in degenerate:
        notes.append(
            f"At good definition F1 >= {cut:.2f} the smaller class holds only {n_small} "
            "channels (n < 5), so the two classes are too small for discrimination to be "
            "evaluated; the apparent separation at this criterion, including an AUC of "
            "1.0000, is a degenerate consequence of the class imbalance and is not evidence "
            "of performance. The row is listed for completeness only."
        )
    fmt = {c: "0.0000" for c in df.columns if c in
           ("LOMO threshold (par)", "PPV", "Sensitivity", "Specificity",
            "AUC (par)", "State F1 after QC")}
    return Table("Table S1", "Sensitivity to the definition of a good channel",
                 df, notes, source, fmt)


def build_table_s2(paths: Paths, good_cut: float) -> Table | None:
    """参照ラベル定義 nb >= k への感度。par が不変であることを示すのが主眼。"""
    sw = load(paths, "int_label_sweep_channel.csv")
    if sw is None:
        log("  [Table S2] int_label_sweep_channel.csv が無い → [要実行]")
        return None
    need = ["ch", "mouse_id", "nb_threshold", "par", "nar", "F1_state"]
    miss = [c for c in need if c not in sw.columns]
    if miss:
        log(f"  [Table S2] 列が足りない {miss} → [要実行]")
        return None

    # 本文の運用閾値（測定値なので CSV から読む）
    gs = load(paths, "int_good_sensitivity.csv")
    main_thr = float("nan")
    if gs is not None and "lomo_threshold" in gs.columns:
        m = gs[np.isclose(gs["good_cut"].astype(float), good_cut)]
        if len(m):
            main_thr = float(m["lomo_threshold"].iloc[0])

    rows = []
    for k, g in sw.groupby("nb_threshold"):
        is_good = (g["F1_state"].astype(float) >= good_cut).to_numpy()
        par = g["par"].astype(float).to_numpy()
        thr_sw = youden_threshold(par, is_good)
        c_sw = confusion(par, is_good, thr_sw)
        c_main = confusion(par, is_good, main_thr) if np.isfinite(main_thr) else {}
        rows.append({
            "Reference label (NanoTag counts >=)": int(k),
            "nar (mean)": float(g["nar"].mean()),
            "State F1 (mean of animal means)": mean_of_means(g, "F1_state"),
            "AUC (par)": auc_ranked(par, is_good),
            "good channels (n)": int(is_good.sum()),
            "par (mean)": float(par.mean()),
            "par (distinct values)": int(pd.Series(par).round(9).nunique()),
            "Sweep threshold (Youden)": thr_sw,
            "TP (sweep thr)": c_sw["TP"], "FP (sweep thr)": c_sw["FP"],
            "FN (sweep thr)": c_sw["FN"], "TN (sweep thr)": c_sw["TN"],
            "Main operational threshold": main_thr,
            "TP (main thr)": c_main.get("TP", np.nan), "FP (main thr)": c_main.get("FP", np.nan),
            "FN (main thr)": c_main.get("FN", np.nan), "TN (main thr)": c_main.get("TN", np.nan),
        })
    df = pd.DataFrame(rows).sort_values("Reference label (NanoTag counts >=)").reset_index(drop=True)

    par_invariant = df["par (mean)"].round(9).nunique() == 1
    notes = [
        "The operational reference label is 'active if the NanoTag count in the bin is greater "
        "than zero'. This table varies that threshold.",
        ("par is identical under every label definition (mean {:.6f}), because par is derived "
         "from PAI alone and never sees the reference."
         ).format(float(df["par (mean)"].iloc[0])) if par_invariant else
        "WARNING: par was expected to be invariant across label definitions but is not. "
        "Check the sweep implementation before using this table.",
        "The AUC of par, in contrast, does depend on the label definition and falls as the "
        "definition becomes stricter. This is a limitation of the reported discrimination "
        "performance, not of par itself.",
        "Two thresholds are reported. The sweep threshold maximises Youden's J within each "
        "label condition; the main operational threshold is the leave-one-mouse-out value used "
        "in the main text. The confusion matrices differ because the thresholds differ.",
    ]
    fmt = {c: "0.0000" for c in ["nar (mean)", "State F1 (mean of animal means)", "AUC (par)",
                                 "par (mean)", "Sweep threshold (Youden)",
                                 "Main operational threshold"]}
    return Table("Table S2", "Sensitivity to the definition of the reference label",
                 df, notes, "int_label_sweep_channel.csv + int_good_sensitivity.csv", fmt)


def build_table_s3(paths: Paths) -> Table | None:
    """静的 par ゲート vs 時間分解QC。"""
    cmp = load(paths, "int_qc_temporal_compare.csv")
    chan = load(paths, "int_channel.csv")
    lomo = load(paths, "int_loso_thr.csv")
    if cmp is None or chan is None or lomo is None:
        log("  [Table S3] int_qc_temporal_compare.csv / int_channel.csv / "
            "int_loso_thr.csv が無い → [要実行]")
        return None

    df = cmp.copy()
    guard_pass = (
        df["flag_saturated"].astype(int).eq(0)
        & df["flag_floor_shift"].astype(int).eq(0)
    )
    static_pass = df["qc1_pass"].astype(int).eq(1)
    df["temporal_guard_pass"] = guard_pass.astype(int)
    df["category"] = np.select(
        [static_pass & guard_pass, static_pass & ~guard_pass,
         ~static_pass & guard_pass],
        ["both_pass", "static_only", "temporal_only"],
        default="both_fail",
    )

    keep = [c for c in ["ch", "mouse_id", "record_id", "pir_active_rate"]
            if c in chan.columns]
    df = df.merge(chan[keep], on="ch", how="left")

    ren = {
        "ch": "Channel", "mouse_id": "Animal", "record_id": "Recording",
        "pir_active_rate": "par", "qc1_pass": "Static QC pass",
        "temporal_guard_pass": "Temporal guard pass", "F1_state": "State F1",
        "is_good": "is good", "category": "Category",
    }
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    order = [
        "Channel", "Animal", "Recording", "par", "State F1", "is good",
        "Static QC pass", "Temporal guard pass", "Category",
    ]
    df = df[order]

    guard_fail = df["Temporal guard pass"].astype(int).eq(0)
    n_guard_fail = int(guard_fail.sum())
    n_guard_pass = int((~guard_fail).sum())
    n_guard_fail_static = int(
        (guard_fail & df["Static QC pass"].astype(int).eq(1)).sum()
    )
    operational_thr = float(
        lomo["qc1_threshold"].dropna().astype(float).mean()
    )

    if n_guard_fail_static == n_guard_fail:
        cohort_note = (
            f"本コホートでは {len(df)} チャンネル中 {n_guard_fail} 本がこのガードで不合格となり、"
            "いずれも par ゲートを通過していた。"
            f"ガードは他の {n_guard_pass} チャンネルの判定を変更しない。"
            "すなわち本ガードは par ゲートの競合ではなく補完である。"
        )
    else:
        cohort_note = (
            f"本コホートでは {len(df)} チャンネル中 {n_guard_fail} 本がこのガードで不合格となり、"
            f"そのうち {n_guard_fail_static} 本が par ゲートを通過していた。"
            f"ガードは他の {n_guard_pass} チャンネルの判定を変更しない。"
            "すなわち本ガードは par ゲートの競合ではなく補完である。"
        )

    notes = [
        "par ゲートの故障モードは検出漏れである。時間分解ガードは par 飽和と rest 成分の"
        "フロアシフトにより過剰検出型の故障を検出するもので、いずれも参照を要さず "
        "PIR 信号のみから算出される。" + cohort_note,
        f"時間分解ガードは本研究の運用 QC 規則には含まれない。"
        f"運用規則は par ≥ {operational_thr:.4f} 単独である。",
        "Category は 2 つのゲートの通過状況を示す。both_pass は両方を通過、"
        "static_only は par ゲートのみ通過、temporal_only は時間分解ガードのみ通過、"
        "both_fail は両方とも不合格を意味する。これは state F1 による good の定義とは"
        "独立であり、both_pass のチャンネルが good であるとは限らない。",
    ]
    fmt = {c: "0.0000" for c in ["par", "State F1"] if c in df.columns}
    return Table("Table S3", "Reference-free temporal guard complementing the par gate",
                 df, notes,
                 "int_qc_temporal_compare.csv + int_channel.csv + int_loso_thr.csv", fmt)


def build_table_s4(paths: Paths) -> Table | None:
    """セッション別・暗期ブロック別の検出比。trend_class は載せない。"""
    ss = load(paths, "int_session_summary.csv")
    tr = load(paths, "int_session_trend.csv")
    chan = load(paths, "int_channel.csv")
    if ss is None or tr is None or chan is None:
        log("  [Table S4] int_session_summary.csv / int_session_trend.csv / "
            "int_channel.csv が無い → [要実行]")
        return None
    if "is_dark_block" not in ss.columns:
        log("  [Table S4] is_dark_block 列が無い → [要実行]")
        return None

    qc_by_record = (
        chan.assign(_record_id_key=chan["record_id"].astype(str))
        .groupby("_record_id_key")["qc1_pass"].sum()
    )

    rows = []
    for rec, g in ss[ss["is_dark_block"].eq(1)].groupby("record_id"):
        gg = g.dropna(subset=["par_over_nar_mean"]).sort_values("block_start_h")
        vals = gg["par_over_nar_mean"].astype(float).tolist()
        rec_tr = tr[tr["record_id"].astype(str) == str(rec)]
        row = {
            "Recording": rec,
            "Dark blocks used (n)": len(vals),
            "QC-passing channels (n)": int(qc_by_record.loc[str(rec)]),
            "Detection ratio, block 1": vals[0] if len(vals) > 0 else np.nan,
            # ratio_mid: 暗期ブロックが3つのときの中央ブロック（stage1 に無いのでここで算出）
            "Detection ratio, block 2 (mid)": vals[len(vals) // 2] if len(vals) == 3 else np.nan,
            "Detection ratio, block 3": vals[-1] if len(vals) > 1 else np.nan,
            "Mean": float(np.mean(vals)) if vals else np.nan,
            "SD": float(np.std(vals, ddof=1)) if len(vals) > 1 else np.nan,
            "Delta (last - first)": (vals[-1] - vals[0]) if len(vals) > 1 else np.nan,
        }
        for src, dst in [("ratio_slope_per_day", "Slope (per day)"),
                         ("cohort_ratio_mean_loo", "Mean of the other recordings")]:
            row[dst] = float(rec_tr[src].iloc[0]) if len(rec_tr) and src in rec_tr.columns else np.nan
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("Recording").reset_index(drop=True)

    notes = [
        "Detection ratio = par / nar within each 12-hour dark block, averaged over the eight "
        "channels of that recording.",
        "Only complete blocks that carry an adequate reference coverage are used, so that the "
        "diagnostic describes the same span as the primary analysis.",
        "No trend classification label is reported. The first-to-last difference is a fragile "
        "summary of a non-monotonic series, so the individual block values and the slope are "
        "given instead.",
        "'Mean of the other recordings' excludes the recording in its own row, so that an "
        "outlying recording does not shift the reference it is compared against.",
    ]
    fmt = {c: "0.0000" for c in df.columns
           if c not in ("Recording", "Dark blocks used (n)", "QC-passing channels (n)")}
    return Table("Table S4", "Detection ratio by recording and dark-phase block",
                 df, notes,
                 "int_session_summary.csv + int_session_trend.csv + int_channel.csv", fmt)


def build_table_s5(paths: Paths) -> Table | None:
    """LOMO fold 別。hold-out F1 と LOSO F1 が別量であることを明示する。"""
    ho = load(paths, "int_holdout_f1.csv")
    lo = load(paths, "int_loso_f1.csv")
    if ho is None:
        log("  [Table S5] int_holdout_f1.csv が無い → [要実行]")
        return None
    source_files = ["int_holdout_f1.csv"]
    df = ho.copy()
    if lo is not None and "fold_excluded_mouse" in lo.columns:
        keep = [c for c in ["fold_excluded_mouse", "f1_qc_post", "f1_all",
                            "n_qc_pass_ch_remaining"] if c in lo.columns]
        df = df.merge(lo[keep], on="fold_excluded_mouse", how="left")
        source_files.append("int_loso_f1.csv")
    else:
        log("  [Table S5] int_loso_f1.csv が無いため LOSO 列は [要実行]")

    ren = {
        "fold_excluded_mouse": "Fold (animal held out)",
        "threshold": "Fold threshold (par)",
        "threshold_source_ch": "Channel that set the threshold",
        "n_pass_ch": "QC-passing channels in the held-out animal",
        "holdout_f1": "Hold-out state F1 (held-out animal)",
        "f1_qc_post": "LOSO state F1 after QC (remaining animals)",
        "f1_all": "LOSO state F1, all channels (remaining animals)",
        "n_qc_pass_ch_remaining": "QC-passing channels in the remaining animals",
    }
    df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    col_ho = "Hold-out state F1 (held-out animal)"
    valid = df[col_ho].dropna() if col_ho in df.columns else pd.Series(dtype=float)
    n_drop = int(df[col_ho].isna().sum()) if col_ho in df.columns else -1
    operational_thr = (
        float(ho["threshold"].dropna().astype(float).mean())
        if "threshold" in ho.columns and ho["threshold"].notna().any()
        else np.nan
    )

    notes = [
        "Two different quantities appear in this table and must not be conflated. "
        "The hold-out F1 evaluates the animal that was excluded from threshold derivation. "
        "The LOSO F1 is an in-sample value computed on the remaining animals.",
        (f"Mean hold-out F1 over the {len(valid)} evaluable folds = {valid.mean():.4f}."
         if len(valid) else "Hold-out F1 could not be evaluated in any fold."),
        (f"{n_drop} fold(s) could not be evaluated because the held-out animal had no "
         "QC-passing channel." if n_drop else "Every fold was evaluable."),
        "Folds are not a series; they are not connected by lines in the corresponding figure.",
    ]
    if np.isfinite(operational_thr):
        notes.append(
            f"本表の QC 通過チャンネル数は各 fold 自身の閾値で判定した値であり、"
            f"運用閾値 (par ≥ {operational_thr:.4f}) で判定した Table 2 の値とは"
            "一致しない場合がある。"
        )
    else:
        log("  [Table S5] 運用閾値を算出できないため閾値注記は [要実行]")

    fmt = {c: "0.0000" for c in df.columns if "F1" in c or "threshold (par)" in c}
    return Table("Table S5", "Leave-one-mouse-out folds: hold-out and LOSO performance",
                 df, notes, " + ".join(source_files), fmt)


def build_table_s6(paths: Paths) -> Table | None:
    boot = load(paths, "int_bootstrap_ci.csv")
    lomo = load(paths, "int_loso_thr.csv")
    auc = load(paths, "int_auc_metrics_cluster.csv")
    sensor = load(paths, "int_sensor_consistency_permouse.csv")
    chan = load(paths, "int_channel.csv")
    circ = load(paths, "int_circadian.csv")
    loso = load(paths, "int_loso_f1.csv")
    if boot is None or lomo is None or auc is None or sensor is None:
        log("  [Table S6] 必要な入力 CSV が無い → [要実行]")
        return None

    rows = []
    for key, label in [
        ("intensity_r_mean_of_means", "Intensity r (mean of mouse means)"),
        ("F1_all_mean", "State F1 (all channels)"),
        ("F1_qc1_mean", "State F1 (QC-passing channels)"),
    ]:
        r = boot.loc[boot["metric"].astype(str).eq(key)].iloc[0]
        rows.append({
            "Metric": label,
            "Point estimate": float(r["point"]),
            "95% CI lower": float(r["ci_lower"]),
            "95% CI upper": float(r["ci_upper"]),
            "CI method": str(r["ci_method"]),
            "Resampling unit": str(r["resample_unit"]),
            "n": int(r["n_individuals"]),
            "Source CSV": "int_bootstrap_ci.csv",
        })

    thr_values = lomo["qc1_threshold"].dropna().astype(float)
    if {"ci_lower", "ci_upper"}.issubset(lomo.columns) and (
            lomo["ci_lower"].notna().any() and lomo["ci_upper"].notna().any()):
        thr_lo = float(lomo["ci_lower"].dropna().iloc[0])
        thr_hi = float(lomo["ci_upper"].dropna().iloc[0])
        thr_method = (
            str(lomo["ci_method"].dropna().iloc[0])
            if "ci_method" in lomo.columns and lomo["ci_method"].notna().any()
            else "not recorded"
        )
        thr_unit = (
            str(lomo["resample_unit"].dropna().iloc[0])
            if "resample_unit" in lomo.columns and lomo["resample_unit"].notna().any()
            else ""
        )
    else:
        thr_lo = np.nan
        thr_hi = np.nan
        thr_method = "not estimated"
        thr_unit = ""
        log("  [Table S6] QC threshold par: 95% CI は CSV に無いため空欄")
    rows.append({
        "Metric": "QC threshold (par)",
        "Point estimate": float(thr_values.mean()),
        "95% CI lower": thr_lo,
        "95% CI upper": thr_hi,
        "CI method": thr_method,
        "Resampling unit": thr_unit,
        "n": int(len(thr_values)),
        "Source CSV": "int_loso_thr.csv",
    })

    a = auc.loc[auc["metric"].astype(str).eq("pir_active_rate")].iloc[0]
    rows.append({
        "Metric": "AUC (par)",
        "Point estimate": float(a["auc_observed"]),
        "95% CI lower": float(a["ci_lower"]),
        "95% CI upper": float(a["ci_upper"]),
        "CI method": "percentile bootstrap",
        "Resampling unit": str(a["cluster_unit"]),
        "n": int(a["n_mouse"]),
        "Source CSV": "int_auc_metrics_cluster.csv",
    })

    sensor_values = sensor["mean_inter_sensor_r"].dropna().astype(float)
    log("  [Table S6] Inter-sensor r: 95% CI は CSV に無いため空欄")
    rows.append({
        "Metric": "Inter-sensor r",
        "Point estimate": float(sensor_values.mean()),
        "95% CI lower": np.nan,
        "95% CI upper": np.nan,
        "CI method": "not estimated",
        "Resampling unit": "",
        "n": int(len(sensor_values)),
        "Source CSV": "int_sensor_consistency_permouse.csv",
    })

    source_files = [
        "int_bootstrap_ci.csv",
        "int_loso_thr.csv",
        "int_auc_metrics_cluster.csv",
        "int_sensor_consistency_permouse.csv",
    ]

    extra_metrics = [
        ("Residual intensity r (60-min envelope removed)", "intensity_r_trendrm_sym"),
        ("Mismatched-pairing control r", "placebo_r"),
        ("Random-permutation control r", "phase_shuffle_r"),
    ]
    channel_source_used = False
    if chan is None:
        log("  [Table S6] int_channel.csv が読めないため Abstract 追加 3 指標は追加しない")
    elif "mouse_id" not in chan.columns:
        log("  [Table S6] int_channel.csv に必要列 mouse_id が無いため Abstract 追加 3 指標は追加しない")
    else:
        for metric, value_col in extra_metrics:
            if value_col not in chan.columns:
                log(f"  [Table S6] int_channel.csv に必要列 {value_col} が無いため "
                    f"{metric} は追加しない")
                continue
            valid = chan[["mouse_id", value_col]].dropna()
            if not len(valid):
                log(f"  [Table S6] int_channel.csv の {value_col} に有効値が無いため "
                    f"{metric} は追加しない")
                continue
            rows.append({
                "Metric": metric,
                "Point estimate": mean_of_means(chan, value_col),
                "95% CI lower": np.nan,
                "95% CI upper": np.nan,
                "CI method": "not estimated",
                "Resampling unit": "",
                "n": int(valid["mouse_id"].nunique()),
                "Source CSV": "int_channel.csv",
            })
            channel_source_used = True
        if channel_source_used:
            source_files.append("int_channel.csv")

    if circ is None:
        log("  [Table S6] int_circadian.csv が読めないため概日 r は追加しない")
    else:
        circadian_candidates = []
        for c in circ.columns:
            name = str(c).lower()
            if not (name == "r" or name.endswith("_r") or "corr" in name):
                continue
            values = pd.to_numeric(circ[c], errors="coerce").dropna()
            if len(values) and values.nunique() == 1:
                circadian_candidates.append((c, values))
        if len(circadian_candidates) == 1:
            circadian_col, circadian_values = circadian_candidates[0]
            rows.append({
                "Metric": "Circadian profile r (PIR vs reference)",
                "Point estimate": float(circadian_values.iloc[0]),
                "95% CI lower": np.nan,
                "95% CI upper": np.nan,
                "CI method": "not estimated",
                "Resampling unit": "",
                "n": int(circ["hour"].dropna().nunique()) if "hour" in circ.columns else np.nan,
                "Source CSV": "int_circadian.csv",
            })
            source_files.append("int_circadian.csv")
        elif not circadian_candidates:
            log("  [Table S6] int_circadian.csv に相関のスカラー値として使える列が無いため概日 r は追加しない")
        else:
            candidate_names = [c for c, _ in circadian_candidates]
            log(f"  [Table S6] int_circadian.csv の相関スカラー候補列が複数ある "
                f"{candidate_names} → 概日 r は追加しない")

    loso_note = None
    if loso is None:
        log("  [Table S6] int_loso_f1.csv が読めないため LOSO F1 範囲注記は追加しない")
    elif "f1_qc_post" not in loso.columns:
        log("  [Table S6] int_loso_f1.csv に必要列 f1_qc_post が無いため "
            "LOSO F1 範囲注記は追加しない")
    else:
        loso_values = pd.to_numeric(loso["f1_qc_post"], errors="coerce").dropna()
        if len(loso_values):
            loso_note = (
                f"QC 後の状態 F1 は leave-one-mouse-out の fold 間で "
                f"{loso_values.min():.4f}–{loso_values.max():.4f} の範囲にあった。"
                "これは fold 間のばらつきの範囲であり信頼区間ではない。"
            )
            source_files.append("int_loso_f1.csv")
        else:
            log("  [Table S6] int_loso_f1.csv の f1_qc_post に有効値が無いため "
                "LOSO F1 範囲注記は追加しない")

    df = pd.DataFrame(rows)
    notes = [
        "Confidence intervals are reproduced from the designated source CSV when available; "
        "they are not re-estimated in this table.",
        "Blank confidence-interval cells indicate that no CI was available in the designated "
        "source CSV.",
    ]
    if loso_note is not None:
        notes.append(loso_note)
    fmt = {c: "0.0000" for c in ["Point estimate", "95% CI lower", "95% CI upper"]}
    return Table("Table S6",
                 "Primary outcomes with 95% confidence intervals and their sources",
                 df, notes, " + ".join(source_files), fmt)


# ====================================================================== Excel 出力
_THIN = Side(style="thin", color="FF000000")
_MED = Side(style="medium", color="FF000000")


def _write_sheet(ws, t: Table, stamp: str) -> None:
    ws.cell(row=1, column=1, value=f"{t.label}. {t.title}").font = Font(
        name=FONT, size=11, bold=True)
    hdr = 3
    for j, col in enumerate(t.df.columns, start=1):
        c = ws.cell(row=hdr, column=j, value=str(col))
        c.font = Font(name=FONT, size=10, bold=True)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(top=_MED, bottom=_THIN)

    for i, (_, r) in enumerate(t.df.iterrows(), start=hdr + 1):
        for j, col in enumerate(t.df.columns, start=1):
            v = r[col]
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = None if not np.isfinite(float(v)) else float(v)
            elif pd.isna(v):
                v = None
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(name=FONT, size=10)
            c.alignment = Alignment(horizontal="center" if not isinstance(v, str) else "left")
            if col in t.formats and isinstance(v, float):
                c.number_format = t.formats[col]

    last = hdr + len(t.df)
    for j in range(1, len(t.df.columns) + 1):
        ws.cell(row=last, column=j).border = Border(bottom=_MED)

    r = last + 2
    for n in t.notes:
        cell = ws.cell(row=r, column=1, value=n)
        cell.font = Font(name=FONT, size=9)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=1, end_row=r,
                       end_column=max(2, len(t.df.columns)))
        r += 1
    prov = ws.cell(row=r + 1, column=1, value=f"Source: {t.source}  |  generated {stamp}")
    prov.font = Font(name=FONT, size=8, italic=True)

    for j, col in enumerate(t.df.columns, start=1):
        vals = [len(str(col))] + [len(str(x)) for x in t.df[col].head(60).tolist()]
        ws.column_dimensions[get_column_letter(j)].width = min(38, max(10, max(vals) + 3))
    ws.freeze_panes = ws.cell(row=hdr + 1, column=1)


def write_table(t: Table, paths: Paths, stamp: str) -> None:
    t.df.to_csv(os.path.join(paths.tables, f"{t.stem}.csv"), index=False, encoding=ENC)
    wb = Workbook()
    _write_sheet(wb.active, t, stamp)
    wb.active.title = t.sheet
    wb.save(os.path.join(paths.tables, f"{t.stem}.xlsx"))


def write_combined(tables: list[Table], paths: Paths, stamp: str) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for t in tables:
        _write_sheet(wb.create_sheet(title=t.sheet), t, stamp)
    wb.save(os.path.join(paths.tables, "all_tables.xlsx"))


# --------------------------------------------------------------- 実行環境の準備
def _init_console() -> None:
    """Windows のコンソールは既定が cp932 で日本語ログが化けるため UTF-8 に切り替える。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def _default_base():
    """引数も環境変数も無いとき、同じフォルダの config.py から BASE_DATA_DIR を借りる。

    Code Runner / IDE の実行ボタンは引数を渡せないため、そのままでも動くようにする。
    """
    v = os.environ.get("SENSORS_BASE_DATA_DIR")
    if v:
        return v
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import config as _cfg  # noqa: PLC0415
        b = getattr(_cfg, "BASE_DATA_DIR", None)
        if b and os.path.isdir(str(b)):
            return str(b)
    except Exception:  # noqa: BLE001
        pass
    return None


# ====================================================================== 実行
def main() -> int:
    _init_console()
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default=_default_base())
    ap.add_argument("--good-cut", type=float, default=0.70)
    a = ap.parse_args()
    if not a.base:
        print("データフォルダを特定できませんでした。次のいずれかで指定してください:")
        print(f'  1) 引数で渡す:  python {os.path.basename(__file__)} "C:\\Users\\...\\最新データ"')
        print("  2) 環境変数 SENSORS_BASE_DATA_DIR を設定する")
        print("  3) 同じフォルダに config.py を置く（その BASE_DATA_DIR を読みます）")
        return 1

    paths = Paths(a.base, a.good_cut)
    if not os.path.isdir(paths.inter):
        print(f"[エラー] {paths.inter} が無い")
        return 1
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    log(f"[stage2] intermediate = {paths.inter}")
    log(f"[stage2] good_cut = {a.good_cut}")

    builders = [
        ("Table 1", lambda: build_table1(paths)),
        ("Table 2", lambda: build_table2(paths)),
        ("Table 3", lambda: build_table3(paths)),
        ("Table S1", lambda: build_table_s1(paths)),
        ("Table S2", lambda: build_table_s2(paths, a.good_cut)),
        ("Table S3", lambda: build_table_s3(paths)),
        ("Table S4", lambda: build_table_s4(paths)),
        ("Table S5", lambda: build_table_s5(paths)),
        ("Table S6", lambda: build_table_s6(paths)),
    ]

    tables: list[Table] = []
    reg = []
    for label, fn in builders:
        log(f"\n[{label}]")
        try:
            t = fn()
        except Exception as e:  # noqa: BLE001
            log(f"  [失敗] {e}")
            t = None
        if t is None:
            reg.append({"label": label, "stem": label.replace(" ", ""), "kind": "table",
                        "status": "MISSING", "rows": 0, "cols": 0,
                        "output_dir": "outputs/tables", "source": "", "generated": stamp})
            continue
        write_table(t, paths, stamp)
        tables.append(t)
        log(f"  {t.df.shape[0]} 行 x {t.df.shape[1]} 列 → {t.stem}.csv / {t.stem}.xlsx")
        reg.append({"label": t.label, "stem": t.stem, "kind": "table", "status": "OK",
                    "rows": int(t.df.shape[0]), "cols": int(t.df.shape[1]),
                    "output_dir": "outputs/tables", "source": t.source, "generated": stamp})

    if tables:
        write_combined(tables, paths, stamp)
        log(f"\n[all_tables.xlsx] {len(tables)} シート")

    pd.DataFrame(reg).to_csv(
        os.path.join(paths.captions, "figure_table_registry_tables.csv"),
        index=False, encoding=ENC)

    missing = [r["label"] for r in reg if r["status"] == "MISSING"]
    log("\n=== まとめ ===")
    log(f"生成: {len(tables)} / {len(builders)}")
    if missing:
        log("[要実行] 入力CSVが無く生成できなかった表: " + ", ".join(missing))
    else:
        log("全ての表を生成しました。")
    log(f"出力先: {paths.tables}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
