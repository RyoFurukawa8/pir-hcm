"""
stage3_figures.py — 投稿用の図を生成する（v6 番号体系）

本文 (6点)
    Figure 1  システム構成と信号変換        ※(a)-(c) は著者作成の図版。本ファイルは (d) を出力
    Figure 2  24時間時系列と概日プロファイル      (a)(b)
    Figure 3  活動強度の妥当性検証                (a)(b)
    Figure 4  教師なし状態分類                    (a)(b)
    Figure 5  参照を用いない品質管理              (a)-(e)
    Figure 6  センサー間の独立性と再現性          (a)(b)

補足 (8点)
    Figure S1  PAI の分離と計算                         (a)-(f)
    Figure S2  ビン幅                                   単一
    Figure S3  GMM の設定と誤り                         (a)-(c)
    Figure S4  個体別の強度関係                         (a)-(h)
    Figure S5  QC 指標の判別性能と代数的達成可能域      (a)(b)
    Figure S6  QC の頑健性と汎化                         (a)(b)(c)
    Figure S7  QC の独立性                               (a)(b)
    Figure S8  記録長に対する安定性                      (a)(b)

    旧S6（good 定義感度）は Table S1 に一本化し、図としては廃止。
    旧S8（260702診断）・旧S9（時間分解par）は exploratory へ移動。
    旧S10（リッジライン）は削除し、全ch版を exploratory に残す。
    Fig4(a) 全ch版は exploratory の xfig_grid_pass / xfig_grid_fail として出力する。

出力
    outputs/good070/titled/main/           Fig1.png .pdf … Fig6.png .pdf
    outputs/good070/titled/supplementary/  FigS1.png .pdf … FigS8.png .pdf
    outputs/good070/titled/exploratory/    xfig_*.png .pdf
    outputs/good070/untitled/              同じ main / supplementary 構成
    outputs/good080/                       good070 と同じ titled / untitled 構成
    outputs/captions/figure_table_registry_figures.csv
    outputs/captions/figure_values_<version>.csv   ← キャプションに書く実測値

設計上の約束
  ・測定値をコードに書かない。すべて int_*.csv から読むか、その場で計算する。
  ・パネル単位で失敗を封じ込める。描けなかったパネルは理由を図中に明示し、
    ログと registry に記録する。図全体が落ちることはない。
  ・番号は FIGS / SUPP の辞書が唯一の正。ファイル名を直書きしない。

使い方
    python stage3_figures.py "C:/path/to/data"
    python stage3_figures.py "<BASE>" --versions 0.70          # 片方だけ
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from scipy.stats import norm, spearmanr  # noqa: E402

import config

ENC = "utf-8-sig"
DPI = int(getattr(config, "FIG_DPI", 600))
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": DPI,
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.bbox": None,
    # A7: Type 3 fonts (matplotlib's default for PDF/PS) are rejected by some
    # production workflows. 42 = TrueType. Appearance and values are unchanged.
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# 補足図（S1-S8）は SM の段幅 17.47 cm に合わせた原版設定で描く。
# 本文図は 13.86 cm 実寸（font.size=8 / savefig.bbox=None）。
SUPP_RC = {
    "font.size": 10,
    "axes.labelsize": "medium",
    "axes.titlesize": 11,
    "xtick.labelsize": "medium",
    "ytick.labelsize": "medium",
    "legend.fontsize": "medium",
    "savefig.bbox": "tight",
}

# A5: the display aggregation must come from config, never from a silent fallback.
# Before this, a missing config key made the whole run revert to median-of-medians
# without any message. These are validated once in main() and used everywhere.
DISPLAY_AGG_KEYS = ("DISPLAY_R_AGG", "DISPLAY_F1_AGG")


def check_display_config() -> None:
    """Fail fast when the aggregation rule is missing or unknown."""
    bad = []
    for k in DISPLAY_AGG_KEYS:
        v = getattr(config, k, None)
        if v is None:
            bad.append(f"config.{k} が未定義")
        elif str(v) not in ("mean", "median"):
            bad.append(f"config.{k}={v!r} は 'mean' / 'median' 以外")
    if bad:
        raise SystemExit(
            "[設定エラー] 集約規約を決められないため中止します:\n  "
            + "\n  ".join(bad)
            + "\n  現行の凍結値は mean-of-means 基準です。config.py に "
              "DISPLAY_R_AGG = \"mean\" / DISPLAY_F1_AGG = \"mean\" を置いてください。"
        )

# ============================================================ 番号レジストリ
FIGS = {
    "signal":      ("Figure 1", "Fig1"),
    "timeseries":  ("Figure 2", "Fig2"),
    "intensity":   ("Figure 3", "Fig3"),
    "gmm":         ("Figure 4", "Fig4"),
    "qc":          ("Figure 5", "Fig5"),
    "intersensor": ("Figure 6", "Fig6"),
}
SUPP = {
    "pai_basis":       ("Figure S1", "FigS1"),
    "bin_width":       ("Figure S2", "FigS2"),
    "gmm_spec":        ("Figure S3", "FigS3"),
    "per_mouse":       ("Figure S4", "FigS4"),
    "qc_metrics":      ("Figure S5", "FigS5"),
    "qc_robust":       ("Figure S6", "FigS6"),
    "qc_independence": ("Figure S7", "FigS7"),
    "record_length":   ("Figure S8", "FigS8"),
}
# 旧番号 -> 新番号（原稿の書き換え用）
OLD2NEW = [
    ("Figure S1 (empty-cage calibration)", "Figure S1(a)"),
    ("Figure S2 (log / frequency band)", "Figure S1(b)-(f)"),
    ("Figure S3 (bin width)", "Figure S2"),
    ("Figure S4 (seed / BIC)", "Figure S3(a)(b)"),
    ("Figure S5 (LOMO)", "Figure S6(a)-(c)"),
    ("Figure S6 (good-cut sensitivity)", "RETIRED -> Table S1"),
    ("Figure S7 (per-mouse scatter)", "Figure S4"),
    ("Figure S8 (par vs SNR)", "Figure S5(a)"),
    ("Figure S9 (error by distance)", "Figure S3(c)"),
    ("Figure S10 (record length)", "Figure S8"),
    ("Figure S11 (QC independence)", "Figure S7(a)(b)"),
    ("Figure S12 (session diagnostic)", "RETIRED -> exploratory"),
    ("Figure S13 (temporal stability)", "RETIRED -> exploratory"),
    ("(unnumbered) algebraic nar-par band", "Figure S5(b)"),
]

# ---- 配色・ハッチ規約（描画層全体で統一。以下の値は変更しない） ----
# 色の意味：
#   赤 C_MAIN       採用した条件／PIR・PAI 由来の実測データ／active 状態
#   紺 C_CTRL_NAVY  意味のある比較相手（NanoTag 参照・rest・全体集合・保守的変種）
#                   ／NanoTag との突き合わせの結果（F1・誤り率・r）
#   灰 C_CTRL_GRAY  期待値ゼロ・退けたもの・不活性なもの
#                   （帰無対照・不採用条件・空ケージ・QC 不合格）
#   橙 C_ACCENT     FigS6(a) と exploratory 限定。本文・補足図の他所では使わない
# 単一系列パネル：対比相手がいない場合、プロットしている量が
#   PIR そのもの（PAI・par）なら赤、NanoTag との突き合わせの結果（F1・誤り率・r）なら紺
#   （前例：FigS8(a) par=赤 / FigS8(b) F1=紺）。
# ハッチ（棒グラフのみ）：色に連動。赤＝無地(None)／紺＝"//"／灰＝"xx"。
#   同一パネル内に系列が1つしか無い棒グラフにはハッチを付けない。
# Fig5(e) は内訳パネル（1つの量を2分割）のため、比較の色語彙を使わず
#   白地＋黒縁＋ハッチのみで描く。
C_MAIN = "#c0392b"
C_CTRL_NAVY = "#1f4e79"
C_CTRL_GRAY = "#9aa0a6"
C_ACCENT = "#e08214"
H_MAIN, H_NAVY, H_GRAY, H_ACCENT = None, "//", "xx", "\\\\"
HATCH_CTRL = ["//", "\\\\", "xx", "--", "||", "++", "//\\\\"]  # exploratory 専用（本文・補足図では未使用）

# legacy stage2:138 と同一。S6(a)-(c) の y 軸を広めに固定して小差を誇張しない。
S5_YLIM = {"a": (0.20, 0.40), "b": (0.88, 0.96), "c": (0.55, 0.90)}

# legacy stage2:132-144 と同一。render_state_gmm_panel / get_bimodal_candidates が参照する。
FIG4_XSD_PAD = 3.0        # x を各GMM成分の mean ± この係数 * sd まで広げて裾を見せる
FIG4_XMARGIN_FRAC = 0.04  # さらに x 幅のこの割合を左右のマージンにする
FIG4_N_CANDIDATES = 10


# ==================================================================== 基盤
class Ctx:
    def __init__(self, base: str, good_cut: float, titled: bool = True, collect: bool = True):
        tag = f"{int(round(good_cut * 100)):03d}"
        self.good_cut = float(good_cut)
        self.version = f"good{tag}"
        self.titled = bool(titled)
        self.collect = bool(collect)
        self.mode = "titled" if self.titled else "untitled"
        self.root = os.path.join(base, "paper_pipeline_outputs")
        self.inter = os.path.join(self.root, f"intermediate__{self.version}")
        out = os.path.join(self.root, "outputs")
        self.mode_root = os.path.join(out, self.version, self.mode)
        self.main = os.path.join(self.mode_root, "main")
        self.supp = os.path.join(self.mode_root, "supplementary")
        self.contact = os.path.join(self.mode_root, "contact_sheets")
        # A2: X figures. Diagnostic material that is deliberately NOT part of the
        # submission. Kept out of main/ and supplementary/ so it can never be
        # picked up by the contact sheets or mistaken for a numbered figure.
        self.explore = os.path.join(self.mode_root, "exploratory")
        self.captions = os.path.join(out, "captions")
        for d in (self.main, self.supp, self.contact, self.explore, self.captions):
            os.makedirs(d, exist_ok=True)
        self._cache: dict[str, pd.DataFrame | None] = {}
        self.registry: list[dict] = []
        self.values: list[dict] = []
        self.log_lines: list[str] = []

    def log(self, m: str) -> None:
        if not self.collect:
            return
        print(m, flush=True)
        self.log_lines.append(m)

    def load(self, name: str) -> pd.DataFrame | None:
        if name in self._cache:
            return self._cache[name]
        p = os.path.join(self.inter, name)
        d = None
        if os.path.exists(p):
            try:
                d = pd.read_csv(p, encoding=ENC)
                if not len(d):
                    d = None
            except Exception as e:  # noqa: BLE001
                self.log(f"    [読込失敗] {name}: {e}")
                d = None
        self._cache[name] = d
        return d

    def need(self, name: str, cols: list[str]) -> pd.DataFrame:
        d = self.load(name)
        if d is None:
            raise LookupError(f"{name} が無い")
        miss = [c for c in cols if c not in d.columns]
        if miss:
            raise LookupError(f"{name} に列が無い: {miss}")
        return d

    def value(self, key: str, val, note: str = "") -> None:
        if not self.collect:
            return
        self.values.append({"version": self.version, "key": key, "value": val, "note": note})


def fix_ylim(ax, lo, hi, values, tag):
    """Apply a fixed display range, widening it whenever real data would fall outside."""
    v = np.asarray(
        [x for x in np.ravel(np.asarray(values, dtype=float)) if np.isfinite(x)],
        dtype=float,
    )
    lo2, hi2 = float(lo), float(hi)
    if v.size:
        pad = 0.01
        lo2 = min(lo2, float(v.min()) - pad)
        hi2 = max(hi2, float(v.max()) + pad)
    if (lo2 < lo) or (hi2 > hi):
        # Display-only diagnostic; measured values are not altered.
        print(
            f"  [ylim] {tag}: data outside [{lo:.2f}, {hi:.2f}] -> "
            f"widened to [{lo2:.3f}, {hi2:.3f}]",
            flush=True,
        )
    ax.set_ylim(lo2, hi2)


def zero_baseline(ax, values=None, pad_frac=0.08, top_extra=0.0):
    """Bars start at zero and the visible y-axis always includes the zero baseline."""
    lo, hi = 0.0, 0.0
    try:
        dl = ax.dataLim
        if np.isfinite(dl.y0):
            lo = min(lo, float(dl.y0))
        if np.isfinite(dl.y1):
            hi = max(hi, float(dl.y1))
    except Exception:
        pass
    if values is not None:
        v = np.asarray(
            [x for x in np.ravel(np.asarray(values, dtype=float)) if np.isfinite(x)],
            float,
        )
        if v.size:
            lo = min(lo, float(v.min()))
            hi = max(hi, float(v.max()))
    span = max(hi - lo, 1e-9)
    ax.set_ylim(
        lo - (pad_frac * span if lo < 0 else 0.0),
        hi + (pad_frac + top_extra) * span,
    )
    ax.axhline(0, color="black", lw=0.7, zorder=1)


def bar_dots(
    ax, groups, colors, hatches=None, err="sd", center="median", zero_base=True
):
    """Stage2-style zero-based bars with black edges, uncertainty, and individual dots."""
    seen = []
    for i, grp in enumerate(groups):
        vals = np.asarray(grp.get("values", []), float)
        vals = vals[np.isfinite(vals)]
        if grp.get("value") is not None and np.isfinite(float(grp["value"])):
            cval = float(grp["value"])
        else:
            cval = (
                (float(np.mean(vals)) if center == "mean" else float(np.median(vals)))
                if len(vals)
                else np.nan
            )
        color = colors[i % len(colors)]
        hatch = hatches[i % len(hatches)] if hatches else None
        if err == "ci" and grp.get("ci") is not None:
            lo, hi = grp["ci"]
            yerr = [[max(cval - lo, 0)], [max(hi - cval, 0)]]
        elif err == "iqr" and len(vals) > 1:
            q1, q3 = np.percentile(vals, [25, 75])
            yerr = [[max(cval - q1, 0)], [max(q3 - cval, 0)]]
        elif len(vals) > 1:
            sd = float(np.std(vals, ddof=1))
            yerr = [[sd], [sd]]
        else:
            yerr = [[0], [0]]
        ax.bar(
            i,
            cval,
            bottom=0,
            color=color,
            hatch=hatch,
            edgecolor="black",
            linewidth=0.6,
            yerr=yerr,
            capsize=3,
            ecolor="black",
            alpha=0.88,
            zorder=2,
            width=0.62,
        )
        seen.append(cval)
        seen.extend([cval - yerr[0][0], cval + yerr[1][0]])
        if len(vals):
            xs = np.random.default_rng(0).normal(i, 0.05, len(vals))
            ax.scatter(
                xs,
                vals,
                s=16,
                color="black",
                alpha=0.55,
                zorder=3,
                edgecolor="white",
                linewidth=0.3,
            )
            seen.extend(list(vals))
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g["label"] for g in groups])
    if zero_base:
        zero_baseline(ax, seen)


def _panelize_title(fig):
    """In untitled mode, strip descriptive titles and put the panel letter back.

    A3: the letter now comes from the identity each panel was created with
    (recorded on the axes by draw() / fail_panel()), not from the order of the
    axes that happened to survive. Two failure modes are removed:
      * an inset (Fig3(b)'s mismatched-pair histogram, before A2) was counted as
        a panel and received its own letter;
      * a panel that failed calls ax.axis("off"), which dropped it from the
        count, so every later panel's letter shifted up by one and no longer
        matched the caption.
    Titles still render on an axis-off panel, so a failed panel keeps its letter.
    """
    st = getattr(fig, "_suptitle", None)
    if st is not None:
        st.set_text("")

    lettered = [ax for ax in fig.axes if getattr(ax, "_stage3_letter", "")]
    if lettered:
        for ax in fig.axes:
            lab = getattr(ax, "_stage3_letter", "")
            ax.set_title(f"({lab})" if lab else "")
        return

    def _real_axes(f):
        boxes, out = [], []
        for ax in f.axes:
            if (not ax.get_visible()) or (not ax.axison):
                continue
            bb = ax.get_position()
            box = (round(bb.x0, 3), round(bb.y0, 3), round(bb.width, 3), round(bb.height, 3))
            if box in boxes:
                continue
            boxes.append(box)
            out.append(ax)
        return out

    real = _real_axes(fig)
    if len(real) <= 1:
        for ax in fig.axes:
            ax.set_title("")
        return

    letters = "abcdefghijklmnopqrstuvwxyz"
    real_set = set(id(a) for a in real)
    idx = 0
    for ax in fig.axes:
        if id(ax) not in real_set:
            ax.set_title("")
            continue
        ax.set_title(f"({letters[idx]})" if idx < len(letters) else "")
        idx += 1


def fail_panel(ax, letter: str, reason: str) -> None:
    ax.clear()
    ax.axis("off")
    ax._stage3_letter = str(letter or "")  # A3: keep the letter even when the panel fails
    # Figure text is ASCII-only to prevent missing-glyph artifacts in submission figures.
    safe = "".join(c if ord(c) < 128 else "?" for c in str(reason))[:120]
    ax.text(0.5, 0.5, f"[NOT AVAILABLE]\n{safe}", ha="center", va="center",
            fontsize=8, color=C_MAIN, wrap=True, transform=ax.transAxes)


def draw(ctx: Ctx, ax, letter: str, fn) -> bool:
    """1パネルを描く。失敗しても図全体を落とさず、理由をパネルに残す。"""
    ax._stage3_letter = str(letter or "")  # A3: untitled 版の採番はこの値で固定する
    try:
        fn(ax)
        return True
    except Exception as e:  # noqa: BLE001
        ctx.log(f"    ({letter}) 描画できず: {e}")
        fail_panel(ax, letter, str(e))
        return False


def save(ctx: Ctx, fig, key: str, supp: bool, n_ok: int, n_total: int,
         note: str = "", panel_letter: str | None = None) -> None:
    label, stem = (SUPP if supp else FIGS)[key]
    outdir = ctx.supp if supp else ctx.main
    if panel_letter is not None:
        if not ctx.titled:
            st = getattr(fig, "_suptitle", None)
            if st is not None:
                st.set_text("")
        fig.text(0.005, 0.995, panel_letter, ha="left", va="top",
                 fontsize=12, fontweight="bold")
    elif not ctx.titled:
        _panelize_title(fig)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(outdir, f"{stem}.{ext}"), dpi=DPI,
                    facecolor="white")
    plt.close(fig)
    status = "OK" if n_ok == n_total else ("PARTIAL" if n_ok else "FAILED")
    ctx.registry.append({
        "version": ctx.version, "mode": ctx.mode, "label": label, "stem": stem,
        "kind": "supplementary" if supp else "main",
        "panels_total": n_total, "panels_ok": n_ok, "status": status,
        "output_dir": os.path.relpath(outdir, ctx.root), "note": note,
    })
    ctx.log(f"  {label:12s} -> {stem}.png/.pdf   panels {n_ok}/{n_total}  [{status}]")


def rest_reference_mu(ctx: Ctx) -> tuple[pd.DataFrame | None, str]:
    """B1: per-channel PAI location of the reference (NanoTag-labelled) rest bins.

    stage1 computes this as nano_rest_mu / nano_rest_mu_mean and _gmm_params()
    (stage1:3204-3229) writes it into int_gmm_params.csv as nano_mu / nano_mu_mean.
    But _make_common_diagnostics() (stage1:4027-4049) rewrites the SAME file
    afterwards with a row dict that has no nano_mu, and run_one() always calls it
    after the heavy pass (stage1:4693). The column is therefore absent on disk for
    every good_cut, which is why Fig4(b) failed and why legacy stage2's fig4_diff_med_all
    was never produced either. Re-running stage1 does not fix it.

    The definition is reconstructed exactly instead: nano_rest_mu is the median of
    the PAI values of bins with nano_label == 0 (stage1:1406-1417), taken over
    sq["bins"] -- the identical, unsubsampled set that int_state_hist.csv stores
    row by row (stage1:1391-1401). Returns (df[ch, nano_mu, nano_mu_mean,
    n_rest_bins], source-label).
    """
    gp = ctx.load("int_gmm_params.csv")
    if gp is not None and {"ch", "comp", "nano_mu"}.issubset(gp.columns):
        r = gp[gp["comp"].astype(str) == "rest"].copy()
        if r["nano_mu"].notna().any():
            out = pd.DataFrame({
                "ch": r["ch"].astype(str),
                "nano_mu": pd.to_numeric(r["nano_mu"], errors="coerce"),
                "nano_mu_mean": (pd.to_numeric(r["nano_mu_mean"], errors="coerce")
                                 if "nano_mu_mean" in r.columns else np.nan),
                "n_rest_bins": np.nan,
            })
            return out, "int_gmm_params.csv (nano_mu 列が存在)"

    sh = ctx.load("int_state_hist.csv")
    if sh is None or not {"ch", "log_lp_var", "nano_label"}.issubset(sh.columns):
        return None, "再構成不可（int_state_hist.csv が無い/列不足）"
    d = sh.copy()
    d["_v"] = pd.to_numeric(d["log_lp_var"], errors="coerce")
    d["_y"] = pd.to_numeric(d["nano_label"], errors="coerce")
    d = d[(d["_y"] == 0) & d["_v"].notna()]
    if not len(d):
        return None, "再構成不可（nano_label==0 の行が無い）"
    g = d.groupby(d["ch"].astype(str))["_v"]
    out = pd.DataFrame({
        "nano_mu": g.median(),
        "nano_mu_mean": g.mean(),
        "n_rest_bins": g.size(),
    }).reset_index().rename(columns={"ch": "ch"})
    out["ch"] = out["ch"].astype(str)
    return out, "int_state_hist.csv から再構成（stage1 の nano_rest_mu と同一定義）"


def save_explore(ctx: Ctx, fig, stem: str, note: str = "") -> None:
    """A2: save an X (exploratory) figure. Not a numbered figure, not on the
    contact sheets, never submitted. Registered so its existence is traceable."""
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(ctx.explore, f"{stem}.{ext}"), dpi=DPI,
                    facecolor="white")
    plt.close(fig)
    ctx.registry.append({
        "version": ctx.version, "mode": ctx.mode, "label": stem, "stem": stem,
        "kind": "exploratory", "panels_total": 1, "panels_ok": 1, "status": "OK",
        "output_dir": os.path.relpath(ctx.explore, ctx.root), "note": note,
    })
    ctx.log(f"  {stem:12s} -> exploratory/{stem}.png/.pdf   [X figure, not submitted]")


class RecordLabeler:
    """Map raw record ids (recording dates such as 260626) to neutral display
    labels (Record 1..N) in chronological order. Dates identify when the data
    were taken, which is not information a reader needs in an axis tick, and
    they read as if the date itself were a variable. The raw ids stay in the
    CSVs and in the log so the mapping is always recoverable."""

    def __init__(self):
        self._map = {}

    def fit(self, ids) -> "RecordLabeler":
        for rid in sorted({str(x) for x in ids if str(x) not in ("", "nan")}):
            if rid not in self._map:
                self._map[rid] = f"Record {len(self._map) + 1}"
        return self

    def rec(self, rid) -> str:
        return self._map.get(str(rid), str(rid))

    def ch(self, ch_id) -> str:
        """260706_ch5 -> R4-ch5. Falls back to the raw id when it does not parse."""
        s = str(ch_id)
        if "_" not in s:
            return s
        head, tail = s.split("_", 1)
        lab = self._map.get(head)
        if lab is None:
            return s
        return f"R{lab.split()[-1]}-{tail}"

    def legend_note(self) -> str:
        return "; ".join(f"{v} = {k}" for k, v in self._map.items())


def repr_ch(ctx: Ctx, attr: str, default_key: str) -> str:
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import config as _cfg  # noqa: PLC0415
        v = getattr(_cfg, attr, None)
        if v:
            return str(v)
    except Exception:  # noqa: BLE001
        pass
    d = ctx.load("int_channel.csv")
    if d is not None and "ch" in d.columns:
        return str(sorted(d["ch"].astype(str))[0])
    raise LookupError(f"代表ch を決められない ({default_key})")


def pick_col(d: pd.DataFrame, candidates: list[str], what: str) -> str:
    """実在する列名を候補から選ぶ。stage1 の列名が版によって揺れるための保険。"""
    for c in candidates:
        if c in d.columns:
            return c
    raise LookupError(f"{what} の列が無い（候補: {', '.join(candidates)}）")


def pick_file(ctx: "Ctx", candidates: list[str]) -> pd.DataFrame:
    for n in candidates:
        d = ctx.load(n)
        if d is not None:
            return d
    raise LookupError(f"次のいずれも無い: {', '.join(candidates)}")


def spearman(x, y) -> float:
    a = pd.Series(np.asarray(x, float))
    b = pd.Series(np.asarray(y, float))
    ok = a.notna() & b.notna()
    if ok.sum() < 3:
        return float("nan")
    return float(a[ok].rank().corr(b[ok].rank()))


def med(s):
    s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
    return float(s.median()) if len(s) else np.nan

def permouse_mean(df, col, by="mouse_id"):
    return df.groupby(by)[col].mean()

def permouse_median(df, col, by="mouse_id"):
    return df.groupby(by)[col].median()

def safe_group_series(
    df, key_col, value_col, index_order=None, fallback_map=None, agg="median"
):
    """groupby-based aggregation is inherently duplicate-safe (never raises
    'cannot reindex on an axis with duplicate labels'). agg selects median/mean."""
    if df is None or df.empty:
        s = pd.Series(dtype=float)
    else:
        s = df.groupby(key_col)[value_col].agg(agg)
    if fallback_map:
        for miss, src in fallback_map.items():
            if miss not in s.index and src in s.index:
                s[miss] = s[src]
    if index_order is not None:
        s = s.reindex(index_order)
    return s

def center_ylim(ctx: Ctx, ax, lo, hi, values, tag):
    """Like fix_ylim but CENTERS the plotted data within a window of the same
    width as [lo, hi] (keeps the anti-exaggeration width; places data mid-panel).
    Widens symmetrically if the data span exceeds that width; never clips a datum."""
    v = np.asarray(
        [x for x in np.ravel(np.asarray(values, dtype=float)) if np.isfinite(x)],
        dtype=float,
    )
    if v.size:
        pad = 0.01
        width = max(float(hi) - float(lo), float(v.max()) - float(v.min()) + 2 * pad)
        center = 0.5 * (float(v.min()) + float(v.max()))
        lo2, hi2 = center - width / 2.0, center + width / 2.0
    else:
        lo2, hi2 = float(lo), float(hi)
    ax.set_ylim(lo2, hi2)
    ctx.log(f"  [ylim] {tag}: centered window [{lo2:.3f}, {hi2:.3f}]")

def agglabel(center):
    """Human-readable aggregation name for titles/logs (never hardcode 'median')."""
    return "mean" if str(center) == "mean" else "median"

def wilson_ci(k, n, z=1.96):
    """#3: Wilson score interval for a binomial proportion k/n (matches Methods 2.7.2)."""
    if n is None or n <= 0 or k is None or not np.isfinite(k):
        return (np.nan, np.nan, np.nan)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (float(p), float(max(0.0, centre - half)), float(min(1.0, centre + half)))

def get_threshold(ctx: Ctx, chan):
    lt = ctx.load("int_loso_thr.csv")
    if lt is not None and "qc1_threshold" in lt and len(lt):
        return float(lt["qc1_threshold"].mean())
    if chan is not None:
        p = chan[chan["qc1_pass"] == 1]["pir_active_rate"]
        f = chan[chan["qc1_pass"] == 0]["pir_active_rate"]
        if len(p) and len(f):
            return float((p.min() + f.max()) / 2)
    return np.nan

def ci_of(ctx: Ctx, metric):
    ci = ctx.load("int_bootstrap_ci.csv")
    if ci is None:
        return None
    row = ci[ci["metric"] == metric]
    if len(row):
        r = row.iloc[0]
        return float(r["point"]), float(r["ci_lower"]), float(r["ci_upper"])
    return None

def auc_of(ctx: Ctx, metric, thr=None):
    qc = ctx.load("int_qc_corr.csv")
    if qc is None:
        return np.nan
    thr = ctx.good_cut if thr is None else thr
    row = qc[(qc["qc_metric"] == metric) & (np.isclose(qc["f1_thr"], thr))]
    return float(row.iloc[0]["auc"]) if len(row) else np.nan

def get_repr_ch(ctx: Ctx, chan):
    """Fig2/Fig4's representative channel. config.REPR_CH is authoritative (pinned)."""
    rc = str(getattr(config, "REPR_CH", "") or "").strip()
    if rc and (chan["ch"] == rc).any():
        return rc
    passed = chan[(chan["F1_state"] >= ctx.good_cut) & (chan["qc1_pass"] == 1)].dropna(
        subset=["bimodality_coef"]
    )
    if len(passed) == 0:
        passed = chan.dropna(subset=["bimodality_coef"])
    if len(passed) == 0:
        return chan["ch"].iloc[0]
    return passed.loc[passed["bimodality_coef"].idxmax(), "ch"]

def get_bimodal_candidates(ctx: Ctx, chan, n=5):
    """Top-n channels by bimodality_coef among good, QC-pass channels (deterministic)."""
    passed = chan[(chan["F1_state"] >= ctx.good_cut) & (chan["qc1_pass"] == 1)].dropna(
        subset=["bimodality_coef"]
    )
    if passed.empty:
        return []
    return list(passed.sort_values("bimodality_coef", ascending=False)["ch"].head(n))

def qc_status_of(ctx: Ctx, chan, ch, thr=None):
    """QC status of one channel, straight from int_channel.csv. Returns a dict + a short label."""
    row = chan[chan["ch"].astype(str) == str(ch)]
    if row.empty:
        return None
    r = row.iloc[0]
    par_ok = int(r.get("qc1_pass", 0)) == 1
    multi_ok = (
        int(r.get("qc1_pass_multi", 0)) == 1
        if "qc1_pass_multi" in row.columns
        else None
    )
    good = float(r.get("F1_state", np.nan)) >= ctx.good_cut
    parts = [f"QC par-only: {'PASS' if par_ok else 'FAIL'}"]
    if multi_ok is not None:
        parts.append(f"multi: {'PASS' if multi_ok else 'FAIL'}")
    parts.append(
        f"F1={float(r.get('F1_state', np.nan)):.2f} ({'good' if good else 'not good'})"
    )
    parts.append(f"par={float(r.get('pir_active_rate', np.nan)):.3f}")
    if thr is not None and np.isfinite(thr):
        parts.append(f"thr={thr:.3f}")
    return {
        "ch": str(ch),
        "mouse_id": r.get("mouse_id", "?"),
        "F1_state": float(r.get("F1_state", np.nan)),
        "is_good": int(bool(good)),
        "pir_active_rate": float(r.get("pir_active_rate", np.nan)),
        "qc1_threshold": float(thr) if thr is not None else np.nan,
        "qc1_pass": int(par_ok),
        "qc1_pass_multi": int(multi_ok) if multi_ok is not None else np.nan,
        "snr": float(r.get("snr", np.nan)),
        "gmm_separation": float(r.get("gmm_separation", np.nan)),
        "bimodality_coef": float(r.get("bimodality_coef", np.nan)),
        "label": "  |  ".join(parts),
    }

def center_of(vals, center="mean"):
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return np.nan
    return float(np.mean(v)) if center == "mean" else float(np.median(v))

def _mouse_sort_key(idx):
    """Sort mouse_1 ... mouse_10 numerically, not lexicographically."""
    import pandas as _pd
    return _pd.Index([int(m.group()) if (m := re.search(r"\d+", str(v))) else 10**9
                      for v in idx])


def _mouse_label(value) -> str:
    """Display mouse_1 / mouse 1 as publication-facing 'Mouse 1'."""
    s = str(value)
    m = re.fullmatch(r"mouse[_\s-]*(\d+)", s, flags=re.IGNORECASE)
    return f"Mouse {int(m.group(1))}" if m else s


def _clean_mode_outputs(ctx: Ctx) -> int:
    """Remove stale generated outputs only; never touch intermediate/input data."""
    deleted = 0
    for root in (ctx.main, ctx.supp, ctx.explore, ctx.contact):
        os.makedirs(root, exist_ok=True)
        for name in os.listdir(root):
            p = os.path.join(root, name)
            if os.path.isdir(p) and not os.path.islink(p):
                shutil.rmtree(p)
                deleted += 1
            else:
                os.remove(p)
                deleted += 1
    print(f"  [cleanup] {ctx.version}/{ctx.mode}: deleted {deleted} stale output item(s)", flush=True)
    return deleted


def _json_clean(obj):
    """Recursively make a JSON-safe object; non-finite numbers become null."""
    if isinstance(obj, dict):
        return {str(k): _json_clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if np.isfinite(v) else None
    if isinstance(obj, (np.integer, int)) and not isinstance(obj, bool):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if obj is None or isinstance(obj, (str, int)):
        return obj
    return str(obj)


def _ctx_value_map(ctx: Ctx) -> dict:
    return {str(r.get("key")): r.get("value") for r in ctx.values}


def _panel(panel, what, x, y, n, values=None, reference_lines=None, notes=None, source_files=None):
    return {
        "panel": panel,
        "what": what,
        "x": x,
        "y": y,
        "n": n,
        "values": values or {},
        "reference_lines": reference_lines or [],
        "notes": notes or [],
        "source_files": source_files or [],
    }


def write_caption_payload(ctx: Ctx) -> str:
    """Write caption_payload_<version>.json for the untitled submission figures."""
    chan = ctx.load("int_channel.csv")
    binned = ctx.load("int_binned.csv")
    vals = _ctx_value_map(ctx)
    n_mice = int(chan["mouse_id"].nunique()) if chan is not None and "mouse_id" in chan else None
    n_ch = int(chan["ch"].nunique()) if chan is not None and "ch" in chan else None
    n_bins = int(len(binned)) if binned is not None else None
    base_n = {"mice": n_mice, "channels": n_ch, "bins": n_bins}

    thr = get_threshold(ctx, chan) if chan is not None else np.nan
    qcc = ctx.load("int_qc_corr.csv")
    metric_label = {
        "gmm_separation": "GMM separation",
        "snr": "SNR",
        "floor_rate": "Floor rate",
        "pir_active_rate": "PIR active rate",
    }
    auc_raw = {}
    if qcc is not None and {"qc_metric", "f1_thr", "auc"}.issubset(qcc.columns):
        qq = qcc[np.isclose(pd.to_numeric(qcc["f1_thr"], errors="coerce"), ctx.good_cut)]
        for _, r in qq.iterrows():
            k = metric_label.get(str(r["qc_metric"]), str(r["qc_metric"]).replace("_", " "))
            v = float(r["auc"]) if pd.notna(r["auc"]) else np.nan
            if np.isfinite(v):
                auc_raw[k] = v
    auc_display = {k: round(v, 2) for k, v in auc_raw.items()}

    holdout = ctx.load("int_holdout_f1.csv")
    holdout_n = None
    if holdout is not None and "holdout_f1" in holdout.columns:
        holdout_n = int(pd.to_numeric(
            holdout["holdout_f1"], errors="coerce").notna().sum())
    holdout_notes = (
        [f"Mean is calculated over {holdout_n} evaluable folds."]
        if holdout_n is not None
        else ["[MISSING] Evaluable-fold count could not be determined from int_holdout_f1.csv."]
    )

    _agg_f1 = str(getattr(config, "DISPLAY_F1_AGG", "mean"))
    metric_f1 = "F1_qc1_mean" if _agg_f1 == "mean" else "F1_qc1_median_of_medians"
    ci_qc = ci_of(ctx, metric_f1)
    operational_f1 = ci_qc[0] if ci_qc else None
    if operational_f1 is not None and not np.isfinite(operational_f1):
        operational_f1 = None
    if operational_f1 is None:
        ctx.log(f"    [MISSING] FigS6(c) payload: {metric_f1} in int_bootstrap_ci.csv")

    fig5b_notes = ["GMM separation is an inverse discriminator when AUC < 0.5."]
    _gmm_inv = vals.get("fig5b_auc_gmm_separation_inverted")
    try:
        _gmm_inv = float(_gmm_inv)
    except (TypeError, ValueError):
        _gmm_inv = np.nan
    if np.isfinite(_gmm_inv):
        fig5b_notes.append(
            f"Inverted GMM separation AUC (1 - observed AUC) = {_gmm_inv:.4f}."
        )

    def f1_value(key):
        v = vals.get(key)
        try:
            fv = float(v)
            return round(fv, 2) if np.isfinite(fv) else None
        except Exception:
            return v

    figures = []
    figures.append({"id": "Fig1", "panels": [
        _panel("c", "Raw PIR voltage and the 1-Hz low-pass-filtered signal for active, rest, and empty-box windows.",
               "Time (s)", "PIR signal", base_n,
               notes=["Panels (a)(b) are author-supplied assets; stage3 generates panel (c)."],
               source_files=["int_raw_trace.csv"])]})
    figures.append({"id": "Fig2", "panels": [
        _panel("a", "Representative 24-h PAI and NanoTag activity time series.", "Time of day (h)", "PAI / NanoTag activity", base_n,
               notes=["Grey shading denotes the dark phase (20:00–08:00)."], source_files=["int_repr_24h.csv", "int_channel.csv"]),
        _panel("b", "Normalized circadian profiles of PIR and NanoTag activity.", "Time of day (h)", "Normalized activity", base_n,
               values={"circadian r": vals.get("fig2_circadian_r")},
               notes=["Grey shading denotes the dark phase (20:00–08:00)."], source_files=["int_circadian.csv"]),
    ]})
    figures.append({"id": "Fig3", "panels": [
        _panel("a", "Relationship between PAI and NanoTag activity across 10-min bins; the reported intensity r is aggregated at mouse level.", "PAI", "NanoTag activity", base_n,
               values={"intensity r and 95% CI": vals.get("fig3_intensity_r_ci")}, source_files=["int_binned.csv", "int_bootstrap_ci.csv"]),
        _panel("b", "Specificity controls for the intensity relationship.", "Control series", "Spearman r", base_n,
               reference_lines=[{"y": 0.0, "meaning": "zero correlation"}], source_files=["int_channel.csv"]),
    ]})
    figures.append({"id": "Fig4", "panels": [
        _panel("a", "PAI histogram and two-component GMM for the representative channel, with reference-labelled rest bins.", "PAI", "Count or density", base_n,
               notes=["Dashed/dotted vertical lines identify GMM-estimated and empirical reference rest μ where available."], source_files=["int_state_hist.csv", "int_gmm_params.csv", "int_channel.csv"]),
        _panel("b", "Absolute agreement between GMM rest μ and reference rest μ across channels.", "Absolute difference in rest μ (PAI)", "Channels (n)", base_n,
               values={"median absolute difference": vals.get("fig4_abs_rest_mean_diff_median_meanref")}, source_files=["int_gmm_params.csv", "int_state_hist.csv"]),
    ]})
    figures.append({"id": "Fig5", "panels": [
        _panel("a", "Channel PIR active rate (par) versus state F1, showing the operational QC threshold.", "PIR active rate (par)", "State F1", base_n,
               values={"QC threshold": round(float(thr), 3) if np.isfinite(thr) else None},
               reference_lines=[{"x": round(float(thr), 3) if np.isfinite(thr) else None, "meaning": "QC threshold"}, {"y": round(ctx.good_cut, 2), "meaning": "good-channel threshold"}],
               source_files=["int_channel.csv", "int_loso_thr.csv"]),
        _panel("b", "AUC of four channel-level metrics for predicting good channels (F1 ≥ 0.70).", "Metric", "AUC", base_n,
               values=auc_display, reference_lines=[{"y": 0.5, "meaning": "chance level"}],
               notes=fig5b_notes, source_files=["int_qc_corr.csv"]),
        _panel("c", "State F1 before and after reference-free QC at the mouse aggregation level.", "QC group", "State F1", base_n,
               values={"all": vals.get("fig5c_f1_all"), "QC pass": vals.get("fig5c_f1_qc")}, source_files=["int_channel.csv", "int_bootstrap_ci.csv"]),
        _panel("d", "Confusion matrix for the par-only QC rule against the good-channel definition.", "Good / not good", "QC pass / fail", base_n,
               values={"confusion": vals.get("fig5_confusion")}, source_files=["int_qc_confusion.csv"]),
        _panel("e", "Composition of state-classification errors as false negatives and false positives.", "Error type", "Share of errors (%)", base_n,
               values={"FN share (%)": vals.get("fig5_fn_share_pct")}, source_files=["int_state_confusion_perch.csv", "int_error_summary.csv"]),
    ]})
    figures.append({"id": "Fig6", "panels": [
        _panel("a", "Agreement between paired independent PIR sensors within mouse.", "Sensor A (PAI)", "Sensor B (PAI)", base_n,
               reference_lines=[{"meaning": "identity line", "relation": "y = x"}], source_files=["int_binned.csv", "int_sensor_consistency_permouse.csv"]),
        _panel("b", "Test-retest agreement of intensity r between sensor sets A and B.", "Intensity r, sensor set A", "Intensity r, sensor set B", base_n,
               reference_lines=[{"meaning": "identity line", "relation": "y = x"}], source_files=["int_sensor_swap.csv"]),
    ]})

    figures.append({"id": "FigS1", "panels": [
        _panel("a", "PAI distributions for empty box, occupied rest, and occupied active calibration states.", "PAI", "Density", base_n, source_files=["int_calibration.csv"]),
        _panel("b", "Effect of log transformation on intensity r.", "Feature", "Intensity r", base_n, source_files=["int_feature_bench.csv", "int_feature_bench_perch.csv"]),
        _panel("c", "Effect of log transformation on state F1.", "Feature", "State F1", base_n, source_files=["int_state_feature_bench.csv"]),
        _panel("d", "Intensity r across frequency bands.", "Frequency band", "Intensity r", base_n, source_files=["int_freqband_bench.csv"]),
        _panel("e", "State F1 across frequency bands.", "Frequency band", "State F1", base_n, source_files=["int_freqband_bench.csv"]),
        _panel("f", "Sensitivity to the low-pass cutoff used to construct PAI.", "LPF cutoff (Hz)", "State F1 / intensity r", base_n, source_files=["int_lpf_sweep_agg.csv"]),
    ]})
    figures.append({"id": "FigS2", "panels": [
        _panel("", "Sensitivity of state F1 and intensity r to analysis bin size.", "Bin size (s)", "State F1 / intensity r", base_n,
               reference_lines=[{"x": 60, "meaning": "state operating point (60 s)"}, {"x": 600, "meaning": "intensity operating point (600 s)"}], source_files=["int_bin_sweep_agg.csv"]),
    ]})
    figures.append({"id": "FigS3", "panels": [
        _panel("a", "GMM component stability across random seeds.", "Random seed", "GMM component mean", base_n, source_files=["int_seed_stability.csv"]),
        _panel("b", "BIC across candidate GMM component counts.", "Number of GMM components (K)", "BIC", base_n, source_files=["int_gmm_bic.csv", "int_gmm_bic_elbow.csv"]),
        _panel("c", "Classification error versus standardized distance from the GMM decision boundary.", "Distance from boundary (SD)", "Error rate", base_n,
               notes=["Distance is expressed in side-specific component SD units."], source_files=["int_error_bydist_perch.csv"]),
    ]})

    s4_panels = []
    mids = []
    if binned is not None and "mouse_id" in binned.columns:
        mids = sorted(binned["mouse_id"].astype(str).unique())
    for i, mid in enumerate(mids[:8]):
        letter = "abcdefgh"[i]
        s4_panels.append(_panel(letter, "Within-mouse PAI versus NanoTag activity; displayed r uses the same channel-wise estimator as Table 2.", "PAI", "NanoTag activity", base_n,
                                notes=[f"Panel ({letter}) corresponds to {_mouse_label(mid)} (raw id: {mid})."], source_files=["int_binned.csv", "int_channel.csv"]))
    figures.append({"id": "FigS4", "panels": s4_panels})
    figures.append({"id": "FigS5", "panels": [
        _panel("a", "ROC curves for available channel-level QC metrics with defined AUC.", "False positive rate", "True positive rate", base_n,
               reference_lines=[{"meaning": "chance line", "relation": "y = x"}], notes=["A metric with undefined AUC is omitted rather than displayed as NaN."], source_files=["int_channel.csv", "int_auc_metrics_cluster.csv"]),
        _panel("b", "Algebraic feasibility band linking NanoTag active rate and par for the good-channel F1 definition.", "NanoTag active rate", "par (PIR active rate)", base_n,
               notes=["par denotes PIR active rate."], source_files=["int_channel.csv"]),
    ]})
    figures.append({"id": "FigS6", "panels": [
        _panel("a", "Jackknife stability of the QC threshold when each mouse is held out in turn.", "Held-out mouse", "QC threshold (par), remaining 7 mice", base_n, source_files=["int_loso_thr.csv"]),
        _panel("b", "Jackknife stability of intensity r when each mouse is held out in turn.", "Held-out mouse", "Intensity r, remaining 7 mice", base_n, source_files=["int_channel.csv"]),
        _panel("c", "True held-out state F1 after applying the fold-specific QC threshold.", "Held-out mouse", "F1 of the held-out mouse", base_n,
               values={"mean hold-out F1 over evaluable folds": vals.get("figS6_holdout_f1_mean")},
               reference_lines=[{"meaning": "operational F1 (in-sample, QC-passing channels)", "value": operational_f1}],
               notes=holdout_notes, source_files=["int_holdout_f1.csv", "int_bootstrap_ci.csv"]),
    ]})

    s7_notes = []
    if chan is not None and {"mouse_id", "qc1_pass"}.issubset(chan.columns):
        fail_n = int(chan.loc[chan["qc1_pass"] == 0, "mouse_id"].nunique())
        pass_n = int(chan.loc[chan["qc1_pass"] == 1, "mouse_id"].nunique())
        all_n = int(chan["mouse_id"].nunique())
        s7_notes.append(f"Group N values are mice: QC fail {fail_n}, QC pass {pass_n}, All {all_n}.")
        s7_notes.append("The same mouse can contribute channels to both QC-fail and QC-pass groups.")
    figures.append({"id": "FigS7", "panels": [
        _panel("a", "Intensity r across QC-fail, QC-pass, and all-mouse groups.", "QC group", "Intensity r", base_n, notes=s7_notes, source_files=["int_channel.csv"]),
        _panel("b", "Per-mouse state F1 across channels.", "Mouse", "State F1", base_n,
               reference_lines=[{"y": round(ctx.good_cut, 2), "meaning": f"good threshold (F1 = {ctx.good_cut:.2f})"}], source_files=["int_channel.csv"]),
    ]})
    figures.append({"id": "FigS8", "panels": [
        _panel("a", "Stability of par as cumulative active bins increase.", "Cumulative active bins", "par (mean ± SD across mice)", base_n,
               reference_lines=[{"y": round(float(thr), 3) if np.isfinite(thr) else None, "meaning": "QC threshold"}],
               notes=["Thin background lines are individual channels."], source_files=["int_qc_learning.csv", "int_channel.csv"]),
        _panel("b", "Stability of state F1 as cumulative active bins increase.", "Cumulative active bins", "F1 (mean ± SD across mice)", base_n,
               reference_lines=[{"y": round(ctx.good_cut, 2), "meaning": f"good threshold (F1 = {ctx.good_cut:.2f})"}],
               notes=["Thin background lines are individual channels."], source_files=["int_qc_learning.csv"]),
    ]})

    try:
        sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        sha = None
    agg_name = ("mean-of-means" if str(getattr(config, "DISPLAY_R_AGG", "mean")) == "mean" and
                str(getattr(config, "DISPLAY_F1_AGG", "mean")) == "mean" else
                f"r={getattr(config, 'DISPLAY_R_AGG', None)}, F1={getattr(config, 'DISPLAY_F1_AGG', None)}")
    payload = {
        "meta": {
            "version": ctx.version,
            "good_cut": ctx.good_cut,
            "n_mice": n_mice,
            "n_channels": n_ch,
            "bin_size_s": int(getattr(config, "BIN_STATE_SEC", 60)),
            "titled": False,
            "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "stage3_sha256": sha,
        },
        "glossary": {
            "PAI": "PIR Activity Index (log variance of the 1-Hz low-pass filtered signal)",
            "par": "PIR active rate",
            "nar": "NanoTag active rate",
            "QC": "quality control",
            "LOMO": "leave-one-mouse-out",
        },
        "methods": {
            "aggregation": agg_name,
            "intensity_ci": "BCa bootstrap, mouse-level clusters",
            "qc_threshold": (f"LOMO, Youden J, par ≥ {float(thr):.4f}" if np.isfinite(thr) else "LOMO, Youden J"),
            "good_definition": f"state F1 ≥ {ctx.good_cut:.2f}",
        },
        "figures": figures,
    }
    payload = _json_clean(payload)
    out = os.path.join(ctx.captions, f"caption_payload_{ctx.version}.json")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    ctx.log(f"  caption payload -> {out}")
    return out

def render_state_gmm_panel(ax, ch0, chan, sh, gp, mode="global", qc_label="",
                           nano_mu_ref=None):
    """Shared renderer for Fig4(a) and every Fig4a_* variant.

    mode:
      'global'   - one density over all state bins (rest-dominated; the honest full density)
      'condnorm' - rest and active groups each scaled to max 1 (conditional density); the two
                   modes appear equally tall even though rest bins vastly outnumber active ones
      'restdens' - All state bins (grey) and rest (navy) both as density=True fills; GMM curves on
                   the raw density scale. Rest is concentrated, so on a density axis its peak can
                   look taller than the wider all-bins fill (a known density artefact).
      'restcount'- All state bins (grey) and rest (navy) both as raw COUNT fills (density=False);
                   GMM curves converted to counts. All-bins is the taller envelope, rest a subset.

    v8: the x-axis is fit to THIS channel's own data (plus its GMM components and boundary), so
    no panel is clipped horizontally. The rest-peak-truncating 'yclip' mode has been removed.
    """
    d = sh[sh["ch"] == ch0]
    if len(d) == 0:
        ax.text(0.5, 0.5, f"no state_hist rows for {ch0}", ha="center", va="center")
        ax.axis("off")
        return None
    # v8: fit the x-axis to this channel's own data, widened just enough to show every GMM
    # component (mean ± FIG4_XSD_PAD*sd) and the decision boundary in full, then a small
    # margin. Previously a fixed FIG4_XRANGE window clipped every panel to [-14, -7].
    lo_data, hi_data = float(d["log_lp_var"].min()), float(d["log_lp_var"].max())
    xlo, xhi = lo_data, hi_data
    gpc_pre = gp[gp["ch"] == ch0] if gp is not None else pd.DataFrame()
    if len(gpc_pre):
        for _, _r in gpc_pre.iterrows():
            _m, _s = _r.get("mean", np.nan), _r.get("sd", np.nan)
            if np.isfinite(_m) and np.isfinite(_s):
                xlo = min(xlo, float(_m) - FIG4_XSD_PAD * float(_s))
                xhi = max(xhi, float(_m) + FIG4_XSD_PAD * float(_s))
        if "boundary" in gpc_pre.columns:
            _b = float(gpc_pre["boundary"].iloc[0])
            if np.isfinite(_b):
                xlo, xhi = min(xlo, _b), max(xhi, _b)
    if not (np.isfinite(xlo) and np.isfinite(xhi)) or xhi <= xlo:
        xlo, xhi = lo_data, hi_data
    _margin = FIG4_XMARGIN_FRAC * (xhi - xlo) if xhi > xlo else 0.5
    xlo, xhi = xlo - _margin, xhi + _margin
    dv = d[(d["log_lp_var"] >= xlo) & (d["log_lp_var"] <= xhi)]
    rest = dv[dv["nano_label"] == 0]["log_lp_var"]
    act = dv[dv["nano_label"] == 1]["log_lp_var"]
    n_bins = int(np.clip(np.sqrt(max(len(dv), 4)) * 1.5, 25, 55))
    bins = np.linspace(xlo, xhi, n_bins)
    centers = 0.5 * (bins[:-1] + bins[1:])
    bw = float(bins[1] - bins[0])

    if mode == "condnorm":
        cr, _ = np.histogram(rest, bins=bins)
        ca, _ = np.histogram(act, bins=bins)
        if cr.max() > 0:
            ax.bar(
                centers,
                cr / cr.max(),
                width=bw,
                color=C_CTRL_NAVY,
                alpha=0.55,
                edgecolor="none",
                label=f"Rest (NanoTag=0), n={int(cr.sum())}",
                zorder=1,
            )
        if ca.max() > 0:
            ax.bar(
                centers,
                ca / ca.max(),
                width=bw,
                color=C_MAIN,
                alpha=0.45,
                edgecolor="none",
                label=f"Active (NanoTag>0), n={int(ca.sum())}",
                zorder=2,
            )
        ax.set_ylabel("Conditional density (each group scaled to max = 1)")
    elif mode == "restdens":
        # All state bins (grey) + rest (navy), both density=True. Active is NOT filled.
        ax.hist(
            dv["log_lp_var"],
            bins=bins,
            color="0.85",
            alpha=0.9,
            label="All state bins",
            density=True,
            zorder=1,
        )
        if len(rest) > 0:
            ax.hist(
                rest,
                bins=bins,
                color=C_CTRL_NAVY,
                alpha=0.55,
                edgecolor="none",
                label=f"Rest (NanoTag=0), n={int(len(rest))}",
                density=True,
                zorder=2,
            )
        ax.set_ylabel("Density")
    elif mode == "restcount":
        # All state bins (grey) + rest (navy), both raw COUNT (density=False). Active is NOT filled.
        ax.hist(
            dv["log_lp_var"],
            bins=bins,
            color="0.85",
            alpha=0.9,
            label="All state bins",
            density=False,
            zorder=1,
        )
        if len(rest) > 0:
            ax.hist(
                rest,
                bins=bins,
                color=C_CTRL_NAVY,
                alpha=0.55,
                edgecolor="none",
                label="Rest (NanoTag = 0)",
                density=False,
                zorder=2,
            )
        ax.set_ylabel("Count (60 s bins)")
    else:
        ax.hist(
            dv["log_lp_var"],
            bins=bins,
            color="0.85",
            alpha=0.9,
            label="All state bins",
            density=True,
        )
        ax.hist(
            rest,
            bins=bins,
            color=C_CTRL_NAVY,
            alpha=0.6,
            label="Rest (NanoTag = 0)",
            density=True,
            zorder=2,
        )
        ax.set_ylabel("Density")

    crow = chan[chan["ch"] == ch0]
    if len(crow) == 0:
        return None
    crow = crow.iloc[0]
    gpc = gp[gp["ch"] == ch0] if gp is not None else pd.DataFrame()
    if len(gpc):
        xx = np.linspace(xlo, xhi, 400)
        total = np.zeros_like(xx)
        comp_curves = {}
        comp_curves_mean = {}
        comp_curves_sd = {}
        for _, row in gpc.iterrows():
            comp_y = row["weight"] * norm.pdf(xx, row["mean"], row["sd"])
            total += comp_y
            comp_curves[row["comp"]] = comp_y
            comp_curves_mean[row["comp"]] = float(row["mean"])
            comp_curves_sd[row["comp"]] = float(row["sd"])
        _bw_curve = float(bins[1] - bins[0])
        _n_rest = int(len(rest))
        _n_act = int(len(act))
        for comp, comp_y in comp_curves.items():
            col = C_CTRL_NAVY if comp == "rest" else C_MAIN
            if mode == "condnorm" and comp_y.max() > 0:
                # each component scaled to max=1 (conditional density view)
                y = comp_y / comp_y.max()
            elif mode == "restcount":
                # convert this component's normal pdf (density) to expected COUNT so it overlays
                # the raw-count fills: pdf-per-group * that group's bin count * bin width.
                _norm = norm.pdf(xx, comp_curves_mean[comp], comp_curves_sd[comp])
                _grp_n = _n_rest if comp == "rest" else _n_act
                y = _norm * _grp_n * _bw_curve
            else:
                y = comp_y
            ax.plot(xx, y, color=col, lw=1.8, label=f"GMM {comp.capitalize()} component", zorder=4)
        ax.axvline(
            float(gpc["boundary"].iloc[0]),
            color="black",
            lw=1.8,
            label="GMM boundary",
            zorder=5,
        )
        rest_row = gpc[gpc["comp"] == "rest"]
        if len(rest_row):
            rr0 = rest_row.iloc[0]
            ax.axvline(
                rr0["mean"], color=C_MAIN, lw=1.7,
                ls=(0, (1.8, 3.4)), dash_capstyle="round",
                alpha=1.0, zorder=6
            )
            # int_gmm_params.csv の nano_mu は stage1 の後段処理に上書きで消されるため
            # （_make_common_diagnostics, stage1:4027-4049）、この点線は実際には一度も
            # 描かれていなかったのに凡例だけが載っていた。呼び出し側が再構成した値を
            # 渡せるようにし、描けたときだけ凡例に出す。
            _nmu = nano_mu_ref
            if _nmu is None and "nano_mu" in rr0 and pd.notna(rr0["nano_mu"]):
                _nmu = float(rr0["nano_mu"])
            if _nmu is not None and np.isfinite(_nmu):
                ax.axvline(
                    _nmu,
                    color=C_CTRL_NAVY,
                    lw=1.7,
                    ls=(2.6, (1.8, 3.4)),
                    dash_capstyle="round",
                    alpha=1.0,
                    zorder=6,
                )
        else:
            _nmu = None
        handles, labels = ax.get_legend_handles_labels()
        extra = [
            Line2D([0], [0], color=C_MAIN, lw=1.7,
                   ls=(0, (1.8, 3.4)), dash_capstyle="round",
                   label="GMM-estimated Rest μ"),
        ]
        if _nmu is not None and np.isfinite(_nmu):
            extra.append(
                Line2D([0], [0], color=C_CTRL_NAVY, lw=1.7,
                       ls=(0, (1.8, 3.4)), dash_capstyle="round",
                       label="NanoTag empirical Rest μ")
            )
        ax.legend(handles=handles + extra, fontsize=7, loc="upper right")

    # ---- y-axis handling per mode ----
    if mode == "condnorm":
        ax.set_ylim(0, 1.18)
        ax.text(
            0.02,
            0.97,
            "conditional density (each group normalized);\nrest bins vastly outnumber active",
            transform=ax.transAxes,
            fontsize=7,
            va="top",
            ha="left",
            color="0.25",
        )

    ax.set_xlim(xlo, xhi)
    mouse_id = crow.get("mouse_id", "?")
    title = (
        f"{mouse_id}, {ch0} (bimodality={crow.get('bimodality_coef', np.nan):.2f}, "
        f"F1={crow.get('F1_state', np.nan):.3f})"
    )
    if qc_label:
        title += f"\n{qc_label}"
    ax.set_title(title, fontsize=9 if qc_label else 8.2)
    ax.set_xlabel("PAI")
    return crow, gpc

# ==================================================================== 本文図
def fig1(ctx: Ctx) -> None:
    """A1: legacy stage2 の s_fig1_lpf_compare (legacy stage2:1194-1310) と同じ体裁に戻した。
    上段 = 生 PIR のみ、下段 = 1-Hz LPF のみ、列 = Active / Rest / Empty。
    y 範囲は上段と下段で別々に取る（重ね描き時の共有 y 範囲では LPF が潰れる）。
    値には触れていない: fig1_variance_ratio_raw / _lpf は同じ 150 秒窓の同じ
    np.var から取っており、レイアウト変更で動かない。"""
    rt = ctx.need("int_raw_trace.csv", ["ch", "variant", "phase"])
    use_adc = "raw_value_adc" in rt.columns
    ycol = "raw_value_adc" if use_adc else "raw_value"
    rt = rt.copy()
    repr_ch0 = str(getattr(config, "REPR_CH", "") or "")
    rt["_ch"] = rt["ch"].astype(str) if "ch" in rt.columns else repr_ch0
    rt["_variant"] = rt["variant"].astype(str) if "variant" in rt.columns else "median"
    ch = str(getattr(config, "FIG1_MAIN_CH", repr_ch0) or repr_ch0)
    variant = str(getattr(config, "FIG1_MAIN_VARIANT", "median") or "median")
    is_main = True

    d_all = rt[(rt["_ch"] == ch) & (rt["_variant"] == variant)]
    if d_all.empty:
        raise LookupError(f"int_raw_trace に ch={ch}/variant={variant} が無い")
    # legacy stage2 と同じ列順。transition は legacy stage2 が描かないので既定では出さない。
    order = ["active", "rest", "empty"]
    present = [p for p in order if p in set(d_all["phase"])]
    # the empty-box control is only stored under the 'median' variant; reuse it everywhere
    empty_src = rt[(rt["_ch"] == ch) & (rt["phase"] == "empty")]
    if "empty" not in present and not empty_src.empty:
        present.append("empty")
    if not [p for p in present if p != "empty"]:
        # variant="transition" は phase も "transition" しか持たない。legacy stage2 は黙って
        # 空図になるが、それだと何も分からないので、その variant が実際に持つ phase を使う。
        extra = [p for p in sorted(set(d_all["phase"].astype(str))) if p not in present]
        if extra:
            present = extra + [p for p in present if p == "empty"]
            ctx.log(f"    [Fig1] variant={variant} は {order} を持たないため "
                    f"実在 phase {extra} で描画する")
    if not present:
        raise LookupError(f"int_raw_trace に描画可能な phase が無い: ch={ch}/variant={variant}")

    colmap = {
        "active": C_MAIN,
        "rest": C_CTRL_NAVY,
        "empty": C_CTRL_GRAY,
        "transition": C_MAIN,
    }

    # ---- 先に全 phase の系列を作り、上段/下段それぞれの y 範囲を決める ----
    phase_data = {}
    allv_raw, allv_lpf = [], []
    for ph in present:
        d = (
            empty_src
            if (ph == "empty" and "empty" not in set(d_all["phase"]))
            else d_all[d_all["phase"] == ph]
        ).sort_values("sample_idx")
        _x = pd.to_numeric(d["sample_idx"], errors="coerce") / float(config.FS)
        y = pd.to_numeric(d[ycol], errors="coerce")
        off = (
            float(
                np.median(
                    y.dropna().values - pd.to_numeric(d["raw_value"], errors="coerce").dropna().values
                )
            )
            if use_adc and len(y.dropna())
            else 0.0
        )
        ylpf = pd.to_numeric(d["raw_value_lpf"], errors="coerce") + off
        _draw_w = float(getattr(config, "RAW_DRAW_WINDOW_S", 150))
        _m = _x <= _draw_w
        _x, y, ylpf = _x[_m], y[_m], ylpf[_m]
        phase_data[ph] = (_x, y, ylpf, d)
        allv_raw.append(y.dropna().values)
        allv_lpf.append(ylpf.dropna().values)

    def _range(chunks):
        v = [c for c in chunks if len(c)]
        if not v:
            return 0.0, 1.0, 0.0
        a = np.concatenate(v)
        lo, hi = float(a.min()), float(a.max())
        return lo, hi, 0.04 * max(hi - lo, 1e-9)

    ylo_raw, yhi_raw, pad_raw = _range(allv_raw)
    ylo_lpf, yhi_lpf, pad_lpf = _range(allv_lpf)

    fig, axes = plt.subplots(
        2,
        len(present),
        figsize=(5.456, 3.4),
        sharex=True,
        constrained_layout=True,
    )
    axes = np.asarray(axes).reshape(2, len(present))

    stats = {}
    for i, ph in enumerate(present):
        _x, y, ylpf, d = phase_data[ph]

        ax_raw = axes[0, i]
        ax_raw.plot(_x, y, color=colmap.get(ph, C_CTRL_GRAY), lw=0.5, alpha=0.8,
                    antialiased=True, solid_joinstyle="round", solid_capstyle="round")
        ax_raw.set_ylim(ylo_raw - pad_raw, yhi_raw + pad_raw)
        ax_raw.set_xlim(0, getattr(config, "RAW_DRAW_WINDOW_S", 150))
        ax_raw.text(0.5, 1.02, ph.capitalize(), transform=ax_raw.transAxes,
                    ha="center", va="bottom", fontsize=9, fontweight="bold")
        if i == 0:
            ax_raw.set_ylabel("Raw signal (V)" if use_adc else "Raw signal (median-centered)")

        ax_lpf = axes[1, i]
        ax_lpf.plot(_x, ylpf, color="black", lw=1.3, antialiased=True)
        ax_lpf.set_ylim(ylo_lpf - pad_lpf, yhi_lpf + pad_lpf)
        ax_lpf.set_xlim(0, getattr(config, "RAW_DRAW_WINDOW_S", 150))
        if i == 0:
            ax_lpf.set_ylabel("1 Hz low-pass filtered (V)" if use_adc else "1 Hz low-pass filtered (median-centered)")
        ax_lpf.set_xlabel("Time (s)")

        v = y.dropna().values.astype(float)
        if len(v):
            uq = np.unique(v)
            step = float(np.min(np.diff(uq))) if len(uq) > 1 else np.nan
            stats[ph] = {
                "n": len(v),
                "dur_s": float(_x.max()) if not _x.isna().all() else 0.0,
                "range": float(np.ptp(v)),
                "n_unique": len(uq),
                "step": step,
                "var_raw": float(np.var(v)),
                "var_lpf": float(np.var(ylpf.dropna())),
            }
            _pai_txt = ""
            if "bin_pai" in d.columns and d["bin_pai"].notna().any():
                _pai_txt = f" PAI={float(d['bin_pai'].iloc[0]):.2f}"
            ctx.log(
                f"    {ch}/{variant}/{ph}: n={len(v)} dur={stats[ph]['dur_s']:.0f}s "
                f"min={v.min():.6g} max={v.max():.6g} range={stats[ph]['range']:.6g} "
                f"n_unique={len(uq)} smallest_step={step:.6g} "
                f"var_raw={stats[ph]['var_raw']:.3e} var_lpf={stats[ph]['var_lpf']:.3e}"
                f"{_pai_txt}"
            )
    if is_main and stats:
        # §8-1: the series is recorded VOLTAGE (V), stored at 0.01 V resolution by the LabVIEW
        # VI. A small numeric range is the spec, not an error -- report it once, not per phase.
        _summ = "; ".join(
            f"{p}: n_unique={stats[p]['n_unique']} range={stats[p]['range']:.4g}"
            for p in stats
        )
        ctx.log(
            "  [Recording precision] voltage series, storage resolution 0.01 V "
            "(2 decimal places, LabVIEW VI)."
        )
        ctx.log(f"    per-phase n_unique / range summary: {_summ}")
    if {"active", "rest"}.issubset(stats):
        rv = stats["active"]["var_raw"] / max(stats["rest"]["var_raw"], 1e-30)
        lv = stats["active"]["var_lpf"] / max(stats["rest"]["var_lpf"], 1e-30)
        ctx.log(
            f"    {ch}/{variant}: active/rest variance ratio raw={rv:.2f}x LPF={lv:.2f}x"
        )
        if is_main:
            ctx.value("fig1_variance_ratio_raw", round(rv, 2), f"ch={ch} variant={variant}")
            ctx.value("fig1_variance_ratio_lpf", round(lv, 2), f"ch={ch} variant={variant}")
    fig.suptitle(
        f"Raw vs 1-Hz LPF comparison (ch={ch}, variant={variant})",
        fontsize=10,
        y=1.02,
    )
    ctx.log("    [Fig1] variance ratios above are the values used in the caption of the article.")
    ctx.value("fig1_source", f"ch={ch}, variant={variant}", "")
    fig.set_layout_engine("constrained")
    ok = len(present)
    total = len(present)
    note = "panels (a)(b) are author-supplied assets; this file contains panel (c)"
    save(ctx, fig, "signal", False, ok, total, note, panel_letter="(c)")


def fig2(ctx: Ctx) -> None:
    fig, (axa, axb) = plt.subplots(2, 1, figsize=(5.456, 4.8), constrained_layout=True)
    dark_hours = list(range(int(config.DARK_HOURS[0]), 24)) + list(
        range(int(config.DARK_HOURS[1]))
    )
    ok = 0

    def a(ax):
        chan = ctx.load("int_channel.csv")
        r24 = ctx.load("int_repr_24h.csv")
        if chan is None or r24 is None:
            raise LookupError("int_channel/int_repr_24h missing")
        ch0 = get_repr_ch(ctx, chan)
        sub = r24[r24["ch"] == ch0].copy()
        if sub.empty:
            raise LookupError(f"ch={ch0} absent from int_repr_24h.csv")
        sub["timestamp"] = pd.to_datetime(sub["timestamp"])
        sub = sub.sort_values("timestamp")
        midnight = sub[sub["timestamp"].dt.hour == 0]
        day_start = (
            midnight["timestamp"].iloc[0].normalize()
            if len(midnight)
            else sub["timestamp"].iloc[0].normalize()
        )
        sub24 = sub[
            (sub["timestamp"] >= day_start)
            & (sub["timestamp"] < day_start + pd.Timedelta(hours=24))
        ].copy()
        if len(sub24) < 6:
            sub24 = sub.copy()
            day_start = sub24["timestamp"].iloc[0].normalize()
        sub24["hour_axis"] = (sub24["timestamp"] - day_start).dt.total_seconds() / 3600.0

        for h in dark_hours:
            ax.axvspan(h, h + 1, color="0.85", zorder=0, lw=0)
        ax.plot(
            sub24["hour_axis"],
            sub24["log_lp_var"],
            color=C_MAIN,
            lw=1.2,
            label="PAI (left axis)",
        )
        ax.set_ylabel("PAI", color=C_MAIN)
        ax.tick_params(axis="y", labelcolor=C_MAIN)
        ax.set_xlabel("Time of day (h)")
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 4))
        axa2 = ax.twinx()
        axa2.spines["top"].set_visible(False)
        axa2.plot(
            sub24["hour_axis"],
            sub24["nanotag_count"],
            color=C_CTRL_NAVY,
            lw=1.0,
            alpha=0.8,
            label="NanoTag (right axis)",
        )
        axa2.set_ylabel("NanoTag activity (counts / 10 min)", color=C_CTRL_NAVY)
        axa2.tick_params(axis="y", labelcolor=C_CTRL_NAVY)
        _h1, _l1 = ax.get_legend_handles_labels()
        _h2, _l2 = axa2.get_legend_handles_labels()
        if _h1 or _h2:
            _leg = ax.legend(
                _h1 + _h2, _l1 + _l2,
                loc="lower center", bbox_to_anchor=(0.5, 1.01),
                fontsize=7, ncol=2, frameon=False,
            )
            _leg.set_zorder(10)
        crow = chan[chan["ch"] == ch0]
        mouse_id = crow["mouse_id"].iloc[0] if len(crow) else "?"
        rr = float(crow["intensity_r"].iloc[0]) if len(crow) else np.nan
        ax.set_title(
            f"(a) {mouse_id}, {ch0}: 24-h activity (Spearman r={rr:.3f})", fontsize=8.6
        )
        ctx.log(
            f"  (a) Representative: mouse={mouse_id} ch={ch0} r={rr:.3f} bins={len(sub24)} "
            f"day_start={day_start}"
        )

    def b(ax):
        circ = ctx.load("int_circadian.csv")
        if circ is not None and len(circ):
            d = circ.sort_values("hour")
            for h in dark_hours:
                ax.axvspan(h, h + 1, color="0.88", zorder=0, lw=0)
            yp = d["pir_norm"] if "pir_norm" in d else d["pir_mean"]
            yn = d["nano_norm"] if "nano_norm" in d else d["nano_mean"]
            ax.plot(d["hour"], yp, "-o", color=C_MAIN, ms=3, label="PAI (normalized)")
            ax.plot(
                d["hour"], yn, "-s", color=C_CTRL_NAVY, ms=3, label="NanoTag (normalized)"
            )
            ax.set_xlabel("Time of day (h)")
            ax.set_ylabel("Normalized activity")
            ax.set_xticks(range(0, 25, 4))
            ax.set_xlim(0, 24)
            ax.legend(fontsize=7)
            try:
                rrc = float(spearmanr(yp, yn)[0])
            except Exception:
                rrc = np.nan
            ax.set_title(f"(b) Circadian profile (Spearman r={rrc:.2f})", fontsize=9)
            ctx.value("fig2_circadian_r", round(rrc, 4),
                      "PIR vs NanoTag, normalized circadian profile")
            ctx.log(f"  (b) circadian PIR vs NanoTag r={rrc:.2f}")
        else:
            ax.text(0.5, 0.5, "int_circadian.csv missing", ha="center", va="center")
            ax.axis("off")

    ok += draw(ctx, axa, "a", a)
    ok += draw(ctx, axb, "b", b)
    fig.set_layout_engine("constrained")
    save(ctx, fig, "timeseries", False, ok, 2)


def fig3(ctx: Ctx) -> None:
    _agg = str(getattr(config, "DISPLAY_R_AGG", "mean"))
    if _agg == "mean":
        metric_name = "intensity_r_mean_of_means"
        stat_fn = permouse_mean
    else:
        metric_name = "intensity_r_median"
        stat_fn = permouse_median

    fig = plt.figure(figsize=(5.456, 3.4), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.5], wspace=0.18)
    axa = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])
    ok = 0

    def a(ax):
        b = ctx.load("int_binned.csv")
        mo = ctx.load("int_mouse.csv")
        if b is None or mo is None:
            raise LookupError("required CSVs missing: int_binned/int_mouse")
        ax.scatter(
            b["log_lp_var"],
            b["nanotag_count"],
            s=4,
            alpha=0.16,
            color=C_MAIN,
            edgecolor="none",
        )
        ax.set_xlabel("PAI")
        ax.set_ylabel("NanoTag activity (counts / 10 min)")
        cir = ci_of(ctx, metric_name)
        if cir:
            pt, lo, hi = cir
            ax.set_title(
                f"(a) All bins (N={mo['mouse_id'].nunique()} mice, n={len(b)})\n"
                f"per-mouse {agglabel(_agg)} r={pt:.3f} [{lo:.3f}, {hi:.3f}]",
                fontsize=9,
            )
            ctx.value("fig3_intensity_r_ci", f"{pt:.4f} [{lo:.4f}, {hi:.4f}]", "")
            ctx.log(
                f"  (a) all bins n={len(b)}  per-mouse {agglabel(_agg)} "
                f"r={pt:.3f} 95%CI [{lo:.3f}, {hi:.3f}]"
            )
        else:
            ax.set_title(f"(a) All bins (n={len(b)})", fontsize=9)

    def b(ax):
        chan = ctx.load("int_channel.csv")
        if chan is None:
            raise LookupError("required CSV missing: int_channel.csv")
        real = stat_fn(chan, "intensity_r").dropna().values
        plac = stat_fn(chan, "placebo_r").dropna().values
        phase = stat_fn(chan, "phase_shuffle_r").dropna().values
        trendrm = stat_fn(chan, "intensity_r_trendrm_sym").dropna().values
        actonly = stat_fn(chan, "intensity_r_activeonly").dropna().values
        groups = [
            {"label": "Random-\nshuffle", "values": phase},
            {"label": "Mismatched-\npairing", "values": plac},
            {"label": "Trend-\nremoved", "values": trendrm},
            {"label": "Active-\nonly", "values": actonly},
            {"label": "Measured", "values": real},
        ]
        control_flags = [True, True, True, True, False]

        bar_dots(
            ax,
            groups,
            colors=[C_CTRL_GRAY, C_CTRL_GRAY, C_CTRL_NAVY, C_CTRL_NAVY, C_MAIN],
            hatches=[H_GRAY, H_GRAY, H_NAVY, H_NAVY, H_MAIN],
            err="sd",
            center=_agg,
        )

        annotation_y = []
        for i, g in enumerate(groups):
            v = np.asarray(g["values"], float)
            v = v[np.isfinite(v)]
            if not len(v):
                continue
            cv = center_of(v, _agg)
            top = cv
            if len(v) > 1:
                top = max(
                    top,
                    cv + float(np.std(v, ddof=1)),
                    float(v.max()),
                )
            else:
                top = max(top, float(v.max()))
            text_y = top + 0.03
            ax.text(
                i,
                text_y,
                f"{cv:.4f}",
                ha="center",
                va="bottom",
                fontsize=7,
            )
            annotation_y.append(text_y)

        y_top = ax.get_ylim()[1]
        if annotation_y:
            y_top = max(y_top, max(annotation_y) + 0.03)
        ax.set_ylim(0.0, y_top)

        ax.set_ylabel("Spearman r")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=6.5)
        ax.axhline(0, color="black", lw=0.6, ls=":")

        # A2: the mismatched-pair histogram used to sit here as an inset at
        # [0.56, 0.55, 0.40, 0.38] (inherited verbatim from legacy stage2:1494-1497). The
        # Trend-rm / Act-only bars reach ~0.79, so it always overlapped them, and
        # in untitled mode it was counted as a third panel and lettered "(c)".
        # It is now X_mismatched_pairs (see xfig_mismatched_pairs). No ctx.value
        # key is affected: the inset only ever wrote to the log.
        ax.set_title("(b) Specificity controls", fontsize=9)

        labels = [g["label"] for g in groups]
        n_controls = sum(control_flags)
        ctx.value("fig3_n_series", len(labels), "; ".join(labels))
        ctx.value(
            "fig3_n_controls",
            n_controls,
            "; ".join(
                x for x, is_control in zip(labels, control_flags)
                if is_control
            ),
        )
        ctx.log(
            f"    [Fig3] (b) の系列 {len(labels)} 本 = {', '.join(labels)}"
        )
        ctx.log(
            f"    [Fig3] うち対照は {n_controls} 本（Measured を除く）"
        )

        _n_neg_placebo = int(np.sum(np.asarray(plac, float) < 0))
        _al = agglabel(_agg)
        ctx.log(
            f"  (b) random-shuffle {_al}={center_of(phase, _agg):.3f}  "
            f"mismatched-pairing {_al}={center_of(plac, _agg):.2f}  "
            f"measured {_al}={center_of(real, _agg):.3f}  (each N={len(real)}); "
            f"{_n_neg_placebo} of {len(plac)} mismatched-pairing values are "
            f"negative (null behaviour)"
        )

    ok += draw(ctx, axa, "a", a)
    ok += draw(ctx, axb, "b", b)
    save(ctx, fig, "intensity", False, ok, 2)


def xfig_mismatched_pairs(ctx: Ctx) -> None:
    """A2: X figure. The full mismatched-pair (placebo) r distribution, which used
    to be an inset inside Fig3(b). Diagnostic only -- it supports the claim that
    the Placebo bar is low because the distribution sits at 0, not because a mean
    happens to be small. It is a diagnostic figure and is not part of the article."""
    pp = ctx.load("int_placebo_pairs.csv")
    if pp is None or "placebo_r" not in pp.columns or not len(pp):
        ctx.log("  [skip] int_placebo_pairs.csv が無い/空")
        return
    vals = pd.to_numeric(pp["placebo_r"], errors="coerce").dropna().to_numpy(float)
    if not len(vals):
        ctx.log("  [skip] placebo_r に有限値が無い")
        return
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.hist(vals, bins=min(16, max(6, int(np.sqrt(len(vals))))),
            color=C_CTRL_NAVY, alpha=0.75, edgecolor="black", linewidth=0.4)
    ax.axvline(0.0, color="black", lw=0.8, ls=":")
    ax.axvline(float(np.median(vals)), color=C_MAIN, lw=1.3,
               label=f"median={float(np.median(vals)):.4f}")
    ax.set_xlabel("Spearman r (mismatched pairing)")
    ax.set_ylabel("Pairs (n)")
    ax.set_title(f"Mismatched pairs, n={len(vals)}", fontsize=9)
    ax.legend(fontsize=7)
    zero_baseline(ax, None)
    fig.set_layout_engine("constrained")
    ctx.log(f"  mismatched-pair distribution n={len(vals)}  "
            f"median={float(np.median(vals)):.4f}  "
            f"range=[{vals.min():.4f}, {vals.max():.4f}]")
    save_explore(ctx, fig, "X_mismatched_pairs",
                 "was Fig3(b) inset; exploratory only")


def fig4(ctx: Ctx) -> None:
    """(a) は legacy stage2 の render_state_gmm_panel をそのまま使う（Fig4 の描画本体）。
    (b) は v5 で新設した全チャンネルの rest 成分一致度。legacy stage2 の fig4 が
    _D["fig4_diff_med_all"] / ["fig4_diff_med_qc"] として計算しているのと同じ量。
    B1: 参照側の rest 位置は rest_reference_mu() で取る。int_gmm_params.csv の
    nano_mu は stage1 の後段処理に上書きで消されているため、同一定義で
    int_state_hist.csv から再構成する（stage1 の再実行では直らない）。
    B2: 中央値どうし（legacy stage2 と同じ量）を描き、平均どうしの値も併記・登録して、
    どちらを採用するか後から決められるようにする。"""
    chan = ctx.load("int_channel.csv")
    sh = ctx.load("int_state_hist.csv")
    gp = ctx.load("int_gmm_params.csv")

    fig, axes = plt.subplots(2, 1, figsize=(5.456, 5.6), constrained_layout=True)
    ok = 0

    def a(ax):
        if chan is None or sh is None or gp is None:
            raise LookupError("int_channel/int_state_hist/int_gmm_params missing")
        thr = get_threshold(ctx, chan)
        ch0 = str(getattr(config, "FIG4_MAIN_CH", "") or "")
        if not ch0 or ch0 not in set(chan["ch"].astype(str)):
            ranked = get_bimodal_candidates(ctx, chan, n=1)
            ch0 = ranked[0] if ranked else get_repr_ch(ctx, chan)
            ctx.log(f"    [Fig4] FIG4_MAIN_CH が使えないため {ch0} にフォールバック")
        mode = str(getattr(config, "FIG4_MAIN_MODE", "restcount") or "restcount")
        st = qc_status_of(ctx, chan, ch0, thr=thr)
        qc_label = st["label"] if st is not None else ""
        _ref, _refsrc = rest_reference_mu(ctx)
        _nmu = None
        if _ref is not None and "nano_mu_mean" in _ref.columns:
            _hit = _ref[_ref["ch"].astype(str) == str(ch0)]
            if len(_hit) and pd.notna(_hit["nano_mu_mean"].iloc[0]):
                _nmu = float(_hit["nano_mu_mean"].iloc[0])
                ctx.log(f"  (a) NanoTag empirical rest μ (MEAN) = {_nmu:.4f}  ({_refsrc})")
        if _nmu is None:
            ctx.log("  (a) NanoTag empirical rest μ (MEAN) を復元できないため点線は描かない")
        
        if _nmu is not None and gp is not None and {"ch", "comp", "mean"}.issubset(gp.columns):
            _gr = gp[(gp["ch"].astype(str) == str(ch0)) &
                     (gp["comp"].astype(str) == "rest")]
            if len(_gr) and pd.notna(_gr["mean"].iloc[0]):
                _gmu = float(_gr["mean"].iloc[0])
                ctx.value("fig4_repr_abs_rest_mu_diff", round(abs(_gmu - _nmu), 4),
                          f"ch={ch0}; |GMM rest component mean - reference rest MEAN|")
                ctx.value("fig4_repr_gmm_rest_mu", round(_gmu, 4), f"ch={ch0}")
                ctx.value("fig4_repr_ref_rest_mu_mean", round(_nmu, 4),
                          f"ch={ch0}; reference rest MEAN")
                ctx.log(f"    [Fig4] (a) |Δμ| (mean vs mean) = {abs(_gmu - _nmu):.4f}")
        render_state_gmm_panel(ax, ch0, chan, sh, gp, mode=mode, qc_label=qc_label,
                               nano_mu_ref=_nmu)
        mouse = ""
        if st is not None:
            mouse = str(st.get("mouse_id", "") or "")
        if not mouse:
            mid = ctx.load("int_channel_map.csv")
            if mid is not None and {"ch", "mouse_id"} <= set(mid.columns):
                m = mid[mid["ch"].astype(str) == str(ch0)]
                mouse = str(m["mouse_id"].iloc[0]) if len(m) else ""
        ctx.value("fig4_representative_channel", ch0, f"mouse_id={mouse or '[要確認]'}")
        ctx.log(f"    [Fig4] representative channel = {ch0}, mouse_id = "
                f"{mouse or '[要確認: int_channel_map.csv に無い]'}  mode={mode}")
        if st is not None:
            ctx.log(f"    [Fig4] [QC] {ch0}: {qc_label}")
        if str(getattr(config, "REPR_CH", "")) != str(ch0):
            ctx.log(f"    [Fig4] note: config.REPR_CH = {getattr(config, 'REPR_CH', '?')} と異なる。"
                    "Fig4 は FIG4_MAIN_CH による独自指定を用いている")

    def b(ax):
        if gp is None or not {"ch", "comp", "mean"}.issubset(gp.columns):
            raise LookupError("int_gmm_params.csv に ch/comp/mean が無い")
        ref, ref_src = rest_reference_mu(ctx)
        if ref is None:
            raise LookupError(f"参照 rest μ を用意できない: {ref_src}")
        rest = gp[gp["comp"].astype(str) == "rest"].copy()
        # keep only what this panel needs, so a future stage1 that restores nano_mu
        # into int_gmm_params.csv cannot collide with the reference columns on merge
        rest = pd.DataFrame({
            "ch": rest["ch"].astype(str),
            "gmm_mu": pd.to_numeric(rest["mean"], errors="coerce"),
        })
        rest = rest.merge(ref, on="ch", how="inner")
        rest["absdiff"] = (rest["gmm_mu"] - rest["nano_mu"].astype(float)).abs()
        legacy_vals = rest["absdiff"].dropna().to_numpy(float)
        if not len(legacy_vals):
            raise LookupError("GMM rest μ と参照 rest μ の対が1件も揃わない")
        if "nano_mu_mean" not in rest.columns or not rest["nano_mu_mean"].notna().any():
            raise LookupError("参照 rest の mean を用意できない")
        rest["absdiff_meanref"] = (
            rest["gmm_mu"] - rest["nano_mu_mean"].astype(float)
        ).abs()
        vals = rest["absdiff_meanref"].dropna().to_numpy(float)
        if not len(vals):
            raise LookupError("GMM rest μ と参照 rest mean の対が1件も揃わない")
        ctx.log(f"  (b) 参照 rest μ の出所: {ref_src}")
        if "n_rest_bins" in rest.columns and rest["n_rest_bins"].notna().any():
            _nb = pd.to_numeric(rest["n_rest_bins"], errors="coerce").dropna()
            ctx.log(f"  (b) 参照に使った rest ビン数: median={float(_nb.median()):.0f} "
                    f"min={float(_nb.min()):.0f} max={float(_nb.max()):.0f}")
        ax.hist(vals, bins=16, color=C_CTRL_NAVY, alpha=0.55,
                edgecolor="black", linewidth=0.6)
        medv = float(np.median(vals))
        ax.axvline(medv, color=C_MAIN, lw=1.4, label=f"Median = {medv:.3f}")
        ax.set_xlabel("Absolute difference in Rest μ (PAI)")
        ax.set_ylabel("Channels (n)")
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.legend(fontsize=7)
        ax.set_title(f"(b) Rest-component agreement, all {len(vals)} channels", fontsize=9)
        zero_baseline(ax, None)
        ctx.value("fig4_abs_rest_mean_diff_median_meanref", round(medv, 4),
                  f"n={len(vals)}; GMM component mean vs reference rest MEAN "
                  f"(推定量を揃えた版。採用)")
        ctx.log(f"  (b) rest-mu |diff| median (mean vs mean): "
                f"all ch={medv:.4f} (n={len(vals)})")
        legacy_medv = float(np.median(legacy_vals))
        ctx.value("fig4_abs_rest_mean_diff_median", round(legacy_medv, 4),
                  f"n={len(legacy_vals)}; 従来版（参照 rest の中央値を使用）")
        ctx.log(f"  (b) rest-mu |diff| median (legacy median reference): "
                f"all ch={legacy_medv:.4f} (n={len(legacy_vals)})")
        if chan is not None and "qc1_pass" in chan.columns:
            keep = set(chan[chan["qc1_pass"] == 1]["ch"].astype(str))
            q = rest[rest["ch"].isin(keep)]["absdiff_meanref"].dropna()
            if len(q):
                ctx.value("fig4_abs_rest_mean_diff_median_qc",
                          round(float(q.median()), 4), f"n={len(q)}; GMM component mean vs reference rest MEAN")
                ctx.log(f"  (b) rest-mu |diff| median: QC-pass ch={float(q.median()):.4f} (n={len(q)})")

    ok += draw(ctx, axes[0], "a", a)
    ok += draw(ctx, axes[1], "b", b)
    fig.set_layout_engine("constrained")
    save(ctx, fig, "gmm", False, ok, 2)


def fig5(ctx: Ctx) -> None:
    _agg = str(getattr(config, "DISPLAY_F1_AGG", "mean"))
    if _agg == "mean":
        metric_all, metric_qc = "F1_all_mean", "F1_qc1_mean"
        stat_fn = permouse_mean
    else:
        metric_all, metric_qc = "F1_all_median_of_medians", "F1_qc1_median_of_medians"
        stat_fn = permouse_median

    chan = ctx.load("int_channel.csv")
    GOOD_F1 = ctx.good_cut

    fig = plt.figure(figsize=(5.456, 7.8), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.0])
    axa = fig.add_subplot(gs[0, 0]); axc = fig.add_subplot(gs[0, 1])
    axd = fig.add_subplot(gs[1, 0]); axe = fig.add_subplot(gs[1, 1])
    axf = fig.add_subplot(gs[2, :])
    ok = 0

    def pa(ax):
        if chan is None:
            raise LookupError("int_channel.csv missing")
        thr = get_threshold(ctx, chan)
        for flag, col, lab in [(1, C_MAIN, "QC-pass"), (0, C_CTRL_GRAY, "QC-fail")]:
            s = chan[chan["qc1_pass"] == flag]
            ax.scatter(s["pir_active_rate"], s["F1_state"], s=20, color=col, label=lab,
                       alpha=0.85, edgecolor="white", linewidth=0.4,
                       marker="o" if flag == 1 else "^")
        ax.axvline(thr, color="black", ls="--", lw=1.0)
        ax.axhline(GOOD_F1, color="grey", ls=":", lw=0.8)
        ax.set_xlabel("PIR active rate (PIR-AR)")
        ax.set_ylabel("State F1")
        ax.set_title(f"(a) PIR-AR vs F1\nAUC={auc_of(ctx, 'pir_active_rate'):.2f}, thr={thr:.3f}",
                     fontsize=7.8)
        _handles = [
            Line2D([0], [0], color=C_MAIN, marker="o", ls="none",
                   ms=4, label="QC-pass"),
            Line2D([0], [0], color=C_CTRL_GRAY, marker="^", ls="none",
                   ms=4, label="QC-fail"),
            Line2D([0], [0], color="black", ls="--", lw=1.0,
                   label="QC threshold"),
            Line2D([0], [0], color="grey", ls=":", lw=0.8,
                   label="Good criterion"),
        ]
        _leg = ax.legend(handles=_handles, loc="lower right", fontsize=7,
                         ncol=1, frameon=True, framealpha=0.85,
                         edgecolor="none", facecolor="white")
        _leg.set_zorder(10)
        ctx.value("fig5_qc_threshold", round(float(thr), 4), "LOMO")

    def pb(ax):
        qc_corr = ctx.load("int_qc_corr.csv")
        if qc_corr is None:
            raise LookupError("int_qc_corr.csv missing")
        sub = qc_corr[np.isclose(qc_corr["f1_thr"], GOOD_F1)].copy().sort_values("auc")
        if not len(sub):
            raise LookupError(f"int_qc_corr に f1_thr={GOOD_F1} が無い")
        _is_par = [str(v) == "pir_active_rate" for v in sub["qc_metric"]]
        colors_bar = [C_MAIN if p else C_CTRL_GRAY for p in _is_par]
        hatches_bar = [H_MAIN if p else H_GRAY for p in _is_par]
        ax.bar(range(len(sub)), sub["auc"], color=colors_bar, hatch=hatches_bar,
               edgecolor="black", linewidth=0.6)
        ax.set_xticks(range(len(sub)))
        _metric_labels = {"gmm_separation": "GMM separation", "snr": "SNR",
                          "floor_rate": "Floor rate", "pir_active_rate": "PIR active rate"}
        ax.set_xticklabels([_metric_labels.get(str(v), str(v).replace("_", " "))
                            for v in sub["qc_metric"]], rotation=30, ha="right", fontsize=7)
        ax.axhline(0.5, color="black", ls="--", lw=1.0, label="Chance level (AUC = 0.5)")
        zero_baseline(ax, list(sub["auc"].astype(float)))
        for _i, _r in enumerate(sub.itertuples()):
            if float(_r.auc) < 0.5:
                ax.text(_i, float(_r.auc) + 0.02, "Inverse\n(AUC < 0.5)", ha="center",
                        va="bottom", fontsize=7, color="0.25")
        ax.set_ylabel(f"AUC (F1 ≥ {GOOD_F1:.2f})")
        ax.legend(fontsize=7, loc="upper left")
        ax.set_title("(b) QC-metric AUC", fontsize=9)
        for _, r in sub.iterrows():
            ctx.value(f"fig5_auc_{r['qc_metric']}", float(r["auc"]), "")
        _gmm_auc = pd.to_numeric(
            sub.loc[sub["qc_metric"].astype(str) == "gmm_separation", "auc"],
            errors="coerce",
        ).dropna()
        if len(_gmm_auc):
            _inv_auc = 1.0 - float(_gmm_auc.iloc[0])
            ctx.value("fig5b_auc_gmm_separation_inverted", round(_inv_auc, 4),
                      "1 - observed GMM-separation AUC; caption-only auxiliary value")
        else:
            ctx.log("    [MISSING] Fig5(b): GMM-separation AUC unavailable")
        ctx.log("  (b) AUC (ascending): "
                + "; ".join(f"{r.qc_metric}={r.auc}" for r in sub.itertuples()))

    def pc(ax):
        cap_ci_all = ci_of(ctx, "F1_all_mean")
        cap_ci_qc = ci_of(ctx, "F1_qc1_mean")
        for _key, _metric, _ci in [
            ("fig5c_f1_all", "F1_all_mean", cap_ci_all),
            ("fig5c_f1_qc", "F1_qc1_mean", cap_ci_qc),
        ]:
            if _ci is not None and all(np.isfinite(float(v)) for v in _ci):
                ctx.value(
                    _key,
                    f"{_ci[0]:.4f} [{_ci[1]:.4f}, {_ci[2]:.4f}]",
                    f"{_metric}; point [95% CI] from int_bootstrap_ci.csv",
                )
            else:
                ctx.value(_key, None,
                          f"[MISSING] {_metric} in int_bootstrap_ci.csv")
                ctx.log(f"    [MISSING] Fig5(c): "
                        f"{_metric} in int_bootstrap_ci.csv")
        if chan is None:
            raise LookupError("int_channel.csv missing")
        ci_all, ci_qc = ci_of(ctx, metric_all), ci_of(ctx, metric_qc)
        f_all = stat_fn(chan, "F1_state").dropna().values
        q = chan[chan["qc1_pass"] == 1]
        f_qc = stat_fn(q, "F1_state").dropna().values
        groups_d = [
            {"label": f"All (N = {len(f_all)})", "values": f_all,
             "value": ci_all[0] if ci_all else None,
             "ci": (ci_all[1], ci_all[2]) if ci_all else None},
            {"label": f"QC-pass (N = {len(f_qc)})", "values": f_qc,
             "value": ci_qc[0] if ci_qc else None,
             "ci": (ci_qc[1], ci_qc[2]) if ci_qc else None},
        ]
        bar_dots(ax, groups_d, colors=[C_CTRL_NAVY, C_MAIN],
                 hatches=[H_NAVY, H_MAIN], err="ci")
        ax.set_ylabel("State F1")
        ax.set_title("(c) F1 improves after QC", fontsize=9)
        if ci_all and ci_qc:
            ctx.log(f"  (c) F1 all {ci_all[0]:.4f}[{ci_all[1]:.4f},{ci_all[2]:.4f}] -> "
                    f"QC-pass {ci_qc[0]:.4f}[{ci_qc[1]:.4f},{ci_qc[2]:.4f}]")

    def pd_(ax):
        qconf = ctx.load("int_qc_confusion.csv")
        if qconf is None or not len(qconf):
            raise LookupError("int_qc_confusion.csv missing")
        row_before = qconf[np.isclose(qconf["good_cut"], GOOD_F1)
                           & (qconf["rule"].astype(str) == "par_only")]
        row_after = qconf[np.isclose(qconf["good_cut"], GOOD_F1)
                          & (qconf["rule"].astype(str) == "par_snr_sep")]
        target = row_before if len(row_before) else row_after
        if not len(target):
            raise LookupError("int_qc_confusion に該当行が無い")
        r0 = target.iloc[0]
        mat = np.array([[r0["TP"], r0["FP"]], [r0["FN"], r0["TN"]]], dtype=float)
        lab = np.array([["TP", "FP"], ["FN", "TN"]])
        ax.imshow(mat, cmap="Blues", vmin=0)
        for (ii, jj), v in np.ndenumerate(mat):
            ax.text(jj, ii, f"{lab[ii, jj]}\n{int(v)}", ha="center", va="center",
                    fontsize=7.5, color="white" if v > mat.max() / 2 else "black")
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"good\n(F1 ≥ {GOOD_F1:.2f})", f"not good\n(F1 < {GOOD_F1:.2f})"], fontsize=7)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["pass", "fail"], fontsize=7)
        ax.set_xlabel("Channel quality", fontsize=7.5)
        ax.set_ylabel("QC decision", fontsize=7.5)
        subtitle = f"PPV={r0['PPV']:.3f} sens={r0['sensitivity']:.3f}"
        ax.set_title(f"(d) Confusion (PIR-AR-only QC)\n{subtitle}", fontsize=9)
        ctx.value("fig5_confusion",
                  f"TP={int(r0['TP'])} FP={int(r0['FP'])} FN={int(r0['FN'])} TN={int(r0['TN'])}",
                  "par_only")
        ctx.log(f"  (d) confusion matrix (par-only): {subtitle}")

    def pe(ax):
        tot_fp = tot_fn = np.nan
        pc_ = ctx.load("int_state_confusion_perch.csv")
        if pc_ is not None and {"FP", "FN"}.issubset(pc_.columns):
            tot_fp, tot_fn = float(pc_["FP"].sum()), float(pc_["FN"].sum())
        else:
            es = ctx.load("int_error_summary.csv")
            if es is not None and {"FP", "FN"}.issubset(es.columns) and len(es):
                tot_fp, tot_fn = float(es["FP"].iloc[0]), float(es["FN"].iloc[0])
        if not (np.isfinite(tot_fp) and np.isfinite(tot_fn)) or (tot_fp + tot_fn) <= 0:
            raise LookupError("FP/FN source missing")
        tot = tot_fp + tot_fn
        shares = [tot_fn / tot * 100.0, tot_fp / tot * 100.0]
        # 内訳パネル（§3-4）：比較の色語彙は使わず、紺の逐次（濃淡）で量の大小を示す。
        # 濃淡＝割合の大小のみを表し、採用/対照の別ではない。FN=大→濃 / FP=小→淡。
        # 意味色 C_CTRL_NAVY ではなくリテラルで書く（比較語彙でないことを明示）。ハッチ無し。
        ax.bar([0, 1], shares, color=["#1f4e79", "#8fa9c4"],
               edgecolor="black", linewidth=0.6, width=0.6)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["FN\n(missed Active)", "FP\n(false Active)"], fontsize=7)
        ax.set_ylabel("Share of errors (%)")
        ax.set_ylim(0, 112)
        for i, (shv, ct) in enumerate(zip(shares, [tot_fn, tot_fp])):
            ax.text(i, shv + 1.5, f"{shv:.1f}%\n(n = {int(ct):,})", ha="center", fontsize=7)
        ax.set_title("(e) Errors are mostly misses\n(PIR is conservative)", fontsize=9)
        ctx.value("fig5_fn_share_pct", round(shares[0], 1), f"FN={int(tot_fn)} FP={int(tot_fp)}")
        ctx.log(f"  (e) FN share={shares[0]:.1f}% FP share={shares[1]:.1f}% "
                f"(FN={int(tot_fn)}, FP={int(tot_fp)})")

    for ax, letter, fn in zip([axa, axc, axd, axe, axf], "abcde",
                              [pa, pb, pc, pd_, pe]):
        ok += draw(ctx, ax, letter, fn)
    save(ctx, fig, "qc", False, ok, 5)


def fig6(ctx: Ctx) -> None:
    _agg = str(getattr(config, "DISPLAY_R_AGG", "mean"))
    permouse = ctx.load("int_sensor_consistency_permouse.csv")
    b = ctx.load("int_binned.csv")
    sw = ctx.load("int_sensor_swap.csv")

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(5.456, 2.8), constrained_layout=True)
    ok = 0

    def a(ax):
        if b is None or not len(b):
            raise LookupError("int_binned.csv missing")
        pairs_a, pairs_b = [], []
        for (_rec, _mid), g in b.groupby(["record_id", "mouse_id"]):
            chs = sorted(g["ch"].unique())
            if len(chs) >= 2:
                aa = g[g["ch"] == chs[0]][["timestamp", "log_lp_var"]].rename(
                    columns={"log_lp_var": "a"})
                bb = g[g["ch"] == chs[1]][["timestamp", "log_lp_var"]].rename(
                    columns={"log_lp_var": "b"})
                mg = aa.merge(bb, on="timestamp").dropna()
                pairs_a.extend(mg["a"].tolist())
                pairs_b.extend(mg["b"].tolist())
        if not pairs_a:
            raise LookupError("no paired bins")
        pairs_a = np.array(pairs_a); pairs_b = np.array(pairs_b)
        ax.scatter(pairs_a, pairs_b, s=5, alpha=0.15, color=C_MAIN,
                   edgecolor="none", zorder=1)
        lo = float(min(pairs_a.min(), pairs_b.min()))
        hi = float(max(pairs_a.max(), pairs_b.max()))
        ax.plot([lo, hi], [lo, hi], color="black", lw=1.2, ls="--",
                label="Identity", zorder=3)
        ax.set_xlabel("Sensor A (PAI)")
        ax.set_ylabel("Sensor B (PAI)")
        med_ind = (center_of(permouse["median_inter_sensor_r"].values, _agg)
                   if permouse is not None and len(permouse) else np.nan)
        _across = agglabel(_agg)
        ax.set_title(f"(a) Independent-sensor agreement\n"
                     f"per-mouse {_across} of within-mouse median r={med_ind:.2f}",
                     fontsize=7.8)
        ax.legend(fontsize=7)
        rr_pool = spearman(pairs_a, pairs_b)
        ctx.log(f"  (a) per-mouse {_across} of within-mouse median inter-sensor r={med_ind:.2f} "
                f"[primary]  pooled r={rr_pool:.2f} n={len(pairs_a)} [reference]")
        ctx.log("  [AGG-HYBRID] Fig6(a): within-mouse aggregation is median (fixed in stage1); "
                f"across-mouse aggregation is {_across}")

    def b_(ax):
        if sw is None or not {"set1_r", "set2_r"}.issubset(sw.columns):
            raise LookupError("int_sensor_swap.csv missing")
        valid = sw.dropna(subset=["set1_r", "set2_r"])
        if not len(valid):
            raise LookupError("no valid pairs")
        ax.scatter(valid["set1_r"], valid["set2_r"], s=36, color=C_MAIN,
                   edgecolor="white", linewidth=0.6, zorder=3)
        lo = float(min(valid["set1_r"].min(), valid["set2_r"].min())) - 0.02
        hi = float(max(valid["set1_r"].max(), valid["set2_r"].max())) + 0.02
        ax.plot([lo, hi], [lo, hi], color="black", lw=1.0, ls="--",
                label="Identity", zorder=2)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_xlabel("Intensity r, sensor set A")
        ax.set_ylabel("Intensity r, sensor set B")
        diff_col = (valid["set1_r"] - valid["set2_r"]).abs()
        diff_med = center_of(diff_col.values, _agg)
        out_row = valid.loc[diff_col.idxmax()]
        diff_excl = diff_col.drop(index=diff_col.idxmax())
        diff_med_excl = center_of(diff_excl.values, _agg) if len(diff_excl) else np.nan
        _alb = agglabel(_agg)
        ax.set_title(f"(b) Sensor-set test-retest\n{_alb} |Δr|={diff_med:.3f}",
                     fontsize=8.2)
        ax.legend(fontsize=7)
        ctx.log(f"  (b) {_alb} |Δr|={diff_med:.3f} [primary]; outlier "
                f"{out_row['mouse_id']} (A={out_row['set1_r']:.3f}, B={out_row['set2_r']:.3f}); "
                f"{_alb} |Δr| excluding that mouse={diff_med_excl:.3f} "
                f"(conclusion unchanged); ICC/Spearman not shown (range-restricted, misleading)")

    ok += draw(ctx, axa, "a", a)
    ok += draw(ctx, axb, "b", b_)
    fig.set_layout_engine("constrained")
    save(ctx, fig, "intersensor", False, ok, 2)


# ==================================================================== 補足図
def figS1(ctx: Ctx) -> None:
    """(a) は legacy stage2 の s7_calib、(b)-(f) は legacy stage2 の _s2_build。
    v5 で1枚に統合したため、(a) と (f) を全幅に置いて legacy stage2 の (a)(b) / (c)(d) の
    左右ペアをそのまま保つ配置にしている。"""
    with plt.rc_context(SUPP_RC):
        center = "mean" if str(getattr(config, "DISPLAY_R_AGG", "mean")) == "mean" else "median"
        sb = ctx.load("int_state_feature_bench.csv")
        ib = ctx.load("int_feature_bench.csv")
        ibp = ctx.load("int_feature_bench_perch.csv")
        fb = ctx.load("int_freqband_bench.csv")

        fig = plt.figure(figsize=(9.6, 12.0))
        gs = fig.add_gridspec(4, 2, wspace=0.42, hspace=0.62,
                              height_ratios=[0.85, 1, 1, 0.9])
        axa = fig.add_subplot(gs[0, :])
        axb = fig.add_subplot(gs[1, 0]); axc = fig.add_subplot(gs[1, 1])
        axd = fig.add_subplot(gs[2, 0]); axe = fig.add_subplot(gs[2, 1])
        axf = fig.add_subplot(gs[3, :])
        ok = 0

        def pa(ax):
            d = ctx.load("int_calibration.csv")
            if d is None or d.empty:
                raise LookupError("int_calibration.csv missing")
            for t, col, lab in [("empty", C_CTRL_GRAY, "Empty cage"),
                                ("active_rest", C_CTRL_NAVY, "Occupied, Rest"),
                                ("active_move", C_MAIN, "Occupied, Active")]:
                v = d[d["type"] == t]["log_lp_var"].dropna()
                if len(v):
                    ax.hist(v, bins=30, alpha=0.55, color=col, label=lab, density=True)
                    ctx.value(f"figS1_median_{t}", round(float(v.median()), 2), f"n={len(v)}")
                    ctx.log(f"  (a) {t}: median={v.median():.3f} n={len(v)}")
            ax.set_xlabel("PAI")
            ax.set_ylabel("Density")
            ax.legend(fontsize=7)
            ax.set_title("(a) Empty cage vs occupied (Rest/Active) calibration", fontsize=9)

        def pb(ax):
            feat_a = [("raw_lp_var", "Linear variance"), ("log_lp_var", "Log variance (PAI)")]
            groups_a, vals_a_center = [], {}
            for f, lab in feat_a:
                vals = np.array([], float)
                if ibp is not None and {"feature", "r"}.issubset(ibp.columns):
                    vals = ibp[ibp["feature"] == f]["r"].dropna().values.astype(float)
                val = None
                if not len(vals) and ib is not None and "feature" in ib.columns:
                    col = "mean_r" if center == "mean" else "median_r"
                    row = ib[ib["feature"] == f]
                    if len(row) and col in ib.columns:
                        val = float(row.iloc[0][col])
                groups_a.append({"label": lab, "values": vals, "value": val})
                vals_a_center[f] = val if val is not None else center_of(vals, center)
            if not any(np.isfinite(v) for v in vals_a_center.values()):
                raise LookupError("intensity bench の log/no-log が揃わない")
            bar_dots(ax, groups_a, colors=[C_CTRL_GRAY, C_MAIN],
                     hatches=[H_GRAY, H_MAIN], err="sd", center=center)
            ax.set_ylabel("Intensity r")
            d_a = vals_a_center["log_lp_var"] - vals_a_center["raw_lp_var"]
            ax.set_title("(b) Effect of log on intensity r"
                         + (f"\nSpearman is rank-invariant: log changes r by {d_a:+.4f} (harmless)"
                            if np.isfinite(d_a) else ""), fontsize=8.0)
            ctx.log("  (b) " + "; ".join(f"{k}={v:.4f}" for k, v in vals_a_center.items()))

        def pc(ax):
            feat_b = [("lp_var", "Linear variance"), ("log_lp_var", "Log variance (PAI)")]
            groups_b, vals_b_center = [], {}
            for f, lab in feat_b:
                vals = np.array([], float)
                if sb is not None and {"feature", "f1_state"}.issubset(sb.columns):
                    vals = sb[sb["feature"] == f]["f1_state"].dropna().values.astype(float)
                groups_b.append({"label": lab, "values": vals, "value": None})
                vals_b_center[f] = center_of(vals, center)
            if not any(np.isfinite(v) for v in vals_b_center.values()):
                raise LookupError("state bench の log/no-log が揃わない")
            bar_dots(ax, groups_b, colors=[C_CTRL_GRAY, C_MAIN],
                     hatches=[H_GRAY, H_MAIN], err="sd", center=center)
            ax.set_ylabel("State F1")
            ax.set_title("(c) Effect of log on state F1: without log the GMM degenerates",
                         fontsize=7.8)
            ymax_b = max([v for v in vals_b_center.values() if np.isfinite(v)] + [0.1])
            for i, (f, _lab) in enumerate(feat_b):
                cv = vals_b_center[f]
                if np.isfinite(cv) and cv < 0.05:
                    ax.annotate("F1 ≈ 0\n(GMM degenerate)", xy=(i, cv),
                                xytext=(i, ymax_b * 0.45), ha="center", fontsize=6.4,
                                color=C_CTRL_GRAY,
                                arrowprops=dict(arrowstyle="->", color=C_CTRL_GRAY, lw=0.8))
            zero_baseline(ax, [ymax_b * 0.62], top_extra=0.10)
            ctx.log("  (c) " + "; ".join(f"{k}={v:.4f}" for k, v in vals_b_center.items()))

        # NOTE: these strings are DATA KEYS matched against int_freqband_bench.csv["band"].
        # Never rewrite them for display; use BAND_DISPLAY below for tick labels.
        band_order = ["Low-Pass (<=1Hz, B0)", "Mid-Band (1-2Hz)",
                      "Mid-Band (2-5Hz)", "High-Pass (>5Hz)"]
        BAND_DISPLAY = {"Low-Pass (<=1Hz, B0)": "Low-pass (≤ 1 Hz)",
                        "Mid-Band (1-2Hz)": "Mid-band (1–2 Hz)",
                        "Mid-Band (2-5Hz)": "Mid-band (2–5 Hz)",
                        "High-Pass (>5Hz)": "High-pass (> 5 Hz)"}
        colors_c = [C_MAIN if bd == band_order[0] else C_CTRL_GRAY for bd in band_order]
        hatches_c = [H_MAIN if bd == band_order[0] else H_GRAY for bd in band_order]

        def _band(ax, metric, ylab, letter_title):
            if fb is None or not len(fb):
                raise LookupError("int_freqband_bench.csv missing")
            groups, vals = [], {}
            for bd in band_order:
                v = fb[(fb["metric"] == metric) & (fb["band"] == bd)]["value"]
                v = v.dropna().values.astype(float)
                groups.append({"label": BAND_DISPLAY.get(bd, bd), "values": v, "value": None})
                vals[bd] = center_of(v, center)
            bar_dots(ax, groups, colors=colors_c, hatches=hatches_c, err="sd", center=center)
            plt.setp(ax.get_xticklabels(), rotation=35, ha="right", fontsize=6.5)
            ax.set_ylabel(ylab)
            ax.set_title(letter_title, fontsize=9)
            return vals

        def pd_(ax):
            cvals = _band(ax, "intensity_r", "Intensity r", "(d) Intensity r by frequency band")
            ctx.log("  (d) " + "; ".join(f"{k}={v:.4f}" for k, v in cvals.items()))

        def pe(ax):
            dvals = _band(ax, "state_f1", "State F1", "(e) State F1 by frequency band")
            series_d = pd.Series(dvals).dropna()
            if len(series_d) == len(band_order):
                mono_d = all(series_d.iloc[i] >= series_d.iloc[i + 1]
                             for i in range(len(series_d) - 1)) or \
                         all(series_d.iloc[i] <= series_d.iloc[i + 1]
                             for i in range(len(series_d) - 1))
                best_band, worst_band = series_d.idxmax(), series_d.idxmin()
                if best_band == band_order[0] and not mono_d:
                    ax.set_title("(e) State F1 by band: Low-Pass best, mid-bands non-monotonic",
                                 fontsize=7.4)
                    ctx.log(f"  (e) [reviewer note] non-monotonic in frequency: {best_band}="
                            f"{series_d[best_band]:.3f} best, lowest={worst_band}="
                            f"{series_d[worst_band]:.3f}. Both metrics agree <=1 Hz is best "
                            f"-> justifies the 1-Hz low-pass.")
            dmax = max([v for v in dvals.values() if np.isfinite(v)] + [0.1])
            for i, bd in enumerate(band_order):
                cv = dvals.get(bd, np.nan)
                if np.isfinite(cv) and cv < 0.05:
                    ax.annotate("F1 ≈ 0\n(GMM degenerate)", xy=(i, cv),
                                xytext=(i, dmax * 0.45), ha="center", fontsize=6.2,
                                color=C_CTRL_GRAY,
                                arrowprops=dict(arrowstyle="->", color=C_CTRL_GRAY, lw=0.8))
            zero_baseline(ax, [dmax * 0.62], top_extra=0.10)
            ctx.log("  (e) " + "; ".join(f"{k}={v:.4f}" for k, v in dvals.items()))

        def pf(ax):
            dlpf = ctx.load("int_lpf_sweep_agg.csv")
            _agg_r = str(getattr(config, "DISPLAY_R_AGG", "mean"))
            if _agg_r == "mean":
                _r_col, _r_lab = "intensity_r_mean_of_means", "Intensity r (mean-of-means)"
            else:
                _r_col, _r_lab = "intensity_r_median_of_medians", "Intensity r (median-of-medians)"
            if dlpf is None or dlpf.empty or "f1_qc_mean_of_means" not in dlpf.columns:
                raise LookupError("int_lpf_sweep_agg.csv missing/empty")
            ax.plot(dlpf["cutoff_hz"], dlpf["f1_qc_mean_of_means"], "o-", color=C_MAIN,
                    label="State F1 (QC pass)")
            ax.set_xlabel("LPF cutoff (Hz)")
            ax.set_ylabel("State F1 (mean-of-means)", color=C_MAIN)
            ax.tick_params(axis="y", labelcolor=C_MAIN)
            ax2 = ax.twinx()
            ax2.spines["top"].set_visible(False)
            if _r_col in dlpf.columns:
                ax2.plot(dlpf["cutoff_hz"], dlpf[_r_col], "s--", color=C_CTRL_NAVY,
                         label="Intensity r")
                ax2.set_ylabel(_r_lab, color=C_CTRL_NAVY)
                ax2.tick_params(axis="y", labelcolor=C_CTRL_NAVY)
                ctx.log(f"  [AGG-SOURCE] S1(f) lpf sweep intensity r column = {_r_col}")
            else:
                ctx.log(f"  [MISSING] S1(f): column {_r_col} absent; r series not drawn")
            ax.axvline(float(config.LOWPASS_CUTOFF_HZ), color="black", ls=":", lw=1.0)
            ax.set_title("(f) The adopted LPF cutoff is a robust choice", fontsize=9)

        for ax, letter, fn in zip([axa, axb, axc, axd, axe, axf], "abcdef",
                                  [pa, pb, pc, pd_, pe, pf]):
            ok += draw(ctx, ax, letter, fn)
        save(ctx, fig, "pai_basis", True, ok, 6)


def figS2(ctx: Ctx) -> None:
    with plt.rc_context(SUPP_RC):
        fig, ax1 = plt.subplots(figsize=(8.0, 4.2))
        ok = 0

        def one(ax):
            dagg = ctx.load("int_bin_sweep_agg.csv")
            if dagg is None or dagg.empty:
                raise LookupError("int_bin_sweep_agg.csv missing")
            dagg = dagg.sort_values("bin_sec")
            has_mom = "f1_all_mean_of_means" in dagg.columns
            f1_qc_col = "f1_qc_mean_of_means" if has_mom else "f1_qc_mean"
            f1_all_col = "f1_all_mean_of_means" if has_mom else "f1_all_mean"
            ax.plot(dagg["bin_sec"], dagg[f1_all_col], "o:", color=C_MAIN, alpha=0.5,
                    label="State F1, all ch")
            if f1_qc_col in dagg.columns:
                ax.plot(dagg["bin_sec"], dagg[f1_qc_col], "^-", color=C_MAIN,
                        label="State F1, QC-pass ch")
            ax.set_ylabel("State F1 (mean-of-means)", color=C_MAIN)
            ax.tick_params(axis="y", labelcolor=C_MAIN)
            ax.set_xlabel("Bin size (s)")
            ax.axvline(config.BIN_STATE_SEC, color=C_MAIN, ls=":", lw=1.0)
            ax.axvline(config.BIN_INTENSITY_SEC, color=C_CTRL_NAVY, ls="-.", lw=1.0)
            # Operating points are annotated directly: a 5-entry legend does not fit.
            ax.annotate(f"State operating point\n({int(config.BIN_STATE_SEC)} s)",
                        xy=(config.BIN_STATE_SEC, 0.02), xycoords=("data", "axes fraction"),
                        xytext=(4, 0), textcoords="offset points",
                        fontsize=5.8, color=C_MAIN, ha="left", va="bottom")
            ax.annotate(f"Intensity operating point\n({int(config.BIN_INTENSITY_SEC)} s)",
                        xy=(config.BIN_INTENSITY_SEC, 0.02), xycoords=("data", "axes fraction"),
                        xytext=(-4, 0), textcoords="offset points",
                        fontsize=5.8, color=C_CTRL_NAVY, ha="right", va="bottom")
            ax2 = ax.twinx()
            ax2.spines["top"].set_visible(False)
            _agg_r = str(getattr(config, "DISPLAY_R_AGG", "mean"))
            if _agg_r == "mean":
                _r_col, _r_lab = "intensity_r_mean_of_means", "Intensity r (mean-of-means)"
            else:
                _r_col, _r_lab = "intensity_r_median_of_medians", "Intensity r (median-of-medians)"
            if _r_col in dagg.columns:
                ctx.log(f"  [AGG-SOURCE] S2 bin sweep intensity r column = {_r_col}")
                ax2.plot(dagg["bin_sec"], dagg[_r_col], "s--", color=C_CTRL_NAVY,
                         label="Intensity r")
                ax2.set_ylabel(_r_lab, color=C_CTRL_NAVY)
                ax2.tick_params(axis="y", labelcolor=C_CTRL_NAVY)
            else:
                ctx.log(f"  [MISSING] S2 intensity r: column {_r_col} absent; series not drawn")
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, fontsize=6.0, loc="upper left",
                      bbox_to_anchor=(1.14, 1.0), framealpha=0.85, borderpad=0.4)
            ax.set_title("Coarser bins help intensity r but hurt state F1\n"
                         "(red dotted = state operating point; blue dash-dot = intensity operating point)",
                         fontsize=7.6)
            row60 = dagg[dagg["bin_sec"] == config.BIN_STATE_SEC]
            if len(row60) and f1_qc_col in row60.columns:
                ctx.log(f"  {config.BIN_STATE_SEC}s QC-pass F1 (mean-of-means) = "
                        f"{float(row60[f1_qc_col].iloc[0]):.4f}")
            row600 = dagg[dagg["bin_sec"] == config.BIN_INTENSITY_SEC]
            if len(row600) and _r_col in row600.columns:
                ctx.log(f"  {config.BIN_INTENSITY_SEC}s intensity r "
                        f"({agglabel(_agg_r)}-agg) = {float(row600[_r_col].iloc[0]):.4f}")

        ok += draw(ctx, ax1, "", one)
        fig.set_layout_engine("constrained")
        save(ctx, fig, "bin_width", True, ok, 1)


def figS3(ctx: Ctx) -> None:
    """(a)(b) は legacy stage2 の s3_seed_bic、(c) は s6_error。"""
    with plt.rc_context(SUPP_RC):
        fig = plt.figure(figsize=(12.4, 3.2))
        # a-b は既定間隔(0.20)を維持し、詰まっていた b-c だけ広げる（スペーサ列で個別指定）
        _gs = fig.add_gridspec(1, 5, width_ratios=[1, 0.07, 1, 0.07, 1], wspace=0.0)
        axa = fig.add_subplot(_gs[0, 0]); axb = fig.add_subplot(_gs[0, 2]); axc = fig.add_subplot(_gs[0, 4])
        ok = 0

        def pa(ax):
            d = ctx.load("int_seed_stability.csv")
            if d is None or not len(d):
                raise LookupError("int_seed_stability.csv missing")
            # Section 3.4 は状態分類（τ = 60 s）。bin_sec を分けずに集約すると
            # 60 s と 600 s の rest_mu が混ざり、シード間変動ではなく
            # ビン幅間の差（約 10 対数分散単位）を拾ってしまう。
            if "bin_sec" not in d.columns:
                raise LookupError("int_seed_stability.csv: bin_sec 列がない")
            d = d[d["bin_sec"] == 60]
            if not len(d):
                raise LookupError("int_seed_stability.csv: bin_sec == 60 の行がない")
            agg = (d.groupby("seed")
                     .agg(rest_mean=("rest_mu", "mean"), rest_sd=("rest_mu", "std"),
                          act_mean=("active_mu", "mean"), act_sd=("active_mu", "std"))
                     .reset_index())
            ax.errorbar(agg["seed"], agg["rest_mean"], yerr=agg["rest_sd"], fmt="o", ms=4,
                        color=C_CTRL_NAVY, label="Rest μ", capsize=2, lw=0.9)
            ax.errorbar(agg["seed"], agg["act_mean"], yerr=agg["act_sd"], fmt="s", ms=4,
                        color=C_MAIN, label="Active μ", capsize=2, lw=0.9)
            ax.set_xlabel("Random seed")
            ax.set_ylabel("GMM component mean (PAI)")
            ax.legend(fontsize=6.0, loc="upper left", bbox_to_anchor=(1.005, 1.0),
                      frameon=False, borderaxespad=0.0, handletextpad=0.4)
            sd_rest = float(agg["rest_mean"].std())
            sd_act = float(agg["act_mean"].std())
            ax.set_title(f"(a) Seed stability (SD across seeds: rest={sd_rest:.4f}, "
                         f"act={sd_act:.4f})", fontsize=7.6)
            ctx.log(f"  (a) cross-seed SD: rest_mu={sd_rest:.5f}  active_mu={sd_act:.5f}")

        def pb(ax):
            dbic = ctx.load("int_gmm_bic.csv")
            if dbic is None or not len(dbic):
                raise LookupError("int_gmm_bic.csv missing")
            kcol = next((c for c in ("k", "K", "n_components") if c in dbic.columns), None)
            bcol = next((c for c in ("bic", "BIC") if c in dbic.columns), None)
            if not (kcol and bcol):
                raise LookupError(f"int_gmm_bic.csv: unexpected columns {list(dbic.columns)}")
            bic_med = dbic.groupby(kcol)[bcol].median().sort_index()
            ks = list(bic_med.index)
            yv = bic_med.values.astype(float)
            cols_k = [C_MAIN if int(k) == 2 else C_CTRL_GRAY for k in ks]
            hats_k = [H_MAIN if int(k) == 2 else H_GRAY for k in ks]
            ax.bar(range(len(ks)), yv, bottom=0, color=cols_k, hatch=hats_k,
                   edgecolor="black", linewidth=0.6, width=0.6, zorder=2)
            ax.set_xticks(range(len(ks)))
            ax.set_xticklabels([str(k) for k in ks])
            for i, v in enumerate(yv):
                ax.annotate(f"{v:,.0f}", (i, v), textcoords="offset points",
                            xytext=(0, 4), ha="center", fontsize=6.6)
            zero_baseline(ax, list(yv), top_extra=0.12)
            _kmin = int(ks[int(np.nanargmin(yv))]) if len(yv) else 2
            from matplotlib.patches import Patch as _Patch
            ax.legend(handles=[_Patch(facecolor=C_MAIN, hatch=H_MAIN, edgecolor="black",
                                      linewidth=0.6, label="Adopted (K = 2)"),
                               _Patch(facecolor=C_CTRL_GRAY, edgecolor="black",
                                      linewidth=0.6, label=f"Not adopted (BIC minimum: K = {_kmin})")],
                      fontsize=5.6, loc="upper right", framealpha=0.85)
            ctx.log(f"    [S3] BIC minimum is K={_kmin}; K=2 is adopted by elbow + interpretability, "
                    f"not by BIC minimum")
            ax.set_xlabel("Number of GMM components (K)")
            ax.set_ylabel("BIC (median across channels)")
            d12 = float(bic_med.loc[1] - bic_med.loc[2]) if {1, 2} <= set(bic_med.index) else np.nan
            d23 = float(bic_med.loc[2] - bic_med.loc[3]) if {2, 3} <= set(bic_med.index) else np.nan
            el = ctx.load("int_gmm_bic_elbow.csv")
            n_elbow2 = n_ch_total = 0
            if el is not None and "elbow_at_2" in el.columns:
                n_elbow2, n_ch_total = int(el["elbow_at_2"].sum()), len(el)
            if el is not None and "argmin_k" in el.columns:
                n2 = int((el["argmin_k"].astype(int) == 2).sum())
                ctx.value("figS3_n_ch_argmin_k_is_2", n2, f"of {len(el)} channels")
                ctx.log(f"    [S3] BIC argmin_k == 2 のチャンネル数 = {n2} / {len(el)}")
            if np.isfinite(d12) and np.isfinite(d23):
                ax.set_title(f"(b) BIC elbow: K=1->2 drop={d12:,.0f}; K=2->3 drop={d23:,.0f}\n"
                             f"BIC minimum never selects K=2 (argmin_k >= 3 in all channels);\n"
                             f"K=2 adopted by elbow + interpretability. "
                             f"elbow_at_2: {n_elbow2}/{n_ch_total} channels", fontsize=6.0)
            else:
                ax.set_title("(b) GMM component-count BIC", fontsize=9)
            ctx.log("  (b) " + "; ".join(f"K={k}: BIC={v:,.1f}" for k, v in bic_med.items()))
            try:
                _idx = dbic.groupby("ch")[bcol].idxmin()
                _votes = dbic.loc[_idx, kcol].astype(int).value_counts().sort_index()
                ctx.log("  (b) K-argmin votes across channels: "
                        + ", ".join(f"K={int(k)}:{int(n)}ch" for k, n in _votes.items())
                        + f" (total {int(_votes.sum())} ch)")
            except Exception as _e:  # noqa: BLE001
                ctx.log(f"  (b) K-argmin votes unavailable: {_e}")

        def pc(ax):
            d = ctx.load("int_error_bydist_perch.csv")
            if d is None or d.empty:
                raise LookupError("int_error_bydist_perch.csv missing/empty")
            mouse = (d.groupby(["mouse_id", "db"], observed=True)[["n", "n_error"]]
                       .sum().reset_index())
            mouse["error_rate"] = mouse["n_error"] / mouse["n"]
            rng = np.random.default_rng(2026)
            rows = []
            order = list(dict.fromkeys(d["db"].astype(str)))
            for db in order:
                g = mouse[mouse["db"].astype(str) == db].dropna(subset=["error_rate"])
                vals = g["error_rate"].to_numpy(float)
                pt = float(vals.mean()) if len(vals) else np.nan
                boots = []
                if len(vals):
                    for _ in range(5000):
                        boots.append(float(np.mean(rng.choice(vals, size=len(vals), replace=True))))
                lo, hi = (np.percentile(boots, [2.5, 97.5]) if boots else (np.nan, np.nan))
                rows.append({"db": db, "error_rate_mouse_mean": pt,
                             "ci_lower": lo, "ci_upper": hi, "n_mouse": len(vals)})
            z = pd.DataFrame(rows)
            x = np.arange(len(z))
            y = z["error_rate_mouse_mean"].to_numpy(float)
            lo = y - z["ci_lower"].to_numpy(float)
            hi = z["ci_upper"].to_numpy(float) - y
            ax.bar(x, y, yerr=[lo, hi], color=C_CTRL_NAVY, edgecolor="black",
                   linewidth=.5, capsize=3)
            ax.set_xticks(x)
            _db_labels = {"0-0.5": "0–0.5", "0.5-1": "0.5–1", "1-1.5": "1–1.5",
                          "1.5-2": "1.5–2", "2-3": "2–3"}
            ax.set_xticklabels([_db_labels.get(str(v), str(v)) for v in z["db"]],
                               rotation=30, ha="right")
            ax.set_xlabel("Distance from boundary (SD)")
            ax.set_ylabel("Error rate (mouse-cluster 95% CI)")
            rr = list(y[np.isfinite(y)])
            mono = all(rr[i] >= rr[i + 1] for i in range(len(rr) - 1)) if len(rr) > 1 else True
            ax.set_title(f"(c) Error vs standardized boundary distance\n"
                         f"monotonic decrease = {mono}; monotonicity is descriptive, "
                         f"not a publication criterion", fontsize=7.4)
            zero_baseline(ax, list(y + np.nan_to_num(hi)), top_extra=.08)
            ctx.log(f"  (c) monotonic decrease? {mono}. Figure retained regardless of this result.")

        for ax, letter, fn in zip([axa, axb, axc], "abc", [pa, pb, pc]):
            ok += draw(ctx, ax, letter, fn)
        fig.set_layout_engine("constrained")
        save(ctx, fig, "gmm_spec", True, ok, 3)


def figS4(ctx: Ctx) -> None:
    """legacy stage2 の s8_percapita と同じ共有軸グリッド。
    散布点はプールされたビンのまま描くが、表示する r は Table 2 と同じ
    per-channel Spearman を各 mouse 内で平均した推定量に一本化する。"""
    with plt.rc_context(SUPP_RC):
        b = ctx.load("int_binned.csv")
        chan = ctx.load("int_channel.csv")
        if b is None or b.empty or not {"mouse_id", "log_lp_var", "nanotag_count"}.issubset(b.columns):
            fig, axx = plt.subplots(figsize=(5, 3))
            fail_panel(axx, "", "int_binned.csv missing required columns")
            save(ctx, fig, "per_mouse", True, 0, 1)
            return

        ch_stats = {}
        ch_error = None
        if chan is None:
            ch_error = "int_channel.csv が無い"
        else:
            miss = [c for c in ("mouse_id", "intensity_r") if c not in chan.columns]
            if miss:
                ch_error = f"int_channel.csv に列が無い: {miss}"
            else:
                for mid, cg in chan.groupby("mouse_id"):
                    ch_stats[str(mid)] = {
                        "mean": float(cg["intensity_r"].mean()),
                        "n_ch": int(len(cg)),
                    }

        mids = sorted(b["mouse_id"].astype(str).unique())
        n = len(mids)
        cols = 4
        rows = int(np.ceil(n / cols))
        xlo, xhi = float(b["log_lp_var"].min()), float(b["log_lp_var"].max())
        ylo, yhi = float(b["nanotag_count"].min()), float(b["nanotag_count"].max())
        xpad = 0.03 * (xhi - xlo + 1e-9)
        ypad = 0.03 * (yhi - ylo + 1e-9)
        fig, axes = plt.subplots(rows, cols, figsize=(2.4 * cols, 2.2 * rows), squeeze=False)
        ax = axes.reshape(-1)
        ok = 0
        rs_chmean, rs_pooled = [], []

        for i, mid in enumerate(mids):
            def mk(mm):
                def f(axx):
                    if ch_error is not None:
                        raise LookupError(ch_error)
                    if mm not in ch_stats:
                        raise LookupError(f"int_channel.csv に mouse_id={mm} が無い")
                    chmean = ch_stats[mm]["mean"]
                    n_ch = ch_stats[mm]["n_ch"]
                    if not np.isfinite(chmean):
                        raise LookupError(f"mouse_id={mm} の intensity_r 平均が計算できない")
                    s = b[b["mouse_id"].astype(str) == mm]
                    axx.scatter(s["log_lp_var"], s["nanotag_count"], s=3, alpha=0.2,
                                color=C_MAIN)
                    pooled = spearman(s["log_lp_var"], s["nanotag_count"])
                    if not np.isfinite(pooled):
                        raise LookupError(f"mouse_id={mm} の pooled Spearman r を計算できない")
                    # legacy stage2 と同じ共有軸。8個体を直接見比べられるようにする。
                    axx.set_xlim(xlo - xpad, xhi + xpad)
                    axx.set_ylim(ylo - ypad, yhi + ypad)
                    axx.set_title(f"{_mouse_label(mm)}: Table 2 r={chmean:.3f} (n={n_ch} ch)", fontsize=7.0)
                    rs_chmean.append(chmean)
                    rs_pooled.append(pooled)
                    ctx.value(f"figS4_spearman_{mm}", round(chmean, 4),
                              "mean of channel-wise intensity_r, matches Table 2")
                    ctx.value(f"figS4_spearman_pooled_{mm}", round(pooled, 4),
                              "pooled bins within animal (not Table 2)")
                    ctx.log(f"  {_mouse_label(mm)}: mean r (ch)={chmean:.3f} (n={n_ch} ch); "
                            f"pooled-bin Spearman r={pooled:.3f} (n={len(s)} bins)")
                return f
            ok += draw(ctx, ax[i], "abcdefgh"[i] if i < 8 else str(i + 1), mk(mid))
        for j in range(n, len(ax)):
            ax[j].axis("off")
        # 共有軸グリッドの外周だけにラベルを置く（legacy stage2 と同じ体裁）
        for i in range(n):
            r, c = divmod(i, cols)
            if c == 0:
                ax[i].set_ylabel("NanoTag activity (counts / 10 min)", fontsize=8)
            if (r == rows - 1) or (i + cols >= n):
                ax[i].set_xlabel("PAI", fontsize=8)

        if rs_chmean and rs_pooled:
            cm_lo, cm_hi = min(rs_chmean), max(rs_chmean)
            pl_lo, pl_hi = min(rs_pooled), max(rs_pooled)
            ctx.log(f"    [S4] 個体別 Spearman r (ch平均, Table 2 と同一定義) = "
                    f"{cm_lo:.4f} - {cm_hi:.4f} (n={len(rs_chmean)})")
            ctx.log(f"    [S4] 個体別 Spearman r (ビンプール, 別定義) = "
                    f"{pl_lo:.4f} - {pl_hi:.4f} (n={len(rs_pooled)})")
            cm_range = f"{cm_lo:.4f}-{cm_hi:.4f}"
            ctx.value("figS4_spearman_range", cm_range,
                      "mean of channel-wise intensity_r, matches Table 2")
            ctx.value("figS4_spearman_range_chmean", cm_range,
                      "mean of channel-wise intensity_r, matches Table 2")
            ctx.log(f"  N mice={n}  shared x=[{xlo:.2f},{xhi:.2f}] y=[{ylo:.1f},{yhi:.1f}]")
        fig.suptitle("r = per-channel Spearman, averaged within each mouse (same estimator as Table 2)",
                     fontsize=9, y=0.995)
        fig.set_layout_engine("constrained")
        save(ctx, fig, "per_mouse", True, ok, n)


def figS5(ctx: Ctx) -> None:
    """(a) は legacy stage2 の s10_roc、(b) は s_algebraic_band。
    現物は2パネルのみ。旧S8のROCをS5(a)、代数的達成可能域をS5(b)とする。"""
    with plt.rc_context(SUPP_RC):
        chan = ctx.load("int_channel.csv")
        aucd = ctx.load("int_auc_metrics_cluster.csv")
        dif = ctx.load("int_auc_boot.csv")
        GOOD_F1 = ctx.good_cut

        # 旧 (a)（SNR と PAI contrast を1本のx軸に載せた散布図）は X_metric_vs_f1 に移した。
        # 単位の違う指標を共有x軸に置いていて軸が成立せず、しかも比較対象の par 自身が
        # 描かれていなかった。定量的な比較は (a) の ROC が担う。
        fig = plt.figure(figsize=(8.0, 3.6))
        gs = fig.add_gridspec(1, 2, wspace=.22)
        axb = fig.add_subplot(gs[0, 0]); axc = fig.add_subplot(gs[0, 1])
        ok = 0

        def pb(ax):
            if chan is None:
                raise LookupError("int_channel.csv missing")
            try:
                from sklearn.metrics import roc_curve  # noqa: PLC0415
            except Exception:  # noqa: BLE001
                def roc_curve(y, s):
                    o = np.argsort(-np.asarray(s, float))
                    yy = np.asarray(y, int)[o]
                    tpr = np.concatenate([[0], np.cumsum(yy) / max(yy.sum(), 1)])
                    fpr = np.concatenate([[0], np.cumsum(1 - yy) / max((1 - yy).sum(), 1)])
                    return fpr, tpr, None
            drew = 0
            for metric, label, col, ls in [("pir_active_rate", "PIR-AR", C_MAIN, "-"),
                                           ("snr", "SNR", C_CTRL_GRAY, "--"),
                                           ("pai_contrast", "PAI contrast", C_CTRL_GRAY, "-.")]:
                if metric not in chan:
                    continue
                v = chan.dropna(subset=[metric, "F1_state"])
                gg = (v["F1_state"] >= GOOD_F1).astype(int)
                if gg.nunique() < 2:
                    continue
                fpr, tpr, _ = roc_curve(gg, v[metric])
                ar = np.nan
                if aucd is not None and "metric" in aucd:
                    q = aucd[aucd["metric"].astype(str) == metric]
                    if len(q):
                        ar = float(q.iloc[0]["auc_observed"])
                if not np.isfinite(ar):
                    ctx.log(f"  {label}: AUC undefined, series omitted")
                    continue
                ax.plot(fpr, tpr, color=col, ls=ls, lw=1.5, label=f"{label} (AUC = {ar:.2f})")
                drew += 1
            if not drew:
                raise LookupError("ROC を描ける指標が無い")
            ax.plot([0, 1], [0, 1], ls=":", color="black", lw=.8)
            ax.set_xlabel("False positive rate")
            ax.set_ylabel("True positive rate")
            ax.set_title("(a) ROC", fontsize=9)
            ax.legend(fontsize=6, loc="lower right")
            if aucd is None:
                ctx.log("  [MISSING] S5(b): int_auc_metrics_cluster.csv が無いため AUC は nan 表示")
            if dif is not None:
                ctx.log("  paired AUC differences (exploratory CI only; no confirmatory "
                        "bootstrap p-value):\n" + dif.to_string(index=False))

        def pc(ax):
            d = ctx.load("int_channel.csv")
            if d is None or d.empty:
                raise LookupError("int_channel.csv missing")
            c = GOOD_F1
            x = np.linspace(0, max(float(d["nanotag_active_rate"].max()) * 1.08, 0.01), 300)
            lower = (c / (2 - c)) * x
            upper = ((2 - c) / c) * x
            ax.scatter(d["nanotag_active_rate"], d["pir_active_rate"], s=28, alpha=.8,
                       color=C_CTRL_NAVY)
            ax.plot(x, lower, "-", color="black", lw=1.3, label="Algebraic lower bound")
            ax.plot(x, upper, "--", color="black", lw=1.3, label="Algebraic upper bound")
            ax.set_xlabel("NanoTag active rate (NT-AR)")
            ax.set_ylabel("PIR active rate (PIR-AR)")
            ax.legend(fontsize=6.5)
            ax.set_title(f"(b) F1 >= {c:.2f} feasibility band (good_cut={c:.2f})", fontsize=9)
            nar = d["nanotag_active_rate"].astype(float).to_numpy()
            par = d["pir_active_rate"].astype(float).to_numpy()
            good = d["F1_state"].astype(float).to_numpy() >= c
            lo_hit = par < (c / (2 - c)) * nar
            hi_hit = par > ((2 - c) / c) * nar
            # 論文の主張は「QC を通過したのに bad だったチャンネル（= FP）を代数帯が説明できるか」。
            # bad チャンネル全体ではなく FP 部分集合が見出しの数値になる。
            fp = ((~good) & (d["qc1_pass"].astype(int).to_numpy() == 1)
                  if "qc1_pass" in d.columns else np.zeros(len(good), bool))
            ctx.value("figS5_fp_below_lower_bound", int(np.sum(fp & lo_hit)), f"of {int(fp.sum())} FP")
            ctx.value("figS5_fp_above_upper_bound", int(np.sum(fp & hi_hit)), f"of {int(fp.sum())} FP")
            ctx.value("figS5_bad_below_lower_bound", int(np.sum((~good) & lo_hit)),
                      f"of {int((~good).sum())} bad channels")
            ctx.value("figS5_bad_above_upper_bound", int(np.sum((~good) & hi_hit)),
                      f"of {int((~good).sum())} bad channels")
            ctx.log(f"    [S5] 代数帯 / QC通過かつbad(FP) {int(fp.sum())} ch中: "
                    f"下界違反 {int(np.sum(fp & lo_hit))} / 上界違反 {int(np.sum(fp & hi_hit))}")
            ctx.log(f"    [S5] 参考 / bad 全体 {int((~good).sum())} ch中: "
                    f"下界違反 {int(np.sum((~good) & lo_hit))} / 上界違反 "
                    f"{int(np.sum((~good) & hi_hit))}")

        for ax, letter, fn in zip([axb, axc], "ab", [pb, pc]):
            ok += draw(ctx, ax, letter, fn)
        save(ctx, fig, "qc_metrics", True, ok, 2)


def xfig_metric_vs_f1(ctx: Ctx) -> None:
    """X figure. Replaces the old FigS5(a). Each QC/reference metric gets its own
    panel and its own x axis, and par -- the metric the others are being compared
    against -- is now shown alongside them. Only par is reference-free; SNR,
    PAI contrast and within/between all need the NanoTag labels, so they cannot
    be used as an operational QC rule even where they discriminate well."""
    chan = ctx.load("int_channel.csv")
    if chan is None or chan.empty:
        ctx.log("  [skip] int_channel.csv が無い")
        return
    GOOD_F1 = ctx.good_cut
    specs = [("pir_active_rate", "par (PIR active rate)", "reference-free", C_MAIN),
             ("snr", "SNR", "needs reference", C_CTRL_NAVY),
             ("pai_contrast", "PAI contrast", "needs reference", C_ACCENT),
             ("within_over_between", "within / between", "needs reference", C_CTRL_GRAY)]
    specs = [t for t in specs if t[0] in chan.columns]
    if not specs:
        ctx.log("  [skip] 描ける指標が無い")
        return
    fig, axes = plt.subplots(1, len(specs), figsize=(2.6 * len(specs), 2.9))
    axes = np.atleast_1d(axes)
    for ax, (col, lab, tag, color) in zip(axes, specs):
        d = chan.dropna(subset=[col, "F1_state"])
        good = d["F1_state"].astype(float) >= GOOD_F1
        ax.scatter(d.loc[good, col], d.loc[good, "F1_state"], s=20, color=color,
                   alpha=.85, label="good")
        ax.scatter(d.loc[~good, col], d.loc[~good, "F1_state"], s=20,
                   facecolor="none", edgecolor=color, linewidth=.9, label="not good")
        ax.axhline(GOOD_F1, color="grey", ls=":", lw=.8)
        ax.set_xlabel(lab, fontsize=7)
        ax.set_title(f"{lab}\n({tag}, Spearman={spearman(d[col], d['F1_state']):.3f})",
                     fontsize=7)
        ctx.log(f"  {col}: Spearman vs F1 = {spearman(d[col], d['F1_state']):.4f}  "
                f"({tag}, n={len(d)})")
    axes[0].set_ylabel("State F1")
    axes[0].legend(fontsize=7)
    fig.set_layout_engine("constrained")
    save_explore(ctx, fig, "X_metric_vs_f1", "was FigS5(a); par added, per-metric axes")


def figS6(ctx: Ctx) -> None:
    """QC robustness and generalization.

    (a)(b): jackknife stability -- the plotted value is recomputed from the
    remaining seven mice after one mouse is removed. (c): true hold-out
    performance -- a threshold derived from the other seven mice is applied to
    the left-out mouse. r is descriptive and has no LOSO application target.
    """
    with plt.rc_context(SUPP_RC):
        _agg_r = str(getattr(config, "DISPLAY_R_AGG", "mean"))
        _agg_f1 = str(getattr(config, "DISPLAY_F1_AGG", "mean"))
        metric_f1 = "F1_qc1_mean" if _agg_f1 == "mean" else "F1_qc1_median_of_medians"
        chan = ctx.load("int_channel.csv")
        lt = ctx.load("int_loso_thr.csv")
        ho = ctx.load("int_holdout_f1.csv")

        fig, axes = plt.subplots(1, 3, figsize=(11.3, 3.7))
        ok = 0

        def pa(ax):
            if lt is None or not len(lt):
                raise LookupError("int_loso_thr.csv missing")
            if "qc1_threshold" not in lt.columns or "fold_excluded_mouse" not in lt.columns:
                raise LookupError("int_loso_thr.csv missing qc1_threshold/fold_excluded_mouse")
            d = lt.dropna(subset=["qc1_threshold"]).copy()
            x = np.arange(len(d))
            vals = pd.to_numeric(d["qc1_threshold"], errors="coerce").to_numpy(float)
            ref = get_threshold(ctx, chan)
            ax.plot(x, vals, linestyle="none", marker="o", ms=5.5,
                    markerfacecolor=C_ACCENT, markeredgecolor=C_ACCENT,
                    label="Jackknife (remaining 7 mice)")
            if np.isfinite(ref):
                ax.axhline(ref, color="black", lw=1.2, label=f"All-8 value = {ref:.3f}")
            ax.set_xticks(x)
            ax.set_xticklabels([_mouse_label(v) for v in d["fold_excluded_mouse"]], rotation=45,
                               ha="right", fontsize=6.5)
            ax.set_xlabel("Held-out mouse")
            ax.set_ylabel("QC threshold (PIR-AR), remaining 7 mice")
            ax.set_title("(a) QC threshold: jackknife stability", fontsize=8.5)
            ax.legend(fontsize=5.7)
            center_ylim(ctx, ax, S5_YLIM["a"][0], S5_YLIM["a"][1],
                        list(vals) + ([ref] if np.isfinite(ref) else []), "S6(a)")
            ctx.log(f"  (a) jackknife threshold: n={len(vals)} "
                    f"range=[{np.nanmin(vals):.3f}, {np.nanmax(vals):.3f}] "
                    f"all-8 reference = {ref:.3f}")

        def pb(ax):
            if chan is None or chan.empty:
                raise LookupError("int_channel.csv missing")
            _gfn = "mean" if _agg_r == "mean" else "median"
            pm = chan.groupby("mouse_id")["intensity_r"].agg(_gfn).dropna()
            mice = list(pm.index)
            if len(mice) < 2:
                raise LookupError("too few mice for jackknife r")
            vals = [center_of(pm.drop(index=excl).values, _agg_r) for excl in mice]
            ref = center_of(pm.values, _agg_r)
            x = np.arange(len(mice))
            ax.plot(x, vals, linestyle="none", marker="o", ms=5.5,
                    markerfacecolor=C_CTRL_NAVY, markeredgecolor=C_CTRL_NAVY,
                    label="Jackknife (remaining 7 mice)")
            ax.axhline(ref, color="black", lw=1.2, label=f"All-8 value = {ref:.3f}")
            ax.set_xticks(x)
            ax.set_xticklabels([_mouse_label(v) for v in mice], rotation=45, ha="right", fontsize=6.5)
            ax.set_xlabel("Held-out mouse")
            ax.set_ylabel("Intensity r, remaining 7 mice")
            ax.set_title("(b) Intensity r: jackknife stability", fontsize=8.5)
            ax.legend(fontsize=5.7)
            center_ylim(ctx, ax, S5_YLIM["b"][0], S5_YLIM["b"][1],
                        vals + [ref], "S6(b)")
            ctx.log(f"  (b) jackknife r: all-8 = {ref:.3f} "
                    f"range=[{min(vals):.3f}, {max(vals):.3f}]")

        def pc(ax):
            if ho is None or not len(ho) or "holdout_f1" not in ho.columns:
                raise LookupError("int_holdout_f1.csv missing")
            if "fold_excluded_mouse" not in ho.columns:
                raise LookupError("int_holdout_f1.csv missing fold_excluded_mouse")
            d = ho.copy()
            d["holdout_f1"] = pd.to_numeric(d["holdout_f1"], errors="coerce")
            d = d.dropna(subset=["holdout_f1"]).reset_index(drop=True)
            if not len(d):
                raise LookupError("no evaluable hold-out folds")
            x = np.arange(len(d))
            vals = d["holdout_f1"].to_numpy(float)
            ax.plot(x, vals, color=C_MAIN, lw=1.2, linestyle="none", marker="^", ms=6.0,
                    markerfacecolor=C_MAIN, markeredgecolor=C_MAIN, markeredgewidth=1.1,
                    label="Held-out mouse")
            ci_qc = ci_of(ctx, metric_f1)
            ref = ci_qc[0] if ci_qc else np.nan
            if np.isfinite(ref):
                ax.axhline(ref, color="black", lw=1.2,
                           label=f"Operational F1 = {ref:.2f}")
            ax.set_xticks(x)
            ax.set_xticklabels([_mouse_label(v) for v in d["fold_excluded_mouse"]], rotation=45,
                               ha="right", fontsize=6.5)
            ax.set_xlabel("Held-out mouse")
            ax.set_ylabel("F1 of the held-out mouse")
            ax.set_title("(c) Generalization to the held-out mouse", fontsize=8.5)
            ax.legend(fontsize=5.2)
            center_ylim(ctx, ax, S5_YLIM["c"][0], S5_YLIM["c"][1],
                        list(vals) + ([ref] if np.isfinite(ref) else []), "S6(c)")
            hm = float(np.mean(vals))
            ctx.value("figS6_holdout_f1_mean", round(hm, 4),
                      f"n={len(vals)} folds; true leave-one-mouse-out")
            ctx.log(f"  (c) hold-out F1: n={len(vals)} mean={hm:.2f} "
                    f"range=[{np.min(vals):.2f}, {np.max(vals):.2f}] "
                    f"operational reference={ref:.2f}")

        for ax, letter, fn in zip(axes, "abc", [pa, pb, pc]):
            ok += draw(ctx, ax, letter, fn)
        fig.set_layout_engine("constrained", wspace=0.12)
        note = ("(a)(b) は leave-one-mouse-out による推定の安定性、(c) は各 fold の7頭から得た"
                "閾値を除外した1頭に適用した hold-out 性能（pass channel を持たない個体を除くため N=7）。"
                "参照線は (a)(b) が全8頭の凍結値、(c) が運用値。")
        save(ctx, fig, "qc_robust", True, ok, 3, note)
        ctx.log("  [caption] (a)(b) は leave-one-mouse-out による推定の安定性、"
                "(c) は各 fold の7頭から得た閾値を除外した1頭に適用した hold-out 性能"
                "（pass channel を持たない個体を除くため N=7）。")
        ctx.log("  [caption] 参照線: (a)(b)=全8頭の凍結値、(c)=運用値。")


def figS7(ctx: Ctx) -> None:
    """QC independence. Former FigS6(d)(e), re-lettered to (a)(b)."""
    with plt.rc_context(SUPP_RC):
        _agg_r = str(getattr(config, "DISPLAY_R_AGG", "mean"))
        stat_fn_r = permouse_mean if _agg_r == "mean" else permouse_median
        GOOD_F1 = ctx.good_cut
        chan = ctx.load("int_channel.csv")

        fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.5))
        ok = 0

        def pa(ax):
            if chan is None:
                raise LookupError("int_channel.csv missing")
            r_fail = stat_fn_r(chan[chan["qc1_pass"] == 0], "intensity_r").dropna().values
            r_pass = stat_fn_r(chan[chan["qc1_pass"] == 1], "intensity_r").dropna().values
            r_all = stat_fn_r(chan, "intensity_r").dropna().values
            groups = [
                {"label": f"QC-fail\n(N = {len(r_fail)})", "values": r_fail},
                {"label": f"QC-pass\n(N = {len(r_pass)})", "values": r_pass},
                {"label": f"All\n(N = {len(r_all)})", "values": r_all},
            ]
            bar_dots(ax, groups, colors=[C_CTRL_GRAY, C_MAIN, C_CTRL_NAVY],
                     hatches=[H_GRAY, H_MAIN, H_NAVY], err="sd", center=_agg_r)
            _alr = agglabel(_agg_r)
            ax.set_ylabel("Intensity r")
            sp_par_r = spearman(chan["pir_active_rate"], chan["intensity_r"])
            ax.set_title(f"(a) Intensity r across QC state\n"
                         f"Spearman par vs r={sp_par_r:.3f}", fontsize=8.0)
            ctx.log(f"  S7(a) r {_alr}: fail={center_of(r_fail, _agg_r):.3f} "
                    f"pass={center_of(r_pass, _agg_r):.3f} all={center_of(r_all, _agg_r):.3f}  "
                    f"Spearman(par,r)={sp_par_r:.3f}")

        def pb(ax):
            if chan is None:
                raise LookupError("int_channel.csv missing")
            cc = chan.dropna(subset=["F1_state"]).copy()
            per_mouse = cc.groupby("mouse_id")["F1_state"].mean().sort_index(key=_mouse_sort_key)
            groups_b = [{"label": _mouse_label(mid), "values": cc[cc["mouse_id"] == mid]["F1_state"].values}
                        for mid in per_mouse.index]
            bar_dots(ax, groups_b, colors=[C_CTRL_NAVY] * len(groups_b),
                     hatches=[H_MAIN] * len(groups_b), err="sd", center="mean")
            ax.axhline(GOOD_F1, color="black", ls=":", lw=0.9,
                       label=f"Good-channel criterion (F1 ≥ {GOOD_F1:.2f})")
            ax.legend(fontsize=6.0)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=6.5)
            ax.set_ylabel("State F1 (per mouse: ch mean ± SD)")
            ax.set_title(f"(b) Per-mouse state F1 (good={GOOD_F1:g})", fontsize=8.5)
            ctx.log(f"  S7(b) flat median F1 across all channels={med(cc['F1_state']):.4f}  "
                    f"N_mice={len(per_mouse)}")

        for ax, letter, fn in zip(axes, "ab", [pa, pb]):
            ok += draw(ctx, ax, letter, fn)
        fig.set_layout_engine("constrained", wspace=0.12)
        save(ctx, fig, "qc_independence", True, ok, 2,
             "QC-independence panels moved from former S6(d)(e) and re-lettered (a)(b)")

def figS8(ctx: Ctx) -> None:
    """Recording-length stability (former Figure S7 / old Figure S10)."""
    with plt.rc_context(SUPP_RC):
        d = ctx.load("int_qc_learning.csv")
        chan = ctx.load("int_channel.csv")
        GOOD_F1 = ctx.good_cut
        fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.1))
        ok = 0

        if d is None or d.empty:
            for i, letter in enumerate("ab"):
                fail_panel(axes[i], letter, "int_qc_learning.csv missing")
            save(ctx, fig, "record_length", True, 0, 2)
            return

        thr = get_threshold(ctx, chan) if chan is not None else np.nan
        has_hours = "approx_hours" in d.columns
        # 集約単位の修正: 以前は n_active_bins_state で直接 std を取っていたため、帯は
        # 32チャンネル間のSD（技術的反復）だったのに凡例は "across mice" と書いていた。
        # 論文の推論単位は個体(n=8)なので、まず個体内でチャンネルを平均し、その個体平均に
        # 対して mean と SD を取る（mean-of-means と同じ規約）。
        _pm = (d.groupby(["n_active_bins_state", "mouse_id"])
                 .agg(par_so_far=("par_so_far", "mean"), f1_so_far=("f1_so_far", "mean"))
                 .reset_index())
        aggd = {"par_mean": ("par_so_far", "mean"), "par_sd": ("par_so_far", "std"),
                "f1_mean": ("f1_so_far", "mean"), "f1_sd": ("f1_so_far", "std"),
                "n_mouse": ("par_so_far", "count")}
        agg = (_pm.groupby("n_active_bins_state").agg(**aggd).reset_index()
                  .sort_values("n_active_bins_state"))
        agg["n_ch"] = (d.groupby("n_active_bins_state")["par_so_far"].count()
                        .reindex(agg["n_active_bins_state"]).to_numpy())
        if has_hours:
            agg["approx_hours"] = (d.groupby("n_active_bins_state")["approx_hours"].median()
                                    .reindex(agg["n_active_bins_state"]).to_numpy())

        stable = {}
        if len(agg) > 1:
            # 収束の基準も mean-of-means に揃える（旧版は ch のフラット平均で、曲線側の
            # 集約単位と食い違っていた）。参考として旧定義の値もログに出す。
            if chan is not None and not chan.empty and "mouse_id" in chan.columns:
                final_par = float(chan.groupby("mouse_id")["pir_active_rate"].mean().mean())
                final_f1 = float(chan.groupby("mouse_id")["F1_state"].mean().mean())
                ctx.log(f"  [参考] 旧定義(ch フラット平均) final par="
                        f"{float(chan['pir_active_rate'].mean()):.4f} "
                        f"F1={float(chan['F1_state'].mean()):.4f} / "
                        f"本図で使う mean-of-means par={final_par:.4f} F1={final_f1:.4f}")
            else:
                final_par = agg["par_mean"].iloc[-1]
                final_f1 = agg["f1_mean"].iloc[-1]
            _x = list(agg["n_active_bins_state"])
            _pv = list(agg["par_mean"]); _fv = list(agg["f1_mean"])
            _ptol = .02 * max(abs(final_par), 1e-9); _ftol = .02 * max(abs(final_f1), 1e-9)
            for i, xv in enumerate(_x):
                if "par_first" not in stable and abs(_pv[i] - final_par) <= _ptol:
                    stable["par_first"] = xv
                if "f1_first" not in stable and abs(_fv[i] - final_f1) <= _ftol:
                    stable["f1_first"] = xv
                if "par" not in stable and all(abs(v - final_par) <= _ptol for v in _pv[i:]):
                    stable["par"] = xv
                if "f1" not in stable and all(abs(v - final_f1) <= _ftol for v in _fv[i:]):
                    stable["f1"] = xv
            ctx.log(f"  convergence first-hit vs sustained: "
                    f"par={stable.get('par_first')}/{stable.get('par')}; "
                    f"F1={stable.get('f1_first')}/{stable.get('f1')}. Sustained means every later "
                    f"evaluation remains within ± 2% of final.")

        def pa(ax):
            if "ch" in d.columns:
                for _i, (_ch, _g) in enumerate(d.groupby("ch")):
                    _g = _g.sort_values("n_active_bins_state")
                    ax.plot(_g["n_active_bins_state"], _g["par_so_far"], lw=.45, alpha=.25,
                            label="Individual channels" if _i == 0 else None)
            ax.plot(agg["n_active_bins_state"], agg["par_mean"], "-o", color=C_MAIN, ms=3)
            ax.fill_between(agg["n_active_bins_state"], agg["par_mean"] - agg["par_sd"],
                            agg["par_mean"] + agg["par_sd"], color=C_MAIN, alpha=0.2,
                            label="Mean ± SD across mice (N = 8)")
            if pd.notna(thr):
                ax.axhline(thr, color="black", ls="--", lw=1.0,
                           label=f"QC threshold = {thr:.3f}")
            ax.legend(fontsize=6.3, loc="upper right", framealpha=0.85)
            ax.set_xlabel("Cumulative Active bins")
            ax.set_ylabel("PIR-AR (mean ± SD across mice)")
            ax.set_title("(a) PIR-AR vs cumulative Active bins", fontsize=9)
            if has_hours and stable.get("par") is not None:
                hrow = agg[agg["n_active_bins_state"] == stable["par"]]
                if len(hrow):
                    ax.annotate(f"≈{float(hrow['approx_hours'].iloc[0]):.1f} h equiv. "
                                f"at n={int(stable['par'])}", xy=(0.03, 0.94),
                                xycoords="axes fraction", fontsize=6.0, color="black", ha="left")

        def pb(ax):
            if "ch" in d.columns:
                for _i, (_ch, _g) in enumerate(d.groupby("ch")):
                    _g = _g.sort_values("n_active_bins_state")
                    ax.plot(_g["n_active_bins_state"], _g["f1_so_far"], lw=.45, alpha=.25,
                            label="Individual channels" if _i == 0 else None)
            ax.plot(agg["n_active_bins_state"], agg["f1_mean"], "-o", color=C_CTRL_NAVY, ms=3)
            ax.fill_between(agg["n_active_bins_state"], agg["f1_mean"] - agg["f1_sd"],
                            agg["f1_mean"] + agg["f1_sd"], color=C_CTRL_NAVY, alpha=0.2,
                            label="Mean ± SD across mice (N = 8)")
            ax.axhline(GOOD_F1, color="black", ls=":", lw=0.9,
                       label=f"Good-channel criterion (F1 ≥ {GOOD_F1:.2f})")
            ax.legend(fontsize=6.3, loc="upper right", framealpha=0.85)
            ax.set_xlabel("Cumulative Active bins")
            ax.set_ylabel("State F1 (mean ± SD across mice)")
            ax.set_title("(b) F1 vs cumulative active bins", fontsize=9)

        ok += draw(ctx, axes[0], "a", pa)
        ok += draw(ctx, axes[1], "b", pb)
        fig.set_layout_engine("constrained", wspace=0.12)
        save(ctx, fig, "record_length", True, ok, 2)
        ctx.log(f"  集約単位=個体(mean-of-means), 帯=個体間SD  "
                f"N mice={d['mouse_id'].nunique()}  par-stable at={stable.get('par')}  "
                f"F1-stable at={stable.get('f1')}")


def xfig_session_diag(ctx: Ctx) -> None:
    """Exploratory: former supplementary session diagnostic (old S8)."""
    rec = ctx.load("int_session_diagnostic.csv")
    summ = ctx.load("int_session_summary.csv")
    trend = ctx.load("int_session_trend.csv")
    sy = ctx.load("int_session_sensor_control.csv")

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 3.4))
    ok = 0

    def pa(ax):
        if rec is None or rec.empty:
            raise LookupError("int_session_diagnostic.csv missing")
        r = (rec[rec["row_type"].astype(str).eq("record_summary")]
             if "row_type" in rec.columns else rec.copy())
        r = r.sort_values("record_id")
        _lab = RecordLabeler().fit(r["record_id"])
        ctx.log(f"  [record 表示名] {_lab.legend_note()}")
        ycol = ("par_over_nar_ch_mean" if "par_over_nar_ch_mean" in r.columns
                else "par_over_nar")
        y = pd.to_numeric(r[ycol], errors="coerce").to_numpy(float)
        yerr = pd.to_numeric(r.get("par_over_nar_ch_sd", pd.Series(np.zeros(len(r)))),
                             errors="coerce").fillna(0).to_numpy(float)
        x = np.arange(len(r))
        ax.bar(x, y, yerr=yerr, capsize=3, edgecolor="black", linewidth=0.6,
               color=C_MAIN, alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels([_lab.rec(v) for v in r["record_id"]], rotation=30, ha="right")
        ax.set_ylabel("Detection ratio par/nar\n(mean ± SD across channels in the record)")
        ax.set_xlabel("Record")
        ax.set_title("(a) Record-level detection ratio", fontsize=9)
        zero_baseline(ax, list(y + yerr), top_extra=0.08)

    def pb(ax):
        if summ is None or not len(summ):
            raise LookupError("int_session_summary.csv missing")
        z = summ.copy().sort_values(["record_id", "block_start_h"])
        _lab = RecordLabeler().fit(z["record_id"])
        shade = (z[z["block_index"].astype(int) % 2 == 0][["block_start_h", "block_end_h"]]
                 .drop_duplicates())
        for _, q in shade.iterrows():
            ax.axvspan(float(q["block_start_h"]), float(q["block_end_h"]),
                       color="0.90", zorder=0)
        for recid, g in z.groupby("record_id"):
            gx = pd.to_numeric(g["block_start_h"], errors="coerce").to_numpy(float)
            gy = pd.to_numeric(g["par_over_nar_mean"], errors="coerce").to_numpy(float)
            ge = pd.to_numeric(g["par_over_nar_sd"], errors="coerce").to_numpy(float)
            ax.plot(gx, gy, marker="o", lw=1.1, label=_lab.rec(recid))
            okm = np.isfinite(gx) & np.isfinite(gy) & np.isfinite(ge)
            if okm.any():
                ax.fill_between(gx[okm], gy[okm] - ge[okm], gy[okm] + ge[okm], alpha=0.08)
        ax.set_xlabel("Hours from record start")
        ax.set_ylabel("Detection ratio par/nar\n(mean ± SD across channels in each 12-h block)")
        ax.set_title("(b) 12-h block trajectory (grey = dark blocks)", fontsize=9)
        ax.legend(fontsize=7)

    def pc(ax):
        if sy is None or not len(sy):
            raise LookupError("int_session_sensor_control.csv missing")
        recids = []
        for col in sy.columns:
            if col.startswith("pir_active_rate_"):
                rr = col.replace("pir_active_rate_", "")
                if f"nanotag_active_rate_{rr}" in sy.columns:
                    recids.append(rr)
        recids = sorted(set(recids))
        _labc = RecordLabeler().fit(recids)
        if len(recids) < 2:
            raise LookupError("paired Set-Y columns missing")
        sx = np.arange(len(sy), dtype=float)
        offsets = np.linspace(-0.16, 0.16, len(recids))
        for off, rr in zip(offsets, recids):
            pv = pd.to_numeric(sy[f"pir_active_rate_{rr}"], errors="coerce")
            nv = pd.to_numeric(sy[f"nanotag_active_rate_{rr}"], errors="coerce").replace(0, np.nan)
            ratio = (pv / nv).to_numpy(float)
            ax.plot(sx + off, ratio, "o", ms=4, label=_labc.rec(rr))
        if len(recids) == 2:
            a = (pd.to_numeric(sy[f"pir_active_rate_{recids[0]}"], errors="coerce")
                 / pd.to_numeric(sy[f"nanotag_active_rate_{recids[0]}"],
                                 errors="coerce").replace(0, np.nan)).to_numpy(float)
            bb = (pd.to_numeric(sy[f"pir_active_rate_{recids[1]}"], errors="coerce")
                  / pd.to_numeric(sy[f"nanotag_active_rate_{recids[1]}"],
                                  errors="coerce").replace(0, np.nan)).to_numpy(float)
            for i in range(len(sy)):
                if np.isfinite(a[i]) and np.isfinite(bb[i]):
                    ax.plot([sx[i] + offsets[0], sx[i] + offsets[1]], [a[i], bb[i]],
                            color="0.65", lw=0.7, zorder=0)
        ax.set_xticks(sx)
        ax.set_xticklabels(sy["sensor_id"].astype(str), rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("par/nar")
        ax.set_xlabel("Set-Y physical sensor ID")
        ax.set_title("(c) Same physical sensors (set Y), different mice", fontsize=9)
        ax.legend(fontsize=7)

    for ax, letter, fn in zip(axes, "abc", [pa, pb, pc]):
        ok += draw(ctx, ax, letter, fn)
    fig.set_layout_engine("constrained")
    save_explore(ctx, fig, "xfig_session_diag",
                 "former FigS8; 2x2 residual is interaction/session-confounded and is not a session effect")
    if trend is not None and len(trend):
        for _, q in trend.sort_values("record_id").iterrows():
            ctx.log(f"  trend {q['record_id']}: {q.get('trend_class','?')}  "
                    f"first={q.get('ratio_first', np.nan):.4f} "
                    f"last={q.get('ratio_last', np.nan):.4f} "
                    f"delta={q.get('ratio_delta', np.nan):+.4f}")


def xfig_temporal_qc(ctx: Ctx) -> None:
    """Exploratory: legacy stage2 s13 temporal stability (former supplementary S9).
    強調するチャンネルは運用規則（flag_saturated / flag_floor_shift）で決める。
    legacy stage2 は stability_flag != 'stable' を使うが、それは flag_unstable_range を含み
    運用判定と一致しないため、強調チャンネルは運用規則側で決める。"""
    tc = ctx.load("int_session_timecourse.csv")
    st = ctx.load("int_channel_stability.csv")

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.6), sharex=False)
    ok = 0

    if tc is None or tc.empty or st is None or st.empty:
        for i, letter in enumerate("ab"):
            fail_panel(axes[i], letter,
                       "int_session_timecourse.csv or int_channel_stability.csv missing")
        fig.set_layout_engine("constrained")
        save_explore(ctx, fig, "xfig_temporal_qc",
                     "former FigS9; inputs missing, panel failure is shown in the figure")
        return

    if "block_usable" in tc.columns:
        tc = tc[tc["block_usable"].eq(1)]
    st = st.copy()
    op = (st.get("flag_saturated", pd.Series(0, index=st.index)).fillna(0).astype(int).eq(1)
          | st.get("flag_floor_shift", pd.Series(0, index=st.index)).fillna(0).astype(int).eq(1))
    flagged = set(st.loc[op, "ch"].astype(str))
    flag_map = {}
    if "stability_flag" in st.columns:
        flag_map = st.set_index(st["ch"].astype(str))["stability_flag"].astype(str).to_dict()

    _lab = RecordLabeler().fit(
        [str(c).split("_")[0] for c in tc["ch"].astype(str).unique()])

    def _panel(ax, ycol, ylab, title):
        for ch, g in tc.groupby("ch"):
            chs = str(ch)
            gg = g.sort_values("block_start_h") if "block_start_h" in g.columns \
                else g.sort_values("block_index")
            xcol = "block_start_h" if "block_start_h" in gg.columns else "block_index"
            x = pd.to_numeric(gg[xcol], errors="coerce").to_numpy(float)
            y = pd.to_numeric(gg[ycol], errors="coerce").to_numpy(float)
            is_flag = chs in flagged
            color = C_MAIN if is_flag else "0.72"
            ax.plot(x, y, marker="o" if is_flag else None, ms=3, color=color,
                    lw=1.8 if is_flag else 0.55, alpha=0.95 if is_flag else 0.45,
                    zorder=3 if is_flag else 1)
            if is_flag:
                okk = np.where(np.isfinite(x) & np.isfinite(y))[0]
                if len(okk):
                    j = okk[-1]
                    ax.annotate(_lab.ch(chs), (x[j], y[j]), xytext=(3, 0),
                                textcoords="offset points", fontsize=7, color=color)
        ax.set_xlabel("Hours from record start"
                      if "block_start_h" in tc.columns else "12 h block index")
        ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=9)

    def pa(ax):
        _panel(ax, "par", "Blockwise par", "(a) 32-channel blockwise par")
        sat = float(getattr(config, "TEMPORAL_PAR_SATURATION_THRESHOLD", 0.95))
        ax.axhline(sat, color="black", ls="--", lw=0.8,
                   label=f"saturation rule par ≥ {sat:g}")
        ax.legend(fontsize=7)
        ctx.log(f"    [S9] record 表示名: {_lab.legend_note()}")
        ctx.log(f"    [S9] 運用フラグが立ったch = {len(flagged)}: "
                f"{', '.join(sorted(flagged)) or 'なし'}")
        for ch in sorted(flagged):
            ctx.log(f"      {ch}: {flag_map.get(ch, '?')}")

    def pb(ax):
        if "pai_rest_component_mean" not in tc.columns:
            raise LookupError("int_session_timecourse.csv に pai_rest_component_mean が無い")
        _panel(ax, "pai_rest_component_mean", "PAI rest-component mean",
               "(b) Blockwise GMM rest component")

    ok += draw(ctx, axes[0], "a", pa)
    ok += draw(ctx, axes[1], "b", pb)
    fig.set_layout_engine("constrained")
    save_explore(ctx, fig, "xfig_temporal_qc",
                 "former FigS9; temporal stability screen (reference-free); flagged channels highlighted")



def _xfig_state_grid(ctx: Ctx, qc_flag: int, stem: str) -> None:
    """All-channel Fig4(a) disclosure grid.

    Each channel is a two-row pair using ONE rest-centered scale and ONE set of
    bin edges. Top: the pooled histogram plus the fitted GMM curves. Bottom: the
    same histogram bins partitioned only by the NanoTag truth label. The lower
    stacked counts therefore sum exactly to the upper histogram bin-by-bin.
    """
    sh = ctx.load("int_state_hist.csv")
    chan = ctx.load("int_channel.csv")
    gp = ctx.load("int_gmm_params.csv")
    if sh is None or chan is None or gp is None:
        ctx.log(f"  [skip] {stem}: int_state_hist/int_channel/int_gmm_params missing")
        return
    need_sh = {"ch", "log_lp_var", "nano_label"}
    need_ch = {"ch", "qc1_pass", "pir_active_rate"}
    need_gp = {"ch", "comp", "mean", "sd", "weight"}
    if not need_sh.issubset(sh.columns) or not need_ch.issubset(chan.columns) \
            or not need_gp.issubset(gp.columns):
        ctx.log(f"  [skip] {stem}: required columns missing")
        return

    meta = chan[["ch", "qc1_pass", "pir_active_rate"]].copy()
    meta["ch"] = meta["ch"].astype(str)
    meta["qc1_pass"] = pd.to_numeric(meta["qc1_pass"], errors="coerce")
    meta["pir_active_rate"] = pd.to_numeric(meta["pir_active_rate"], errors="coerce")
    meta = (meta[meta["qc1_pass"].eq(int(qc_flag))]
            .dropna(subset=["pir_active_rate"]).drop_duplicates("ch")
            .sort_values(["pir_active_rate", "ch"]).reset_index(drop=True))
    if meta.empty:
        ctx.log(f"  [skip] {stem}: no channels in qc_flag={qc_flag}")
        return

    rr = gp[gp["comp"].astype(str).eq("rest")][["ch", "mean"]].copy()
    rr["ch"] = rr["ch"].astype(str)
    rr["rest_mode"] = pd.to_numeric(rr["mean"], errors="coerce")
    rr = rr.dropna(subset=["rest_mode"]).drop_duplicates("ch")
    if rr.empty:
        ref, _ = rest_reference_mu(ctx)
        if ref is None or ref.empty:
            ctx.log(f"  [skip] {stem}: rest centering unavailable")
            return
        rr = ref[["ch", "nano_mu"]].copy().rename(columns={"nano_mu": "rest_mode"})
        rr["ch"] = rr["ch"].astype(str)

    d = sh[["ch", "log_lp_var", "nano_label"]].copy()
    d["ch"] = d["ch"].astype(str)
    d["log_lp_var"] = pd.to_numeric(d["log_lp_var"], errors="coerce")
    d["nano_label"] = pd.to_numeric(d["nano_label"], errors="coerce")
    d = d.merge(rr[["ch", "rest_mode"]], on="ch", how="inner")
    d["pai_centered"] = d["log_lp_var"] - pd.to_numeric(d["rest_mode"], errors="coerce")
    d = d[d["ch"].isin(meta["ch"])].dropna(subset=["pai_centered", "nano_label"])

    n = len(meta)
    ncol = min(4, n)
    nrow = int(np.ceil(n / ncol))
    fig = plt.figure(figsize=(2.8 * ncol, 3.15 * nrow))
    outer = fig.add_gridspec(nrow, ncol, wspace=0.34, hspace=0.50)

    for i, q in meta.iterrows():
        r, c = divmod(i, ncol)
        sub = outer[r, c].subgridspec(2, 1, hspace=0.05)
        at = fig.add_subplot(sub[0, 0])
        ab = fig.add_subplot(sub[1, 0], sharex=at)
        ch = str(q["ch"])
        dd = d[d["ch"] == ch]
        vals = dd["pai_centered"].to_numpy(float)
        if len(vals) < 4:
            at.text(.5, .5, "insufficient bins", ha="center", va="center", transform=at.transAxes)
            ab.axis("off")
            continue
        lo, hi = float(np.min(vals)), float(np.max(vals))
        gpc = gp[gp["ch"].astype(str).eq(ch)].copy()
        rest0 = float(rr.loc[rr["ch"].eq(ch), "rest_mode"].iloc[0])
        for _, gr in gpc.iterrows():
            mm = pd.to_numeric(pd.Series([gr.get("mean")]), errors="coerce").iloc[0]
            ss = pd.to_numeric(pd.Series([gr.get("sd")]), errors="coerce").iloc[0]
            if np.isfinite(mm) and np.isfinite(ss):
                lo = min(lo, float(mm) - rest0 - FIG4_XSD_PAD * float(ss))
                hi = max(hi, float(mm) - rest0 + FIG4_XSD_PAD * float(ss))
        pad = FIG4_XMARGIN_FRAC * max(hi - lo, 1e-9)
        lo, hi = lo - pad, hi + pad
        nedge = int(np.clip(np.sqrt(max(len(vals), 4)) * 1.5, 25, 55))
        bins = np.linspace(lo, hi, nedge)
        centers = 0.5 * (bins[:-1] + bins[1:])
        bw = float(bins[1] - bins[0])
        all_counts, _ = np.histogram(vals, bins=bins)
        rest_vals = dd[dd["nano_label"].eq(0)]["pai_centered"].to_numpy(float)
        act_vals = dd[dd["nano_label"].eq(1)]["pai_centered"].to_numpy(float)
        rest_counts, _ = np.histogram(rest_vals, bins=bins)
        act_counts, _ = np.histogram(act_vals, bins=bins)

        at.bar(centers, all_counts, width=bw, color="0.82", edgecolor="none", align="center")
        xx = np.linspace(lo, hi, 300)
        total_curve = np.zeros_like(xx)
        for _, gr in gpc.iterrows():
            mm = float(gr["mean"]) - rest0
            ss = float(gr["sd"])
            ww = float(gr["weight"])
            yy = ww * norm.pdf(xx, mm, ss) * len(vals) * bw
            total_curve += yy
            col = C_CTRL_NAVY if str(gr["comp"]) == "rest" else C_MAIN
            at.plot(xx, yy, color=col, lw=1.0)
        if len(gpc):
            at.plot(xx, total_curve, color="black", lw=0.8, ls="--")
        at.axvline(0, color="black", lw=0.6, ls=":")

        ab.bar(centers, rest_counts, width=bw, color=C_CTRL_NAVY, alpha=0.60,
               edgecolor="none", align="center")
        ab.bar(centers, act_counts, bottom=rest_counts, width=bw, color=C_MAIN, alpha=0.52,
               edgecolor="none", align="center")
        ab.axvline(0, color="black", lw=0.6, ls=":")
        ymax = max(float(np.max(all_counts)) if len(all_counts) else 0.0,
                   float(np.max(rest_counts + act_counts)) if len(rest_counts) else 0.0)
        if ymax > 0:
            at.set_ylim(0, ymax * 1.08)
            ab.set_ylim(0, ymax * 1.08)
        at.set_xlim(lo, hi)
        at.tick_params(labelbottom=False, labelsize=5.2)
        ab.tick_params(labelsize=5.2)
        at.set_title(f"{ch}  par={float(q['pir_active_rate']):.2f}", fontsize=7)
        at.text(0.01, 0.95, "Grid 1: all bins + GMM", transform=at.transAxes,
                ha="left", va="top", fontsize=7)
        ab.text(0.01, 0.95, "Grid 2: same bins by NanoTag", transform=ab.transAxes,
                ha="left", va="top", fontsize=7)
        if c == 0:
            at.set_ylabel("Count", fontsize=7)
            ab.set_ylabel("Count", fontsize=7)
        if r == nrow - 1:
            ab.set_xlabel("PAI - channel rest mode", fontsize=7)

    status = "QC pass" if int(qc_flag) == 1 else "QC fail"
    fig.suptitle(f"{status} channels: each lower histogram is the upper histogram recolored by NanoTag truth",
                 fontsize=9.0, y=0.998)
    fig.legend(handles=[
        Line2D([0], [0], color=C_CTRL_NAVY, lw=5, label="Rest (NanoTag=0)"),
        Line2D([0], [0], color=C_MAIN, lw=5, label="Active (NanoTag>0)"),
        Line2D([0], [0], color="black", lw=1, ls="--", label="GMM total"),
    ], loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 0.002))
    fig.set_layout_engine("constrained")
    ctx.log(f"  {stem}: n_channels={n}; paired top/bottom axes share x scale and exact bin edges")
    save_explore(ctx, fig, stem,
                 f"Fig4(a) all-channel disclosure; {status}; top=all bins+GMM, bottom=same bins recolored by NanoTag")


def xfig_grid_pass(ctx: Ctx) -> None:
    _xfig_state_grid(ctx, 1, "xfig_grid_pass")


def xfig_grid_fail(ctx: Ctx) -> None:
    _xfig_state_grid(ctx, 0, "xfig_grid_fail")

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



def xfig_channel_ridge(ctx: Ctx) -> None:
    """Exploratory disclosure: all-channel PAI ridgeline ordered by par."""
    sh = ctx.load("int_state_hist.csv")
    chan = ctx.load("int_channel.csv")
    gp = ctx.load("int_gmm_params.csv")

    fig, ax = plt.subplots(figsize=(4.6, 6.4))
    try:
        if sh is None or chan is None:
            raise LookupError("int_state_hist.csv / int_channel.csv missing")
        need_sh = {"ch", "log_lp_var"}
        need_ch = {"ch", "pir_active_rate", "qc1_pass"}
        if not need_sh.issubset(sh.columns):
            raise LookupError(f"int_state_hist.csv missing columns: {sorted(need_sh - set(sh.columns))}")
        if not need_ch.issubset(chan.columns):
            raise LookupError(f"int_channel.csv missing columns: {sorted(need_ch - set(chan.columns))}")

        meta = chan[["ch", "pir_active_rate", "qc1_pass"]].copy()
        meta["ch"] = meta["ch"].astype(str)
        meta["pir_active_rate"] = pd.to_numeric(meta["pir_active_rate"], errors="coerce")
        meta["qc1_pass"] = pd.to_numeric(meta["qc1_pass"], errors="coerce")
        meta = meta.dropna(subset=["pir_active_rate", "qc1_pass"]).drop_duplicates("ch")
        meta = meta.sort_values(["pir_active_rate", "ch"]).reset_index(drop=True)
        if meta.empty:
            raise LookupError("no channel metadata for ridgeline")

        d = sh[["ch", "log_lp_var"]].copy()
        d["ch"] = d["ch"].astype(str)
        d["log_lp_var"] = pd.to_numeric(d["log_lp_var"], errors="coerce")
        d = d[d["ch"].isin(meta["ch"])].dropna(subset=["log_lp_var"])
        if d.empty:
            raise LookupError("no state_hist values for ridgeline")

        xv = d["log_lp_var"].to_numpy(float)
        xlo, xhi = float(np.nanmin(xv)), float(np.nanmax(xv))
        if not (np.isfinite(xlo) and np.isfinite(xhi)) or xhi <= xlo:
            raise LookupError("PAI range is not finite")
        xpad = 0.02 * max(xhi - xlo, 1e-9)
        xlo, xhi = xlo - xpad, xhi + xpad
        bins = np.linspace(xlo, xhi, 70)
        centers = 0.5 * (bins[:-1] + bins[1:])

        boundary_map = {}
        if gp is not None and {"ch", "boundary"}.issubset(gp.columns):
            gg = gp[["ch", "boundary"]].copy()
            gg["ch"] = gg["ch"].astype(str)
            gg["boundary"] = pd.to_numeric(gg["boundary"], errors="coerce")
            boundary_map = (gg.dropna(subset=["boundary"]).drop_duplicates("ch")
                            .set_index("ch")["boundary"].to_dict())
        if "gmm_boundary" in chan.columns:
            for _, q in chan[["ch", "gmm_boundary"]].dropna().iterrows():
                boundary_map.setdefault(str(q["ch"]), float(q["gmm_boundary"]))

        for yi, q in meta.iterrows():
            ch = str(q["ch"])
            vv = d[d["ch"] == ch]["log_lp_var"].to_numpy(float)
            if not len(vv):
                continue
            h, _ = np.histogram(vv, bins=bins, density=True)
            peak = float(np.nanmax(h)) if len(h) else 0.0
            hs = (h / peak * 0.78) if peak > 0 else h
            col = C_MAIN if int(q["qc1_pass"]) == 1 else C_CTRL_GRAY
            ax.fill_between(centers, yi, yi + hs, color=col, alpha=0.72, linewidth=0)
            ax.plot(centers, yi + hs, color=col, lw=0.65)
            bnd = boundary_map.get(ch, np.nan)
            if np.isfinite(bnd):
                ax.vlines(float(bnd), yi, yi + 0.70, color="black", lw=0.75)

        flags = meta["qc1_pass"].astype(int).to_numpy()
        pass_idx = np.where(flags == 1)[0]
        split = int(pass_idx.min()) if len(pass_idx) else None
        if split is not None and split > 0:
            ax.axhline(split - 0.5, color="black", lw=1.0, ls="--")
            ax.text(xhi, split - 0.38, "QC threshold", ha="right", va="bottom", fontsize=7)

        tick_step = max(1, int(np.ceil(len(meta) / 16)))
        ticks = np.arange(0, len(meta), tick_step)
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"{meta.iloc[i]['ch']}  par={meta.iloc[i]['pir_active_rate']:.2f}"
                            for i in ticks], fontsize=7)
        ax.set_ylim(-0.2, len(meta) - 0.05 + 0.82)
        ax.set_xlim(xlo, xhi)
        ax.set_xlabel("PAI")
        ax.set_ylabel("Channels ordered by par (low to high)")
        ax.set_title("All-channel PAI distributions ordered by par (disclosure only)", fontsize=8.6)
        ax.legend(handles=[
            Line2D([0], [0], color=C_MAIN, lw=5, label="QC pass"),
            Line2D([0], [0], color=C_CTRL_GRAY, lw=5, label="QC fail"),
            Line2D([0], [0], color="black", lw=1, label="GMM boundary"),
        ], fontsize=7, loc="upper left")
        ctx.log(f"  xfig_channel_ridge: n_channels={len(meta)} ordered by par; "
                f"QC pass={int((flags == 1).sum())}, fail={int((flags == 0).sum())}; "
                f"x=[{xlo:.3f},{xhi:.3f}]")
        if split is not None:
            ctx.log(f"  ridgeline QC transition after sorted row {split} "
                    f"(low side fail, high side pass; no ctx.value added)")
        fig.set_layout_engine("constrained")
        save_explore(ctx, fig, "xfig_channel_ridge",
                     "all-channel PAI ridgeline ordered by par; disclosure only")
    except Exception as e:  # noqa: BLE001
        ctx.log(f"    xfig_channel_ridge 描画できず: {e}")
        fail_panel(ax, "", str(e))
        fig.set_layout_engine("constrained")
        save_explore(ctx, fig, "xfig_channel_ridge",
                     "all-channel PAI ridgeline ordered by par; disclosure only; failure shown in figure")

# ==================================================================== 実行
BUILDERS = [fig1, fig2, fig3, fig4, fig5, fig6,
            figS1, figS2, figS3, figS4, figS5, figS6, figS7, figS8,
            xfig_mismatched_pairs, xfig_metric_vs_f1,
            xfig_grid_pass, xfig_grid_fail, xfig_channel_ridge,
            xfig_session_diag, xfig_temporal_qc]


def _natkey(p):
    # Natural sort so FigS2 precedes FigS10.
    import re as _re
    base = os.path.splitext(os.path.basename(p))[0]
    return [int(t) if t.isdigit() else t.lower() for t in _re.split(r"(\d+)", base)]


def build_contact_sheets(ctx: Ctx) -> None:
    import glob
    os.makedirs(ctx.contact, exist_ok=True)
    for catdir, d, out_name in [
        ("main", ctx.main, "contact_sheet_main.png"),
        ("supplementary", ctx.supp, "contact_sheet_supp.png"),
    ]:
        pngs = [
            q for q in glob.glob(os.path.join(d, "**", "*.png"), recursive=True)
            if "contact_sheet" not in os.path.basename(q)
        ]
        pngs = sorted(pngs, key=_natkey)
        if not pngs:
            continue
        ncol = min(4, len(pngs))
        nrow = int(np.ceil(len(pngs) / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(ncol * 4.2, nrow * 3.2))
        axes = np.atleast_1d(axes).ravel()
        for ax in axes:
            ax.axis("off")
        for ax, q in zip(axes, pngs):
            try:
                ax.imshow(plt.imread(q))
            except Exception:
                pass
            ax.set_title(os.path.splitext(os.path.basename(q))[0], fontsize=9)
            ax.axis("off")
        fig.set_layout_engine("constrained")
        fig.savefig(os.path.join(ctx.contact, out_name), dpi=110)
        plt.close(fig)
        ctx.log(f"  contact sheet [{ctx.mode}/{catdir}]: {len(pngs)} -> {out_name}")


def run_version(base: str, good_cut: float) -> Ctx | None:
    collected: Ctx | None = None
    for titled in (True, False):
        ctx = Ctx(base, good_cut, titled=titled, collect=titled)
        if not os.path.isdir(ctx.inter):
            print(f"[skip] {ctx.inter} missing")
            return None
        _clean_mode_outputs(ctx)
        if titled:
            ctx.log(f"\n================ {ctx.version} (good_cut={good_cut}) ================")
            ctx.log(f"入力: {ctx.inter}")
        else:
            print(f"\n================ {ctx.version} / untitled ================", flush=True)
        for fn in BUILDERS:
            ctx.log(f"\n[{fn.__name__}]")
            try:
                fn(ctx)
            except Exception as e:  # noqa: BLE001
                ctx.log(f"  [図全体が失敗] {e}")
                ctx.log("  " + traceback.format_exc(limit=2).replace("\n", "\n  "))
                ctx.registry.append({
                    "version": ctx.version, "mode": ctx.mode,
                    "label": fn.__name__, "stem": fn.__name__,
                    "kind": ("exploratory" if fn.__name__.startswith("xfig") else
                             ("main" if fn.__name__.startswith("fig") and
                              not fn.__name__.startswith("figS") else "supplementary")),
                    "panels_total": -1, "panels_ok": 0, "status": "FAILED",
                    "output_dir": "", "note": str(e)})
        build_contact_sheets(ctx)
        if collected is None:
            collected = ctx
        else:
            collected.registry.extend(ctx.registry)
    return collected


def main() -> int:
    _init_console()
    check_display_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default=_default_base())
    ap.add_argument("--versions", nargs="*", type=float, default=[0.70, 0.80])
    a = ap.parse_args()
    if not a.base:
        print("データフォルダを特定できませんでした。次のいずれかで指定してください:")
        print(f'  1) 引数で渡す:  python {os.path.basename(__file__)} "C:\\Users\\...\\最新データ"')
        print("  2) 環境変数 SENSORS_BASE_DATA_DIR を設定する")
        print("  3) 同じフォルダに config.py を置く（その BASE_DATA_DIR を読みます）")
        return 1

    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    reg, vals, caps = [], [], None
    for gc in a.versions:
        ctx = run_version(a.base, gc)
        if ctx is None:
            continue
        caps = ctx.captions
        reg += ctx.registry
        vals += ctx.values
        pd.DataFrame(ctx.values).to_csv(
            os.path.join(ctx.captions, f"figure_values_{ctx.version}.csv"),
            index=False, encoding=ENC)
        write_caption_payload(ctx)

    if caps:
        r = pd.DataFrame(reg)
        r["generated"] = stamp
        r.to_csv(os.path.join(caps, "figure_table_registry_figures.csv"),
                 index=False, encoding=ENC)
        pd.DataFrame(OLD2NEW, columns=["old_label", "new_label"]).to_csv(
            os.path.join(caps, "figure_number_old2new.csv"), index=False, encoding=ENC)

        print("\n================ まとめ ================")
        for (v, mode), g in r.groupby(["version", "mode"], sort=False):
            bad = g[g["status"] != "OK"]
            print(f"{v}/{mode}: {len(g)} 図中 OK {int((g['status'] == 'OK').sum())}")
            for _, x in bad.iterrows():
                print(f"   [{x['status']}] {x['label']}  "
                      f"panels {x['panels_ok']}/{x['panels_total']}  {x['note']}")
        print(f"\n番号一覧: {os.path.join(caps, 'figure_table_registry_figures.csv')}")
        print(f"旧新対応: {os.path.join(caps, 'figure_number_old2new.csv')}")
        print("キャプション用の実測値: figure_values_<version>.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())