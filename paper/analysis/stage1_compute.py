"""
stage1_compute.py — 完全置換版（改良バッチ v3）

全数値は mapping.csv＋生データから計算（結果値の手打ちリテラル禁止）。
確定ゲートは PAPER_VALUES.md の専用照合ブロックだけに旧値リテラルを保持する。
追加はすべて加算的（新規列・新規CSV・新規print）。

■ 改良バッチ v3（既存の fit_gmm / compute_state_qc / _boot / load_nano / run_one 構造は維持）
  [V3-1] PAPER_VALUES: 1.2M上限、重要度順、巨大CSV要約、前後TRUNCATION WARNING。
  [V3-2] CSV writer registry: 全 int_*.csv を _write_csv 経由で追跡し、生成 / PRE-EXISTING / ORPHAN を区別。
  [V3-3] int_session_summary / int_session_trend: 12hブロック集計と記録内トレンド。
  [V3-4] int_channel_stability / int_qc_temporal_compare: 参照不要の時間的安定性QC。
  [V3-5] label sweepの閾値出所と main threshold を併記、gmm_argmax の threshold_note を追加。

■ 第7版での変更（Fig1候補の複線化。既存の計算経路には触れない）
  [V7-1] int_raw_trace.csv に ch / variant 列を追加し、窓の選び方を3通り保存する。
         median     … 従来と同一（active/rest それぞれ median-PAI ビン）＝既存Fig1の再現性を保証
         high       … active=最大PAIビン / rest=最小PAIビン（コントラスト最大）
         transition … rest→active の切替（PAI跳躍が最大の箇所）から lead ビン手前で開始
         config.RAW_TRACE_EXTRA_CH で REPR_CH 以外のchも候補にできる。
         一覧は int_raw_trace_index.csv に出力（legacy stage2がFig1候補として全部描く）。
  ※ int_raw_trace は描画専用。PAI/GMM/F1/強度r の計算には一切使われない＝確定ゲート不変。

■ 第6版での変更（3点。いずれも既存の計算経路には触れない）
  [V6-1] 生ADC診断＋ raw_value_adc 列
         ・ch ループ先頭で「読んでいる列が本当に生ADCか」を毎回印字する
           （dtype / min / max / range / median / n_unique / smallest_step）。
           10bit ADC なら smallest_step=1・range=数十〜数百。小数ステップや range<1 なら
           前処理済み・正規化済みの列を掴んでいる＝mapping.csv の pir_col を要確認。
         ・int_raw_trace.csv に raw_value_adc（中央値減算前の生値）を追加。
           ※中央値減算は平行移動なので分散・PAI・GMM・F1・r には一切影響しない＝ゲート不変。
  [V6-2] int_feature_bench_perch.csv（集約前の ch別 強度r）を追加保存。
         S2(a) に個体点を重ねるため（第6版 §0b）。新規CSVを1本増やすだけ。
  [V6-3] _good_sensitivity() に threshold_source 列とフォールバックを追加。
         good_cut を上げると fold 内で good/bad が片側に偏り LOMO が成立せず全列 NaN になる。
         その cut に限り全データROCで閾値を代替し、出所を threshold_source に明記する。
         good=0.70 は必ず fold が成立するためフォールバックに入らない＝確定ゲート不変。
  ※ 現行 config.RAW_WINDOW_S / RAW_DRAW_WINDOW_S は 150 秒。int_raw_trace は描画専用なのでゲートに影響しない。

■ 第4版からの構成（維持）
  [A-1] int_raw_trace.csv: 窓を config.RAW_WINDOW_S に、nanotag_count 列つきで保存。
  [A-3] log効果軸・帯域効果軸の特徴量を state/intensity 両側で出力。
  [A-4] 状態F1(QC後)のLOSO → int_loso_f1.csv
  [A-5] good_cut 感度に PPV / par-AUC / n_good_ch / n_bad_ch / n_fold_used
  [A-6] QCルール梯子を4段に拡張: par_only / par_snr / par_sep / par_snr_sep（ASCIIキー）
  [Old] RECORDS_OLD=[] を前提に、Old在庫チェックを print
  [Set] sensor_set を sensor_id 先頭文字（X/Y）で決定。旧方式（ファイル名署名）も併走して比較。
  [Gate] 検算printに SetA/SetB の r・IQR・多条件QCの通過頭数を追加

■ 探索計算（config.RUN_EXPLORATORY / RUN_LPF_SWEEP）
  X1  int_lpf_sweep.csv            LPFカットオフ掃引 0.5/1/2/5Hz × 強度r・状態F1【重い】
  X2  int_state_confusion_perch.csv ch別 TP/FP/FN/TN + precision/recall/MCC/kappa/FP-FN比
  X3  int_auc_boot.csv             par vs SNR の AUC差ブートストラップCI（個体クラスタ）
  X4  int_state_baseline.csv       GMM vs Otsu vs 中央値分割 vs 固定分位 の F1
  X5  int_channel の列             intensity_r_darkonly / _lightonly / _lightincl
  X6  int_channel の列             n_hours / n_bins_intensity / frac_missing
  X7  int_bland_altman.csv         センサー間一致の Bland-Altman（bias, LoA）
  X8  int_darkdef_sensitivity.csv  暗期定義 ±1h ずらしの強度r
  X9  int_qc_confusion / int_good_sensitivity（上記A-5/A-6で拡張）
  X10 int_qc_threshold_sweep.csv   par閾値の連続掃引（通過ch数・PPV・QC後F1）

■ 重要（実装上の不変条件）
  ・int_bootstrap_ci の rng は 1個を使い回すため、新規指標は必ず既存5件の「後ろ」に追加すること。
    途中挿入すると乱数ストリームがずれ、確定ゲートの95%CIが変わる。
  ・_good_sensitivity / _feat / 生ADC診断はいずれも乱数を使わない＝乱数ストリームに影響しない。
"""

import gc
import glob
import io
import os
import re
import sys
import time
import traceback
import argparse
import hashlib
import inspect
import shutil

import numpy as np
import pandas as pd
from scipy import signal as scipy_signal
from scipy.stats import kurtosis, skew, spearmanr, bootstrap
from sklearn.metrics import (
    cohen_kappa_score,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
    roc_curve,
)
from sklearn.mixture import GaussianMixture

if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
        write_through=True,
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
        write_through=True,
    )

import config

LPF_ORDER = int(getattr(config, "LOWPASS_ORDER", 4))  # configを唯一の実効値ソースにする

GOOD_F1 = float(getattr(config, "QC1_GOOD_F1", 0.70))
GOOD_CUT_SWEEP = sorted(
    set(float(x) for x in getattr(config, "GOOD_CUT_SWEEP", [0.70]))
)
# [S1-GRID] Table S1 のみが使う good 定義のグリッド。
#   採用 good_cut / GOOD_CUT_SWEEP / GOOD_CUT_VERSIONS とは独立で、
#   int_good_sensitivity_grid.csv にだけ書き出す（他の出力には一切影響しない）。
GOOD_CUT_GRID = sorted(
    set(
        float(x)
        for x in getattr(
            config, "GOOD_CUT_GRID", [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
        )
    )
)
QC1_MULTI_SNR_MIN = float(getattr(config, "QC1_MULTI_SNR_MIN", 1.0))
QC1_MULTI_GMM_SEP_MIN = float(getattr(config, "QC1_MULTI_GMM_SEP_MIN", 1.0))
RUN_SUPP = bool(getattr(config, "RUN_SUPPLEMENTARY", True))
RUN_EXPL = bool(getattr(config, "RUN_EXPLORATORY", True))
RAW_WINDOW_S = int(getattr(config, "RAW_WINDOW_S", 300))
SENSOR_SET_ORDER = list(getattr(config, "SENSOR_SET_ORDER", ["X", "Y"]))
LPF_SWEEP_HZ = list(getattr(config, "LPF_SWEEP_HZ", [0.5, 1.0, 2.0, 5.0]))
DARK_DEF_SHIFTS = list(getattr(config, "DARK_DEF_SHIFTS", [-1, 0, 1]))
PAR_THRESHOLD_SWEEP = list(getattr(config, "PAR_THRESHOLD_SWEEP", []))

# ---------------------------------------------------------------- trace utils
_T0 = time.time()


def log(msg):
    print(f"[{time.time() - _T0:7.1f}s] {msg}", flush=True)


# ---------------------------------------------------------------- loaders
def load_and_concat_csvs(file_list, target_cols=None, _tag="csv"):
    if not file_list:
        return None
    df_list = []
    for fpath in sorted(file_list):
        if not os.path.exists(fpath):
            continue
        _t = time.time()
        log(f"      [{_tag}] read開始: {os.path.basename(fpath)}")
        try:
            if target_cols:
                header = pd.read_csv(
                    fpath,
                    encoding="shift_jis",
                    nrows=0,
                    usecols=lambda c: "Unnamed" not in str(c),
                ).columns.tolist()
                if not header:
                    log(f"      [{_tag}] header空スキップ: {os.path.basename(fpath)}")
                    continue
                first = header[0]
                use_c = [
                    c for c in header if str(c) == str(first) or str(c) in target_cols
                ]
                df_sub = pd.read_csv(fpath, encoding="shift_jis", usecols=use_c)
            else:
                df_sub = pd.read_csv(
                    fpath,
                    encoding="shift_jis",
                    usecols=lambda c: "Unnamed" not in str(c),
                )
        except Exception as e:
            log(f"      [{_tag}] shift_jis失敗→utf-8再読込 ({e})")
            df_sub = pd.read_csv(
                fpath, encoding="utf-8", usecols=lambda c: "Unnamed" not in str(c)
            )
        log(f"      [{_tag}] read完了 rows={len(df_sub)} → 日時パース中...")
        if not df_sub.empty:
            t = df_sub.columns[0]
            df_sub[t] = pd.to_datetime(df_sub[t], errors="coerce", cache=True)
            df_sub.dropna(subset=[t], inplace=True)
            df_sub.set_index(t, inplace=True)
            df_list.append(df_sub)
        log(
            f"      [{_tag}] {os.path.basename(fpath)} 完了 rows={len(df_sub)} ({time.time() - _t:.1f}s)"
        )
    if not df_list:
        return None
    if len(df_list) == 1:
        return df_list[0]
    log(f"      [{_tag}] concat {len(df_list)}ファイル ...")
    res = pd.concat(df_list, axis=0)
    res.sort_index(inplace=True)
    return res[~res.index.duplicated(keep="first")]


def load_nano(nid, s_path, nano_fullpath):
    cand = [
        f
        for f in glob.glob(os.path.join(s_path, f"*nanotag*{nid}*.csv"))
        if not any(k in f.lower() for k in ["pir", "control", "summary", "results"])
    ]
    if nano_fullpath not in cand and os.path.exists(nano_fullpath):
        cand.append(nano_fullpath)
    merged = []
    for c in sorted(set(cand)):
        if not os.path.exists(c):
            continue
        _t = time.time()
        log(f"      [nano {nid}] read開始: {os.path.basename(c)}")
        d = pd.read_csv(c, encoding="shift_jis", usecols=[0, 1])
        tc, vc = d.columns[0], d.columns[1]
        _raw_v = d[vc].copy()
        _missing_before = int(_raw_v.isna().sum())
        _num_v = pd.to_numeric(_raw_v, errors="coerce")
        _coercion_fail = int((_num_v.isna() & _raw_v.notna()).sum())
        _bad = _num_v.isna().to_numpy()
        _runs = []
        _cur = 0
        for _z in _bad:
            if _z:
                _cur += 1
            elif _cur:
                _runs.append(_cur); _cur = 0
        if _cur:
            _runs.append(_cur)
        d[tc] = pd.to_datetime(d[tc], errors="coerce", cache=True)
        d[vc] = _num_v.fillna(0)  # 既存挙動は維持。診断は fillna 前に取得済み。
        d.dropna(subset=[tc], inplace=True)
        d.set_index(tc, inplace=True)
        d.columns = ["Activity"]
        d.attrs["integrity"] = {
            "source_file": os.path.basename(c),
            "missing_cells_before_coercion": _missing_before,
            "coercion_to_nan_count": _coercion_fail,
            "missing_run_count": int(len(_runs)),
            "longest_missing_run": int(max(_runs) if _runs else 0),
        }
        merged.append(d)
        log(f"      [nano {nid}] 完了 rows={len(d)} ({time.time() - _t:.1f}s)")
    if not merged:
        return None
    _ints = [m.attrs.get("integrity", {}) for m in merged]
    dn = pd.concat(merged, axis=0)
    dn.sort_index(inplace=True)
    dn = dn[~dn.index.duplicated(keep="first")]
    dn.attrs["integrity"] = {
        "source_file": ";".join(i.get("source_file", "") for i in _ints),
        "missing_cells_before_coercion": int(sum(i.get("missing_cells_before_coercion", 0) for i in _ints)),
        "coercion_to_nan_count": int(sum(i.get("coercion_to_nan_count", 0) for i in _ints)),
        "missing_run_count": int(sum(i.get("missing_run_count", 0) for i in _ints)),
        "longest_missing_run": int(max([i.get("longest_missing_run", 0) for i in _ints] or [0])),
    }
    return dn


def lpf_coef(fs, cutoff=1.0, order=LPF_ORDER):
    b, a = scipy_signal.butter(order, cutoff / (0.5 * fs), btype="low")
    return b, a


def logvar_perbin(series, rule, origin, b, a):
    """per-binにLPF→分散→log（step0_exploreと同一の per-bin filtfilt）"""

    def _f(x):
        v = x.values
        if len(v) < 30:
            return np.nan
        try:
            return np.log(np.var(scipy_signal.filtfilt(b, a, v)) + 1e-10)
        except Exception:
            return np.nan

    return series.resample(rule, origin=origin).apply(_f)


def stat_perbin(series, rule, origin, b, a, statfn):
    """per-binにLPF→任意統計量(statfn)。logvar_perbinの対関数。"""

    def _f(x):
        v = x.values
        if len(v) < 30:
            return np.nan
        try:
            return float(statfn(scipy_signal.filtfilt(b, a, v)))
        except Exception:
            return np.nan

    return series.resample(rule, origin=origin).apply(_f)


def var_perbin(series, rule, origin, b, a):
    """per-binにLPF→分散（logなし）。"""
    return stat_perbin(series, rule, origin, b, a, np.var)


def raw_stat_perbin(series, rule, origin, statfn):
    """LPFなしのper-bin統計量。"""

    def _f(x):
        v = x.values
        if len(v) < 30:
            return np.nan
        try:
            return float(statfn(v))
        except Exception:
            return np.nan

    return series.resample(rule, origin=origin).apply(_f)


def band_power_perbin(series, rule, origin, fs, lo, hi):
    """per-binにWelch PSD→指定帯域[lo,hi)Hzのパワー(和)。"""

    def _f(x):
        v = x.values
        if len(v) < 64:
            return np.nan
        try:
            f, p = scipy_signal.welch(v, fs, nperseg=min(len(v), 256))
            return float(np.sum(p[(f >= lo) & (f < hi)]))
        except Exception:
            return np.nan

    return series.resample(rule, origin=origin).apply(_f)


def highpass_coef(fs, cutoff_hz, order=4):
    nyq = fs / 2.0
    return scipy_signal.butter(order, cutoff_hz / nyq, btype="highpass")


def bandpass_coef(fs, lo_hz, hi_hz, order=4):
    nyq = fs / 2.0
    return scipy_signal.butter(order, [lo_hz / nyq, hi_hz / nyq], btype="bandpass")


def fit_gmm(logvar):
    """2成分GMMをfitし、分類は predict() の事後確率argmaxを維持する。

    boundary は分類には使わない。S9距離軸・Fig4境界線・報告列専用。
    rest_mu--act_mu の内部で事後確率差が符号反転する場合だけ boundary を返す。
    全域の交点が rest_mu より外側にある場合は outer_crossing_flag を立てる。
    """
    x = np.asarray(logvar, float)
    x = x[np.isfinite(x)]
    if len(x) < 12 or np.std(x) < 1e-12:
        return None
    g = GaussianMixture(
        n_components=int(getattr(config, "GMM_N_COMPONENTS", 2)),
        random_state=int(getattr(config, "GMM_RANDOM_STATE", 42)),
        n_init=int(getattr(config, "GMM_N_INIT", 1)),
    ).fit(x.reshape(-1, 1))
    m = g.means_.flatten()
    rest = int(np.argmin(m))
    act = 1 - rest
    rest_mu, act_mu = float(m[rest]), float(m[act])

    def _crossings(grid):
        proba = g.predict_proba(np.asarray(grid).reshape(-1, 1))
        d = proba[:, rest] - proba[:, act]
        hit = np.where(np.isclose(d, 0.0, atol=1e-12))[0].tolist()
        flip = np.where(np.signbit(d[:-1]) != np.signbit(d[1:]))[0].tolist()
        vals = []
        for i in hit:
            vals.append(float(grid[i]))
        for i in flip:
            x0, x1 = float(grid[i]), float(grid[i + 1])
            y0, y1 = float(d[i]), float(d[i + 1])
            vals.append(x0 if y1 == y0 else x0 - y0 * (x1 - x0) / (y1 - y0))
        return sorted(set(vals))

    inner_grid = np.linspace(rest_mu, act_mu, 4001)
    inner = [v for v in _crossings(inner_grid) if rest_mu <= v <= act_mu]
    no_interior_crossing = len(inner) == 0
    boundary = float(inner[0]) if inner else np.nan

    full_grid = np.linspace(float(x.min()), float(x.max()), 8001)
    outer_all = _crossings(full_grid)
    outer_low = [v for v in outer_all if v < rest_mu]
    outer_crossing_flag = int(bool(outer_low))
    outer_crossing = float(max(outer_low)) if outer_low else np.nan

    return {
        "g": g,
        "rest": rest,
        "rest_mu": rest_mu,
        "act_mu": act_mu,
        "boundary": boundary,
        "no_interior_crossing": bool(no_interior_crossing),
        "outer_crossing_flag": outer_crossing_flag,
        "outer_crossing": outer_crossing,
    }


# ★X4: 1次元 Otsu 閾値（GMM不使用ベースライン用）
def otsu_threshold(x, nbins=256):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 12 or np.std(x) < 1e-12:
        return np.nan
    hist, edges = np.histogram(x, bins=nbins)
    centers = (edges[:-1] + edges[1:]) / 2.0
    w = hist.astype(float)
    tot = w.sum()
    if tot <= 0:
        return np.nan
    p = w / tot
    omega = np.cumsum(p)
    mu = np.cumsum(p * centers)
    mu_t = mu[-1]
    denom = omega * (1.0 - omega)
    with np.errstate(divide="ignore", invalid="ignore"):
        sigma_b = (mu_t * omega - mu) ** 2 / denom
    sigma_b[~np.isfinite(sigma_b)] = -np.inf
    return float(centers[int(np.argmax(sigma_b))])


# ★V6-1: 生ADC列の素性診断（読んでいる系列が本当に生ADCかを毎回開示する）
def adc_diagnostic(series, col_name, dtype):
    """戻り値は表示用の文字列。計算には一切使わない（副作用なし）。"""
    try:
        v = np.asarray(series.values, dtype=float)
        v = v[np.isfinite(v)]
        if not len(v):
            return f"col='{col_name}' 有効値なし"
        uq = np.unique(v)
        step = float(np.min(np.diff(uq))) if len(uq) > 1 else np.nan
        rng = float(np.ptp(v))
        msg = (
            f"col='{col_name}' dtype={dtype} min={v.min():.6g} max={v.max():.6g} "
            f"range={rng:.6g} median={float(np.median(v)):.6g} n_unique={len(uq)} "
            f"smallest_step={step:.6g}"
        )
        if rng < 1.0:
            msg += "  <<< range<1: 10bit ADC(0-1023)ではない＝前処理済み列の疑い。"
        elif np.isfinite(step) and abs(step - 1.0) < 1e-9:
            msg += "  (step=1 → 整数ADC系列として整合)"
        return msg
    except Exception as e:
        return f"col='{col_name}' 診断失敗 {e}"


# ---------------- state/QC：step0_explore.process_session の忠実移植 -------------
def compute_state_qc(
    pir_ser_full,
    nano_full,
    fs,
    rule="60s",
    want_bins=False,
    trace=False,
    cutoff=None,
):
    """cutoff=None のとき従来通り 1.0Hz。X1(LPF掃引)のみ cutoff を明示指定する。"""
    cut = 1.0 if cutoff is None else float(cutoff)
    if trace:
        log(f"    [state] LPF係数/リサンプル rule={rule} cutoff={cut}Hz 開始")
    b, a = lpf_coef(fs, cut, LPF_ORDER)
    origin = nano_full.index[0]
    nb = nano_full["Activity"].resample(rule, origin=origin).sum()
    label = (nb > 0).astype(int)  # 運用定義。label sweepは別診断で実行
    if trace:
        log("    [state] per-bin filtfilt(logvar) 開始")
    loglp = logvar_perbin(pir_ser_full, rule, origin, b, a)  # PAI
    if trace:
        log("    [state] per-bin filtfilt 完了 → 生分散リサンプル")
    rawvar = pir_ser_full.resample(rule, origin=origin).var()  # snr/floor用の生分散
    df = pd.DataFrame({"label": label, "loglp": loglp, "rawvar": rawvar}).dropna()
    if len(df) < 10:
        if trace:
            log(f"    [state] 有効ビン<10 ({len(df)}) → None")
        return None
    y = df["label"].values
    if trace:
        log(f"    [state] GMMフィット 開始 (bins={len(df)})")
    gm = fit_gmm(df["loglp"].values)
    if gm is None:
        if trace:
            log("    [state] GMM None → None")
        return None
    if trace:
        log("    [state] GMM完了 → F1/QC指標算出")
    pred = (gm["g"].predict(df["loglp"].values.reshape(-1, 1)) != gm["rest"]).astype(
        int
    )
    f1 = float(f1_score(y, pred, zero_division=0)) if len(np.unique(y)) > 1 else np.nan
    par = float(np.mean(pred))  # pir_active_rate = GMM active割合
    nar = float(np.mean(y))
    va = df["rawvar"][df["label"] == 1].mean()
    vr = df["rawvar"][df["label"] == 0].mean()
    snr = float(va / (vr + 1e-10)) if (pd.notna(va) and pd.notna(vr)) else np.nan
    lr = np.log(df["rawvar"].values + 1e-10)
    floor_rate = float(np.mean(lr <= lr.min() + 0.5) * 100)
    mm = gm["g"].means_.flatten()
    cv = gm["g"].covariances_.flatten()
    sep = float(abs(mm[0] - mm[1]) / (np.sqrt(cv[0]) + np.sqrt(cv[1])))
    _rest_i = gm["rest"]
    _act_i = 1 - _rest_i
    _ww = gm["g"].weights_.flatten()

    # --- append-only diagnostics (do NOT touch df/label/pred/f1/par -> frozen gates unchanged) ---
    # 提案1: NanoTag coverage. resample().sum() returns 0 for bins with NO epochs, silently
    # labelling them Rest. Count epochs per analysis bin; recompute sensitivity F1 on bins that
    # actually contain NanoTag epochs. Keep the frozen F1; report BOTH (honest form).
    _cov = nano_full["Activity"].resample(rule, origin=origin).count().reindex(df.index)
    n_empty_bins = int((_cov == 0).sum())
    _ne = _cov.values > 0
    f1_nonempty = (
        float(f1_score(y[_ne], pred[_ne], zero_division=0))
        if (_ne.sum() >= 1 and len(np.unique(y[_ne])) > 1)
        else np.nan
    )
    # 提案2: keep the NanoTag count on the confirmed bins (reindex AFTER dropna) for TP vs FN test
    _nba = nb.reindex(df.index).values.astype(float)
    _tp = (y == 1) & (pred == 1)
    _fn = (y == 1) & (pred == 0)
    median_nb_tp = float(np.median(_nba[_tp])) if _tp.any() else np.nan
    median_nb_fn = float(np.median(_nba[_fn])) if _fn.any() else np.nan
    # B: within-Active PAI dispersion (continuous good vs collapsed bad) -- explains inverse discrim
    _actv = df.loc[df["label"] == 1, "loglp"].to_numpy()
    _resv = df.loc[df["label"] == 0, "loglp"].to_numpy()
    if len(_actv) >= 2 and len(_resv) >= 1:
        pai_iqr_active = float(np.subtract(*np.percentile(_actv, [75, 25])))
        pai_sd_active = float(np.std(_actv, ddof=1))
        within_over_between = float(
            np.std(_actv, ddof=1) / (abs(_actv.mean() - _resv.mean()) + 1e-12)
        )
    else:
        pai_iqr_active = pai_sd_active = within_over_between = np.nan

    out = {
        "F1_state": f1,
        "pir_active_rate": par,
        "nanotag_active_rate": nar,
        "snr": snr,
        "floor_rate": floor_rate,
        "gmm_separation": sep,
        "gmm_boundary": gm["boundary"],
        "gmm_rest_mu": gm["rest_mu"],
        "gmm_act_mu": gm["act_mu"],
        "n_state_bins": len(df),
        "gmm_rest_sd": float(np.sqrt(cv[_rest_i])),
        "gmm_act_sd": float(np.sqrt(cv[_act_i])),
        "gmm_rest_w": float(_ww[_rest_i]),
        "gmm_act_w": float(_ww[_act_i]),
        "no_interior_crossing": int(gm.get("no_interior_crossing", False)),
        "outer_crossing_flag": int(gm.get("outer_crossing_flag", 0)),
        "outer_crossing": gm.get("outer_crossing", np.nan),
        # append-only diagnostics
        "n_empty_nanobins": n_empty_bins,
        "F1_state_nanotag_present": f1_nonempty,
        "median_nb_tp": median_nb_tp,
        "median_nb_fn": median_nb_fn,
        "pai_iqr_active": pai_iqr_active,
        "pai_sd_active": pai_sd_active,
        "within_over_between": within_over_between,
    }
    if want_bins:
        dist = (
            np.abs(df["loglp"].values - gm["boundary"])
            if np.isfinite(gm["boundary"])
            else np.full(len(df), np.nan)
        )
        err = (pred != y).astype(int)
        kind = np.where(
            (y == 1) & (pred == 0), "FN", np.where((y == 0) & (pred == 1), "FP", "OK")
        )
        out["bins"] = list(
            zip(
                dist.tolist(),
                err.tolist(),
                kind.tolist(),
                df["loglp"].values.tolist(),
                y.tolist(),
            )
        )
        out["bin_index"] = df.index
        out["pred"] = pred
        out["y"] = y
        out["loglp_vals"] = df["loglp"].values
        out["bins_nb"] = _nba.tolist()  # 提案2: NanoTag count per confirmed bin (aligned to bins)
    if trace:
        log(f"    [state] 完了 F1={f1:.3f} par={par:.3f}")
    return out


def extract_raw_window(raw_series, start_ts, dur_s, b_lp, a_lp):
    """指定開始時刻から dur_s 秒の生サンプル(+LPF後)を抽出。index も返す（NanoTag付与用）。"""
    seg = raw_series[
        (raw_series.index >= start_ts)
        & (raw_series.index < start_ts + pd.Timedelta(seconds=dur_s))
    ]
    if len(seg) < 10:
        return None
    v = seg.values.astype(float)
    try:
        v_lpf = scipy_signal.filtfilt(b_lp, a_lp, v)
    except Exception:
        v_lpf = np.full_like(v, np.nan)
    t0 = seg.index[0]
    times = (seg.index - t0).total_seconds().values
    return times, v, v_lpf, seg.index


def nanotag_asof_values(nano_ser, tidx):
    """各サンプル時刻に対応するNanoTag値（直前の観測を前方保持）。

    ※pandas 2.x の Series.asof() は index の時間分解能が異なると
      「Cannot losslessly cast '...ns' to us」で ValueError を投げる。
      PIRは30Hz(ns精度)・NanoTagは12s(us精度)なので必ず踏む。
      両者を datetime64[ns] に明示アップキャストして searchsorted で解決する。
    """
    try:
        ni = np.asarray(pd.DatetimeIndex(nano_ser.index).values, dtype="datetime64[ns]")
        ti = np.asarray(pd.DatetimeIndex(tidx).values, dtype="datetime64[ns]")
        vals = np.asarray(nano_ser.values, dtype=float)
        pos = np.searchsorted(ni, ti, side="right") - 1
        out = np.full(len(ti), np.nan, dtype=float)
        ok = pos >= 0
        out[ok] = vals[pos[ok]]
        return out
    except Exception:
        return np.full(len(tidx), np.nan, dtype=float)


def bimodality_coef(x):
    x = x[np.isfinite(x)]
    if len(x) < 4:
        return np.nan
    k = kurtosis(x, fisher=False)
    return float((skew(x) ** 2 + 1) / k) if k else np.nan


def _f1_from_feature_series(feat_series, label_series):
    """任意のper-bin特徴量+ラベルから GMM→F1。compute_state_qc と同一手順の軽量版。"""
    df = pd.DataFrame({"feat": feat_series, "label": label_series}).dropna()
    if len(df) < 10:
        return np.nan
    y = df["label"].values
    gm = fit_gmm(df["feat"].values)
    if gm is None or len(np.unique(y)) < 2:
        return np.nan
    pred = (gm["g"].predict(df["feat"].values.reshape(-1, 1)) != gm["rest"]).astype(int)
    return float(f1_score(y, pred, zero_division=0))


def _icc21(a, b):
    """ICC(2,1) 二元配置ランダム効果・単一測定（Shrout & Fleiss 1979）。参考値専用。"""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    n = len(a)
    if n < 3:
        return np.nan
    y = np.stack([a, b], axis=1)
    k = 2
    grand = y.mean()
    row_means = y.mean(axis=1)
    col_means = y.mean(axis=0)
    ss_total = ((y - grand) ** 2).sum()
    ss_rows = k * ((row_means - grand) ** 2).sum()
    ss_cols = n * ((col_means - grand) ** 2).sum()
    ss_error = ss_total - ss_rows - ss_cols
    msr = ss_rows / (n - 1)
    msc = ss_cols / (k - 1)
    mse = ss_error / ((n - 1) * (k - 1)) if (n - 1) * (k - 1) else np.nan
    denom = msr + (k - 1) * mse + (k * (msc - mse) / n)
    return float((msr - mse) / denom) if denom else np.nan


def _confusion_counts(pred, true):
    """pred/true (0/1配列) → TP/FP/FN/TN"""
    pred = np.asarray(pred, int)
    true = np.asarray(true, int)
    tp = int(((pred == 1) & (true == 1)).sum())
    fp = int(((pred == 1) & (true == 0)).sum())
    fn = int(((pred == 0) & (true == 1)).sum())
    tn = int(((pred == 0) & (true == 0)).sum())
    return tp, fp, fn, tn


def _rate_metrics(tp, fp, fn, tn):
    ppv = tp / (tp + fp) if (tp + fp) else np.nan
    npv = tn / (tn + fn) if (tn + fn) else np.nan
    sens = tp / (tp + fn) if (tp + fn) else np.nan
    spec = tn / (tn + fp) if (tn + fp) else np.nan
    return ppv, npv, sens, spec


# ---------------------------------------------------------------- main
def _legacy_main():
    print("=" * 66, flush=True)
    print(
        "【Stage 1 完全置換版・第6版: step0_explore定義移植・Young限定・探索計算X1-X10付き】",
        flush=True,
    )
    print("=" * 66, flush=True)
    log(
        f"Python {sys.version.split()[0]} / numpy {np.__version__} / pandas {pd.__version__}"
    )
    for ln in config.settings_report():
        print(ln, flush=True)
    print("-" * 66, flush=True)

    os.makedirs(config.INTERMEDIATE_DIR, exist_ok=True)

    # ---- X1 スキップ判定（既存 int_lpf_sweep.csv があれば再計算しない）----
    _lpf_path = os.path.join(config.INTERMEDIATE_DIR, "int_lpf_sweep.csv")
    DO_LPF_SWEEP = bool(getattr(config, "RUN_LPF_SWEEP", False)) and (
        bool(getattr(config, "FORCE_LPF_SWEEP", False)) or not os.path.exists(_lpf_path)
    )
    if getattr(config, "RUN_LPF_SWEEP", False) and not DO_LPF_SWEEP:
        log(
            "[X1] int_lpf_sweep.csv が既存 → 再計算スキップ（FORCE_LPF_SWEEP=Trueで強制再計算）"
        )
    elif DO_LPF_SWEEP:
        log(
            f"[X1] LPFカットオフ掃引を実行します {LPF_SWEEP_HZ} Hz（重い: +40〜60分想定）"
        )

    # ---- Old在庫チェック（0でなければゲートが崩れる）----
    old_list = list(getattr(config, "RECORDS_OLD", []))
    print(
        f"[age check] RECORDS_OLD = {old_list}  → {len(old_list)} records. "
        f"{'OK: gates unaffected.' if len(old_list) == 0 else '!!! WARNING: Old群が混入します。ゲートが崩れます !!!'}",
        flush=True,
    )

    session_paths = []
    for r in config.RECORDS_YOUNG:
        p = os.path.join(config.BASE_DATA_DIR, "本番データ", r)
        if not os.path.exists(p):
            p = os.path.join(config.BASE_DATA_DIR, r)
        if os.path.exists(p):
            session_paths.append((r, p, "Young"))
        else:
            log(f"  [警告] 記録パスが見つからない: {r}")
    log(f"対象セッション {len(session_paths)}件: {[s[0] for s in session_paths]}")

    try:
        df_map = pd.read_csv(config.MAPPING_CSV_PATH, encoding="utf-8-sig")
    except (UnicodeDecodeError, UnicodeError):
        log("  mapping.csv がUTF-8で読めず → cp932(Shift-JIS)で再読込")
        df_map = pd.read_csv(config.MAPPING_CSV_PATH, encoding="cp932")
    print("【mapping.csv（唯一の正）】", flush=True)
    for _, m in df_map.iterrows():
        print(
            f"  {m['record_id']} col{m['pir_col']} -> {m['mouse_id']} / "
            f"sensor_id={m.get('sensor_id', 'NA')} / {m['nanotag_filename']}",
            flush=True,
        )
    print("-" * 66, flush=True)

    binned_rows, channel_rows, feature_rows = [], [], []
    sweep_rows, seed_rows, seed_state_rows, learn_rows, err_rows, calib_rows = [], [], [], [], [], []
    plc_pair_rows, bic_rows, state_learn_rows = [], [], []
    state_hist_rows = []
    repr24_rows = []
    raw_trace_rows = []
    repr_timeline_rows = []
    plc_cross_cache = []
    nano_dark_cache = []
    lpf_sweep_rows = []  # X1
    perch_conf_rows = []  # X2
    baseline_rows = []  # X4
    darkdef_rows = []  # X8
    adc_diag_rows = []  # ★V6-1
    nanotag_integrity_rows = []
    bin_coverage_rows = []
    calibration60_rows = []
    filter_compare_rows = []
    label_sweep_channel_rows = []
    session_timecourse_rows = []
    channel_map_rows = []  # Addition C: explicit (recording, ch) -> nanotag_id -> mouse_N map
    circ = {}
    measured_fs = config.FS
    sensor_set_fallback_used = 0

    for rec_id, s_path, age_grp in session_paths:
        log(f"■ 記録 {rec_id} ({age_grp}) 開始  path={s_path}")
        all_c = glob.glob(os.path.join(s_path, "*.csv"))
        pir_c = [
            f
            for f in all_c
            if "pir" in f.lower()
            and "control" not in f.lower()
            and "summary" not in f.lower()
        ]
        ctrl_c = [f for f in all_c if "control" in f.lower()]
        log(f"  csv合計={len(all_c)} / pir={len(pir_c)} / control={len(ctrl_c)}")
        if not pir_c:
            log("  PIR CSVなし → この記録スキップ")
            continue
        sess_map = df_map[df_map["record_id"].astype(str) == str(rec_id)]
        tgt = set(
            str(m["pir_col"])
            for _, m in sess_map.iterrows()
            if m["nanotag_filename"] != "None"
        )
        log(f"  PIRロード開始 target_cols={sorted(tgt)}")
        df_p = load_and_concat_csvs(pir_c, target_cols=tgt, _tag="pir")
        if df_p is None or df_p.empty:
            log("  PIRロード結果が空 → この記録スキップ")
            continue
        log(f"  PIRロード完了 rows={len(df_p)} cols={list(df_p.columns)}")
        el = (df_p.index[-1] - df_p.index[0]).total_seconds()
        if el > 0 and abs(len(df_p) / el - config.FS) < 3.0:
            measured_fs = round(len(df_p) / el, 1)
        log(f"  fs実測={measured_fs}Hz (経過時間{el / 3600:.1f}h)")

        # ★旧方式のセンサーセット署名（照合用に温存。SetA/B判定には使わない）
        _sig = re.search(
            r"sensor\s*([0-9]+(?:,[0-9]+)*)", os.path.basename(sorted(pir_c)[0])
        )
        sensor_set_sig = (
            ",".join(sorted(_sig.group(1).split(","), key=int)) if _sig else str(rec_id)
        )
        log(f"  センサーセット署名(旧方式・照合用) = {sensor_set_sig}")

        if ctrl_c:
            log("  controlロード開始")
        df_ctrl = (
            load_and_concat_csvs(ctrl_c, target_cols=tgt, _tag="ctrl")
            if ctrl_c
            else None
        )
        dark = (df_p.index.hour >= config.DARK_HOURS[0]) | (
            df_p.index.hour < config.DARK_HOURS[1]
        )
        b_lp, a_lp = lpf_coef(config.FS, 1.0, LPF_ORDER)

        nanos = {}
        for _, m in sess_map.iterrows():
            nid = str(m["nanotag_id"])
            if m["nanotag_filename"] == "None" or nid in nanos:
                continue
            log(f"  NanoTag {nid} ロード開始")
            dn = load_nano(nid, s_path, str(m["nanotag_fullpath"]))
            if dn is not None:
                nanos[nid] = dn
                _ii = dn.attrs.get("integrity", {})
                nanotag_integrity_rows.append({
                    "record_id": str(rec_id), "nanotag_id": str(nid),
                    "source_file": _ii.get("source_file", ""),
                    "missing_cells_before_coercion": _ii.get("missing_cells_before_coercion", 0),
                    "coercion_to_nan_count": _ii.get("coercion_to_nan_count", 0),
                    "missing_run_count": _ii.get("missing_run_count", 0),
                    "longest_missing_run": _ii.get("longest_missing_run", 0),
                })
            else:
                log(f"  NanoTag {nid} ロード失敗(None)")
        log(f"  NanoTag {len(nanos)}個 ロード完了: {sorted(nanos)}")

        for _, m in sess_map.iterrows():
            c = str(m["pir_col"])
            if c not in df_p.columns or m["nanotag_filename"] == "None":
                continue
            nid = str(m["nanotag_id"])
            if nid not in nanos:
                log(f"  [skip] col{c}: nano {nid} 不在")
                continue
            ch_id = f"{rec_id}_ch{c}"
            mouse_id = str(m["mouse_id"])
            sensor_id = str(m.get("sensor_id", f"X_{c}"))

            # ★sensor_id 先頭文字で SetA/SetB を決定（フォールバック検知つき）
            #   実データは "X_1" 形式。区切り(_ - 空白)の有無・ゼロ埋め・大小文字を許容する。
            _sid_m = re.match(r"^\s*([A-Za-z])[\s_\-]?0*([0-9]+)\s*$", str(sensor_id))
            if _sid_m and _sid_m.group(1).upper() in SENSOR_SET_ORDER:
                sensor_set = _sid_m.group(1).upper()
                _fb = 0
            else:
                sensor_set = sensor_set_sig
                _fb = 1
                sensor_set_fallback_used += 1
                log(
                    f"    [警告] sensor_id='{sensor_id}' が X1-X8/Y1-Y8 形式でない → "
                    f"署名フォールバック({sensor_set_sig})を使用"
                )

            log(
                f"  ── ch {ch_id} (mouse {mouse_id}, sensor {sensor_id}, set {sensor_set}) 開始"
            )
            channel_map_rows.append({
                "record_id": str(rec_id),
                "ch": ch_id,
                "pir_col": str(c),
                "nanotag_id": str(nid),
                "mouse_id": str(mouse_id),
                "sensor_id": str(sensor_id),
                "sensor_set": str(sensor_set),
            })

            _raw_col = pd.to_numeric(df_p[c], errors="coerce")
            frac_missing = float(_raw_col.isna().mean())  # ★X6
            pir_full = _raw_col.ffill().fillna(0.0)
            # ★V6-1: 生ADC（中央値減算前）の素性を毎回開示し、オフセットを保持する。
            #   中央値減算は平行移動なので分散・PAI・GMM・F1・r には影響しない＝ゲート不変。
            _adc_offset = float(np.median(pir_full.values))
            _diag_msg = adc_diagnostic(pir_full, c, str(_raw_col.dtype))
            log(f"    [ADC診断] {_diag_msg}")
            try:
                _vv = np.asarray(pir_full.values, dtype=float)
                _vv = _vv[np.isfinite(_vv)]
                _uq = np.unique(_vv)
                # Addition A: saturation is detected data-drivenly (proximity to the observed
                # extremes), NOT with a hardcoded +/-10V rail -- the recorded values are ~0.4-0.7 V,
                # so an absolute >9.9 test would always be zero. An optional absolute rail
                # (config.RAW_RAIL_ABS) is also honoured when the true input range is known.
                if len(_vv) > 1:
                    _vmin, _vmax = float(_vv.min()), float(_vv.max())
                    _step = float(np.min(np.diff(_uq))) if len(_uq) > 1 else 0.0
                    _tol = max(_step, 0.005 * (np.ptp(_vv)))  # 1 quant step or 0.5% of range
                    _rail_frac = float(np.mean((_vv <= _vmin + _tol) | (_vv >= _vmax - _tol)))
                    _rail_abs = getattr(config, "RAW_RAIL_ABS", None)
                    _rail_frac_abs = (
                        float(np.mean(np.abs(_vv) >= float(_rail_abs)))
                        if _rail_abs is not None
                        else np.nan
                    )
                    _v_p1, _v_p99 = float(np.percentile(_vv, 1)), float(np.percentile(_vv, 99))
                else:
                    _vmin = _vmax = _v_p1 = _v_p99 = np.nan
                    _rail_frac = _rail_frac_abs = np.nan
                adc_diag_rows.append(
                    {
                        "ch": ch_id,
                        "mouse_id": mouse_id,
                        "pir_col": c,
                        "dtype": str(_raw_col.dtype),
                        "min": float(_vv.min()) if len(_vv) else np.nan,
                        "max": float(_vv.max()) if len(_vv) else np.nan,
                        "range": float(np.ptp(_vv)) if len(_vv) else np.nan,
                        "median": _adc_offset,
                        "n_unique": len(_uq),
                        "smallest_step": float(np.min(np.diff(_uq)))
                        if len(_uq) > 1
                        else np.nan,
                        "looks_like_0p01_adc": int(
                            len(_uq) > 1
                            and abs(float(np.min(np.diff(_uq))) - 0.01) <= 0.001
                        ),
                        # Addition A: saturation / dynamic-range diagnostics
                        "v_p1": _v_p1,
                        "v_p99": _v_p99,
                        "rail_frac": _rail_frac,
                        "rail_frac_abs": _rail_frac_abs,
                    }
                )
            except Exception as _e:
                log(f"    [ADC診断] 行の記録をスキップ {_e}")
            pir_full = pir_full - np.median(pir_full.values)
            nano_full = nanos[nid]
            origin = nano_full.index[0]
            n_hours = float(
                (pir_full.index[-1] - pir_full.index[0]).total_seconds() / 3600.0
            )  # ★X6

            # ---- 状態/QC（全録画・60s）----
            log("    [1/9 state/QC] 開始")
            sq = compute_state_qc(
                pir_full,
                nano_full,
                config.FS,
                config.BIN_STATE,
                want_bins=True,
                trace=True,
            )
            if sq is None:
                log("    [1/9 state/QC] None → chスキップ")
                continue
            log(
                f"    [1/9 state/QC] 完了 F1={sq['F1_state']:.3f} par={sq['pir_active_rate']:.3f}"
            )

            # ---- v2 diagnostics: coverage / label sweep / filter-mode / 12h session timecourse ----
            try:
                _state_origin = nano_full.index[0]
                _pir_count = pir_full.resample(config.BIN_STATE, origin=_state_origin).count()
                _nano_count = nano_full["Activity"].resample(config.BIN_STATE, origin=_state_origin).count()
                _idx_cov = _pir_count.index.union(_nano_count.index)
                _exp_pir = float(config.FS) * float(getattr(config, "BIN_STATE_SEC", 60))
                for _t in _idx_cov:
                    _pc = float(_pir_count.get(_t, 0))
                    _nc = float(_nano_count.get(_t, 0))
                    bin_coverage_rows.append({
                        "ch": ch_id, "mouse_id": mouse_id, "record_id": rec_id,
                        "timestamp": str(_t), "pir_samples": _pc, "nanotag_samples": _nc,
                        "pir_fraction_expected": (_pc / _exp_pir if _exp_pir else np.nan),
                    })
            except Exception as _e:
                log(f"    [bin_coverage] スキップ {_e}")

            try:
                _pai = np.asarray(sq["loglp_vals"], float)
                _pred = np.asarray(sq["pred"], int)
                _bidx = pd.DatetimeIndex(sq.get("bin_index"))
                _nb_aligned = nano_full["Activity"].resample(config.BIN_STATE, origin=nano_full.index[0]).sum().reindex(_bidx).fillna(0).to_numpy(float)
                for _nb_thr in getattr(config, "LABEL_NB_SWEEP", [1, 2, 3]):
                    _yy = (_nb_aligned >= float(_nb_thr)).astype(int)
                    _f1s = float(f1_score(_yy, _pred, zero_division=0)) if len(np.unique(_yy)) > 1 else np.nan
                    label_sweep_channel_rows.append({
                        "ch": ch_id, "mouse_id": mouse_id, "record_id": rec_id,
                        "nb_threshold": int(_nb_thr), "par": float(np.mean(_pred)),
                        "nar": float(np.mean(_yy)), "F1_state": _f1s,
                    })
            except Exception as _e:
                log(f"    [label_sweep] スキップ {_e}")

            try:
                _bf, _af = lpf_coef(config.FS, float(getattr(config, "LOWPASS_CUTOFF_HZ", 1.0)), LPF_ORDER)
                _vf = scipy_signal.filtfilt(_bf, _af, pir_full.values.astype(float))
                _sf = pd.Series(_vf, index=pir_full.index)
                _lv_cont = _sf.resample(config.BIN_STATE, origin=nano_full.index[0]).var().map(lambda z: np.log(z + 1e-10) if pd.notna(z) else np.nan)
                _nbc = nano_full["Activity"].resample(config.BIN_STATE, origin=nano_full.index[0]).sum()
                _dc = pd.DataFrame({"lv": _lv_cont, "label": (_nbc > 0).astype(int)}).dropna()
                _gmc = fit_gmm(_dc["lv"].values)
                _f1c = np.nan
                if _gmc is not None and _dc["label"].nunique() > 1:
                    _pc = (_gmc["g"].predict(_dc["lv"].values.reshape(-1,1)) != _gmc["rest"]).astype(int)
                    _f1c = float(f1_score(_dc["label"].values, _pc, zero_division=0))
                _common = _dc.index.intersection(pd.DatetimeIndex(sq.get("bin_index")))
                _per = pd.Series(np.asarray(sq["loglp_vals"],float), index=pd.DatetimeIndex(sq.get("bin_index")))
                _pai_mae = float(np.mean(np.abs(_per.reindex(_common).values - _dc.loc[_common,"lv"].values))) if len(_common) else np.nan
                _darkc = (_sf.index.hour >= config.DARK_HOURS[0]) | (_sf.index.hour < config.DARK_HOURS[1])
                _lv10 = _sf[_darkc].resample(config.BIN_INTENSITY, origin=nano_full.index[0]).var().map(lambda z: np.log(z + 1e-10) if pd.notna(z) else np.nan)
                _ct10 = nano_full[(nano_full.index.hour >= config.DARK_HOURS[0]) | (nano_full.index.hour < config.DARK_HOURS[1])]["Activity"].resample(config.BIN_INTENSITY, origin=nano_full.index[0]).sum()
                _di = pd.DataFrame({"lv":_lv10,"ct":_ct10}).iloc[1:-1].dropna()
                _rc = float(spearmanr(_di["lv"],_di["ct"])[0]) if len(_di)>10 else np.nan
                filter_compare_rows.append({"ch":ch_id,"mouse_id":mouse_id,"record_id":rec_id,"pai_mean_abs_diff":_pai_mae,"f1_perbin":sq["F1_state"],"f1_continuous":_f1c,"f1_diff":_f1c-sq["F1_state"] if pd.notna(_f1c) else np.nan,"r_perbin":np.nan,"r_continuous":_rc})
            except Exception as _e:
                log(f"    [filter_mode_compare] スキップ {_e}")

            try:
                _origin_full = pir_full.index[0]
                _bfull, _afull = lpf_coef(config.FS, float(getattr(config, "LOWPASS_CUTOFF_HZ", 1.0)), LPF_ORDER)
                _pai_full = logvar_perbin(pir_full, config.BIN_STATE, _origin_full, _bfull, _afull).dropna()
                _gm_global = sq["gmm_boundary"]  # report only; classification below remains argmax from the fitted model
                _gmfit = fit_gmm(pd.Series(np.asarray(sq["loglp_vals"],float)).values)
                if _gmfit is not None:
                    _pred_full = pd.Series((_gmfit["g"].predict(_pai_full.values.reshape(-1,1)) != _gmfit["rest"]).astype(int), index=_pai_full.index)
                    _nb_full = nano_full["Activity"].resample(config.BIN_STATE, origin=_origin_full).sum()
                    # Count reference epochs separately: resample().sum() can produce zero for an
                    # empty interval, which must NOT be interpreted as a true Rest reference bin.
                    _nb_count_full = nano_full["Activity"].resample(config.BIN_STATE, origin=_origin_full).count()
                    _hours = int(getattr(config, "SESSION_BLOCK_HOURS", 12))
                    _block_s = _hours*3600
                    _block_idx = ((_pai_full.index - _origin_full).total_seconds() // _block_s).astype(int)
                    for _bi in sorted(set(_block_idx)):
                        _mask = _block_idx == _bi
                        _pvals = _pai_full.iloc[np.where(_mask)[0]]
                        _pidx = _pvals.index
                        _pr = _pred_full.reindex(_pidx)
                        _nbv = _nb_full.reindex(_pidx)
                        _nbcv = _nb_count_full.reindex(_pidx).fillna(0)
                        _present = _nbcv > 0
                        _n_present = int(_present.sum())
                        _pai_frac = float(len(_pvals) / (_block_s / config.BIN_STATE_SEC)) if _block_s > 0 else np.nan
                        _nano_frac = float(_n_present / len(_pvals)) if len(_pvals) else np.nan
                        _block_usable = int(
                            pd.notna(_pai_frac) and pd.notna(_nano_frac)
                            and _pai_frac >= float(config.SESSION_BLOCK_MIN_PAI_FRAC)
                            and _nano_frac >= float(config.SESSION_BLOCK_MIN_NANO_FRAC)
                        )
                        _nar_b = float((_nbv[_present] > 0).mean()) if _n_present > 0 else np.nan
                        _par_b = float(_pr.mean()) if len(_pr) else np.nan
                        _gmb = fit_gmm(_pvals.values)
                        session_timecourse_rows.append({
                            "ch":ch_id,"mouse_id":mouse_id,"record_id":rec_id,"sensor_id":sensor_id,
                            "block_index":int(_bi),"block_start_h":float(_bi*_hours),"block_end_h":float((_bi+1)*_hours),
                            "par":_par_b,"nar":_nar_b,"par_over_nar":(_par_b/_nar_b if _n_present>0 and pd.notna(_nar_b) and _nar_b>0 else np.nan),
                            "pai_rest_component_mean":(_gmb["rest_mu"] if _gmb is not None else np.nan),
                            "n_pai_bins":int(len(_pvals)),"n_nano_bins_present":_n_present,
                            "pai_frac":_pai_frac,"nano_frac":_nano_frac,"block_usable":_block_usable,
                        })
            except Exception as _e:
                log(f"    [session_timecourse] スキップ {_e}")

            # ---- ★X2: ch別 ビン単位混同行列＋分類指標 ----
            try:
                _y = np.asarray(sq["y"], int)
                _p = np.asarray(sq["pred"], int)
                tp, fp, fn, tn = _confusion_counts(_p, _y)
                ppv, npv, sens, spec = _rate_metrics(tp, fp, fn, tn)
                n_err = fp + fn
                perch_conf_rows.append(
                    {
                        "ch": ch_id,
                        "mouse_id": mouse_id,
                        "TP": tp,
                        "FP": fp,
                        "FN": fn,
                        "TN": tn,
                        "n_bins": len(_y),
                        "n_error": n_err,
                        "fp_share": round(fp / n_err, 4) if n_err else np.nan,
                        "fn_share": round(fn / n_err, 4) if n_err else np.nan,
                        "precision": round(ppv, 4) if pd.notna(ppv) else np.nan,
                        "recall": round(sens, 4) if pd.notna(sens) else np.nan,
                        "specificity": round(spec, 4) if pd.notna(spec) else np.nan,
                        "npv": round(npv, 4) if pd.notna(npv) else np.nan,
                        "balanced_acc": round((sens + spec) / 2, 4)
                        if pd.notna(sens) and pd.notna(spec)
                        else np.nan,
                        "f1": round(float(f1_score(_y, _p, zero_division=0)), 4),
                        "mcc": round(float(matthews_corrcoef(_y, _p)), 4)
                        if len(np.unique(_y)) > 1 and len(np.unique(_p)) > 1
                        else np.nan,
                        "kappa": round(float(cohen_kappa_score(_y, _p)), 4)
                        if len(np.unique(_y)) > 1
                        else np.nan,
                    }
                )
            except Exception as _e:
                log(f"    [X2 perch_confusion] スキップ {_e}")

            # ---- ★X4: GMM以外のベースライン状態分類 ----
            if RUN_EXPL:
                try:
                    _pai_s = np.asarray(sq["loglp_vals"], float)
                    _y_s = np.asarray(sq["y"], int)
                    _cands = {
                        "gmm": float(sq["gmm_boundary"]),
                        "otsu": otsu_threshold(_pai_s),
                        "median_split": float(np.median(_pai_s)),
                        "fixed_quantile": float(
                            np.quantile(
                                _pai_s,
                                float(getattr(config, "BASELINE_FIXED_QUANTILE", 0.5)),
                            )
                        ),
                    }
                    for _nm, _thr_v in _cands.items():
                        if not np.isfinite(_thr_v):
                            continue
                        _pd_ = (_pai_s > _thr_v).astype(int)
                        baseline_rows.append(
                            {
                                "ch": ch_id,
                                "mouse_id": mouse_id,
                                "method": _nm,
                                "threshold": round(float(_thr_v), 4),
                                "f1_state": round(
                                    float(f1_score(_y_s, _pd_, zero_division=0)), 4
                                ),
                            }
                        )
                except Exception as _e:
                    log(f"    [X4 baseline] スキップ {_e}")

            # ---- 生波形抽出（Fig1候補: 窓の選び方を複数）＋状態タイムライン ----
            #   第7版: Fig1 は「変化が見える区間」を示したいので、窓の選択規則を複数持たせる。
            #     median     … 従来と同一（active/rest それぞれ median-PAI のビン）＝既存Fig1の再現性を保証
            #     high       … active は最大PAIビン、rest は最小PAIビン＝コントラスト最大
            #     transition … rest→active の切替直前から始まる窓（PAI跳躍が最大の箇所）
            #   さらに RAW_TRACE_EXTRA_CH で REPR_CH 以外のchも候補として保存できる。
            #   ※ int_raw_trace は描画専用。PAI/GMM/F1/強度r には一切使われない＝確定ゲート不変。
            _repr_ch = str(getattr(config, "REPR_CH", "") or "")
            _extra_raw = [str(x) for x in getattr(config, "RAW_TRACE_EXTRA_CH", [])]
            _want_raw = (ch_id == _repr_ch) or (ch_id in _extra_raw)
            if _want_raw:
                _bidx = sq.get("bin_index")
                _predarr = sq.get("pred")
                try:
                    _paiarr = np.array([bb[3] for bb in sq["bins"]])
                    _yarr = np.array([bb[4] for bb in sq["bins"]])
                    _nano_ser = nano_full["Activity"]
                    _nano_bin = _nano_ser.resample(config.BIN_STATE).sum()
                    _variants = [
                        str(v)
                        for v in getattr(config, "RAW_TRACE_VARIANTS", ["median"])
                    ]
                    _lead = int(getattr(config, "RAW_TRACE_TRANSITION_LEAD_BINS", 2))
                    if _bidx is not None and len(_bidx) == len(_paiarr):

                        def _emit_window(_variant, _phase, _local_idx, _note=""):
                            """1窓ぶんの生サンプルを raw_trace_rows に流し込む（共通処理）。"""
                            _local_idx = int(_local_idx)
                            if _local_idx < 0 or _local_idx >= len(_bidx):
                                return
                            _start_ts = _bidx[_local_idx]
                            _res = extract_raw_window(
                                pir_full, _start_ts, RAW_WINDOW_S, b_lp, a_lp
                            )
                            if _res is None:
                                return
                            _times, _v, _vlpf, _tidx = _res
                            _bin_pai = float(_paiarr[_local_idx])
                            # 各サンプル時刻に対応するNanoTag値（12s分解能・前方保持）
                            _nvals = nanotag_asof_values(_nano_ser, _tidx)
                            _bin_nano = float(_nano_bin.get(_start_ts, np.nan))
                            for _si, (_tt, _rv, _rvl, _nv) in enumerate(
                                zip(_times, _v, _vlpf, _nvals)
                            ):
                                raw_trace_rows.append(
                                    {
                                        "ch": ch_id,
                                        "mouse_id": mouse_id,
                                        "variant": _variant,
                                        "phase": _phase,
                                        "sample_idx": _si,
                                        "time_s": float(_tt),
                                        "raw_value": float(_rv),
                                        # 中央値減算前の生ADC値（Fig1の縦軸はこちらを使う）
                                        "raw_value_adc": float(_rv) + _adc_offset,
                                        "raw_value_lpf": float(_rvl),
                                        "bin_pai": _bin_pai,
                                        "nanotag_count": float(_nv)
                                        if pd.notna(_nv)
                                        else np.nan,
                                        "nanotag_count_bin": _bin_nano,
                                        "window_s": RAW_WINDOW_S,
                                    }
                                )
                            log(
                                f"    [raw_trace] {ch_id} {_variant}/{_phase}: "
                                f"bin_start={_start_ts} PAI={_bin_pai:.3f} n={len(_v)} "
                                f"window={RAW_WINDOW_S}s raw_var={float(np.var(_v)):.3e} "
                                f"lpf_var={float(np.var(_vlpf)):.3e} "
                                f"adc_range={float(np.ptp(_v)):.6g} "
                                f"nano_bin={_bin_nano} {_note}"
                            )

                        # --- median: 従来と同一の選択規則（変更禁止）---
                        if "median" in _variants:
                            for _phase, _mask_val in [("active", 1), ("rest", 0)]:
                                _mask = _yarr == _mask_val
                                if _mask.sum() == 0:
                                    continue
                                _target_med = float(np.median(_paiarr[_mask]))
                                _cand_idx = np.where(_mask)[0]
                                _best_local = _cand_idx[
                                    np.argmin(np.abs(_paiarr[_cand_idx] - _target_med))
                                ]
                                _emit_window(
                                    "median",
                                    _phase,
                                    _best_local,
                                    f"(median-PAI={_target_med:.3f})",
                                )

                        # --- high: active=最大PAI / rest=最小PAI（コントラスト最大）---
                        if "high" in _variants:
                            _am = _yarr == 1
                            if _am.sum():
                                _ci = np.where(_am)[0]
                                _emit_window(
                                    "high",
                                    "active",
                                    _ci[np.argmax(_paiarr[_ci])],
                                    "(max PAI among active bins)",
                                )
                            _rm = _yarr == 0
                            if _rm.sum():
                                _ci = np.where(_rm)[0]
                                _emit_window(
                                    "high",
                                    "rest",
                                    _ci[np.argmin(_paiarr[_ci])],
                                    "(min PAI among rest bins)",
                                )

                        # --- transition: rest→active の切替（PAI跳躍が最大の箇所）---
                        if "transition" in _variants:
                            _tr = [
                                j
                                for j in range(1, len(_yarr))
                                if _yarr[j - 1] == 0 and _yarr[j] == 1
                            ]
                            if _tr:
                                _jump = [
                                    float(_paiarr[j] - _paiarr[j - 1]) for j in _tr
                                ]
                                _jbest = _tr[int(np.argmax(_jump))]
                                _emit_window(
                                    "transition",
                                    "transition",
                                    max(_jbest - _lead, 0),
                                    f"(rest->active at bin {_jbest}, "
                                    f"PAI jump={max(_jump):.3f}, lead={_lead} bins)",
                                )
                            else:
                                log(
                                    f"    [raw_trace] {ch_id} transition: rest->active の"
                                    f"切替ビンが無い → スキップ"
                                )

                        # --- empty(空箱control)代表窓: 対照なので median 変種にのみ保存 ---
                        if df_ctrl is not None and c in df_ctrl.columns:
                            _cs = (
                                pd.to_numeric(df_ctrl[c], errors="coerce")
                                .ffill()
                                .fillna(0.0)
                            )
                            _cs_offset = float(np.median(_cs.values))
                            _cs = _cs - np.median(_cs.values)
                            _cpai = logvar_perbin(
                                _cs, config.BIN_STATE, _cs.index[0], b_lp, a_lp
                            ).dropna()
                            if len(_cpai) > 0:
                                _cmed = float(_cpai.median())
                                _cbest_ts = (_cpai - _cmed).abs().idxmin()
                                _res2 = extract_raw_window(
                                    _cs, _cbest_ts, RAW_WINDOW_S, b_lp, a_lp
                                )
                                if _res2 is not None:
                                    _times2, _v2, _vlpf2, _tidx2 = _res2
                                    _bin_pai_empty = float(_cpai.loc[_cbest_ts])
                                    for _si, (_tt, _rv, _rvl) in enumerate(
                                        zip(_times2, _v2, _vlpf2)
                                    ):
                                        raw_trace_rows.append(
                                            {
                                                "ch": ch_id,
                                                "mouse_id": mouse_id,
                                                "variant": "median",
                                                "phase": "empty",
                                                "sample_idx": _si,
                                                "time_s": float(_tt),
                                                "raw_value": float(_rv),
                                                "raw_value_adc": float(_rv)
                                                + _cs_offset,
                                                "raw_value_lpf": float(_rvl),
                                                "bin_pai": _bin_pai_empty,
                                                "nanotag_count": np.nan,
                                                "nanotag_count_bin": np.nan,
                                                "window_s": RAW_WINDOW_S,
                                            }
                                        )
                                    log(
                                        f"    [raw_trace] {ch_id} median/empty: "
                                        f"bin_start={_cbest_ts} PAI={_bin_pai_empty:.3f}"
                                        f"(median={_cmed:.3f}) n={len(_v2)} "
                                        f"window={RAW_WINDOW_S}s "
                                        f"raw_var={float(np.var(_v2)):.3e} "
                                        f"adc_offset={_cs_offset:.6g} (no NanoTag: empty box)"
                                    )
                            else:
                                log(
                                    "    [raw_trace] empty: control PAIビン無し → スキップ"
                                )
                        else:
                            log("    [raw_trace] empty: df_ctrl無し/列無し → スキップ")
                except Exception as _e:
                    log(f"    [raw_trace] スキップ {_e}")
            if ch_id == _repr_ch:
                _bidx = sq.get("bin_index")
                _predarr = sq.get("pred")
                # --- 状態タイムライン(全60sビン) ---
                try:
                    if _bidx is not None and _predarr is not None:
                        _t0 = _bidx[0]
                        for _i, (_t, _pv, _bb) in enumerate(
                            zip(_bidx, _predarr, sq["bins"])
                        ):
                            _dist, _err, _kind, _pai, _y2 = _bb
                            repr_timeline_rows.append(
                                {
                                    "bin_idx": _i,
                                    "time_s": (_t - _t0).total_seconds(),
                                    "log_lp_var": _pai,
                                    "pred_state": "active" if int(_pv) == 1 else "rest",
                                    "true_state": "active" if int(_y2) == 1 else "rest",
                                    "is_dark": bool(
                                        (_t.hour >= config.DARK_HOURS[0])
                                        or (_t.hour < config.DARK_HOURS[1])
                                    ),
                                }
                            )
                        log(f"    [repr_state_timeline] {len(_bidx)}ビンを記録")
                except Exception as _e:
                    log(f"    [repr_state_timeline] スキップ {_e}")

            # ---- 二峰性係数＋BIC(K=1,2,3) ----
            bimod = np.nan
            try:
                _spai = np.array([bb[3] for bb in sq["bins"]], float)
                _spai = _spai[np.isfinite(_spai)]
                bimod = bimodality_coef(_spai)
                if len(_spai) >= 12:
                    for _k in (1, 2, 3, 4, 5):
                        _gk = GaussianMixture(n_components=_k, random_state=42).fit(
                            _spai.reshape(-1, 1)
                        )
                        bic_rows.append(
                            {
                                "ch": ch_id,
                                "mouse_id": mouse_id,
                                "k": _k,
                                "bic": float(_gk.bic(_spai.reshape(-1, 1))),
                            }
                        )
            except Exception as _e:
                log(f"    [BIC/bimodality] スキップ {_e}")

            # ---- 状態PAI分布のエクスポート ----
            try:
                for _bb in sq["bins"]:
                    state_hist_rows.append(
                        {
                            "ch": ch_id,
                            "mouse_id": mouse_id,
                            "log_lp_var": float(_bb[3]),
                            "nano_label": int(_bb[4]),
                        }
                    )
            except Exception:
                pass

            # ---- NanoTag経験的μ（GMM推定μとの照合用）----
            nano_rest_mu = nano_rest_mu_mean = nano_act_mu = nano_act_mu_mean = np.nan
            try:
                _paivals = np.array([bb[3] for bb in sq["bins"]], dtype=float)
                _yvals = np.array([bb[4] for bb in sq["bins"]], dtype=int)
                _rv = _paivals[_yvals == 0]
                _av = _paivals[_yvals == 1]
                if len(_rv):
                    nano_rest_mu = float(np.median(_rv))
                    nano_rest_mu_mean = float(np.mean(_rv))
                if len(_av):
                    nano_act_mu = float(np.median(_av))
                    nano_act_mu_mean = float(np.mean(_av))
            except Exception as _e:
                log(f"    [nano経験的μ] スキップ {_e}")

            # ---- 状態特徴量アブレーション（log/LPFの効果分離）----
            f1_rawvar = f1_std = f1_range = np.nan
            f1_var_nolpf = f1_logvar_nolpf = f1_band01 = f1_band15 = f1_band515 = np.nan
            f1_high_pass = f1_raw_amp = f1_bandpass_var = f1_band12 = f1_band25 = np.nan
            # 帯域「だけ」を比較するには log を固定する必要がある（生パワーはGMMが退化）
            f1_logband01 = f1_logband12 = f1_logband25 = f1_logband515 = np.nan
            try:
                _nb_qc = nano_full["Activity"].resample(config.BIN_STATE).sum()
                _label_qc = (_nb_qc > 0).astype(int)
                _origin_qc = nano_full.index[0]
                _rawvar_bin = var_perbin(
                    pir_full, config.BIN_STATE, _origin_qc, b_lp, a_lp
                )
                f1_rawvar = _f1_from_feature_series(_rawvar_bin, _label_qc)
                _std_bin = stat_perbin(
                    pir_full, config.BIN_STATE, _origin_qc, b_lp, a_lp, np.std
                )
                f1_std = _f1_from_feature_series(_std_bin, _label_qc)
                _range_bin = stat_perbin(
                    pir_full, config.BIN_STATE, _origin_qc, b_lp, a_lp, np.ptp
                )
                f1_range = _f1_from_feature_series(_range_bin, _label_qc)
                _var_nolpf_bin = raw_stat_perbin(
                    pir_full, config.BIN_STATE, _origin_qc, np.var
                )
                f1_var_nolpf = _f1_from_feature_series(_var_nolpf_bin, _label_qc)
                _logvar_nolpf_bin = raw_stat_perbin(
                    pir_full,
                    config.BIN_STATE,
                    _origin_qc,
                    lambda v: np.log(np.var(v) + 1e-10),
                )
                f1_logvar_nolpf = _f1_from_feature_series(_logvar_nolpf_bin, _label_qc)
                _rawamp_bin = raw_stat_perbin(
                    pir_full, config.BIN_STATE, _origin_qc, np.std
                )
                f1_raw_amp = _f1_from_feature_series(_rawamp_bin, _label_qc)
            except Exception as _e:
                log(f"    [F1_state rawvar/std/range] スキップ {_e}")
            if RUN_SUPP:
                try:
                    _b01_bin = band_power_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, config.FS, 0, 1
                    )
                    f1_band01 = _f1_from_feature_series(_b01_bin, _label_qc)
                    _b15_bin = band_power_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, config.FS, 1, 5
                    )
                    f1_band15 = _f1_from_feature_series(_b15_bin, _label_qc)
                    _b515_bin = band_power_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, config.FS, 5, 15
                    )
                    f1_band515 = _f1_from_feature_series(_b515_bin, _label_qc)
                    _b12_bin = band_power_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, config.FS, 1, 2
                    )
                    f1_band12 = _f1_from_feature_series(_b12_bin, _label_qc)
                    _b25_bin = band_power_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, config.FS, 2, 5
                    )
                    f1_band25 = _f1_from_feature_series(_b25_bin, _label_qc)
                    # log-band variance（Welchは計算済みなので追加コストはGMM4回のみ）。
                    #   生パワーはスケールが極端に歪んでGMMが退化するため、帯域軸の比較は
                    #   log を掛けた上で行う（= log の効果を固定して帯域の効果だけを見る）。
                    f1_logband01 = _f1_from_feature_series(
                        np.log(_b01_bin + 1e-30), _label_qc
                    )
                    f1_logband12 = _f1_from_feature_series(
                        np.log(_b12_bin + 1e-30), _label_qc
                    )
                    f1_logband25 = _f1_from_feature_series(
                        np.log(_b25_bin + 1e-30), _label_qc
                    )
                    f1_logband515 = _f1_from_feature_series(
                        np.log(_b515_bin + 1e-30), _label_qc
                    )
                except Exception as _e:
                    log(f"    [F1_state band] スキップ {_e}")
                try:
                    _bh, _ah = highpass_coef(config.FS, 5.0, LPF_ORDER)
                    _hp_bin = stat_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, _bh, _ah, np.var
                    )
                    f1_high_pass = _f1_from_feature_series(_hp_bin, _label_qc)
                    _bb_bp, _ab_bp = bandpass_coef(config.FS, 1.0, 5.0, LPF_ORDER)
                    _bp_bin = stat_perbin(
                        pir_full, config.BIN_STATE, _origin_qc, _bb_bp, _ab_bp, np.var
                    )
                    f1_bandpass_var = _f1_from_feature_series(_bp_bin, _label_qc)
                except Exception as _e:
                    log(f"    [F1_state high_pass/bandpass] スキップ {_e}")

            # ---- 強度（暗期・10min）----
            log("    [2/9 intensity 暗期10min] 開始")
            s_dark = pir_full[dark]
            nano_dark = nano_full[
                (nano_full.index.hour >= config.DARK_HOURS[0])
                | (nano_full.index.hour < config.DARK_HOURS[1])
            ]
            loglp_i = logvar_perbin(s_dark, config.BIN_INTENSITY, origin, b_lp, a_lp)
            cnt_i = (
                nano_dark["Activity"]
                .resample(config.BIN_INTENSITY, origin=origin)
                .sum()
            )
            dfm = pd.DataFrame({"lv": loglp_i, "ct": cnt_i}).iloc[1:-1].dropna()
            if len(dfm) < 10:
                log(f"    [2/9 intensity] 有効ビン<10 ({len(dfm)}) → chスキップ")
                continue
            int_r = float(spearmanr(dfm["lv"], dfm["ct"])[0])
            # D (append-only): PIR-NanoTag lag by Spearman cross-correlation over +/-5 bins.
            # A peak at lag 0 justifies 'no delay correction'; a systematic offset would flag one.
            try:
                _xv, _yv = dfm["lv"].values, dfm["ct"].values
                _best_lag, _best_rr = 0, -np.inf
                for _k in range(-5, 6):
                    if _k < 0:
                        _a, _b = _xv[-_k:], _yv[: len(_yv) + _k]
                    elif _k > 0:
                        _a, _b = _xv[:-_k], _yv[_k:]
                    else:
                        _a, _b = _xv, _yv
                    if len(_a) > 10:
                        _rr = float(spearmanr(_a, _b)[0])
                        if np.isfinite(_rr) and _rr > _best_rr:
                            _best_rr, _best_lag = _rr, _k
                phase_lag_bins = int(_best_lag)
                phase_lag_r = float(_best_rr) if np.isfinite(_best_rr) else np.nan
            except Exception:
                phase_lag_bins, phase_lag_r = 0, np.nan
            dfa = dfm[dfm["ct"] > 0]
            r_act = (
                float(spearmanr(dfa["lv"], dfa["ct"])[0]) if len(dfa) > 5 else np.nan
            )
            trend = dfm["ct"].rolling(6, min_periods=1, center=True).mean()
            r_trend = (
                float(spearmanr(dfm["lv"], dfm["ct"] - trend)[0])
                if len(dfm) > 10
                else int_r
            )
            trend_lv = dfm["lv"].rolling(6, min_periods=1, center=True).mean()
            r_trend_sym = (
                float(spearmanr(dfm["lv"] - trend_lv, dfm["ct"] - trend)[0])
                if len(dfm) > 10 else np.nan
            )
            log(f"    [2/9 intensity] 完了 r={int_r:.3f} (bins={len(dfm)})")

            gmi = fit_gmm(dfm["lv"].values)
            pstate = (
                (
                    gmi["g"].predict(dfm["lv"].values.reshape(-1, 1)) != gmi["rest"]
                ).astype(int)
                if gmi
                else np.zeros(len(dfm), int)
            )
            nstate = (dfm["ct"].values > 0).astype(int)
            for i, (t, row) in enumerate(dfm.iterrows()):
                binned_rows.append(
                    {
                        "timestamp": str(t),
                        "ch": ch_id,
                        "mouse_id": mouse_id,
                        "sensor_id": sensor_id,
                        "record_id": rec_id,
                        "age_group": age_grp,
                        "log_lp_var": row["lv"],
                        "state": int(pstate[i]),
                        "nanotag_count": row["ct"],
                        "nanotag_state": int(nstate[i]),
                    }
                )

            # ---- 24h全期間(10min) PAI（Fig2用）＋ ★X5/X8 の材料 ----
            r_lightincl = r_lightonly = r_darkonly_24 = np.nan
            try:
                lv_24full = logvar_perbin(
                    pir_full, config.BIN_INTENSITY, origin, b_lp, a_lp
                )
                ct_24full = (
                    nano_full["Activity"]
                    .resample(config.BIN_INTENSITY, origin=origin)
                    .sum()
                )
                d24f = pd.DataFrame({"lv": lv_24full, "ct": ct_24full}).dropna()
                for t24, row24 in d24f.iterrows():
                    _is_dark = bool(
                        (t24.hour >= config.DARK_HOURS[0])
                        or (t24.hour < config.DARK_HOURS[1])
                    )
                    repr24_rows.append(
                        {
                            "ch": ch_id,
                            "mouse_id": mouse_id,
                            "timestamp": str(t24),
                            "hour": int(t24.hour),
                            "log_lp_var": float(row24["lv"]),
                            "nanotag_count": float(row24["ct"]),
                            "is_dark": _is_dark,
                        }
                    )
                if len(d24f) > 10:
                    r_lightincl = float(spearmanr(d24f["lv"], d24f["ct"])[0])
                # ★X5: 明期のみ / 暗期のみ（同一ビン集合から抽出＝公平比較）
                _hh = d24f.index.hour
                _dmask = (_hh >= config.DARK_HOURS[0]) | (_hh < config.DARK_HOURS[1])
                _dsub, _lsub = d24f[_dmask], d24f[~_dmask]
                if len(_dsub) > 10:
                    r_darkonly_24 = float(spearmanr(_dsub["lv"], _dsub["ct"])[0])
                if len(_lsub) > 10:
                    r_lightonly = float(spearmanr(_lsub["lv"], _lsub["ct"])[0])
                # ★X8: 暗期定義 ±1h ずらし
                if RUN_EXPL:
                    for _sh in DARK_DEF_SHIFTS:
                        _d0 = (int(config.DARK_HOURS[0]) + _sh) % 24
                        _d1 = (int(config.DARK_HOURS[1]) + _sh) % 24
                        _mk = (_hh >= _d0) | (_hh < _d1)
                        _ss = d24f[_mk]
                        darkdef_rows.append(
                            {
                                "ch": ch_id,
                                "mouse_id": mouse_id,
                                "shift_h": _sh,
                                "dark_start": _d0,
                                "dark_end": _d1,
                                "n_bins": len(_ss),
                                "intensity_r": round(
                                    float(spearmanr(_ss["lv"], _ss["ct"])[0]), 4
                                )
                                if len(_ss) > 10
                                else np.nan,
                            }
                        )
            except Exception as _e:
                log(f"    [repr_24h / X5 / X8] スキップ {_e}")

            # ---- プラセボ（別個体 nid±2）----
            log("    [3/9 placebo/phase] 開始")
            try:
                peer = (
                    str(int(nid) + 2) if int(nid) in [1, 2, 5, 6] else str(int(nid) - 2)
                )
            except ValueError:
                peer = None
            o = (
                nanos.get(peer)
                if (peer and peer in nanos)
                else next((nanos[k] for k in nanos if k != nid), None)
            )
            plac_r = np.nan
            if o is not None:
                od = o[
                    (o.index.hour >= config.DARK_HOURS[0])
                    | (o.index.hour < config.DARK_HOURS[1])
                ]
                oc = od["Activity"].resample(config.BIN_INTENSITY, origin=origin).sum()
                dp = pd.DataFrame({"lv": loglp_i, "pl": oc}).iloc[1:-1].dropna()
                if len(dp) > 10:
                    plac_r = float(spearmanr(dp["lv"], dp["pl"])[0])
            # R11: permutation null over N_PHASE_PERM shuffles (was a single shuffle).
            # shuff_r stays the *mean* null r (back-compatible); also expose the null SD and
            # a one-sided permutation p-value vs the observed intensity r for Methods.
            _n_perm = int(getattr(config, "N_PHASE_PERM", 200))
            _rng_perm = np.random.default_rng(42)
            _ct = dfm["ct"].values
            _lv = dfm["lv"].values
            _null = np.array(
                [float(spearmanr(_lv, _rng_perm.permutation(_ct))[0]) for _ in range(_n_perm)],
                dtype=float,
            )
            _null = _null[np.isfinite(_null)]
            shuff_r = float(np.mean(_null)) if len(_null) else np.nan
            shuff_r_sd = float(np.std(_null, ddof=1)) if len(_null) > 1 else np.nan
            shuff_p = (
                float((np.sum(_null >= int_r) + 1) / (len(_null) + 1))
                if (len(_null) and np.isfinite(int_r))
                else np.nan
            )
            log(
                f"    [3/9 placebo/phase] 完了 placebo={plac_r} "
                f"shuffle(mean of {len(_null)} perms)={shuff_r:.3f} sd={shuff_r_sd:.3f} p={shuff_p}"
            )

            try:
                for _kpid, _kser in nanos.items():
                    if _kpid == nid:
                        continue
                    _kd = _kser[
                        (_kser.index.hour >= config.DARK_HOURS[0])
                        | (_kser.index.hour < config.DARK_HOURS[1])
                    ]
                    _kc = (
                        _kd["Activity"]
                        .resample(config.BIN_INTENSITY, origin=origin)
                        .sum()
                    )
                    _dpp = pd.DataFrame({"lv": loglp_i, "pl": _kc}).iloc[1:-1].dropna()
                    if len(_dpp) > 10:
                        plc_pair_rows.append(
                            {
                                "ch": ch_id,
                                "mouse_id": mouse_id,
                                "ref_nanotag_id": _kpid,
                                "same_session": True,
                                "placebo_r": float(
                                    spearmanr(_dpp["lv"], _dpp["pl"])[0]
                                ),
                            }
                        )
            except Exception as _e:
                log(f"    [placebo全ペア] スキップ {_e}")

            try:
                plc_cross_cache.append(
                    {
                        "ch": ch_id,
                        "mouse_id": mouse_id,
                        "rec_id": rec_id,
                        "loglp_i": loglp_i.copy(),
                    }
                )
                nano_dark_cache.append(
                    {
                        "rec_id": rec_id,
                        "nid": nid,
                        "mouse_id": mouse_id,
                        "series": nano_full[
                            (nano_full.index.hour >= config.DARK_HOURS[0])
                            | (nano_full.index.hour < config.DARK_HOURS[1])
                        ]["Activity"]
                        .resample(config.BIN_INTENSITY, origin=origin)
                        .sum(),
                    }
                )
            except Exception as _e:
                log(f"    [placebo_cross キャッシュ] スキップ {_e}")

            # ---- ビン掃引 ----
            if RUN_SUPP:
                log(f"    [4/9 bin sweep] 開始 {list(config.BIN_SWEEP_SEC)}")
                for sec in config.BIN_SWEEP_SEC:
                    _t = time.time()
                    rule = f"{sec}s"
                    sqs = (
                        sq
                        if rule == config.BIN_STATE
                        else compute_state_qc(pir_full, nano_full, config.FS, rule)
                    )
                    lv_s = logvar_perbin(s_dark, rule, origin, b_lp, a_lp)
                    ct_s = nano_dark["Activity"].resample(rule, origin=origin).sum()
                    ds = pd.DataFrame({"lv": lv_s, "ct": ct_s}).iloc[1:-1].dropna()
                    r_s = (
                        float(spearmanr(ds["lv"], ds["ct"])[0])
                        if len(ds) > 10
                        else np.nan
                    )
                    sweep_rows.append(
                        {
                            "ch": ch_id,
                            "mouse_id": mouse_id,
                            "bin_sec": sec,
                            "f1_state": (sqs["F1_state"] if sqs else np.nan),
                            "intensity_r": r_s,
                        }
                    )
                    log(f"      sweep bin={sec}s 完了 ({time.time() - _t:.1f}s)")
                log("    [4/9 bin sweep] 完了")
            else:
                log("    [4/9 bin sweep] 高速モードのため省略")

            # ---- ★X1（重い）: LPFカットオフ掃引 ----
            if DO_LPF_SWEEP:
                log(f"    [4b/9 X1 LPF sweep] 開始 {LPF_SWEEP_HZ} Hz")
                for _cut in LPF_SWEEP_HZ:
                    _t = time.time()
                    if abs(_cut - 1.0) < 1e-12:
                        _sqc = sq  # 1.0Hzは既存結果を再利用（同一入力→同一値）
                        _r_c = int_r
                    else:
                        _sqc = compute_state_qc(
                            pir_full,
                            nano_full,
                            config.FS,
                            config.BIN_STATE,
                            cutoff=_cut,
                        )
                        _bc, _ac = lpf_coef(config.FS, _cut, LPF_ORDER)
                        _lvc = logvar_perbin(
                            s_dark, config.BIN_INTENSITY, origin, _bc, _ac
                        )
                        _dc = (
                            pd.DataFrame({"lv": _lvc, "ct": cnt_i}).iloc[1:-1].dropna()
                        )
                        _r_c = (
                            float(spearmanr(_dc["lv"], _dc["ct"])[0])
                            if len(_dc) > 10
                            else np.nan
                        )
                    lpf_sweep_rows.append(
                        {
                            "ch": ch_id,
                            "mouse_id": mouse_id,
                            "cutoff_hz": _cut,
                            "f1_state": (_sqc["F1_state"] if _sqc else np.nan),
                            "pir_active_rate": (
                                _sqc["pir_active_rate"] if _sqc else np.nan
                            ),
                            "intensity_r": _r_c,
                        }
                    )
                    log(f"      X1 cutoff={_cut}Hz 完了 ({time.time() - _t:.1f}s)")
                log("    [4b/9 X1 LPF sweep] 完了")

            # ---- 誤差分析 ----
            _bins_nb = sq.get("bins_nb", [np.nan] * len(sq["bins"]))
            for _bi, (dist, e, kind, pai, yt) in enumerate(sq["bins"]):
                err_rows.append({
                    "ch": ch_id, "dist": dist, "error": e, "kind": kind,
                    "pai": pai, "nb": (_bins_nb[_bi] if _bi < len(_bins_nb) else np.nan),
                })

            # ---- 特徴量ベンチ（実Welch帯域）----
            if RUN_SUPP:
                log("    [5/9 feature bench / Welch] 開始")
                res_v = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: np.var(x.values) if len(x) else np.nan
                )
                res_s = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: np.std(x.values) if len(x) else np.nan
                )
                res_r = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: np.ptp(x.values) if len(x) else np.nan
                )

                def _band(x, lo, hi):
                    v = x.values
                    if len(v) < 64:
                        return np.nan
                    f, P = scipy_signal.welch(v, config.FS, nperseg=min(len(v), 256))
                    return float(np.sum(P[(f >= lo) & (f < hi)]))

                b01 = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: _band(x, 0, 1)
                )
                b15 = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: _band(x, 1, 5)
                )
                b515 = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: _band(x, 5, 15)
                )
                b12 = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: _band(x, 1, 2)
                )
                b25 = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: _band(x, 2, 5)
                )
                _bh, _ah = highpass_coef(config.FS, 5.0, LPF_ORDER)
                _bbp, _abp = bandpass_coef(config.FS, 1.0, 5.0, LPF_ORDER)
                res_hp = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: (
                        float(np.var(scipy_signal.filtfilt(_bh, _ah, x.values)))
                        if len(x.values) > 30
                        else np.nan
                    )
                )
                res_bp = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: (
                        float(np.var(scipy_signal.filtfilt(_bbp, _abp, x.values)))
                        if len(x.values) > 30
                        else np.nan
                    )
                )
                res_lpvar = s_dark.resample(config.BIN_INTENSITY, origin=origin).apply(
                    lambda x: (
                        float(np.var(scipy_signal.filtfilt(b_lp, a_lp, x.values)))
                        if len(x.values) > 30
                        else np.nan
                    )
                )
                dff = (
                    pd.DataFrame(
                        {
                            "nano": cnt_i,
                            "log_lp_var": loglp_i,
                            "variance": res_v,
                            "std": res_s,
                            "range": res_r,
                            "band_0_1Hz": b01,
                            "band_1_5Hz": b15,
                            "band_5_15Hz": b515,
                            "band_1_2Hz": b12,
                            "band_2_5Hz": b25,
                            "high_pass": res_hp,
                            "bandpass_var": res_bp,
                            "raw_lp_var": res_lpvar,
                            "raw_amp": res_s,
                        }
                    )
                    .iloc[1:-1]
                    .dropna()
                )
                for fn in [
                    "log_lp_var",
                    "variance",
                    "std",
                    "range",
                    "band_0_1Hz",
                    "band_1_5Hz",
                    "band_5_15Hz",
                    "band_1_2Hz",
                    "band_2_5Hz",
                    "high_pass",
                    "bandpass_var",
                    "raw_lp_var",
                    "raw_amp",
                ]:
                    if len(dff) > 5:
                        feature_rows.append(
                            {
                                "ch": ch_id,
                                "mouse_id": mouse_id,
                                "feature": fn,
                                "r": float(spearmanr(dff[fn], dff["nano"])[0]),
                            }
                        )
                log("    [5/9 feature bench / Welch] 完了")
            else:
                log("    [5/9 feature bench / Welch] 高速モードのため省略")

            # ---- シード安定性 ----
            log("    [6/9 seed安定性] 開始")
            for seed in config.GMM_SEED_LIST:
                try:
                    g = GaussianMixture(
                        n_components=2, n_init=1, random_state=int(seed)
                    ).fit(dfm["lv"].values.reshape(-1, 1))
                    mu = np.sort(g.means_.flatten())
                    seed_rows.append(
                        {
                            "ch": ch_id,
                            "seed": int(seed),
                            "rest_mu": float(mu[0]),
                            "active_mu": float(mu[1]),
                            "bin_sec": 600,
                        }
                    )
                except Exception:
                    pass
                try:
                    _pai_state = np.array([bb[3] for bb in sq["bins"]], float)
                    if len(_pai_state) > 0:
                        _pai_s = np.array([bb[3] for bb in sq["bins"]], float)
                        _y_s = np.array([bb[4] for bb in sq["bins"]], int)
                        g60 = GaussianMixture(
                            n_components=2, n_init=1, random_state=int(seed)
                        ).fit(_pai_state.reshape(-1, 1))
                        mu60 = np.sort(g60.means_.flatten())
                        seed_rows.append(
                            {
                                "ch": ch_id,
                                "seed": int(seed),
                                "rest_mu": float(mu60[0]),
                                "active_mu": float(mu60[1]),
                                "bin_sec": 60,
                            }
                        )
                        _g = GaussianMixture(n_components=2, n_init=1, random_state=int(seed)).fit(_pai_s.reshape(-1, 1))
                        _m = _g.means_.flatten()
                        _rest = int(np.argmin(_m))
                        _pred = (_g.predict(_pai_s.reshape(-1, 1)) != _rest).astype(int)
                        _grid = np.linspace(_pai_s.min(), _pai_s.max(), 1000)
                        _resp = _g.predict_proba(_grid.reshape(-1, 1))[:, _rest]
                        _bnd = float(_grid[np.argmin(np.abs(_resp - 0.5))])
                        seed_state_rows.append({
                            "ch": ch_id, "mouse_id": mouse_id, "seed": int(seed),
                            "f1_state": float(f1_score(_y_s, _pred, zero_division=0)),
                            "pir_active_rate": float(np.mean(_pred)),
                            "gmm_boundary": _bnd,
                            "rest_mu": float(_m[_rest]),
                            "act_mu": float(_m[1 - _rest]),
                        })
                except Exception:
                    pass
            log("    [6/9 seed安定性] 完了")

            # ---- 学習曲線（強度側）----
            log("    [7/9 学習曲線] 開始")
            cum = 0
            grid = list(config.CUM_ACTIVE_BIN_GRID)
            gi = 0
            t0 = dfm.index[0]
            for i2 in range(len(dfm)):
                if dfm["ct"].iloc[i2] > 0:
                    cum += 1
                if gi < len(grid) and cum >= grid[gi]:
                    sub = dfm.iloc[: i2 + 1]
                    rr = (
                        float(spearmanr(sub["lv"], sub["ct"])[0])
                        if len(sub) > 5
                        else np.nan
                    )
                    gs = fit_gmm(sub["lv"].values)
                    learn_rows.append(
                        {
                            "ch": ch_id,
                            "mouse_id": mouse_id,
                            "n_active_bins": grid[gi],
                            "intensity_r": rr,
                            "rest_mu": (gs["rest_mu"] if gs else np.nan),
                            "elapsed_hours": round(
                                (dfm.index[i2] - t0).total_seconds() / 3600.0, 2
                            ),
                        }
                    )
                    gi += 1
            log("    [7/9 学習曲線] 完了")

            # ---- 学習曲線（状態側）----
            try:
                _pai = np.array([bb[3] for bb in sq["bins"]], float)
                _yy = np.array([bb[4] for bb in sq["bins"]], int)
                _grid = list(config.CUM_ACTIVE_BIN_GRID)
                _cum = 0
                _gi = 0
                for _j in range(len(_pai)):
                    if _yy[_j] == 1:
                        _cum += 1
                    if _gi < len(_grid) and _cum >= _grid[_gi]:
                        _sub = _pai[: _j + 1]
                        _gs = fit_gmm(_sub)
                        if _gs is not None:
                            _pred = (
                                _gs["g"].predict(_sub.reshape(-1, 1)) != _gs["rest"]
                            ).astype(int)
                            _parj = float(np.mean(_pred))
                            _f1j = (
                                float(f1_score(_yy[: _j + 1], _pred, zero_division=0))
                                if len(np.unique(_yy[: _j + 1])) > 1
                                else np.nan
                            )
                        else:
                            _parj, _f1j = np.nan, np.nan
                        state_learn_rows.append(
                            {
                                "ch": ch_id,
                                "mouse_id": mouse_id,
                                "n_active_bins_state": _grid[_gi],
                                "par_so_far": _parj,
                                "f1_so_far": _f1j,
                                "state_bins_used": _j + 1,
                                "approx_hours": round((_j + 1) * 60 / 3600.0, 2),
                                "final_par": sq["pir_active_rate"],
                            }
                        )
                        _gi += 1
            except Exception as _e:
                log(f"    [状態側学習曲線] スキップ {_e}")

            # ---- 較正 ＋ 概日 ----
            log("    [8/9 較正/概日] 開始")
            if df_ctrl is not None and c in df_ctrl.columns:
                cs = pd.to_numeric(df_ctrl[c], errors="coerce").ffill().fillna(0.0)
                cs = cs - np.median(cs.values)
                clv = logvar_perbin(
                    cs, config.BIN_INTENSITY, cs.index[0], b_lp, a_lp
                ).dropna()
                _clv60 = logvar_perbin(cs, config.BIN_STATE, cs.index[0], b_lp, a_lp).dropna()
                for _tt, _vv60 in _clv60.items():
                    calibration60_rows.append({"ch": ch_id, "mouse_id": mouse_id, "record_id": rec_id, "sensor_id": sensor_id, "timestamp": str(_tt), "log_lp_var": float(_vv60)})
                for v in clv.values:
                    calib_rows.append({"type": "empty", "log_lp_var": float(v)})
            for _lv_v, _ct_v in zip(dfm["lv"].values, dfm["ct"].values):
                _typ = "active_move" if _ct_v > 0 else "active_rest"
                calib_rows.append({"type": _typ, "log_lp_var": float(_lv_v)})

            if RUN_SUPP:
                lv24 = logvar_perbin(
                    pir_full, config.BIN_INTENSITY, origin, b_lp, a_lp
                ).dropna()
                ct24 = (
                    nano_full["Activity"]
                    .resample(config.BIN_INTENSITY, origin=origin)
                    .sum()
                )
                d24 = pd.DataFrame({"lv": lv24, "ct": ct24}).dropna()
                for t, row in d24.iterrows():
                    aa = circ.setdefault(t.hour, [0.0, 0, 0.0, 0])
                    aa[0] += row["lv"]
                    aa[1] += 1
                    aa[2] += row["ct"]
                    aa[3] += 1

            empty_mu = np.nan
            noise_sigma = np.nan
            if df_ctrl is not None and c in df_ctrl.columns:
                cv = pd.to_numeric(df_ctrl[c], errors="coerce").dropna().values
                if len(cv) > 0:
                    empty_mu, noise_sigma = float(np.mean(cv)), float(np.std(cv))
            log("    [8/9 較正/概日] 完了")

            try:
                _pai_state = np.array([bb[3] for bb in sq["bins"]], float)
                _eps_floor = float(np.log(1e-10))
                pai_floor_rate = float(np.mean(_pai_state <= _eps_floor + 1e-6))
                pai_near_floor_rate = float(np.mean(_pai_state <= _pai_state.min() + 0.5))
            except Exception:
                pai_floor_rate = np.nan
                pai_near_floor_rate = np.nan

            channel_rows.append(
                {
                    "ch": ch_id,
                    "mouse_id": mouse_id,
                    "sensor_id": sensor_id,
                    "record_id": rec_id,
                    "age_group": age_grp,
                    "sensor_set": sensor_set,
                    "sensor_set_sig": sensor_set_sig,
                    "sensor_set_fallback": _fb,
                    "F1_state": sq["F1_state"],
                    "pir_active_rate": sq["pir_active_rate"],
                    "nanotag_active_rate": sq["nanotag_active_rate"],
                    "snr": sq["snr"],
                    "floor_rate": sq["floor_rate"],
                    "pai_floor_rate": pai_floor_rate,
                    "pai_near_floor_rate": pai_near_floor_rate,
                    "gmm_separation": sq["gmm_separation"],
                    "gmm_boundary": sq["gmm_boundary"],
                    "gmm_rest_mu": sq["gmm_rest_mu"],
                    "gmm_act_mu": sq.get("gmm_act_mu", np.nan),
                    "n_state_bins": sq["n_state_bins"],
                    "empty_box_mu": empty_mu,
                    "noise_sigma": noise_sigma,
                    "intensity_r": int_r,
                    "intensity_r_trendrm": r_trend,
                    "intensity_r_trendrm_sym": r_trend_sym,
                    "intensity_r_activeonly": r_act,
                    "placebo_r": plac_r,
                    "phase_shuffle_r": shuff_r,
                    "phase_shuffle_r_sd": shuff_r_sd,
                    "phase_shuffle_p": shuff_p,
                    "bimodality_coef": bimod,
                    "gmm_rest_sd": sq.get("gmm_rest_sd", np.nan),
                    "gmm_act_sd": sq.get("gmm_act_sd", np.nan),
                    "gmm_rest_w": sq.get("gmm_rest_w", np.nan),
                    "gmm_act_w": sq.get("gmm_act_w", np.nan),
                    # append-only diagnostics (提案1/2/B)
                    "n_empty_nanobins": sq.get("n_empty_nanobins", np.nan),
                    "F1_state_nanotag_present": sq.get("F1_state_nanotag_present", np.nan),
                    "median_nb_tp": sq.get("median_nb_tp", np.nan),
                    "median_nb_fn": sq.get("median_nb_fn", np.nan),
                    "pai_iqr_active": sq.get("pai_iqr_active", np.nan),
                    "pai_sd_active": sq.get("pai_sd_active", np.nan),
                    "within_over_between": sq.get("within_over_between", np.nan),
                    "phase_lag_bins": phase_lag_bins,   # D: PIR-NanoTag lag (intensity bins)
                    "phase_lag_r": phase_lag_r,
                    "F1_state_rawvar": f1_rawvar,
                    "F1_state_std": f1_std,
                    "F1_state_range": f1_range,
                    "nano_rest_mu": nano_rest_mu,
                    "nano_rest_mu_mean": nano_rest_mu_mean,
                    "nano_act_mu": nano_act_mu,
                    "nano_act_mu_mean": nano_act_mu_mean,
                    "F1_state_var_nolpf": f1_var_nolpf,
                    "F1_state_logvar_nolpf": f1_logvar_nolpf,
                    "F1_state_band01": f1_band01,
                    "F1_state_band15": f1_band15,
                    "F1_state_band515": f1_band515,
                    "F1_state_high_pass": f1_high_pass,
                    "F1_state_raw_amp": f1_raw_amp,
                    "F1_state_bandpass_var": f1_bandpass_var,
                    "F1_state_band12": f1_band12,
                    "F1_state_band25": f1_band25,
                    # log-band variance の状態F1（帯域軸の正しい比較用）
                    "F1_state_logband01": f1_logband01,
                    "F1_state_logband12": f1_logband12,
                    "F1_state_logband25": f1_logband25,
                    "F1_state_logband515": f1_logband515,
                    # ★X5
                    "intensity_r_lightincl": r_lightincl,
                    "intensity_r_darkonly_24grid": r_darkonly_24,
                    "intensity_r_lightonly": r_lightonly,
                    # ★X6
                    "n_hours": round(n_hours, 3),
                    "n_bins_intensity": len(dfm),
                    "frac_missing": round(frac_missing, 5),
                    # ★V6-1: 生ADCの中央値（raw_value → raw_value_adc の復元に使う）
                    "adc_median_offset": _adc_offset,
                    "adc_range": float(np.ptp(_vv)) if len(_vv) else np.nan,
                    "adc_range_outlier": int(float(np.ptp(_vv)) > float(getattr(config, "ADC_RANGE_OUTLIER_V", 2.0))) if len(_vv) else 0,
                    "pai_contrast": (float(nano_act_mu_mean - nano_rest_mu_mean) if pd.notna(nano_act_mu_mean) and pd.notna(nano_rest_mu_mean) else np.nan),
                    "no_interior_crossing": int(sq.get("no_interior_crossing", 0)),
                    "outer_crossing_flag": int(sq.get("outer_crossing_flag", 0)),
                    "outer_crossing": sq.get("outer_crossing", np.nan),
                }
            )
            log(f"  ── ch {ch_id} 完了  (累積ch={len(channel_rows)})")
        del df_p
        if df_ctrl is not None:
            del df_ctrl
        gc.collect()
        log(f"■ 記録 {rec_id} 完了")

    log("全記録ループ終了 → 中核CSV書き出しへ")

    # ---------- 中核CSV ----------
    df_chan = pd.DataFrame(channel_rows)
    df_binned = pd.DataFrame(binned_rows)
    log(f"df_chan={len(df_chan)}行  df_binned={len(df_binned)}行")

    # 防御的フィルタ: Young以外が混じっていないか
    _n_all = len(df_chan)
    df_chan = df_chan[df_chan["age_group"] == "Young"].reset_index(drop=True)
    if len(df_chan) != _n_all:
        log(
            f"  [警告] Young以外を {_n_all - len(df_chan)} ch 除外しました（ゲート要再確認）"
        )
    else:
        log(f"  [age check] 全 {len(df_chan)} ch が Young。ゲート影響なし。")

    if sensor_set_fallback_used:
        log(
            f"  [警告] sensor_set フォールバック使用 {sensor_set_fallback_used} ch。"
            f"mapping.csv の sensor_id を確認してください（X1-X8 / Y1-Y8 形式）。"
        )
    else:
        log("  [sensor set] 全ch が sensor_id 由来で判定（fallback_used=0）")

    # QC閾値をYoung LOMOで導出
    log(f"QC1閾値 Young LOMO 導出 開始 (good=F1>={GOOD_F1})")
    yng = (
        df_chan[df_chan["age_group"] == "Young"]
        .dropna(subset=["pir_active_rate", "F1_state"])
        .copy()
    )
    loso_thr = []
    for exc in sorted(yng["mouse_id"].unique()):
        tr = yng[yng["mouse_id"] != exc]
        good = (tr["F1_state"] >= GOOD_F1).astype(int)
        if good.nunique() < 2:
            continue
        fpr, tpr, thr = roc_curve(good, tr["pir_active_rate"])
        thr = np.where(np.isinf(thr), np.nan, thr)
        _idx = np.nanargmax(tpr - fpr)
        _thr_val = float(thr[_idx])
        _match = tr.loc[np.isclose(tr["pir_active_rate"].astype(float), _thr_val, rtol=0, atol=1e-12), "ch"].astype(str).tolist()
        loso_thr.append(
            {
                "fold_excluded_mouse": exc,
                "qc1_threshold": _thr_val,
                "threshold_source_ch": ";".join(_match) if _match else "[no exact par match]",
                "sensitivity": float(tpr[_idx]),
                "specificity": float(1 - fpr[_idx]),
            }
        )
    df_loso_thr = pd.DataFrame(loso_thr)
    qc1_thr = (
        float(df_loso_thr["qc1_threshold"].mean())
        if len(df_loso_thr)
        else config.QC1_THRESHOLD
    )
    df_chan["qc1_pass"] = (df_chan["pir_active_rate"] >= qc1_thr).astype(int)
    _c = float(GOOD_F1)
    _nar = df_chan["nanotag_active_rate"].astype(float)
    _par = df_chan["pir_active_rate"].astype(float)
    df_chan["f1_upper_bound"] = 2.0 * np.minimum(_par, _nar) / (_par + _nar).replace(0, np.nan)
    df_chan["par_needed_for_good"] = (_c / (2.0 - _c)) * _nar
    df_chan["par_upper_for_good"] = ((2.0 - _c) / _c) * _nar
    df_chan["clears_algebraic_bound"] = ((_par >= df_chan["par_needed_for_good"]) & (_par <= df_chan["par_upper_for_good"])).astype(int)
    log(f"QC1閾値 導出完了 qc1_thr={qc1_thr:.4f}")

    # ★QCルール梯子（4段・ASCIIキー）
    _par_ok = df_chan["pir_active_rate"] >= qc1_thr
    _snr_ok = df_chan["snr"] >= QC1_MULTI_SNR_MIN
    _sep_ok = df_chan["gmm_separation"] >= QC1_MULTI_GMM_SEP_MIN
    df_chan["qc1_pass_snrguard"] = (_par_ok & _snr_ok).astype(int)
    df_chan["qc1_pass_sepguard"] = (_par_ok & _sep_ok).astype(int)
    df_chan["qc1_pass_multi"] = (_par_ok & _snr_ok & _sep_ok).astype(int)
    RULE_COLS = {
        "par_only": "qc1_pass",
        "par_snr": "qc1_pass_snrguard",
        "par_sep": "qc1_pass_sepguard",
        "par_snr_sep": "qc1_pass_multi",
    }
    for _k, _c in RULE_COLS.items():
        log(
            f"  [QC ladder] {_k:<12}: 通過 {int(df_chan[_c].sum())} ch / "
            f"{int(df_chan[df_chan[_c] == 1]['mouse_id'].nunique())} 頭"
        )

    _write_csv(df_chan, os.path.join(config.INTERMEDIATE_DIR, "int_channel.csv"))
    _write_csv(df_binned, os.path.join(config.INTERMEDIATE_DIR, "int_binned.csv"))
    _write_csv(df_loso_thr, os.path.join(config.INTERMEDIATE_DIR, "int_loso_thr.csv"))
    if RUN_SUPP:
        _write_csv(pd.DataFrame(sweep_rows), os.path.join(config.INTERMEDIATE_DIR, "int_bin_sweep.csv"))
    log("中核CSV 保存完了")

    def save(n, d):
        # v3: every intermediate writer goes through _write_csv so the generator is auditable.
        _write_csv(d, os.path.join(config.INTERMEDIATE_DIR, n))

    def block(n, fn):
        _t = time.time()
        log(f"  [補足 {n}] 開始")
        try:
            fn()
            log(f"  [補足 {n}] 完了 ({time.time() - _t:.1f}s)")
        except Exception as e:
            print(f"  [補足スキップ] {n}: {e}", flush=True)

    # ---- ★V6-1: 生ADC診断表（Fig1で読む列が正しいかの一次資料）----
    def _adc_diag():
        if not adc_diag_rows:
            log("    [ADC診断] 行なし → スキップ")
            return
        d = pd.DataFrame(adc_diag_rows)
        save("int_adc_diagnostic.csv", d)
        if channel_map_rows:
            save("int_channel_map.csv", pd.DataFrame(channel_map_rows))
            log(f"    [ch->mouse map] int_channel_map.csv saved ({len(channel_map_rows)} ch)")
        _bad = d[d["looks_like_0p01_adc"] == 0]
        log(
            f"    [ADC診断] {len(d)} ch 中 0.01刻みとして整合 {int(d['looks_like_0p01_adc'].sum())} ch"
        )
        for _, r in _bad.iterrows():
            log(
                f"      !! {r['ch']} col='{r['pir_col']}' range={r['range']:.6g} "
                f"step={r['smallest_step']:.6g} → 生ADCでない可能性。mapping.csv を確認。"
            )

    block("adc_diagnostic", _adc_diag)
    block("nanotag_integrity", lambda: save("int_nanotag_integrity.csv", pd.DataFrame(nanotag_integrity_rows)))
    block("bin_coverage", lambda: save("int_bin_coverage.csv", pd.DataFrame(bin_coverage_rows)))
    block("calibration_60s", lambda: save("int_calibration_60s.csv", pd.DataFrame(calibration60_rows)))
    block("filter_mode_compare_raw", lambda: save("int_filter_mode_compare.csv", pd.DataFrame(filter_compare_rows)))
    block("label_sweep_channel", lambda: save("int_label_sweep_channel.csv", pd.DataFrame(label_sweep_channel_rows)))
    block("session_timecourse", lambda: save("int_session_timecourse.csv", pd.DataFrame(session_timecourse_rows)))
    block("session_timecourse_admission", lambda: save(
        "int_session_timecourse_admission.csv",
        pd.DataFrame(session_timecourse_rows).reindex(columns=[
            "ch", "mouse_id", "record_id", "block_index", "block_start_h",
            "n_pai_bins", "n_nano_bins_present", "pai_frac", "nano_frac", "block_usable"
        ])))

    # ---- int_mouse ----
    log("  int_mouse 集約 開始")
    mr = []
    for mid, g in df_chan.groupby("mouse_id"):
        vi = g["intensity_r"].dropna()
        mr.append(
            {
                "mouse_id": mid,
                "n_ch": len(g),
                "agg_intensity_r": float(vi.median()) if len(vi) else np.nan,
                "mean_active_rate": float(g["pir_active_rate"].mean()),
                "mean_f1": float(g[g["qc1_pass"] == 1]["F1_state"].mean())
                if (g["qc1_pass"] == 1).any()
                else float(g["F1_state"].mean()),
                "qc1_any": int((g["qc1_pass"] == 1).any()),
            }
        )
    save("int_mouse.csv", pd.DataFrame(mr))
    log("  int_mouse 保存完了")

    def _feat():
        fb = (
            pd.DataFrame(feature_rows)
            .groupby("feature")["r"]
            .agg(
                median_r="median",
                mean_r="mean",
                iqr_r=lambda x: x.quantile(0.75) - x.quantile(0.25),
                sd_r="std",
                n_ch="count",
            )
            .reset_index()
            .sort_values("median_r", ascending=False)
        )
        save("int_feature_bench.csv", fb)
        # ★V6-2: S2(a) に個体点を重ねるため、集約前の生値も保存する（加算的・ゲート不変）。
        save("int_feature_bench_perch.csv", pd.DataFrame(feature_rows))

    if RUN_SUPP:
        block("feature_bench", _feat)

    # ---- QC相関/AUC（good_cut 全掃引 + 0.60 互換）----
    def _qcc():
        rows = []
        thr_list = sorted(set(list(GOOD_CUT_SWEEP) + [0.60]))
        for qm in ["pir_active_rate", "snr", "floor_rate", "gmm_separation"]:
            v = df_chan.dropna(subset=[qm, "F1_state"])
            for thr in thr_list:
                lbl = (v["F1_state"] >= thr).astype(int)
                auc = float(roc_auc_score(lbl, v[qm])) if lbl.nunique() > 1 else np.nan
                sp = float(spearmanr(v[qm], v["F1_state"])[0])
                rows.append(
                    {
                        "qc_metric": qm,
                        "f1_thr": thr,
                        "spearman": round(sp, 4),
                        "auc": round(auc, 4) if pd.notna(auc) else np.nan,
                        "n_good": int(lbl.sum()),
                        "n_bad": int((1 - lbl).sum()),
                    }
                )
        save("int_qc_corr.csv", pd.DataFrame(rows))

    block("qc_corr", _qcc)

    # ---- 混同行列（good_cut × 4ルール・ASCIIキー）----
    def _qcconf():
        rows = []
        for gc_cut in GOOD_CUT_SWEEP:
            true_good = (df_chan["F1_state"] >= gc_cut).astype(int)
            for rule_name, col in RULE_COLS.items():
                pred = df_chan[col].astype(int)
                tp, fp, fn, tn = _confusion_counts(pred, true_good)
                ppv, npv, sens, spec = _rate_metrics(tp, fp, fn, tn)
                rows.append(
                    {
                        "good_cut": gc_cut,
                        "rule": rule_name,
                        "TP": tp,
                        "FP": fp,
                        "FN": fn,
                        "TN": tn,
                        "n_pass": tp + fp,
                        "n_pass_mice": int(
                            df_chan[df_chan[col] == 1]["mouse_id"].nunique()
                        ),
                        "n_good_ch": int(true_good.sum()),
                        "n_bad_ch": int((1 - true_good).sum()),
                        "PPV": round(ppv, 4) if pd.notna(ppv) else np.nan,
                        "NPV": round(npv, 4) if pd.notna(npv) else np.nan,
                        "sensitivity": round(sens, 4) if pd.notna(sens) else np.nan,
                        "specificity": round(spec, 4) if pd.notna(spec) else np.nan,
                        "interpretable": int(
                            min(int(true_good.sum()), int((1 - true_good).sum())) >= 5
                        ),
                    }
                )
        dfc = pd.DataFrame(rows)
        save("int_qc_confusion.csv", dfc)
        for _rk in ["par_only", "par_snr_sep"]:
            chk = dfc[(np.isclose(dfc["good_cut"], GOOD_F1)) & (dfc["rule"] == _rk)]
            if len(chk):
                r0 = chk.iloc[0]
                log(
                    f"    [検算] good={GOOD_F1}・{_rk}: TP={r0['TP']} FP={r0['FP']} "
                    f"FN={r0['FN']} TN={r0['TN']} PPV={r0['PPV']} sens={r0['sensitivity']} "
                    f"n_pass={r0['n_pass']}/{r0['n_pass_mice']}頭"
                )

    block("qc_confusion", _qcconf)

    # ---- 集約サマリ（両統計）----
    def _agg_summary():
        rows = []
        pm_r = df_chan.groupby("mouse_id")["intensity_r"].median()
        mm_r = df_chan.groupby("mouse_id")["intensity_r"].mean()
        rows.append(
            {
                "metric": "intensity_r",
                "scope": "all",
                "median_of_medians": round(float(pm_r.median()), 4),
                "mean_of_means": round(float(mm_r.mean()), 4),
                "flat_mean": round(float(df_chan["intensity_r"].mean()), 4),
                "flat_median": round(float(df_chan["intensity_r"].median()), 4),
                "iqr_of_permouse": round(
                    float(pm_r.quantile(0.75) - pm_r.quantile(0.25)), 4
                ),
                "n_mouse": int(pm_r.size),
                "n_ch": len(df_chan),
            }
        )
        scopes = [("all", pd.Series(True, index=df_chan.index))]
        for _k, _c in RULE_COLS.items():
            scopes.append((_k, df_chan[_c] == 1))
        for scope, mask in scopes:
            sub = df_chan[mask]
            if len(sub) == 0:
                continue
            pm_f1 = sub.groupby("mouse_id")["F1_state"].median()
            mm_f1 = sub.groupby("mouse_id")["F1_state"].mean()
            rows.append(
                {
                    "metric": "F1_state",
                    "scope": scope,
                    "median_of_medians": round(float(pm_f1.median()), 4),
                    "mean_of_means": round(float(mm_f1.mean()), 4),
                    "flat_mean": round(float(sub["F1_state"].mean()), 4),
                    "flat_median": round(float(sub["F1_state"].median()), 4),
                    "iqr_of_permouse": round(
                        float(pm_f1.quantile(0.75) - pm_f1.quantile(0.25)), 4
                    ),
                    "n_mouse": int(pm_f1.size),
                    "n_ch": len(sub),
                }
            )
        save("int_aggregation_summary.csv", pd.DataFrame(rows))
        for r in rows:
            log(
                f"    [検算] {r['metric']}/{r['scope']}: MoM={r['median_of_medians']} "
                f"MeanOfMeans={r['mean_of_means']} (n_mouse={r['n_mouse']}, n_ch={r['n_ch']})"
            )

    block("aggregation_summary", _agg_summary)

    # ---- good定義の感度（PPV・par-AUC・クラス数つき）----
    def _good_sensitivity():
        rows = []
        for gc_cut in GOOD_CUT_SWEEP:
            _thrs = []
            _nfold = 0
            for exc in sorted(yng["mouse_id"].unique()):
                tr = yng[yng["mouse_id"] != exc]
                good = (tr["F1_state"] >= gc_cut).astype(int)
                if good.nunique() < 2:
                    continue
                fpr, tpr, thr = roc_curve(good, tr["pir_active_rate"])
                thr = np.where(np.isinf(thr), np.nan, thr)
                _thrs.append(float(thr[np.nanargmax(tpr - fpr)]))
                _nfold += 1
            gc_thr = float(np.mean(_thrs)) if _thrs else np.nan
            thr_source = "lomo" if _thrs else "none"
            # ★V6-3: 全foldで good/bad が片側に偏り LOMO が成立しない cut のみ、
            #   全データROCで閾値を代替し「行が空で理由不明」という状態をなくす。
            #   good=0.70 は必ず _thrs が埋まるため、この分岐には入らない＝確定ゲート不変。
            if not np.isfinite(gc_thr):
                _v0 = yng.dropna(subset=["pir_active_rate", "F1_state"])
                _lab0 = (_v0["F1_state"] >= gc_cut).astype(int)
                if _lab0.nunique() > 1:
                    fpr, tpr, thr = roc_curve(_lab0, _v0["pir_active_rate"])
                    thr = np.where(np.isinf(thr), np.nan, thr)
                    gc_thr = float(thr[np.nanargmax(tpr - fpr)])
                    thr_source = "full_roc_fallback"
            true_good = (df_chan["F1_state"] >= gc_cut).astype(int)
            n_good = int(true_good.sum())
            n_bad = int((1 - true_good).sum())
            if pd.notna(gc_thr):
                pred = (df_chan["pir_active_rate"] >= gc_thr).astype(int)
                passed = df_chan[pred == 1]
                tp, fp, fn, tn = _confusion_counts(pred, true_good)
                ppv, npv, sens, spec = _rate_metrics(tp, fp, fn, tn)
            else:
                passed = df_chan.iloc[0:0]
                ppv = sens = spec = np.nan
            v = df_chan.dropna(subset=["pir_active_rate", "F1_state"])
            lbl = (v["F1_state"] >= gc_cut).astype(int)
            par_auc = (
                float(roc_auc_score(lbl, v["pir_active_rate"]))
                if lbl.nunique() > 1
                else np.nan
            )
            f1_qc_post = (
                float(passed.groupby("mouse_id")["F1_state"].mean().mean())
                if len(passed)
                else np.nan
            )
            rows.append(
                {
                    "good_cut": gc_cut,
                    "lomo_threshold": round(gc_thr, 4) if pd.notna(gc_thr) else np.nan,
                    "threshold_source": thr_source,
                    "n_fold_used": _nfold,
                    "n_good_ch": n_good,
                    "n_bad_ch": n_bad,
                    "n_pass_ch": len(passed),
                    "n_pass_mice": int(passed["mouse_id"].nunique())
                    if len(passed)
                    else 0,
                    "PPV": round(ppv, 4) if pd.notna(ppv) else np.nan,
                    "sensitivity": round(sens, 4) if pd.notna(sens) else np.nan,
                    "specificity": round(spec, 4) if pd.notna(spec) else np.nan,
                    "par_auc": round(par_auc, 4) if pd.notna(par_auc) else np.nan,
                    "f1_qc_post": round(f1_qc_post, 4)
                    if pd.notna(f1_qc_post)
                    else np.nan,
                    # クラス不均衡で解釈不能なセルを明示（片側 <5 なら 0）
                    "interpretable": int(min(n_good, n_bad) >= 5),
                }
            )
        dfg = pd.DataFrame(rows)
        save("int_good_sensitivity.csv", dfg)
        for _, r in dfg.iterrows():
            log(
                f"    [good_sens] cut={r['good_cut']:.2f} thr={r['lomo_threshold']} "
                f"src={r['threshold_source']} n_fold={r['n_fold_used']} "
                f"good/bad={r['n_good_ch']}/{r['n_bad_ch']} pass={r['n_pass_ch']}ch "
                f"PPV={r['PPV']} AUC={r['par_auc']} F1post={r['f1_qc_post']} "
                f"interpretable={r['interpretable']}"
            )

    block("good_sensitivity", _good_sensitivity)

    # ---- ★X10: par閾値の連続掃引 ----
    def _thr_sweep():
        rows = []
        true_good = (df_chan["F1_state"] >= GOOD_F1).astype(int)
        for t in PAR_THRESHOLD_SWEEP:
            pred = (df_chan["pir_active_rate"] >= t).astype(int)
            passed = df_chan[pred == 1]
            tp, fp, fn, tn = _confusion_counts(pred, true_good)
            ppv, npv, sens, spec = _rate_metrics(tp, fp, fn, tn)
            rows.append(
                {
                    "par_threshold": t,
                    "n_pass_ch": int(pred.sum()),
                    "n_pass_mice": int(passed["mouse_id"].nunique())
                    if len(passed)
                    else 0,
                    "TP": tp,
                    "FP": fp,
                    "FN": fn,
                    "TN": tn,
                    "PPV": round(ppv, 4) if pd.notna(ppv) else np.nan,
                    "sensitivity": round(sens, 4) if pd.notna(sens) else np.nan,
                    "f1_qc_post": round(
                        float(passed.groupby("mouse_id")["F1_state"].mean().mean()), 4
                    )
                    if len(passed)
                    else np.nan,
                    "is_confirmed_threshold": int(abs(t - qc1_thr) < 0.005),
                }
            )
        save("int_qc_threshold_sweep.csv", pd.DataFrame(rows))

    if RUN_EXPL:
        block("qc_threshold_sweep", _thr_sweep)

    def _lomo():
        rows = []
        for exc in sorted(df_chan["mouse_id"].unique()):
            rem = df_chan[df_chan["mouse_id"] != exc]
            rows.append(
                {
                    "fold_excluded_mouse": exc,
                    "median_r_after": round(
                        float(rem.groupby("mouse_id")["intensity_r"].median().median()),
                        4,
                    ),
                    "mean_f1_after": round(
                        float(rem.groupby("mouse_id")["F1_state"].mean().mean()), 4
                    ),
                }
            )
        save("int_lomo.csv", pd.DataFrame(rows))

    block("lomo", _lomo)

    # ---- 状態F1(QC後)のLOSO ----
    def _loso_f1():
        rows = []
        for exc in sorted(df_chan["mouse_id"].unique()):
            rem = df_chan[df_chan["mouse_id"] != exc]
            rows.append(
                {
                    "fold_excluded_mouse": exc,
                    "n_mouse_remaining": int(rem["mouse_id"].nunique()),
                    "f1_all": round(
                        float(rem.groupby("mouse_id")["F1_state"].mean().mean()), 4
                    ),
                    "f1_qc_post": round(
                        float(
                            rem[rem["qc1_pass"] == 1]
                            .groupby("mouse_id")["F1_state"]
                            .mean()
                            .mean()
                        ),
                        4,
                    )
                    if (rem["qc1_pass"] == 1).any()
                    else np.nan,
                    "f1_qc_post_multi": round(
                        float(
                            rem[rem["qc1_pass_multi"] == 1]
                            .groupby("mouse_id")["F1_state"]
                            .mean()
                            .mean()
                        ),
                        4,
                    )
                    if (rem["qc1_pass_multi"] == 1).any()
                    else np.nan,
                    "n_qc_pass_ch_remaining": int((rem["qc1_pass"] == 1).sum()),
                }
            )
        dfl = pd.DataFrame(rows)
        save("int_loso_f1.csv", dfl)
        log(
            f"    [検算] LOSO F1(QC後): range=[{dfl['f1_qc_post'].min():.4f}, "
            f"{dfl['f1_qc_post'].max():.4f}] (全体基準は検算ゲート参照)"
        )

    # FIX: _loso_f1 was defined but never registered, so int_loso_f1.csv was never
    # written and Figure S5(c) fell back to its "missing" placeholder.
    block("loso_f1", _loso_f1)

    block("seed", lambda: save("int_seed_stability.csv", pd.DataFrame(seed_rows)))
    block("seed_state", lambda: save("int_seed_state_stability.csv", pd.DataFrame(seed_state_rows)))
    block("learn", lambda: save("int_learning_curve.csv", pd.DataFrame(learn_rows)))
    block("calib", lambda: save("int_calibration.csv", pd.DataFrame(calib_rows)))

    def _err():
        e = pd.DataFrame(err_rows)
        if e.empty:
            return
        save(
            "int_error_summary.csv",
            pd.DataFrame(
                [
                    {
                        "FN": int((e["kind"] == "FN").sum()),
                        "FP": int((e["kind"] == "FP").sum()),
                        "errors": int(e["error"].sum()),
                        "bins": len(e),
                    }
                ]
            ),
        )
        e["db"] = pd.cut(
            e["dist"],
            [0, 0.5, 1, 1.5, 2, 3, np.inf],
            labels=["0-0.5", "0.5-1", "1-1.5", "1.5-2", "2-3", ">3"],
        )
        by = (
            e.groupby("db", observed=True)["error"]
            .agg(n="count", err="sum")
            .reset_index()
        )
        by["error_rate"] = (by["err"] / by["n"]).round(4)
        by["n_error"] = by["err"]
        save("int_error_bydist.csv", by)
        byc = (e.groupby(["ch", "db"], observed=True)["error"].agg(n="count", n_error="sum").reset_index())
        byc["error_rate"] = byc["n_error"] / byc["n"]
        save("int_error_bydist_perch.csv", byc)
        byk = (
            e[e["kind"].isin(["FN", "FP"])]
            .groupby(["db", "kind"], observed=True)
            .size()
            .reset_index(name="n")
        )
        save("int_error_bydist_bykind.csv", byk)
        # S6キャプションの根拠: 非単調が n 不足で説明できるかを判定材料として出す
        log("    [S6根拠] 距離bin別 error_rate と n:")
        for r in by.itertuples():
            log(
                f"       {r.db}: rate={r.error_rate} n={int(r.n)} n_error={int(r.n_error)}"
            )

    block("error", _err)

    def _circ():
        rows = [
            {
                "hour": h,
                "pir_mean": circ[h][0] / max(circ[h][1], 1),
                "nano_mean": circ[h][2] / max(circ[h][3], 1),
            }
            for h in sorted(circ)
        ]
        cc = pd.DataFrame(rows)
        if len(cc) > 2:
            nz = lambda x: (
                (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0
            )
            cc["pir_norm"] = nz(cc["pir_mean"])
            cc["nano_norm"] = nz(cc["nano_mean"])
            print(
                f"  [S6概日] 実測 r = {spearmanr(cc['pir_norm'], cc['nano_norm'])[0]:.4f}",
                flush=True,
            )
        save("int_circadian.csv", cc)

    if RUN_SUPP:
        block("circadian", _circ)

    # ---- センサー間一致（＋★X7 Bland-Altman）----
    def _sens():
        rows = []
        ba_rows = []
        ba_pairs = []
        for (rec, mid), g in df_binned.groupby(["record_id", "mouse_id"]):
            chs = sorted(g["ch"].unique())
            if len(chs) >= 2:
                aa = g[g["ch"] == chs[0]][["timestamp", "log_lp_var"]].rename(
                    columns={"log_lp_var": "a"}
                )
                bb = g[g["ch"] == chs[1]][["timestamp", "log_lp_var"]].rename(
                    columns={"log_lp_var": "b"}
                )
                mg = aa.merge(bb, on="timestamp").dropna()
                if len(mg) > 5:
                    rows.append(
                        {
                            "record_id": rec,
                            "mouse_id": mid,
                            "ch_a": chs[0],
                            "ch_b": chs[1],
                            "inter_sensor_r": round(
                                float(spearmanr(mg["a"], mg["b"])[0]), 4
                            ),
                            "n_pairs": len(mg),
                        }
                    )
                    d = mg["a"].values - mg["b"].values
                    m_ = (mg["a"].values + mg["b"].values) / 2.0
                    bias = float(np.mean(d))
                    sd = float(np.std(d, ddof=1))
                    ba_rows.append(
                        {
                            "record_id": rec,
                            "mouse_id": mid,
                            "ch_a": chs[0],
                            "ch_b": chs[1],
                            "n": len(d),
                            "bias": round(bias, 4),
                            "sd_diff": round(sd, 4),
                            "loa_lower": round(bias - 1.96 * sd, 4),
                            "loa_upper": round(bias + 1.96 * sd, 4),
                        }
                    )
                    for _m, _d in zip(m_, d):
                        ba_pairs.append(
                            {
                                "mouse_id": mid,
                                "record_id": rec,
                                "mean_ab": float(_m),
                                "diff_ab": float(_d),
                            }
                        )
        dfr = pd.DataFrame(rows)
        save("int_sensor_consistency.csv", dfr)
        if len(dfr):
            pm = (
                dfr.groupby("mouse_id")["inter_sensor_r"]
                .median()
                .reset_index()
                .rename(columns={"inter_sensor_r": "median_inter_sensor_r"})
            )
            # #2: also expose the per-mouse MEAN (append-only) so a pure-mean Fig6(a) is possible
            _pmmean = (
                dfr.groupby("mouse_id")["inter_sensor_r"]
                .mean()
                .reset_index()
                .rename(columns={"inter_sensor_r": "mean_inter_sensor_r"})
            )
            _pmn = (
                dfr.groupby("mouse_id")["inter_sensor_r"]
                .size()
                .reset_index()
                .rename(columns={"inter_sensor_r": "n_pairs_inter_sensor"})
            )
            pm = pm.merge(_pmmean, on="mouse_id", how="left").merge(_pmn, on="mouse_id", how="left")
            save("int_sensor_consistency_permouse.csv", pm)
            log(
                f"    [検算] 個体別inter-sensor r 中央={pm['median_inter_sensor_r'].median():.4f} "
                f"平均={pm['mean_inter_sensor_r'].mean():.4f} (n_mouse={len(pm)})"
            )
        if RUN_EXPL and ba_rows:
            save("int_bland_altman.csv", pd.DataFrame(ba_rows))
            save("int_bland_altman_pairs.csv", pd.DataFrame(ba_pairs))
            _all_d = np.array([r["diff_ab"] for r in ba_pairs], float)
            log(
                f"    [X7 Bland-Altman] pooled bias={np.mean(_all_d):.4f} "
                f"SD={np.std(_all_d, ddof=1):.4f} "
                f"LoA=[{np.mean(_all_d) - 1.96 * np.std(_all_d, ddof=1):.4f}, "
                f"{np.mean(_all_d) + 1.96 * np.std(_all_d, ddof=1):.4f}] n={len(_all_d)}"
            )

    block("sensor", _sens)

    block(
        "placebo_pairs",
        lambda: save("int_placebo_pairs.csv", pd.DataFrame(plc_pair_rows)),
    )

    def _plc_cross():
        if not plc_cross_cache or not nano_dark_cache:
            log("    [placebo_cross] キャッシュ空 → スキップ")
            return
        seen = {}
        for e in nano_dark_cache:
            key = (e["rec_id"], e["nid"])
            if key not in seen:
                seen[key] = e
        cand = list(seen.values())
        rows = []
        for chc in plc_cross_cache:
            slot_pai = chc["loglp_i"].index.hour * 6 + chc["loglp_i"].index.minute // 10
            tod_pai = chc["loglp_i"].groupby(slot_pai).median()
            for e in cand:
                if e["rec_id"] == chc["rec_id"] or e["mouse_id"] == chc["mouse_id"]:
                    continue
                slot_nano = e["series"].index.hour * 6 + e["series"].index.minute // 10
                tod_nano = e["series"].groupby(slot_nano).median()
                common = tod_pai.index.intersection(tod_nano.index)
                if len(common) > 10:
                    rr = float(spearmanr(tod_pai.loc[common], tod_nano.loc[common])[0])
                    rows.append(
                        {
                            "ch": chc["ch"],
                            "mouse_id": chc["mouse_id"],
                            "ref_nanotag_id": e["nid"],
                            "ref_record_id": e["rec_id"],
                            "same_session": False,
                            "placebo_r": rr,
                        }
                    )
        base = pd.DataFrame(plc_pair_rows)
        combined = (
            pd.concat([base, pd.DataFrame(rows)], ignore_index=True) if rows else base
        )
        save("int_placebo_pairs.csv", combined)
        log(f"    [placebo_cross] 別セッション別個体ペア {len(rows)}件を追加保存")

    block("placebo_pairs_cross", _plc_cross)
    def _save_bic():
        df_bic = pd.DataFrame(bic_rows)
        save("int_gmm_bic.csv", df_bic)
        if not df_bic.empty:
            elbow_rows = []
            for ch, g in df_bic.groupby("ch"):
                s = g.set_index("k")["bic"]
                argmin_k = s.idxmin()
                # elbow_at_2: (BIC[K=1] - BIC[K=2]) > 2 * (BIC[K=2] - BIC[K=3])
                v1, v2, v3 = s.get(1, 0), s.get(2, 0), s.get(3, 0)
                elbow_at_2 = 1 if (v1 - v2) > 2 * (v2 - v3) else 0
                elbow_rows.append({"ch": ch, "argmin_k": argmin_k, "elbow_at_2": elbow_at_2})
            save("int_gmm_bic_elbow.csv", pd.DataFrame(elbow_rows))
            log(f"    [gmm_bic] Saved int_gmm_bic.csv and int_gmm_bic_elbow.csv")
    block("gmm_bic", _save_bic)
    block(
        "qc_learning",
        lambda: save("int_qc_learning.csv", pd.DataFrame(state_learn_rows)),
    )

    # ---- bin掃引の事前集約 ----
    def _sweep_agg():
        d = pd.DataFrame(sweep_rows)
        if d.empty:
            log("    [bin_sweep_agg] sweep_rows空 → スキップ")
            return
        d = d.merge(df_chan[["ch", "qc1_pass"]], on="ch", how="left")
        rows = []
        for sec, g in d.groupby("bin_sec"):
            gq = g[g["qc1_pass"] == 1]
            f1_all_mom = float(g.groupby("mouse_id")["f1_state"].mean().mean())
            f1_qc_mom = (
                float(gq.groupby("mouse_id")["f1_state"].mean().mean())
                if len(gq)
                else np.nan
            )
            rows.append(
                {
                    "bin_sec": sec,
                    "f1_all_mean": round(float(g["f1_state"].mean()), 4),
                    "f1_all_median": round(float(g["f1_state"].median()), 4),
                    "f1_qc_mean": round(float(gq["f1_state"].mean()), 4)
                    if len(gq)
                    else np.nan,
                    "f1_qc_median": round(float(gq["f1_state"].median()), 4)
                    if len(gq)
                    else np.nan,
                    "f1_all_mean_of_means": round(f1_all_mom, 4),
                    "f1_qc_mean_of_means": round(f1_qc_mom, 4)
                    if pd.notna(f1_qc_mom)
                    else np.nan,
                    "f1_all_median_of_medians": round(
                        float(g.groupby("mouse_id")["f1_state"].median().median()), 4
                    ),
                    "f1_qc_median_of_medians": round(
                        float(gq.groupby("mouse_id")["f1_state"].median().median()), 4
                    )
                    if len(gq)
                    else np.nan,
                    "intensity_r_median_of_medians": round(
                        float(g.groupby("mouse_id")["intensity_r"].median().median()), 4
                    ),
                    "intensity_r_mean_of_means": round(
                        float(g.groupby("mouse_id")["intensity_r"].mean().mean()), 4
                    ),
                    "n_ch_all": int(g["ch"].nunique()),
                    "n_ch_qc": int(gq["ch"].nunique()),
                }
            )
        dfa = pd.DataFrame(rows)
        save("int_bin_sweep_agg.csv", dfa)
        chk = dfa[dfa["bin_sec"] == 60]
        if len(chk):
            log(
                f"    [検算] 60s: F1_qc mean-of-means={chk.iloc[0]['f1_qc_mean_of_means']} "
                f"(表示規則と一致するはず)  flat={chk.iloc[0]['f1_qc_mean']}"
            )

    block("bin_sweep_agg", _sweep_agg)
    block(
        "state_hist", lambda: save("int_state_hist.csv", pd.DataFrame(state_hist_rows))
    )
    block("repr_24h", lambda: save("int_repr_24h.csv", pd.DataFrame(repr24_rows)))

    # ---- 生波形（RAW_WINDOW_S 窓・nanotag_count・raw_value_adc 付き）----
    def _raw_trace():
        if not raw_trace_rows:
            log(
                f"    [raw_trace] 空 → REPR_CH={getattr(config, 'REPR_CH', '')} が対象記録に含まれない"
                f"可能性。生データのパス/形式を確認（合成データ代替は行わない）。"
            )
            return
        d = pd.DataFrame(raw_trace_rows)
        save("int_raw_trace.csv", d)
        _keys = [k for k in ["ch", "variant", "phase"] if k in d.columns]
        log(
            f"    [raw_trace] 保存 {len(d)}行 / 窓={d['window_s'].iloc[0]}s / "
            f"ch={sorted(d['ch'].unique()) if 'ch' in d.columns else 'NA'} / "
            f"variant={sorted(d['variant'].unique()) if 'variant' in d.columns else 'NA'}"
        )
        for kv, g in d.groupby(_keys):
            _adc = (
                g["raw_value_adc"] if "raw_value_adc" in g.columns else g["raw_value"]
            )
            log(
                f"    [raw_trace] {kv}: n={len(g)} "
                f"PAI={float(g['bin_pai'].iloc[0]):.3f} raw_var={float(np.var(g['raw_value'])):.3e} "
                f"lpf_var={float(np.var(g['raw_value_lpf'])):.3e} "
                f"adc_min={float(_adc.min()):.6g} adc_max={float(_adc.max()):.6g} "
                f"adc_range={float(np.ptp(_adc.values)):.6g} "
                f"nano_bin={g['nanotag_count_bin'].iloc[0]}"
            )
        # Fig1候補として何が使えるかを一覧化（legacy stage2はこれをそのまま図にする）
        if {"ch", "variant"}.issubset(d.columns):
            _av = (
                d.groupby(["ch", "variant"])["phase"]
                .agg(lambda x: ",".join(sorted(set(x))))
                .reset_index()
                .rename(columns={"phase": "phases"})
            )
            save("int_raw_trace_index.csv", _av)
            for _, r in _av.iterrows():
                log(f"    [Fig1候補] {r['ch']} / {r['variant']}: phases={r['phases']}")

    block("raw_trace", _raw_trace)
    block(
        "repr_state_timeline",
        lambda: save("int_repr_state_timeline.csv", pd.DataFrame(repr_timeline_rows)),
    )

    # ---- QC解剖表 ----
    def _qc_anatomy():
        sub = df_chan[
            (df_chan["qc1_pass"] == 1) & (df_chan["F1_state"] < GOOD_F1)
        ].copy()
        if sub.empty:
            log("    [qc_anatomy] par-QCすり抜けch なし")
            save("int_qc_anatomy.csv", pd.DataFrame())
            return
        rows = []
        for _, r in sub.iterrows():
            par_minus_true = float(r["pir_active_rate"] - r["nanotag_active_rate"])
            _snr = r.get("snr", np.nan)
            _sep = r.get("gmm_separation", np.nan)
            _by = []
            if pd.notna(_snr) and _snr < QC1_MULTI_SNR_MIN:
                _by.append("snr>=1")
            if pd.notna(_sep) and _sep < QC1_MULTI_GMM_SEP_MIN:
                _by.append("sep>=1.0")
            captured = "+".join(_by) if _by else "uncatchable"
            rows.append(
                {
                    "ch": r["ch"],
                    "mouse_id": r["mouse_id"],
                    "F1_state": r["F1_state"],
                    "par": r["pir_active_rate"],
                    "nanotag_active_rate": r["nanotag_active_rate"],
                    "par_minus_true": round(par_minus_true, 4),
                    "gmm_separation": _sep,
                    "snr": _snr,
                    "bimodality_coef": r.get("bimodality_coef", np.nan),
                    "captured_by": captured,
                }
            )
        save("int_qc_anatomy.csv", pd.DataFrame(rows))
        for r in rows:
            log(
                f"    [qc_anatomy] {r['ch']} ({r['mouse_id']}): F1={r['F1_state']:.3f} "
                f"par={r['par']:.3f} true={r['nanotag_active_rate']:.3f} snr={r['snr']:.2f} "
                f"sep={r['gmm_separation']:.2f} captured_by={r['captured_by']}"
            )

    block("qc_anatomy", _qc_anatomy)

    # ---- 周波数帯ベンチ（state F1 + intensity r）----
    def _freqband_bench():
        # 帯域軸の主表示は log-band（logの効果を固定して帯域だけを比較）。
        #   生パワー版は「非logはGMMが退化する」ことの実証として metric=state_f1_rawband に残す。
        bandcols_f1_log = {
            "Low-Pass (<=1Hz, B0)": "F1_state_logband01",
            "Mid-Band (1-2Hz)": "F1_state_logband12",
            "Mid-Band (2-5Hz)": "F1_state_logband25",
            "High-Pass (>5Hz)": "F1_state_logband515",
        }
        bandcols_f1_raw = {
            "Low-Pass (<=1Hz, B0)": "F1_state_band01",
            "Mid-Band (1-2Hz)": "F1_state_band12",
            "Mid-Band (2-5Hz)": "F1_state_band25",
            "High-Pass (>5Hz)": "F1_state_band515",
        }
        # 強度rはSpearman（順位不変）なのでlog有無で完全同値。生bandの値をそのまま使ってよい。
        bandcols_r = {
            "Low-Pass (<=1Hz, B0)": "band_0_1Hz",
            "Mid-Band (1-2Hz)": "band_1_2Hz",
            "Mid-Band (2-5Hz)": "band_2_5Hz",
            "High-Pass (>5Hz)": "band_5_15Hz",
        }
        rows = []
        for _metric_name, _cols in [
            ("state_f1", bandcols_f1_log),
            ("state_f1_rawband", bandcols_f1_raw),
        ]:
            for band, col_f1 in _cols.items():
                if col_f1 not in df_chan.columns:
                    continue
                for _, r in (
                    df_chan[["ch", "mouse_id", col_f1]]
                    .dropna(subset=[col_f1])
                    .iterrows()
                ):
                    rows.append(
                        {
                            "ch": r["ch"],
                            "mouse_id": r["mouse_id"],
                            "band": band,
                            "metric": _metric_name,
                            "value": float(r[col_f1]),
                        }
                    )
        df_feat = pd.DataFrame(feature_rows)
        if len(df_feat):
            for band, feat_name in bandcols_r.items():
                sub = df_feat[df_feat["feature"] == feat_name]
                for _, r in sub.iterrows():
                    rows.append(
                        {
                            "ch": r["ch"],
                            "mouse_id": r["mouse_id"],
                            "band": band,
                            "metric": "intensity_r",
                            "value": float(r["r"]),
                        }
                    )
        dfb = pd.DataFrame(rows)
        save("int_freqband_bench.csv", dfb)
        if len(dfb):
            for _mt in ["state_f1", "state_f1_rawband", "intensity_r"]:
                _s = dfb[dfb["metric"] == _mt]
                if len(_s):
                    _med = _s.groupby("band")["value"].median()
                    _mean = _s.groupby("band")["value"].mean()
                    log(
                        f"    [freqband/{_mt}] median: "
                        + "; ".join(f"{k}={v:.4f}" for k, v in _med.items())
                    )
                    log(
                        f"    [freqband/{_mt}] mean  : "
                        + "; ".join(f"{k}={v:.4f}" for k, v in _mean.items())
                    )

    block("freqband_bench", _freqband_bench)

    def _gmm_params():
        need_cols = [
            "ch",
            "gmm_boundary",
            "gmm_rest_mu",
            "gmm_act_mu",
            "gmm_rest_sd",
            "gmm_act_sd",
            "gmm_rest_w",
            "gmm_act_w",
        ]
        if not set(need_cols).issubset(df_chan.columns):
            log("    [gmm_params] 必要列なし → スキップ")
            return
        has_nano = {"nano_rest_mu", "nano_act_mu"}.issubset(df_chan.columns)
        rows = []
        for _, r in df_chan.iterrows():
            rest_row = {
                "ch": r["ch"],
                "comp": "rest",
                "mean": r["gmm_rest_mu"],
                "sd": r["gmm_rest_sd"],
                "weight": r["gmm_rest_w"],
                "boundary": r["gmm_boundary"],
            }
            act_row = {
                "ch": r["ch"],
                "comp": "active",
                "mean": r["gmm_act_mu"],
                "sd": r["gmm_act_sd"],
                "weight": r["gmm_act_w"],
                "boundary": r["gmm_boundary"],
            }
            if has_nano:
                rest_row["nano_mu"] = r.get("nano_rest_mu", np.nan)
                rest_row["nano_mu_mean"] = r.get("nano_rest_mu_mean", np.nan)
                act_row["nano_mu"] = r.get("nano_act_mu", np.nan)
                act_row["nano_mu_mean"] = r.get("nano_act_mu_mean", np.nan)
            rows.append(rest_row)
            rows.append(act_row)
        save("int_gmm_params.csv", pd.DataFrame(rows))

    block("gmm_params", _gmm_params)

    def _state_feature_bench():
        colmap = {
            "var": "F1_state_var_nolpf",
            "lp_var": "F1_state_rawvar",
            "log_var": "F1_state_logvar_nolpf",
            "log_lp_var": "F1_state",
            "std": "F1_state_std",
            "range": "F1_state_range",
            "band_0_1Hz": "F1_state_band01",
            "band_1_5Hz": "F1_state_band15",
            "band_5_15Hz": "F1_state_band515",
            "high_pass": "F1_state_high_pass",
            "raw_amp": "F1_state_raw_amp",
            "bandpass_var": "F1_state_bandpass_var",
            "raw_lp_var": "F1_state_rawvar",
            "band_1_2Hz": "F1_state_band12",
            "band_2_5Hz": "F1_state_band25",
            "log_band_0_1Hz": "F1_state_logband01",
            "log_band_1_2Hz": "F1_state_logband12",
            "log_band_2_5Hz": "F1_state_logband25",
            "log_band_5_15Hz": "F1_state_logband515",
        }
        rows = []
        for feat, col in colmap.items():
            if col not in df_chan.columns:
                continue
            sub = df_chan[["ch", "mouse_id", col]].dropna(subset=[col])
            for _, r in sub.iterrows():
                rows.append(
                    {
                        "ch": r["ch"],
                        "mouse_id": r["mouse_id"],
                        "feature": feat,
                        "f1_state": float(r[col]),
                    }
                )
        dff = pd.DataFrame(rows)
        save("int_state_feature_bench.csv", dff)
        if len(dff):
            agg_med = dff.groupby("feature")["f1_state"].median().sort_values()
            agg_mean = dff.groupby("feature")["f1_state"].mean()
            log(
                "    [state feature] median昇順: "
                + "; ".join(f"{k}={v:.3f}" for k, v in agg_med.items())
            )
            log(
                "    [state feature] mean      : "
                + "; ".join(f"{k}={agg_mean[k]:.3f}" for k in agg_med.index)
            )

    block("state_feature_bench", _state_feature_bench)

    # ---- ★X2/X4/X8/X1 の保存 ----
    if perch_conf_rows:
        block(
            "X2_perch_confusion",
            lambda: save(
                "int_state_confusion_perch.csv", pd.DataFrame(perch_conf_rows)
            ),
        )
        _pc = pd.DataFrame(perch_conf_rows)
        _tot_fp, _tot_fn = int(_pc["FP"].sum()), int(_pc["FN"].sum())
        log(
            f"    [X2] pooled FP={_tot_fp} FN={_tot_fn}  "
            f"FP share={_tot_fp / max(_tot_fp + _tot_fn, 1):.4f} "
            f"FN share={_tot_fn / max(_tot_fp + _tot_fn, 1):.4f}"
        )
    if baseline_rows:

        def _bl():
            d = pd.DataFrame(baseline_rows)
            save("int_state_baseline.csv", d)
            agg = d.groupby("method")["f1_state"].agg(["median", "mean", "count"])
            for k, r in agg.iterrows():
                log(
                    f"    [X4 baseline] {k:<16} median={r['median']:.4f} "
                    f"mean={r['mean']:.4f} n_ch={int(r['count'])}"
                )

        block("X4_state_baseline", _bl)
    if darkdef_rows:

        def _dd():
            d = pd.DataFrame(darkdef_rows)
            save("int_darkdef_sensitivity.csv", d)
            agg = d.groupby("shift_h")["intensity_r"].median()
            log(
                "    [X8 darkdef] shift別 中央r: "
                + "; ".join(f"{int(k):+d}h={v:.4f}" for k, v in agg.items())
            )

        block("X8_darkdef", _dd)
    if lpf_sweep_rows:

        def _lpf():
            d = pd.DataFrame(lpf_sweep_rows)
            d = d.merge(df_chan[["ch", "qc1_pass"]], on="ch", how="left")
            save("int_lpf_sweep.csv", d)
            rows = []
            for cut, g in d.groupby("cutoff_hz"):
                gq = g[g["qc1_pass"] == 1]
                rows.append(
                    {
                        "cutoff_hz": cut,
                        "intensity_r_median_of_medians": round(
                            float(
                                g.groupby("mouse_id")["intensity_r"].median().median()
                            ),
                            4,
                        ),
                        "intensity_r_mean_of_means": round(
                            float(
                                g.groupby("mouse_id")["intensity_r"].mean().mean()
                            ),
                            4,
                        ),
                        "f1_all_mean_of_means": round(
                            float(g.groupby("mouse_id")["f1_state"].mean().mean()), 4
                        ),
                        "f1_qc_mean_of_means": round(
                            float(gq.groupby("mouse_id")["f1_state"].mean().mean()), 4
                        )
                        if len(gq)
                        else np.nan,
                        "n_ch": int(g["ch"].nunique()),
                    }
                )
            dfa = pd.DataFrame(rows)
            save("int_lpf_sweep_agg.csv", dfa)
            for _, r in dfa.iterrows():
                log(
                    f"    [X1 LPF] {r['cutoff_hz']}Hz: r={r['intensity_r_median_of_medians']} "
                    f"F1_all={r['f1_all_mean_of_means']} F1_qc={r['f1_qc_mean_of_means']}"
                )

        block("X1_lpf_sweep", _lpf)
    elif os.path.exists(_lpf_path):
        # Raw LPF-sweep CSV exists but the heavy per-cutoff compute did not run this session
        # (RUN_LPF_SWEEP off, or cached). Rebuild the AGGREGATE from the raw CSV regardless of
        # any flag, so newly-added columns (intensity_r_mean_of_means) appear. Cheap; the frozen
        # per-channel metrics are untouched.
        def _lpf_agg_refresh():
            # FIX: there is no load() helper in this module; read the CSV directly.
            _p = os.path.join(config.INTERMEDIATE_DIR, "int_lpf_sweep.csv")
            if not os.path.exists(_p):
                log("[X1] int_lpf_sweep.csv が無いため再集計をスキップ")
                return
            d = pd.read_csv(_p, encoding="utf-8-sig")
            if d is None or d.empty:
                return
            if "qc1_pass" not in d.columns:
                d = d.merge(df_chan[["ch", "qc1_pass"]], on="ch", how="left")
            rows = []
            for cut, g in d.groupby("cutoff_hz"):
                gq = g[g["qc1_pass"] == 1]
                rows.append({
                    "cutoff_hz": cut,
                    "intensity_r_median_of_medians": round(float(g.groupby("mouse_id")["intensity_r"].median().median()), 4),
                    "intensity_r_mean_of_means": round(float(g.groupby("mouse_id")["intensity_r"].mean().mean()), 4),
                    "f1_all_mean_of_means": round(float(g.groupby("mouse_id")["f1_state"].mean().mean()), 4),
                    "f1_qc_mean_of_means": round(float(gq.groupby("mouse_id")["f1_state"].mean().mean()), 4) if len(gq) else np.nan,
                    "n_ch": int(g["ch"].nunique()),
                })
            save("int_lpf_sweep_agg.csv", pd.DataFrame(rows))
            log("[X1] int_lpf_sweep_agg.csv を既存生CSVから再集計（新列 intensity_r_mean_of_means を反映）")
        block("X1_lpf_agg_refresh", _lpf_agg_refresh)

    # ---- ブートストラップCI ----
    # ！！重要！！ rngは1本を使い回すため、新規指標は必ず既存5件の「後ろ」に追加すること。
    def _boot():
        rng = np.random.default_rng(2024)
        pm_r = df_chan.groupby("mouse_id")["intensity_r"].median().dropna().values
        pm_f1_all = df_chan.groupby("mouse_id")["F1_state"].mean().dropna().values
        _q = df_chan[df_chan["qc1_pass"] == 1]
        pm_f1_qc = _q.groupby("mouse_id")["F1_state"].mean().dropna().values
        pm_f1_all_mom = df_chan.groupby("mouse_id")["F1_state"].median().dropna().values
        pm_f1_qc_mom = _q.groupby("mouse_id")["F1_state"].median().dropna().values
        _qm = df_chan[df_chan["qc1_pass_multi"] == 1]
        pm_f1_qcmulti = _qm.groupby("mouse_id")["F1_state"].mean().dropna().values
        pm_r_qc = _q.groupby("mouse_id")["intensity_r"].median().dropna().values
        # M3: mean-of-means variants of intensity_r (defined AFTER the existing arrays;
        #     added to the very END of the metric list so the shared rng stream for the
        #     existing metrics is untouched and their CIs stay bit-identical).
        pm_r_mean = df_chan.groupby("mouse_id")["intensity_r"].mean().dropna().values
        pm_r_mean_qc = _q.groupby("mouse_id")["intensity_r"].mean().dropna().values
        rows = []
        for name, arr, agg in [
            # ---- 既存5件（順序厳守・変更禁止）----
            ("intensity_r_median", pm_r, np.median),
            ("F1_all_mean", pm_f1_all, np.mean),
            ("F1_qc1_mean", pm_f1_qc, np.mean),
            ("F1_all_median_of_medians", pm_f1_all_mom, np.median),
            ("F1_qc1_median_of_medians", pm_f1_qc_mom, np.median),
            # ---- ここから新規（必ず末尾に追加）----
            ("F1_qc1multi_mean", pm_f1_qcmulti, np.mean),
            ("intensity_r_median_qc1", pm_r_qc, np.median),
            # ---- M3 追加（必ずこの位置=末尾）----
            ("intensity_r_mean_of_means", pm_r_mean, np.mean),
            ("intensity_r_mean_of_means_qc1", pm_r_mean_qc, np.mean),
        ]:
            if len(arr) < 2:
                continue
            boots = [
                float(agg(rng.choice(arr, size=len(arr), replace=True)))
                for _ in range(10000)
            ]
            rows.append(
                {
                    "metric": name,
                    "n_individuals": len(arr),
                    "point": float(agg(arr)),
                    "ci_lower": float(np.percentile(boots, 2.5)),
                    "ci_upper": float(np.percentile(boots, 97.5)),
                    "n_boot": 10000,
                }
            )
        save("int_bootstrap_ci.csv", pd.DataFrame(rows))

    block("bootstrap_ci", _boot)

    # ---- ★X3: AUC差(par vs SNR)のブートストラップ（個体クラスタ復元抽出）----
    def _auc_boot():
        v = df_chan.dropna(subset=["pir_active_rate", "snr", "F1_state"]).copy()
        mice = sorted(v["mouse_id"].unique())
        rng = np.random.default_rng(int(getattr(config, "AUC_BOOT_SEED", 7)))
        nb = int(getattr(config, "AUC_BOOT_N", 5000))
        diffs, a_par, a_snr = [], [], []
        for _ in range(nb):
            pick = rng.choice(mice, size=len(mice), replace=True)
            sub = pd.concat([v[v["mouse_id"] == m] for m in pick], ignore_index=True)
            lbl = (sub["F1_state"] >= GOOD_F1).astype(int)
            if lbl.nunique() < 2:
                continue
            try:
                ap = float(roc_auc_score(lbl, sub["pir_active_rate"]))
                asr = float(roc_auc_score(lbl, sub["snr"]))
            except Exception:
                continue
            a_par.append(ap)
            a_snr.append(asr)
            diffs.append(ap - asr)
        if not diffs:
            log("    [X3 auc_boot] 有効なブートストラップ標本なし")
            return
        diffs = np.asarray(diffs)
        lbl0 = (v["F1_state"] >= GOOD_F1).astype(int)
        obs_par = float(roc_auc_score(lbl0, v["pir_active_rate"]))
        obs_snr = float(roc_auc_score(lbl0, v["snr"]))
        out = pd.DataFrame(
            [
                {
                    "comparison": "pir_active_rate - snr",
                    "auc_par_observed": round(obs_par, 4),
                    "auc_snr_observed": round(obs_snr, 4),
                    "diff_observed": round(obs_par - obs_snr, 4),
                    "diff_boot_median": round(float(np.median(diffs)), 4),
                    "diff_ci_lower": round(float(np.percentile(diffs, 2.5)), 4),
                    "diff_ci_upper": round(float(np.percentile(diffs, 97.5)), 4),
                    "p_two_sided_boot": round(
                        float(2 * min((diffs <= 0).mean(), (diffs >= 0).mean())), 5
                    ),
                    "n_boot_valid": len(diffs),
                    "n_mouse": len(mice),
                    "cluster_unit": "mouse",
                }
            ]
        )
        save("int_auc_boot.csv", out)
        save(
            "int_auc_boot_draws.csv",
            pd.DataFrame({"auc_par": a_par, "auc_snr": a_snr, "diff": diffs}),
        )
        r0 = out.iloc[0]
        log(
            f"    [X3 auc_boot] diff={r0['diff_observed']} "
            f"95%CI[{r0['diff_ci_lower']}, {r0['diff_ci_upper']}] "
            f"p={r0['p_two_sided_boot']} (n_boot={r0['n_boot_valid']}, cluster=mouse)"
        )

    if RUN_EXPL:
        block("X3_auc_boot", _auc_boot)

    # ---- センサー交換 / テスト再テスト（新方式 sensor_id + 旧方式署名の両方）----
    def _swap():
        def _build(setcol, tag):
            rows = []
            for mid, g in df_chan.groupby("mouse_id"):
                sets_avail = [
                    s for s in SENSOR_SET_ORDER if s in set(g[setcol].dropna())
                ]
                if len(sets_avail) < 2:
                    sets_avail = sorted(g[setcol].dropna().unique())[:2]
                rec = {"mouse_id": mid, "n_sets": int(g[setcol].nunique())}
                for i, s in enumerate(sets_avail[:2], start=1):
                    gs = g[g[setcol] == s]
                    rec[f"set{i}_sig"] = s
                    rec[f"set{i}_n_ch"] = len(gs)
                    rec[f"set{i}_r"] = float(gs["intensity_r"].median())
                    rec[f"set{i}_f1"] = float(gs["F1_state"].mean())
                if len(sets_avail) >= 2 and "set2_r" in rec:
                    rec["abs_diff_r"] = round(abs(rec["set1_r"] - rec["set2_r"]), 4)
                    rec["abs_diff_f1"] = round(abs(rec["set1_f1"] - rec["set2_f1"]), 4)
                rows.append(rec)
            d = pd.DataFrame(rows)
            if "abs_diff_r" in d.columns:
                log(
                    f"    [retest/{tag}] median |delta r| = {d['abs_diff_r'].median():.4f} "
                    f"(n_mouse={d['abs_diff_r'].notna().sum()})"
                )
            return d

        df_sw_ind = _build("sensor_set", "sensor_id方式(採用)")
        save("int_sensor_swap.csv", df_sw_ind)
        try:
            df_sw_sig = _build("sensor_set_sig", "署名方式(照合用)")
            save("int_sensor_swap_bysig.csv", df_sw_sig)
        except Exception as _e:
            log(f"    [retest/署名方式] スキップ {_e}")

        # セット別 主結果（SENSOR_SET_ORDER の順で SetA/SetB を固定）
        setrows = []
        _order = [
            s for s in SENSOR_SET_ORDER if s in set(df_chan["sensor_set"].dropna())
        ]
        _order += [
            s
            for s in sorted(df_chan["sensor_set"].dropna().unique())
            if s not in _order
        ]
        for i, s in enumerate(_order):
            sub = df_chan[df_chan["sensor_set"] == s]
            pm = sub.groupby("mouse_id")["intensity_r"].median()
            pf = sub.groupby("mouse_id")["F1_state"].mean()
            setrows.append(
                {
                    "set_label": ["SetA", "SetB"][i] if i < 2 else f"Set{i + 1}",
                    "sensor_set": s,
                    "sensor_ids": ",".join(
                        sorted(sub["sensor_id"].astype(str).unique())
                    ),
                    "sensor_set_sig": ",".join(
                        sorted(sub["sensor_set_sig"].astype(str).unique())
                    ),
                    "n_mouse": int(pm.size),
                    "n_ch": len(sub),
                    "median_r": round(float(pm.median()), 4),
                    "mean_f1": round(float(pf.mean()), 4),
                }
            )
        df_setrows = pd.DataFrame(setrows)
        save("int_sensor_swap_byset.csv", df_setrows)

        try:
            retest_rows = []
            for metric_pair, label, diff_col in [
                (("set1_r", "set2_r"), "intensity_r", "abs_diff_r"),
                (("set1_f1", "set2_f1"), "F1_state", "abs_diff_f1"),
            ]:
                c1, c2 = metric_pair
                if not {c1, c2}.issubset(df_sw_ind.columns):
                    continue
                valid = df_sw_ind.dropna(subset=[c1, c2])
                if len(valid) < 3:
                    continue
                sp_r = float(spearmanr(valid[c1], valid[c2])[0])
                pear_r = float(np.corrcoef(valid[c1], valid[c2])[0, 1])
                icc = _icc21(valid[c1].values, valid[c2].values)
                abs_diff_median = (
                    float(df_sw_ind[diff_col].median())
                    if diff_col in df_sw_ind.columns
                    else np.nan
                )
                abs_diff_mean = (
                    float(df_sw_ind[diff_col].mean())
                    if diff_col in df_sw_ind.columns
                    else np.nan
                )
                row = {
                    "metric": label,
                    "spearman": round(sp_r, 4),
                    "spearman_note": "reference only (range-restricted)",
                    "pearson": round(pear_r, 4),
                    "icc2_1": round(icc, 4) if pd.notna(icc) else np.nan,
                    "icc_note": "reference only (range-restricted; NOT for display)",
                    "abs_diff_median": round(abs_diff_median, 4) if pd.notna(abs_diff_median) else np.nan,
                    "abs_diff_mean": round(abs_diff_mean, 4) if pd.notna(abs_diff_mean) else np.nan,
                    "n_mouse": len(valid),
                }
                if label == "intensity_r" and len(df_setrows) >= 2:
                    row["setA_label"] = df_setrows.iloc[0]["sensor_set"]
                    row["setA_r"] = float(df_setrows.iloc[0]["median_r"])
                    row["setB_label"] = df_setrows.iloc[1]["sensor_set"]
                    row["setB_r"] = float(df_setrows.iloc[1]["median_r"])
                retest_rows.append(row)
            save("int_sensor_retest.csv", pd.DataFrame(retest_rows))
        except Exception as _e:
            log(f"    [sensor_retest] スキップ {_e}")

    block("sensor_swap", _swap)

    save(
        "int_cost.csv",
        pd.DataFrame(
            [
                {"item": "DAQ_Hardware", "labview_cost": 350000, "arduino_cost": 4500},
                {"item": "Software_License", "labview_cost": 450000, "arduino_cost": 0},
                {
                    "item": "Sensor_Interface",
                    "labview_cost": 120000,
                    "arduino_cost": 3500,
                },
                {"item": "Total", "labview_cost": 920000, "arduino_cost": 8000},
            ]
        ),
    )
    log("補足CSV 全保存完了 → 検算ゲートへ")

    # ---------- 検算ゲート ----------
    qc1 = df_chan[df_chan["qc1_pass"] == 1]
    qcm = df_chan[df_chan["qc1_pass_multi"] == 1]
    pm = df_chan.groupby("mouse_id")["intensity_r"].median()
    print("=" * 66, flush=True)
    print("【検算ゲート（全て実計算値）】", flush=True)
    print(f" fs                     : {measured_fs:.1f} Hz", flush=True)
    print(
        f" 有効ch                 : {len(df_chan)} ch / {df_chan['mouse_id'].nunique()}頭 "
        f"(全てYoung)",
        flush=True,
    )
    print(
        f" QC1通過(par単独)        : {len(qc1)} ch / {qc1['mouse_id'].nunique()}頭",
        flush=True,
    )
    print(
        f" 多条件QC(par+snr+sep)   : {len(qcm)} ch / {qcm['mouse_id'].nunique()}頭",
        flush=True,
    )
    print(
        f" good定義 / QC1閾値(LOMO): F1>={GOOD_F1} / {qc1_thr:.4f}",
        flush=True,
    )
    if "qc1_threshold" in df_loso_thr.columns and len(df_loso_thr) > 1:
        print(
            f" LOMO閾値 fold間SD       : {df_loso_thr['qc1_threshold'].std():.4f}  "
            f"(n_fold={len(df_loso_thr)})",
            flush=True,
        )
    print(
        f" 主結果 r(個体中央値)     : {pm.median():.4f}  IQR={pm.quantile(0.75) - pm.quantile(0.25):.4f}",
        flush=True,
    )
    print(
        f" 状態F1                 : 全 {df_chan.groupby('mouse_id')['F1_state'].mean().mean():.4f} "
        f"→ QC1通過 {qc1.groupby('mouse_id')['F1_state'].mean().mean():.4f}  (全24h・60s)",
        flush=True,
    )
    print(
        f" NanoTag Active割合(平均): {df_chan['nanotag_active_rate'].mean():.3f}",
        flush=True,
    )
    print(
        f" プラセボ r 中央値        : {df_chan.groupby('mouse_id')['placebo_r'].median().median():.4f}",
        flush=True,
    )
    print(
        f" 位相シャッフル 中央      : {df_chan.groupby('mouse_id')['phase_shuffle_r'].median().median():.4f}",
        flush=True,
    )
    try:
        qc = pd.read_csv(os.path.join(config.INTERMEDIATE_DIR, "int_qc_corr.csv"))
        for _, r in qc[np.isclose(qc["f1_thr"], GOOD_F1)].iterrows():
            print(
                f" QC-AUC {r['qc_metric']:<16}(F1>={GOOD_F1}): {r['auc']}", flush=True
            )
    except Exception:
        pass
    try:
        sw = pd.read_csv(
            os.path.join(config.INTERMEDIATE_DIR, "int_sensor_swap_byset.csv")
        )
        for _, r in sw.iterrows():
            print(
                f" センサーセット {r['set_label']:<5}    : r={r['median_r']} (F1 {r['mean_f1']}, "
                f"{int(r['n_mouse'])}頭, {int(r['n_ch'])}ch) sensor_ids={r['sensor_ids']} "
                f"sig={r['sensor_set_sig']}",
                flush=True,
            )
    except Exception:
        pass
    try:
        rt = pd.read_csv(os.path.join(config.INTERMEDIATE_DIR, "int_sensor_retest.csv"))
        for _, r in rt.iterrows():
            print(
                f" retest {r['metric']:<12}    : median|delta|={r['abs_diff_median']} "
                f"(ICC={r['icc2_1']} / Spearman={r['spearman']} は参考値・非表示)",
                flush=True,
            )
    except Exception:
        pass
    try:
        sc = pd.read_csv(
            os.path.join(config.INTERMEDIATE_DIR, "int_sensor_consistency_permouse.csv")
        )
        print(
            f" 個体別 inter-sensor r   : {sc['median_inter_sensor_r'].median():.4f} "
            f"(n_mouse={len(sc)})",
            flush=True,
        )
    except Exception:
        pass
    try:
        ci = pd.read_csv(os.path.join(config.INTERMEDIATE_DIR, "int_bootstrap_ci.csv"))
        for _, r in ci.iterrows():
            print(
                f" 95%CI {r['metric']:<26}: {r['point']:.4f} [{r['ci_lower']:.4f}, {r['ci_upper']:.4f}]",
                flush=True,
            )
    except Exception:
        pass
    try:
        cf = pd.read_csv(os.path.join(config.INTERMEDIATE_DIR, "int_qc_confusion.csv"))
        for _rk in ["par_only", "par_snr", "par_sep", "par_snr_sep"]:
            s = cf[(np.isclose(cf["good_cut"], GOOD_F1)) & (cf["rule"] == _rk)]
            if len(s):
                r0 = s.iloc[0]
                print(
                    f" 混同 {_rk:<12}(good={GOOD_F1}): TP={int(r0['TP'])} FP={int(r0['FP'])} "
                    f"FN={int(r0['FN'])} TN={int(r0['TN'])} PPV={r0['PPV']} sens={r0['sensitivity']} "
                    f"pass={int(r0['n_pass'])}ch/{int(r0['n_pass_mice'])}頭",
                    flush=True,
                )
    except Exception:
        pass
    # ★V6-1: Fig1が読む生ADCの素性を検算ゲートにも出す
    try:
        ad = pd.read_csv(
            os.path.join(config.INTERMEDIATE_DIR, "int_adc_diagnostic.csv")
        )
        print(
            f" 生ADC診断              : {int(ad['looks_like_0p01_adc'].sum())}/{len(ad)} ch が"
            f"整数ADC(step=1)として整合  range中央={ad['range'].median():.6g}",
            flush=True,
        )
        if int(ad["looks_like_0p01_adc"].sum()) < len(ad):
            print(
                "   !! 一部chが整数ADCでない → int_adc_diagnostic.csv と mapping.csv の pir_col を確認",
                flush=True,
            )
    except Exception:
        pass
    print("=" * 66, flush=True)
    print(
        f"中間CSV保存完了（RUN_SUPP={RUN_SUPP} / RUN_EXPL={RUN_EXPL} / X1_LPF={DO_LPF_SWEEP}）。",
        flush=True,
    )
    log("main() 正常終了")



# ============================================================================
# v2 versioned post-processing / audit layer
# ============================================================================
_VERSION_DEPENDENT_CHANNEL_COLS = {
    "good_cut", "qc1_pass", "qc1_pass_snrguard", "qc1_pass_sepguard", "qc1_pass_multi",
    "f1_upper_bound", "par_needed_for_good", "par_upper_for_good", "clears_algebraic_bound",
}


def _read_csv(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path, encoding="utf-8")


# v3: central intermediate-writer registry.  Keys are absolute CSV paths so good070/good080
# stay independent even when the same filename is written in both version folders.
_CSV_GENERATOR_REGISTRY = {}
_CSV_WRITE_EVENTS = {}


def _csv_caller_name():
    """Return the first meaningful writer above _write_csv in the call stack."""
    skip = {"_write_csv", "save", "block", "<lambda>"}
    for fr in inspect.stack()[1:]:
        name = str(fr.function)
        if name not in skip:
            return name
    return "[unknown-writer]"



def _write_csv(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    ap = os.path.abspath(path)
    caller = _csv_caller_name()
    _CSV_WRITE_EVENTS.setdefault(ap, []).append(caller)
    # _tag_all_csvs only appends the version tag; it is not the content generator.
    if caller != "_tag_all_csvs":
        _CSV_GENERATOR_REGISTRY[ap] = caller


def _csv_generator_label(path):
    ap = os.path.abspath(path)
    if ap in _CSV_GENERATOR_REGISTRY:
        return _CSV_GENERATOR_REGISTRY[ap]
    if os.path.exists(ap):
        return "[PRE-EXISTING]"
    return "[ORPHAN]"


def _referenced_intermediate_csvs():
    """Find literal int_*.csv references in this pipeline's Python source files."""
    refs = set()
    roots = [os.path.abspath(__file__), os.path.join(os.path.dirname(os.path.abspath(__file__)), "legacy stage2_figures.py")]
    pat = re.compile(r"\bint_[A-Za-z0-9_]+\.csv\b")
    for src in roots:
        if not os.path.exists(src):
            continue
        try:
            txt = open(src, "r", encoding="utf-8").read()
        except Exception:
            continue
        refs.update(pat.findall(txt))
    # These names are explicitly quarantined legacy artifacts, not live pipeline references.
    refs -= {"int_shuffle_null.csv", "int_channel_before.csv", "int_sep_upper_lomo.csv", "int_floor_bin_labels.csv", "int_agecompare.csv"}
    return refs


def _payload_hash_channel(df):
    cols = [c for c in df.columns if c not in _VERSION_DEPENDENT_CHANNEL_COLS]
    z = df[cols].copy().sort_values("ch").reset_index(drop=True)
    payload = z.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _raw_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def _derive_lomo_threshold(df, good_cut):
    rows = []
    v = df.dropna(subset=["pir_active_rate", "F1_state"]).copy()
    for exc in sorted(v["mouse_id"].astype(str).unique()):
        tr = v[v["mouse_id"].astype(str) != str(exc)]
        yy = (tr["F1_state"].astype(float) >= good_cut).astype(int)
        if yy.nunique() < 2:
            continue
        fpr, tpr, thr = roc_curve(yy, tr["pir_active_rate"].astype(float))
        thr = np.where(np.isinf(thr), np.nan, thr)
        if np.all(~np.isfinite(thr)):
            continue
        j = np.nanargmax(tpr - fpr)
        tv = float(thr[j])
        mch = tr.loc[np.isclose(tr["pir_active_rate"].astype(float), tv, rtol=0, atol=1e-12), "ch"].astype(str).tolist()
        rows.append({"fold_excluded_mouse": exc, "qc1_threshold": tv,
                     "threshold_source_ch": ";".join(mch) if mch else "[no exact par match]",
                     "sensitivity": float(tpr[j]), "specificity": float(1-fpr[j])})
    d = pd.DataFrame(rows)
    if len(d):
        return d, float(d["qc1_threshold"].mean()), "lomo", int(len(d))
    vv = v.copy(); yy = (vv["F1_state"].astype(float) >= good_cut).astype(int)
    if yy.nunique() >= 2:
        fpr,tpr,thr=roc_curve(yy,vv["pir_active_rate"].astype(float)); thr=np.where(np.isinf(thr),np.nan,thr)
        j=np.nanargmax(tpr-fpr); return d,float(thr[j]),"full_roc_fallback",0
    return d,np.nan,"none",0


def _cluster_auc_draws(df, metric, good_cut, n_boot, seed):
    v=df.dropna(subset=[metric,"F1_state","mouse_id"]).copy(); mice=sorted(v["mouse_id"].astype(str).unique())
    y0=(v["F1_state"].astype(float)>=good_cut).astype(int)
    obs=float(roc_auc_score(y0,v[metric].astype(float))) if y0.nunique()>1 else np.nan
    rng=np.random.default_rng(seed); draws=[]
    for _ in range(int(n_boot)):
        pick=rng.choice(mice,size=len(mice),replace=True)
        parts=[]
        for j,m in enumerate(pick):
            q=v[v["mouse_id"].astype(str)==str(m)].copy(); q["_cluster_copy"]=j; parts.append(q)
        sub=pd.concat(parts,ignore_index=True); yy=(sub["F1_state"].astype(float)>=good_cut).astype(int)
        if yy.nunique()<2: continue
        try: draws.append(float(roc_auc_score(yy,sub[metric].astype(float))))
        except Exception: pass
    return obs,np.asarray(draws,float),len(mice)


def _bca_or_percentile(arr, stat, metric, mean_type=True):
    arr=np.asarray(arr,float); arr=arr[np.isfinite(arr)]
    if len(arr)<2: return None
    fallback=False; method="BCa" if mean_type else "percentile"
    try:
        if mean_type:
            res=bootstrap((arr,),lambda x: float(stat(x)),vectorized=False,
                          n_resamples=int(getattr(config,"BCa_N_RESAMPLES",10000)),
                          method="BCa",confidence_level=0.95,
                          random_state=int(getattr(config,"BCa_RANDOM_STATE",2024)))
            lo,hi=float(res.confidence_interval.low),float(res.confidence_interval.high)
            if not (np.isfinite(lo) and np.isfinite(hi)): raise ValueError("nonfinite BCa")
        else:
            rng=np.random.default_rng(int(getattr(config,"BCa_RANDOM_STATE",2024)))
            b=[float(stat(rng.choice(arr,size=len(arr),replace=True))) for _ in range(int(getattr(config,"BCa_N_RESAMPLES",10000)))]
            lo,hi=np.percentile(b,[2.5,97.5]); fallback=True
    except Exception:
        rng=np.random.default_rng(int(getattr(config,"BCa_RANDOM_STATE",2024)))
        b=[float(stat(rng.choice(arr,size=len(arr),replace=True))) for _ in range(int(getattr(config,"BCa_N_RESAMPLES",10000)))]
        lo,hi=np.percentile(b,[2.5,97.5]); method="percentile_fallback"; fallback=True
    return {"metric":metric,"n_individuals":len(arr),"point":float(stat(arr)),"ci_lower":float(lo),"ci_upper":float(hi),
            "ci_method":method,"resample_unit":"mouse","n_boot_requested":int(getattr(config,"BCa_N_RESAMPLES",10000)),
            "n_boot_valid":int(getattr(config,"BCa_N_RESAMPLES",10000)),"fallback_flag":int(fallback)}


def _make_common_diagnostics(outdir, good_cut, thr):
    chp=os.path.join(outdir,"int_channel.csv"); df=_read_csv(chp)
    _cfp=os.path.join(outdir,"int_state_confusion_perch.csv")
    if os.path.exists(_cfp):
        _cf=_read_csv(_cfp)
        if "mcc" in _cf.columns and "mcc" not in df.columns:
            df=df.merge(_cf[["ch","mcc"]],on="ch",how="left")
    # channel columns dependent on the version
    c=float(good_cut); par=df["pir_active_rate"].astype(float); nar=df["nanotag_active_rate"].astype(float)
    df["good_cut"]=c; df["f1_upper_bound"]=2*np.minimum(par,nar)/(par+nar).replace(0,np.nan)
    df["par_needed_for_good"]=(c/(2-c))*nar; df["par_upper_for_good"]=((2-c)/c)*nar
    df["clears_algebraic_bound"]=((par>=df["par_needed_for_good"])&(par<=df["par_upper_for_good"])).astype(int)
    df["qc1_pass"]=(par>=thr).astype(int) if np.isfinite(thr) else 0
    df["qc1_pass_snrguard"]=(df["qc1_pass"].eq(1)&(df["snr"]>=float(config.QC1_MULTI_SNR_MIN))).astype(int)
    df["qc1_pass_sepguard"]=(df["qc1_pass"].eq(1)&(df["gmm_separation"]>=float(config.QC1_MULTI_GMM_SEP_MIN))).astype(int)
    df["qc1_pass_multi"]=(df["qc1_pass"].eq(1)&(df["snr"]>=float(config.QC1_MULTI_SNR_MIN))&(df["gmm_separation"]>=float(config.QC1_MULTI_GMM_SEP_MIN))).astype(int)
    _write_csv(df,chp)

    # state baseline: preserve the threshold comparator under an explicit name, add operational argmax.
    bp=os.path.join(outdir,"int_state_baseline.csv")
    if os.path.exists(bp):
        b=_read_csv(bp); b.loc[b["method"].astype(str).eq("gmm"),"method"]="gmm_boundary_threshold"
        if "threshold_note" not in b.columns:
            b["threshold_note"]=""
        g=df[["ch","mouse_id","F1_state","nanotag_active_rate"]].copy(); g["method"]="gmm_argmax"; g["threshold"]=np.nan; g["f1_state"]=g["F1_state"]
        g["threshold_note"]="posterior argmax; no scalar threshold"
        g["degenerate_flag"]=0
        b["degenerate_flag"]=0
        m=b["method"].astype(str).eq("gmm_boundary_threshold")
        bm=b[m].merge(df[["ch","nanotag_active_rate"]],on="ch",how="left",suffixes=("","_ch"))
        target=2*bm["nanotag_active_rate"]/(1+bm["nanotag_active_rate"])
        b.loc[m,"degenerate_flag"]=(np.abs(bm["f1_state"].to_numpy(float)-target.to_numpy(float))<0.02).astype(int)
        add=g[["ch","mouse_id","method","threshold","threshold_note","f1_state","degenerate_flag"]]
        b=pd.concat([b[b["method"]!="gmm_argmax"],add],ignore_index=True); b["good_cut"]=c; _write_csv(b,bp)

    # LOSO r writer (previously orphan read in legacy stage2)
    lr=[]
    pm=df.groupby("mouse_id")["intensity_r"].mean()
    for exc in pm.index:
        lr.append({"mouse_id":exc,"fold_excluded_mouse":exc,"r_test":float(pm.drop(index=exc).mean()),"aggregation":"mean_of_mouse_means","good_cut":c})
    _write_csv(pd.DataFrame(lr),os.path.join(outdir,"int_loso_r.csv"))

    # hold-out F1: apply each fold's threshold to the excluded mouse, generated rather than inherited.
    lt=_read_csv(os.path.join(outdir,"int_loso_thr.csv")) if os.path.exists(os.path.join(outdir,"int_loso_thr.csv")) else pd.DataFrame()
    hr=[]
    for _,r in lt.iterrows():
        ex=str(r["fold_excluded_mouse"]); tv=float(r["qc1_threshold"]); test=df[df["mouse_id"].astype(str)==ex]; pas=test[test["pir_active_rate"]>=tv]
        hr.append({"fold_excluded_mouse":ex,"threshold":tv,"threshold_source_ch":r.get("threshold_source_ch",""),"n_pass_ch":len(pas),
                   "holdout_f1":float(pas["F1_state"].mean()) if len(pas) else np.nan,"good_cut":c})
    _write_csv(pd.DataFrame(hr),os.path.join(outdir,"int_holdout_f1.csv"))

    # filter compare: fill reference r from channel
    fp=os.path.join(outdir,"int_filter_mode_compare.csv")
    if os.path.exists(fp):
        f=_read_csv(fp); mp=df.set_index("ch")["intensity_r"]; f["r_perbin"]=f["ch"].map(mp); f["r_diff"]=f["r_continuous"]-f["r_perbin"]; f["good_cut"]=c; _write_csv(f,fp)

    # label sweep aggregate, QC recalculated per definition. par is copied and must remain invariant.
    lcp=os.path.join(outdir,"int_label_sweep_channel.csv")
    if os.path.exists(lcp):
        lc=_read_csv(lcp); rows=[]
        for nb,g in lc.groupby("nb_threshold"):
            y=(g["F1_state"]>=c).astype(int)
            auc=float(roc_auc_score(y,g["par"])) if y.nunique()>1 else np.nan
            if y.nunique()>1:
                fpr,tpr,tt=roc_curve(y,g["par"]); tt=np.where(np.isinf(tt),np.nan,tt); j=np.nanargmax(tpr-fpr); qt=float(tt[j])
            else: qt=np.nan
            pred=(g["par"]>=qt).astype(int) if np.isfinite(qt) else pd.Series(np.zeros(len(g),int),index=g.index)
            tp,fp0,fn,tn=_confusion_counts(pred,y)
            narg=g.groupby("mouse_id")["nar"].mean(); f1g=g.groupby("mouse_id")["F1_state"].mean()
            rows.append({"nb_threshold":int(nb),"nar_mean_of_mouse_means":float(narg.mean()),"F1_mean_of_mouse_means":float(f1g.mean()),"par_mean":float(g["par"].mean()),
                         "qc_threshold":qt,"sweep_threshold":qt,"sweep_threshold_source":"within_label_sweep_roc_youden",
                         "main_operational_threshold":float(thr) if np.isfinite(thr) else np.nan,
                         "main_threshold_definition":"mean of valid leave-one-mouse-out fold thresholds",
                         "threshold_difference":(float(qt-thr) if np.isfinite(qt) and np.isfinite(thr) else np.nan),
                         "par_auc":auc,"TP":tp,"FP":fp0,"FN":fn,"TN":tn,
                         "algebraic_lower_mean":float(((c/(2-c))*g["nar"]).mean()),"algebraic_upper_mean":float((((2-c)/c)*g["nar"]).mean()),"good_cut":c})
        _write_csv(pd.DataFrame(rows),os.path.join(outdir,"int_label_sweep.csv"))

    # GMM outer-crossing diagnostics and per-channel standardized error-distance table.
    hp=os.path.join(outdir,"int_state_hist.csv")
    if os.path.exists(hp):
        sh=_read_csv(hp); gp=[]; ep=[]
        for _,r in df.iterrows():
            d=sh[sh["ch"].astype(str)==str(r["ch"])]
            gm=fit_gmm(d["log_lp_var"].to_numpy(float)) if len(d) else None
            affected=frac=np.nan
            if gm is not None and gm.get("outer_crossing_flag",0):
                z=d["log_lp_var"].to_numpy(float); ass=(gm["g"].predict(z.reshape(-1,1))==gm["rest"])
                aff=ass & (z>=gm["outer_crossing"]) & (z<gm["rest_mu"]); affected=int(aff.sum()); frac=float(affected/max(int(ass.sum()),1))
            # FIX: the channel table stores the active component as gmm_act_* (not gmm_active_*).
            # The emitted "comp" label stays "active" so it matches _gmm_params() and legacy stage2.
            for comp, _cp in (("rest", "rest"), ("active", "act")):
                gp.append({"ch":r["ch"],"comp":comp,"mean":r[f"gmm_{_cp}_mu"],"sd":r[f"gmm_{_cp}_sd"],"weight":r[f"gmm_{_cp}_w"],"boundary":r["gmm_boundary"],
                           "no_interior_crossing":r.get("no_interior_crossing",np.nan),"outer_crossing_flag":r.get("outer_crossing_flag",np.nan),"outer_crossing":r.get("outer_crossing",np.nan),
                           "outer_affected_bins":affected,"outer_affected_frac_of_rest_component":frac,"good_cut":c})
            if gm is not None and np.isfinite(gm.get("boundary",np.nan)):
                z=d["log_lp_var"].to_numpy(float); yy=d["nano_label"].to_numpy(int); pp=(gm["g"].predict(z.reshape(-1,1))!=gm["rest"]).astype(int)
                sd=np.where(z<=gm["boundary"],float(r["gmm_rest_sd"]),float(r["gmm_act_sd"])); badsd=sd<=1e-12; dist=np.where(~badsd,np.abs(z-gm["boundary"])/sd,np.nan)
                bins=pd.cut(dist,[0,.5,1,1.5,2,3,np.inf],labels=["0-0.5","0.5-1","1-1.5","1.5-2","2-3",">3"])
                tmp=pd.DataFrame({"db":bins,"error":(pp!=yy).astype(int)}).groupby("db",observed=True)["error"].agg(n="count",n_error="sum").reset_index(); tmp["error_rate"]=tmp["n_error"]/tmp["n"]
                for _,q in tmp.iterrows(): ep.append({"ch":r["ch"],"mouse_id":r["mouse_id"],"db":q["db"],"n":q["n"],"n_error":q["n_error"],"error_rate":q["error_rate"],"sd_zero_flag":int(np.any(badsd)),"good_cut":c})
        _write_csv(pd.DataFrame(gp),os.path.join(outdir,"int_gmm_params.csv")); _write_csv(pd.DataFrame(ep),os.path.join(outdir,"int_error_bydist_perch.csv"))

    # Dark-definition mean-of-means aggregate.
    dp=os.path.join(outdir,"int_darkdef_sensitivity.csv")
    if os.path.exists(dp):
        d=_read_csv(dp)
        if {"shift_h","mouse_id","intensity_r"}.issubset(d.columns):
            ag=d.groupby(["shift_h","mouse_id"])["intensity_r"].mean().groupby("shift_h").agg(["mean","median","count"]).reset_index()
            ag.columns=["shift_h","mean_of_mouse_means","median_of_mouse_means","n_mouse"]; ag["good_cut"]=c; _write_csv(ag,os.path.join(outdir,"int_darkdef_sensitivity_agg.csv"))

    # Calibration 60-s reconstructability summary.
    cp=os.path.join(outdir,"int_calibration_60s.csv")
    if os.path.exists(cp):
        cal=_read_csv(cp)
        if len(cal) and {"ch","log_lp_var"}.issubset(cal.columns):
            cm=cal.groupby("ch")["log_lp_var"].median(); summary=pd.DataFrame([{"reconstructable":1,"n_channel":len(cm),"channel_median_mean":float(cm.mean()),"channel_median_sd":float(cm.std(ddof=1)),"channel_median_min":float(cm.min()),"channel_median_max":float(cm.max()),"good_cut":c,"note":"30/32 comparison and Spearman require occupied/rest reference columns; see PAPER_VALUES for availability check."}])
        else: summary=pd.DataFrame([{"reconstructable":0,"good_cut":c,"note":"int_calibration_60s.csv lacks required rows/columns; no values inferred."}])
        _write_csv(summary,os.path.join(outdir,"int_calibration_60s_summary.csv"))

    return df


def _good_sens_row(df, good_cut, thr, thr_source, nfold):
    """[S1-GRID] ある good_cut に対する int_good_sensitivity.csv 形式の 1 行。

    計算内容は _qc_outputs 冒頭のものと同一で、新しいロジックは一切足していない。
    列は既存ファイルと同じ 13 列（追加も削除もしない）。
    """
    c=float(good_cut); true=(df["F1_state"]>=c).astype(int); pred=(df["pir_active_rate"]>=thr).astype(int) if np.isfinite(thr) else pd.Series(np.zeros(len(df),int),index=df.index)
    tp,fp,fn,tn=_confusion_counts(pred,true); ppv,npv,sens,spec=_rate_metrics(tp,fp,fn,tn)
    auc=float(roc_auc_score(true,df["pir_active_rate"])) if true.nunique()>1 else np.nan
    passed=df[pred.eq(1)]; f1post=float(passed.groupby("mouse_id")["F1_state"].mean().mean()) if len(passed) else np.nan
    return {"good_cut":c,"lomo_threshold":thr,"threshold_source":thr_source,"n_fold_used":nfold,"n_good_ch":int(true.sum()),"n_bad_ch":int((1-true).sum()),"n_pass_ch":int(pred.sum()),"n_pass_mice":int(passed["mouse_id"].nunique()),"PPV":ppv,"sensitivity":sens,"specificity":spec,"par_auc":auc,"f1_qc_post":f1post}


def _good_sens_grid(outdir, df, good_cut, thr, thr_source, nfold):
    """[S1-GRID] Table S1 用に good_cut を GOOD_CUT_GRID 全点で再評価して書き出す。

    各 cut について §2.6.5 の既存手続き（leave-one-mouse-out + Youden J、fold 平均）を
    そのまま適用するだけ。採用 cut の行は _qc_outputs が使う (thr, thr_source, nfold) を
    そのまま用いるので、int_good_sensitivity.csv の該当行と全列一致する。
    出力先は新規ファイル int_good_sensitivity_grid.csv のみで、既存の中間ファイル・
    図・表の入力は一切変更しない。
    """
    rows=[]
    for gc in GOOD_CUT_GRID:
        if np.isclose(float(gc), float(good_cut)):
            t,s,nf = thr, thr_source, nfold
        else:
            _lt,t,s,nf = _derive_lomo_threshold(df, float(gc))
        rows.append(_good_sens_row(df, gc, t, s, nf))
    g=pd.DataFrame(rows).sort_values("good_cut").reset_index(drop=True)
    _write_csv(g, os.path.join(outdir,"int_good_sensitivity_grid.csv"))
    for _,r in g.iterrows():
        print(f"    [S1-GRID] cut={float(r['good_cut']):.2f} thr={r['lomo_threshold']} "
              f"src={r['threshold_source']} n_fold={r['n_fold_used']} "
              f"good/bad={r['n_good_ch']}/{r['n_bad_ch']} "
              f"pass={r['n_pass_ch']}ch/{r['n_pass_mice']}mice PPV={r['PPV']} "
              f"AUC={r['par_auc']} F1post={r['f1_qc_post']}", flush=True)
    return g


def _qc_outputs(outdir, df, good_cut, thr, thr_source, nfold, operational_fixed_thr=None):
    c=float(good_cut); true=(df["F1_state"]>=c).astype(int); pred=(df["pir_active_rate"]>=thr).astype(int) if np.isfinite(thr) else pd.Series(np.zeros(len(df),int),index=df.index)
    tp,fp,fn,tn=_confusion_counts(pred,true); ppv,npv,sens,spec=_rate_metrics(tp,fp,fn,tn)
    auc=float(roc_auc_score(true,df["pir_active_rate"])) if true.nunique()>1 else np.nan
    passed=df[pred.eq(1)]; f1post=float(passed.groupby("mouse_id")["F1_state"].mean().mean()) if len(passed) else np.nan
    gs=pd.DataFrame([{"good_cut":c,"lomo_threshold":thr,"threshold_source":thr_source,"n_fold_used":nfold,"n_good_ch":int(true.sum()),"n_bad_ch":int((1-true).sum()),"n_pass_ch":int(pred.sum()),"n_pass_mice":int(passed["mouse_id"].nunique()),"PPV":ppv,"sensitivity":sens,"specificity":spec,"par_auc":auc,"f1_qc_post":f1post}]); _write_csv(gs,os.path.join(outdir,"int_good_sensitivity.csv"))
    # [S1-GRID] Table S1 用の全グリッド。上の 1 行ファイルは従来どおり不変。
    _good_sens_grid(outdir,df,c,thr,thr_source,nfold)
    qc=pd.DataFrame([{"good_cut":c,"rule":"par_only","TP":tp,"FP":fp,"FN":fn,"TN":tn,"PPV":ppv,"NPV":npv,"sensitivity":sens,"specificity":spec,"n_pass":int(pred.sum()),"n_pass_mice":int(passed["mouse_id"].nunique()),"threshold":thr}]); _write_csv(qc,os.path.join(outdir,"int_qc_confusion.csv"))

    # Operational fixed-threshold estimand + re-estimated sensitivity row.
    # All interval estimates below resample the 8 mice as clusters.
    fixed=float(operational_fixed_thr if operational_fixed_thr is not None else thr)
    estimands=[("operational_fixed_threshold",fixed),("threshold_reestimated_sensitivity",thr)]
    metrics=["pir_active_rate","snr","floor_rate","gmm_separation"]
    mice=sorted(df["mouse_id"].astype(str).unique())
    nb=int(getattr(config,"AUC_BOOT_N",5000)); rng=np.random.default_rng(int(getattr(config,"AUC_BOOT_SEED",7)))
    perf_draws={name:{"PPV":[],"sensitivity":[],"specificity":[]} for name,_ in estimands}
    auc_draws={m:[] for m in metrics}
    diff_draws={m:[] for m in metrics[1:]}
    for _ in range(nb):
        pick=rng.choice(mice,size=len(mice),replace=True)
        parts=[]
        for j,m in enumerate(pick):
            q=df[df["mouse_id"].astype(str)==str(m)].copy(); q["_cluster_copy"]=j; parts.append(q)
        sub=pd.concat(parts,ignore_index=True); yy=(sub["F1_state"].astype(float)>=c).astype(int)
        for name,tv in estimands:
            if not np.isfinite(tv): continue
            pr=(sub["pir_active_rate"].astype(float)>=tv).astype(int); a,b,d,e=_confusion_counts(pr,yy); p1,n1,se,sp=_rate_metrics(a,b,d,e)
            for key,val in [("PPV",p1),("sensitivity",se),("specificity",sp)]:
                if pd.notna(val): perf_draws[name][key].append(float(val))
        if yy.nunique()>1:
            vals={}
            for m in metrics:
                vv=sub.dropna(subset=[m,"F1_state"]); yv=(vv["F1_state"].astype(float)>=c).astype(int)
                if yv.nunique()>1:
                    try: vals[m]=float(roc_auc_score(yv,vv[m].astype(float)))
                    except Exception: pass
            for m,vv in vals.items(): auc_draws[m].append(vv)
            if "pir_active_rate" in vals:
                for m in metrics[1:]:
                    if m in vals: diff_draws[m].append(vals["pir_active_rate"]-vals[m])

    rows=[]
    for name,tv in estimands:
        pr=(df["pir_active_rate"]>=tv).astype(int) if np.isfinite(tv) else pd.Series(np.zeros(len(df),int),index=df.index)
        a,b,d,e=_confusion_counts(pr,true); p1,n1,se,sp=_rate_metrics(a,b,d,e)
        row={"estimand":name,"good_cut":c,"threshold":tv,"PPV":p1,"sensitivity":se,"specificity":sp,"TP":a,"FP":b,"FN":d,"TN":e,"resample_unit":"mouse","n_boot_requested":nb}
        for key in ["PPV","sensitivity","specificity"]:
            dr=np.asarray(perf_draws[name][key],float); row[f"{key}_ci_lower"]=float(np.percentile(dr,2.5)) if len(dr) else np.nan; row[f"{key}_ci_upper"]=float(np.percentile(dr,97.5)) if len(dr) else np.nan; row[f"{key}_n_boot_valid"]=len(dr)
        rows.append(row)
    _write_csv(pd.DataFrame(rows),os.path.join(outdir,"int_qc_performance_estimands.csv"))

    # per-mouse raw values requested alongside small-cluster CI.
    pm=df.groupby("mouse_id").agg(par=("pir_active_rate","mean"),F1_state=("F1_state","mean"),intensity_r=("intensity_r","mean"),snr=("snr","mean"),floor_rate=("floor_rate","mean"),gmm_separation=("gmm_separation","mean"),pai_contrast=("pai_contrast","mean")); pm["good_cut"]=c; _write_csv(pm.reset_index(),os.path.join(outdir,"int_permouse_values.csv"))

    # AUCs for four QC metrics + paired-difference CIs from the SAME mouse-cluster draws.
    auc_rows=[]
    for m in metrics:
        v=df.dropna(subset=[m,"F1_state"]); yv=(v["F1_state"]>=c).astype(int); obs=float(roc_auc_score(yv,v[m])) if yv.nunique()>1 else np.nan; dr=np.asarray(auc_draws[m],float)
        auc_rows.append({"metric":m,"good_cut":c,"auc_observed":obs,"ci_lower":float(np.percentile(dr,2.5)) if len(dr) else np.nan,"ci_upper":float(np.percentile(dr,97.5)) if len(dr) else np.nan,"n_boot_valid":len(dr),"n_mouse":len(mice),"cluster_unit":"mouse"})
    refobs=next(x["auc_observed"] for x in auc_rows if x["metric"]=="pir_active_rate"); diffrows=[]
    for m in metrics[1:]:
        dr=np.asarray(diff_draws[m],float); mobs=next(x["auc_observed"] for x in auc_rows if x["metric"]==m)
        diffrows.append({"comparison":f"pir_active_rate - {m}","good_cut":c,"diff_observed":refobs-mobs,"diff_ci_lower":float(np.percentile(dr,2.5)) if len(dr) else np.nan,"diff_ci_upper":float(np.percentile(dr,97.5)) if len(dr) else np.nan,"n_boot_valid":len(dr),"cluster_unit":"mouse","inference_label":"exploratory_CI_only"})
    _write_csv(pd.DataFrame(auc_rows),os.path.join(outdir,"int_auc_metrics_cluster.csv")); _write_csv(pd.DataFrame(diffrows),os.path.join(outdir,"int_auc_boot.csv"))

    # BCa for mean-type, percentile for median-type/fallback.
    q=df[df["qc1_pass"]==1]; ci=[]
    specs=[("intensity_r_mean_of_means",df.groupby("mouse_id")["intensity_r"].mean().values,np.mean,True),
           ("F1_all_mean",df.groupby("mouse_id")["F1_state"].mean().values,np.mean,True),
           ("F1_qc1_mean",q.groupby("mouse_id")["F1_state"].mean().values,np.mean,True),
           ("intensity_r_median",df.groupby("mouse_id")["intensity_r"].median().values,np.median,False),
           ("F1_all_median_of_medians",df.groupby("mouse_id")["F1_state"].median().values,np.median,False)]
    for a,b,st,mt in specs:
        z=_bca_or_percentile(b,st,a,mt)
        if z: z["good_cut"]=c; ci.append(z)
    _write_csv(pd.DataFrame(ci),os.path.join(outdir,"int_bootstrap_ci.csv"))


def _session_outputs(outdir, df, good_cut, thr):
    """Session-level and temporal-QC diagnostics.  Primary analysis columns are read-only here."""
    c = float(good_cut)

    # ---------------------------------------------------------------- record summary
    rows = []
    for rec, g in df.groupby("record_id"):
        _ratio_ch = g["pir_active_rate"].astype(float) / g["nanotag_active_rate"].astype(float).replace(0, np.nan)
        rows.append({
            "row_type": "record_summary",
            "record_id": rec,
            "qc_pass_n": int(g["qc1_pass"].sum()),
            "n_ch": int(len(g)),
            "par_mean": float(g["pir_active_rate"].mean()),
            "nar_mean": float(g["nanotag_active_rate"].mean()),
            "par_over_nar": float(g["pir_active_rate"].mean() / g["nanotag_active_rate"].mean()),
            "par_over_nar_ch_mean": float(_ratio_ch.mean()),
            "par_over_nar_ch_sd": float(_ratio_ch.std(ddof=1)) if _ratio_ch.notna().sum() > 1 else np.nan,
            "F1_mean": float(g["F1_state"].mean()),
            "gmm_rest_w_mean": float(g["gmm_rest_w"].mean()),
            "gmm_separation_mean": float(g["gmm_separation"].mean()),
            "gmm_rest_sd_mean": float(g["gmm_rest_sd"].mean()),
            "gmm_act_mu_mean": float(g["gmm_act_mu"].mean()),
            "floor_rate_mean": float(g["floor_rate"].mean()),
            "adc_range_mean": float(g["adc_range"].mean()),
            "n_hours": float(g["n_hours"].max()),
            "good_cut": c,
            "note": "",
        })
    summ = pd.DataFrame(rows)
    # v3: record summary is kept separate from the 2x2 decomposition.
    _write_csv(summ, os.path.join(outdir, "int_session_diagnostic.csv"))

    # ---------------------------------------------------------------- explicit 2x2 decomposition
    design = {
        "260706": ("X", "mice1-4"),
        "260626": ("X", "mice5-8"),
        "260629": ("Y", "mice1-4"),
        "260702": ("Y", "mice5-8"),
    }
    z = summ[summ["record_id"].astype(str).isin(design)].copy()
    if len(z) == 4:
        z["sensor_set_design"] = z["record_id"].astype(str).map(lambda x: design[x][0])
        z["mouse_group_design"] = z["record_id"].astype(str).map(lambda x: design[x][1])
        grand = float(z["par_over_nar"].mean())
        sm = z.groupby("sensor_set_design")["par_over_nar"].mean()
        mm = z.groupby("mouse_group_design")["par_over_nar"].mean()
        z["grand_mean"] = grand
        z["sensor_set_mean"] = z["sensor_set_design"].map(sm)
        z["mouse_group_mean"] = z["mouse_group_design"].map(mm)
        z["sensor_set_main_effect"] = z["sensor_set_mean"] - grand
        z["mouse_group_main_effect"] = z["mouse_group_mean"] - grand
        z["expected_additive"] = grand + z["sensor_set_main_effect"] + z["mouse_group_main_effect"]
        z["residual_interaction_confounded"] = z["par_over_nar"] - z["expected_additive"]
        z["residual_df"] = 1
        z["metric"] = "par_over_nar"
        z["identifiability_note"] = (
            "Session effect and sensor-set x mouse-group interaction are completely confounded "
            "and cannot be separated in this design; the residual must not be called a session effect."
        )
        z["good_cut"] = c
        _write_csv(z, os.path.join(outdir, "int_session_2x2.csv"))
        log("  [session 2x2] session effect and sensor-set x mouse-group interaction are completely confounded; residual is not a session effect.")

    # ---------------------------------------------------------------- block-level session summary / trend
    tcp = os.path.join(outdir, "int_session_timecourse.csv")
    session_summary = pd.DataFrame()
    if os.path.exists(tcp):
        tc = _read_csv(tcp)
        if len(tc):
            for cc in ["block_index", "block_start_h", "block_end_h", "par", "nar", "par_over_nar", "pai_rest_component_mean", "n_pai_bins", "n_nano_bins_present", "pai_frac", "nano_frac", "block_usable"]:
                if cc in tc.columns:
                    tc[cc] = pd.to_numeric(tc[cc], errors="coerce")
            sr = []
            for (rec, bi), g in tc.groupby(["record_id", "block_index"], dropna=False):
                _present = g["n_nano_bins_present"].fillna(0).astype(float) > 0
                _ratio = g.loc[_present, "par_over_nar"].replace([np.inf, -np.inf], np.nan).dropna()
                _nar = g.loc[_present, "nar"].dropna()
                sr.append({
                    "record_id": rec,
                    "block_index": int(bi),
                    "block_start_h": float(g["block_start_h"].iloc[0]),
                    "block_end_h": float(g["block_end_h"].iloc[0]),
                    "n_ch": int(g["ch"].nunique()),
                    "n_ch_ratio": int(_ratio.shape[0]),
                    "par_mean": float(g["par"].mean()),
                    "nar_mean": float(_nar.mean()) if len(_nar) else np.nan,
                    "par_over_nar_mean": float(_ratio.mean()) if len(_ratio) else np.nan,
                    "par_over_nar_sd": float(_ratio.std(ddof=1)) if len(_ratio) > 1 else np.nan,
                    "pai_rest_component_mean": float(g["pai_rest_component_mean"].mean()),
                    "n_nano_bins_present_mean": float(g["n_nano_bins_present"].mean()),
                    "block_usable": int(g["block_usable"].fillna(0).astype(int).min()),
                    "good_cut": c,
                })
            session_summary = pd.DataFrame(sr).sort_values(["record_id", "block_index"]).reset_index(drop=True)
            # 暗期は偶数ブロックインデックスで決まる。nar による OR は明期ブロックを
            # 暗期側に引き込むため廃止。さらに不正ブロックは暗期集計から除外する。
            session_summary["is_dark_block"] = (
                (session_summary["block_index"].astype(int) % 2 == 0)
                & session_summary["block_usable"].astype(int).eq(1)
            ).astype(int)
            session_summary["dark_rule"] = "block_index even; block_usable == 1 required"
            _write_csv(session_summary, os.path.join(outdir, "int_session_summary.csv"))

            # Trend class is evaluated on dark blocks with a finite reference-derived ratio only.
            tmp_rows = []
            for rec, g in session_summary[session_summary["is_dark_block"].eq(1)].groupby("record_id"):
                gg = g.dropna(subset=["par_over_nar_mean"]).sort_values("block_start_h")
                if not len(gg):
                    tmp_rows.append({"record_id": rec, "n_dark_blocks": 0, "ratio_first": np.nan, "ratio_last": np.nan,
                                     "ratio_delta": np.nan, "ratio_slope_per_day": np.nan, "ratio_mean": np.nan, "ratio_sd": np.nan})
                    continue
                vals = gg["par_over_nar_mean"].to_numpy(float)
                xday = gg["block_start_h"].to_numpy(float) / 24.0
                slope = float(np.polyfit(xday, vals, 1)[0]) if len(vals) >= 2 and np.ptp(xday) > 0 else np.nan
                tmp_rows.append({
                    "record_id": rec,
                    "n_dark_blocks": int(len(vals)),
                    "ratio_first": float(vals[0]),
                    "ratio_last": float(vals[-1]),
                    "ratio_delta": float(vals[-1] - vals[0]),
                    "ratio_slope_per_day": slope,
                    "ratio_mean": float(np.mean(vals)),
                    "ratio_sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else np.nan,
                })
            trend = pd.DataFrame(tmp_rows)
            cohort_mean = float(trend["ratio_mean"].mean()) if len(trend) else np.nan
            # 記録数が少ないため stable_low の比較基準は leave-one-out cohort 平均を使う。
            _rm = trend["ratio_mean"].astype(float)
            _n = int(_rm.notna().sum())
            _tot = float(_rm.sum(skipna=True))
            trend["cohort_ratio_mean_loo"] = [
                (_tot - v) / (_n - 1) if (pd.notna(v) and _n > 1) else np.nan for v in _rm
            ]
            low_margin = float(getattr(config, "SESSION_STABLE_LOW_COHORT_MARGIN", 0.15))
            delta_thr = float(getattr(config, "SESSION_TREND_DELTA_THRESHOLD", 0.10))
            classes, notes = [], []
            for _, r in trend.iterrows():
                mean = float(r["ratio_mean"]) if pd.notna(r["ratio_mean"]) else np.nan
                delta = float(r["ratio_delta"]) if pd.notna(r["ratio_delta"]) else np.nan
                cohort_mean_loo = float(r["cohort_ratio_mean_loo"]) if pd.notna(r["cohort_ratio_mean_loo"]) else np.nan
                if not (np.isfinite(mean) and np.isfinite(delta) and np.isfinite(cohort_mean_loo)):
                    cls = "insufficient_reference"
                    note = "No finite dark-block detection-ratio series or leave-one-out cohort reference available."
                elif mean <= cohort_mean_loo - low_margin and abs(delta) < delta_thr:
                    cls = "stable_low"
                    note = f"ratio_mean={mean:.6g} is >= {low_margin:.3g} below cohort_mean_loo={cohort_mean_loo:.6g}; abs(delta)={abs(delta):.6g} < {delta_thr:.3g}."
                elif delta < -delta_thr:
                    cls = "declining"
                    note = f"ratio_delta={delta:.6g} < -{delta_thr:.3g}."
                elif delta > delta_thr:
                    cls = "improving"
                    note = f"ratio_delta={delta:.6g} > +{delta_thr:.3g}."
                else:
                    cls = "stable_normal"
                    note = f"No stable-low or >|{delta_thr:.3g}| trend criterion was met."
                classes.append(cls); notes.append(note)
            trend["cohort_ratio_mean"] = cohort_mean
            trend["stable_low_margin"] = low_margin
            trend["delta_threshold"] = delta_thr
            trend["trend_class"] = classes
            trend["interpretation"] = notes
            trend["good_cut"] = c
            _write_csv(trend, os.path.join(outdir, "int_session_trend.csv"))

            # ------------------------------------------------------------ reference-free channel stability
            sat_thr = float(getattr(config, "TEMPORAL_PAR_SATURATION_THRESHOLD", 0.95))
            jump_thr = float(getattr(config, "TEMPORAL_PAI_REST_JUMP_THRESHOLD", 2.0))
            range_thr = float(getattr(config, "TEMPORAL_PAR_RANGE_THRESHOLD", 0.50))
            stab_rows = []
            meta = df.set_index("ch", drop=False)
            for ch, g in tc.groupby("ch"):
                gg = (g[g["block_usable"].eq(1)] if "block_usable" in g.columns else g).sort_values("block_index").copy()
                pv = gg["par"].dropna().to_numpy(float)
                rv = gg["pai_rest_component_mean"].dropna().to_numpy(float)
                pmin = float(np.min(pv)) if len(pv) else np.nan
                pmax = float(np.max(pv)) if len(pv) else np.nan
                prange = float(pmax - pmin) if len(pv) else np.nan
                pmean = float(np.mean(pv)) if len(pv) else np.nan
                pcv = float(np.std(pv, ddof=1) / abs(pmean)) if len(pv) > 1 and abs(pmean) > 1e-12 else np.nan
                sat_n = int(np.sum(pv >= sat_thr)) if len(pv) else 0
                rmin = float(np.min(rv)) if len(rv) else np.nan
                rmax = float(np.max(rv)) if len(rv) else np.nan
                rrange = float(rmax - rmin) if len(rv) else np.nan
                # Only consecutive block indices count as adjacent jumps.
                _jumps = []
                _rgg = gg.dropna(subset=["pai_rest_component_mean"])
                _bi = _rgg["block_index"].to_numpy(float)
                _rr = _rgg["pai_rest_component_mean"].to_numpy(float)
                for j in range(1, len(_rr)):
                    if int(_bi[j] - _bi[j-1]) == 1:
                        _jumps.append(abs(float(_rr[j] - _rr[j-1])))
                jumpmax = float(max(_jumps)) if _jumps else np.nan
                flag_sat = bool(sat_n >= 1)
                flag_floor = bool(np.isfinite(jumpmax) and jumpmax >= jump_thr)
                flag_range = bool(np.isfinite(prange) and prange >= range_thr)
                primary = []
                if flag_sat: primary.append("saturated")
                if flag_floor: primary.append("floor_shift")
                if primary:
                    flag = "+".join(primary)
                elif flag_range:
                    flag = "unstable"
                else:
                    flag = "stable"
                reasons = []
                if flag_sat: reasons.append(f"par saturation blocks={sat_n} at par>={sat_thr:g}")
                if flag_floor: reasons.append(f"max adjacent rest-component jump={jumpmax:.6g}>={jump_thr:g}")
                if (not primary) and flag_range: reasons.append(f"par block range={prange:.6g}>={range_thr:g} (auxiliary rule)")
                if not reasons: reasons.append("no temporal instability rule met")
                mr = meta.loc[ch] if ch in meta.index else pd.Series(dtype=object)
                stab_rows.append({
                    "ch": ch,
                    "mouse_id": mr.get("mouse_id", gg["mouse_id"].iloc[0] if "mouse_id" in gg else ""),
                    "record_id": mr.get("record_id", gg["record_id"].iloc[0] if "record_id" in gg else ""),
                    "sensor_id": mr.get("sensor_id", gg["sensor_id"].iloc[0] if "sensor_id" in gg else ""),
                    "n_blocks": int(gg["block_index"].nunique()),
                    "par_block_min": pmin,
                    "par_block_max": pmax,
                    "par_block_range": prange,
                    "par_block_cv": pcv,
                    "par_saturation_blocks": sat_n,
                    "pai_rest_block_min": rmin,
                    "pai_rest_block_max": rmax,
                    "pai_rest_block_range": rrange,
                    "pai_rest_jump_max": jumpmax,
                    "flag_saturated": int(flag_sat),
                    "flag_floor_shift": int(flag_floor),
                    "flag_unstable_range": int(flag_range),
                    "stability_flag": flag,
                    "stability_reason": "; ".join(reasons),
                    "qc1_pass": int(mr.get("qc1_pass", 0)) if len(mr) else 0,
                    "good_cut": c,
                })
            stability = pd.DataFrame(stab_rows)
            _write_csv(stability, os.path.join(outdir, "int_channel_stability.csv"))

            # Static par gate vs temporal stability (temporal pass = no stability flag).
            cmp = stability.merge(df[["ch", "F1_state"]], on="ch", how="left")
            cmp["is_good"] = (cmp["F1_state"].astype(float) >= c).astype(int)
            cmp["temporal_pass"] = cmp["stability_flag"].astype(str).eq("stable").astype(int)
            def _cat(r):
                sp = int(r["qc1_pass"]) == 1
                tp = int(r["temporal_pass"]) == 1
                if sp and tp: return "both_pass"
                if sp and not tp: return "static_only"
                if (not sp) and tp: return "temporal_only"
                return "both_fail"
            cmp["category"] = cmp.apply(_cat, axis=1)
            cols = ["ch", "qc1_pass", "stability_flag", "flag_saturated", "flag_floor_shift", "flag_unstable_range",
                    "temporal_pass", "F1_state", "is_good", "category", "good_cut"]
            _write_csv(cmp[cols], os.path.join(outdir, "int_qc_temporal_compare.csv"))

    # ---------------------------------------------------------------- matched sensor / mouse contrasts
    sy = df[df["record_id"].astype(str).isin(["260629", "260702"])].pivot_table(
        index="sensor_id", columns="record_id", values=["pir_active_rate", "nanotag_active_rate"], aggfunc="mean"
    )
    sy.columns = [f"{a}_{b}" for a, b in sy.columns]
    sy = sy.reset_index()
    _write_csv(sy, os.path.join(outdir, "int_session_sensor_control.csv"))
    mmc = df[df["record_id"].astype(str).isin(["260626", "260702"])].pivot_table(
        index="mouse_id", columns="record_id", values=["pir_active_rate", "nanotag_active_rate"], aggfunc="mean"
    )
    mmc.columns = [f"{a}_{b}" for a, b in mmc.columns]
    mmc = mmc.reset_index()
    _write_csv(mmc, os.path.join(outdir, "int_session_mouse_control.csv"))

    # Calibration constants are sensor-level and therefore not candidate record-level explanations.
    cal = df.groupby("sensor_id")[["empty_box_mu", "noise_sigma"]].nunique(dropna=False)
    same = bool((cal <= 1).all().all())
    _write_csv(pd.DataFrame([{
        "sensor_calibration_constant_within_sensor": int(same),
        "note": "empty_box_mu and noise_sigma are sensor-level calibration constants; do not use them as record-level explanatory variables.",
        "good_cut": c,
    }]), os.path.join(outdir, "int_session_calibration_note.csv"))

    # Exclusion sensitivity (dependence disclosure, not a primary exclusion claim).
    ex = df[df["record_id"].astype(str) != str(getattr(config, "SESSION_DIAGNOSTIC_RECORD", "260702"))].copy()
    _, t2, _, _ = _derive_lomo_threshold(ex, c)
    ex["qc_pass_exclusion"] = (ex["pir_active_rate"] >= t2).astype(int) if np.isfinite(t2) else 0
    _write_csv(pd.DataFrame([{
        "excluded_record": getattr(config, "SESSION_DIAGNOSTIC_RECORD", "260702"),
        "r_mean_of_mouse_means": float(ex.groupby("mouse_id")["intensity_r"].mean().mean()),
        "F1_mean_of_mouse_means": float(ex.groupby("mouse_id")["F1_state"].mean().mean()),
        "qc_threshold": t2,
        "n_pass_ch": int(ex["qc_pass_exclusion"].sum()),
        "n_pass_mice": int(ex.loc[ex["qc_pass_exclusion"] == 1, "mouse_id"].nunique()),
        "good_cut": c,
        "purpose": "dependence disclosure; not a primary exclusion claim",
    }]), os.path.join(outdir, "int_session_exclusion.csv"))


def _gate_values(df, outdir, good_cut, thr):
    q=df[df["qc1_pass"]==1]
    true=(df["F1_state"]>=good_cut).astype(int); pred=df["qc1_pass"].astype(int); tp,fp,fn,tn=_confusion_counts(pred,true)
    auc=float(roc_auc_score(true,df["pir_active_rate"])) if true.nunique()>1 else np.nan
    scp=os.path.join(outdir,"int_sensor_consistency_permouse.csv"); inter=np.nan
    if os.path.exists(scp):
        sc=_read_csv(scp); col="mean_inter_sensor_r" if "mean_inter_sensor_r" in sc else "median_inter_sensor_r"; inter=float(sc[col].mean() if col=="mean_inter_sensor_r" else sc[col].median())
    return {"r":float(df.groupby("mouse_id")["intensity_r"].mean().mean()),"F1_all":float(df.groupby("mouse_id")["F1_state"].mean().mean()),"F1_qc":float(q.groupby("mouse_id")["F1_state"].mean().mean()) if len(q) else np.nan,"threshold":thr,"AUC_par":auc,"TP":tp,"FP":fp,"FN":fn,"TN":tn,"inter_sensor_r":inter}


def _make_audit(outdir, good_cut, cross_rows=None):
    df = _read_csv(os.path.join(outdir, "int_channel.csv"))
    lt = _read_csv(os.path.join(outdir, "int_loso_thr.csv"))
    thr = float(lt["qc1_threshold"].mean()) if len(lt) else np.nan
    new = _gate_values(df, outdir, good_cut, thr)
    # Frozen literals are allowed ONLY in this gate block (implementation specification).
    frozen = {"r":0.9171,"F1_all":0.6840,"F1_qc":0.7715,"threshold":0.2852,"AUC_par":0.9231,"TP":12,"FP":3,"FN":1,"TN":16,"inter_sensor_r":0.9421}

    gate_lines = ["## GATE CHECK", "| metric | old | new | diff | status |", "|---|---:|---:|---:|---|"]
    for k, old in frozen.items():
        nv = new.get(k, np.nan)
        diff = nv - old if np.isfinite(nv) else np.nan
        tol = 5e-5 if isinstance(old, float) else 0
        status = "unchanged" if np.isfinite(diff) and abs(diff) <= tol else "CHECK"
        gate_lines.append(f"| {k} | {old} | {nv} | {diff} | {status} |")

    registry_lines = [
        "## Measurement registry",
        "| metric | value | source CSV | column | aggregation | n | generator |",
        "|---|---:|---|---|---|---:|---|",
    ]
    registry = [
        ("intensity_r",new["r"],"int_channel.csv","intensity_r","mean of mouse means",df["mouse_id"].nunique(),"_gate_values"),
        ("F1_all",new["F1_all"],"int_channel.csv","F1_state","mean of mouse means",df["mouse_id"].nunique(),"_gate_values"),
        ("F1_qc",new["F1_qc"],"int_channel.csv","F1_state","mean of mouse means after qc1_pass",df[df["qc1_pass"]==1]["mouse_id"].nunique(),"_gate_values"),
        ("QC_threshold",thr,"int_loso_thr.csv","qc1_threshold","mean across valid LOMO folds",len(lt),"_derive_lomo_threshold"),
    ]
    for r in registry:
        registry_lines.append("| " + " | ".join(map(str, r)) + " |")

    per_channel_lines = ["## Per-channel major metrics"]
    cols = [c for c in ["ch","mouse_id","record_id","sensor_set","pir_active_rate","nanotag_active_rate","F1_state","mcc","intensity_r","snr","pai_contrast","gmm_separation","adc_range","qc1_pass","f1_upper_bound","clears_algebraic_bound"] if c in df.columns]
    per_channel_lines.append(df[cols].to_markdown(index=False))
    sp = os.path.join(outdir, "int_session_diagnostic.csv")
    if os.path.exists(sp):
        per_channel_lines += ["", "## Record summary", _read_csv(sp).to_markdown(index=False)]

    existing = sorted(x for x in os.listdir(outdir) if x.startswith("int_") and x.endswith(".csv"))
    refs = _referenced_intermediate_csvs()
    union = sorted(set(existing) | set(refs))
    inventory_lines = [
        "## Intermediate CSV inventory",
        "| file | exists | rows | cols | bytes | generator/status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    orphan_names = []
    preexisting_names = []
    generated_names = []
    for fn in union:
        path = os.path.join(outdir, fn)
        exists = os.path.exists(path)
        if exists:
            try:
                d = _read_csv(path); nr, nc = d.shape
            except Exception:
                nr = nc = 0
            label = _csv_generator_label(path)
            if label == "[PRE-EXISTING]": preexisting_names.append(fn)
            else: generated_names.append(fn)
            inventory_lines.append(f"| {fn} | 1 | {nr} | {nc} | {os.path.getsize(path)} | {label} |")
        else:
            orphan_names.append(fn)
            inventory_lines.append(f"| {fn} | 0 | 0 | 0 | 0 | [ORPHAN] |")

    # Build audit sections in configured scientific-priority order, then alphabetically.
    priority_raw = list(getattr(config, "PAPER_VALUES_PRIORITY", []))
    priority = [x if str(x).endswith(".csv") else f"{x}.csv" for x in priority_raw]
    order = [fn for fn in priority if fn in existing]
    order += [fn for fn in existing if fn not in set(order)]
    summary_only = set(getattr(config, "PAPER_VALUES_SUMMARY_ONLY", []))
    section_text = {}
    for fn in order:
        try:
            d = _read_csv(os.path.join(outdir, fn))
        except Exception as e:
            section_text[fn] = f"### {fn}\n\n[read failed: {e}]"
            continue
        block = [f"### {fn}", f"Rows: {len(d)}", "Columns: " + ", ".join(map(str, d.columns))]
        if fn in summary_only or len(d) > 600:
            try:
                block.append("\nSummary (`describe`, full rows intentionally omitted):\n" + d.describe(include="all").transpose().to_markdown())
            except Exception:
                pass
        else:
            block.append(d.to_markdown(index=False))
        section_text[fn] = "\n\n".join(block)

    footer_lines = [
        "## Version hash note",
        "Raw int_channel.csv hashes necessarily differ across good_cut versions because the required good_cut and QC columns differ. The analysis-payload SHA-256 excludes version-dependent columns and is the drift check.",
    ]
    if cross_rows:
        footer_lines += ["", "## Cross-version table", pd.DataFrame(cross_rows).to_markdown(index=False)]

    fixed_lines = [
        "# PAPER_VALUES",
        "",
        f"Generated by stage1_compute.py v3; good_cut={good_cut:.2f}.",
        "",
        "## Settings",
        *list(config.settings_report()),
        "",
        *gate_lines,
        "",
        *registry_lines,
        "",
        *per_channel_lines,
        "",
        *inventory_lines,
        "",
        "## ORPHAN audit",
        f"- Generated this session: {len(generated_names)} existing CSV(s)",
        f"- [PRE-EXISTING]: {len(preexisting_names)} existing CSV(s)",
        f"- [ORPHAN]: {len(orphan_names)} referenced-but-missing CSV(s)",
    ]
    if orphan_names:
        fixed_lines += ["- Missing references: " + ", ".join(orphan_names)]
    fixed_lines += ["", "## CSV contents / summaries"]

    limit = int(getattr(config, "PAPER_VALUES_MAX_CHARS", 1_200_000))
    selected = []
    omitted = []
    # Leave room for dynamic front/end warnings; then trim precisely below if needed.
    base_len = len("\n".join(fixed_lines + footer_lines))
    running = base_len
    reserve = 8000
    for fn in order:
        txt = section_text[fn]
        if running + len(txt) + 2 <= max(limit - reserve, 0):
            selected.append(fn); running += len(txt) + 2
        else:
            omitted.append(fn)

    def _warning_lines(names):
        if not names:
            return []
        return [
            "## ⚠ TRUNCATION WARNING",
            f"上限 {limit} 文字に達したため、以下 {len(names)} 本の CSV は収録されていません:",
            *[f"- {x}" for x in names],
        ]

    def _assemble(sel, omit):
        coverage = [
            "## Audit coverage summary",
            f"- CSV content sections included: {len(sel)} / {len(existing)}",
            f"- Existing CSV inventory: {len(existing)}",
            f"- [PRE-EXISTING]: {len(preexisting_names)}",
            f"- [ORPHAN] referenced-but-missing: {len(orphan_names)}",
        ]
        front_warn = _warning_lines(omit)
        end_warn = _warning_lines(omit)
        parts = ["# PAPER_VALUES", "", f"Generated by stage1_compute.py v3; good_cut={good_cut:.2f}.", "", *coverage]
        if front_warn:
            parts += ["", *front_warn]
        # fixed_lines already starts with the title; drop its first four title/version lines.
        parts += ["", *fixed_lines[4:]]
        for fn in sel:
            parts += ["", section_text[fn]]
        parts += ["", *footer_lines]
        if end_warn:
            parts += ["", *end_warn]
        return "\n".join(parts) + "\n"

    _full_text = _assemble(order, [])
    if len(_full_text) <= limit:
        selected = list(order); omitted = []; text = _full_text
    else:
        text = _assemble(selected, omitted)
    while len(text) > limit and selected:
        omitted.insert(0, selected.pop())
        text = _assemble(selected, omitted)
    if len(text) > limit:
        # Header/inventory alone should never hit this with the configured limit, but never cut silently.
        text = text[:max(limit - 300, 0)] + "\n\n## ⚠ TRUNCATION WARNING\nAudit header itself exceeded the configured limit; increase PAPER_VALUES_MAX_CHARS.\n"

    with open(os.path.join(outdir, "PAPER_VALUES.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    log(f"  [PAPER_VALUES] sections {len(selected)}/{len(existing)}, chars={len(text)}/{limit}, pre-existing={len(preexisting_names)}, orphan={len(orphan_names)}")
    if omitted:
        log("  [PAPER_VALUES] TRUNCATION WARNING: " + ", ".join(omitted))
    if orphan_names:
        log("  [ORPHAN] referenced but missing: " + ", ".join(orphan_names))

    review = [
        "GATE CHECK",
        pd.DataFrame([{"metric":k,"old":frozen[k],"new":new.get(k),"diff":new.get(k)-frozen[k] if np.isfinite(new.get(k,np.nan)) else np.nan} for k in frozen]).to_string(index=False),
        "",
        f"good_cut={good_cut:.2f}",
        f"paper_values_sections={len(selected)}/{len(existing)}",
        f"paper_values_chars={len(text)}/{limit}",
        f"pre_existing_csv_n={len(preexisting_names)}",
        f"orphan_referenced_missing_n={len(orphan_names)}",
    ]
    if omitted:
        review += ["TRUNCATION WARNING", *omitted]
    if orphan_names:
        review += ["ORPHAN REFERENCES", *orphan_names]
    with open(os.path.join(outdir, "REVIEW.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(review) + "\n")
    return new


def _isolate_legacy(outdir):
    legacy_names=["int_shuffle_null.csv","int_channel_before.csv","int_sep_upper_lomo.csv","int_floor_bin_labels.csv","int_agecompare.csv"]
    ldir=os.path.join(outdir,"legacy"); os.makedirs(ldir,exist_ok=True)
    moved=[]
    for fn in legacy_names:
        src=os.path.join(outdir,fn)
        if os.path.exists(src):
            dst=os.path.join(ldir,fn)
            if os.path.exists(dst): os.remove(dst)
            shutil.move(src,dst); moved.append(fn)
    if moved:
        open(os.path.join(ldir,"README.txt"),"w",encoding="utf-8").write("Legacy artifacts isolated by stage1 v2 and excluded from PAPER_VALUES sources:\n"+"\n".join(moved)+"\n")
    return moved

def _tag_all_csvs(outdir, good_cut):
    for fn in os.listdir(outdir):
        # [S1-GRID] グリッドは good_cut 自体が行の識別子なので版タグで上書きしない。
        if fn == "int_good_sensitivity_grid.csv":
            continue
        if fn.startswith("int_") and fn.endswith(".csv"):
            p=os.path.join(outdir,fn)
            try: d=_read_csv(p)
            except Exception: continue
            d["good_cut"]=float(good_cut); _write_csv(d,p)


def run_one(good_cut, source_dir=None, heavy=False, operational_fixed_thr=None):
    """Clean version context. Heavy signal processing is executed only when heavy=True."""
    global GOOD_F1
    GOOD_F1=float(good_cut); config.QC1_GOOD_F1=float(good_cut)
    root=config.ANALYSIS_OUTPUTS_DIR; outdir=os.path.join(root,f"intermediate__good{int(round(good_cut*100)):03d}")
    os.makedirs(outdir,exist_ok=True)
    if heavy:
        config.INTERMEDIATE_DIR=outdir
        _legacy_main()
    elif source_dir:
        if os.path.abspath(source_dir)!=os.path.abspath(outdir):
            for fn in os.listdir(source_dir):
                if fn.startswith("int_") and fn.endswith(".csv"):
                    shutil.copy2(os.path.join(source_dir,fn),os.path.join(outdir,fn))
    _isolate_legacy(outdir)
    ch=_read_csv(os.path.join(outdir,"int_channel.csv")); lt,thr,src,nfold=_derive_lomo_threshold(ch,float(good_cut)); lt["good_cut"]=float(good_cut); _write_csv(lt,os.path.join(outdir,"int_loso_thr.csv"))
    ch=_make_common_diagnostics(outdir,float(good_cut),thr); _qc_outputs(outdir,ch,float(good_cut),thr,src,nfold,operational_fixed_thr=operational_fixed_thr); _session_outputs(outdir,ch,float(good_cut),thr); _tag_all_csvs(outdir,float(good_cut))
    ch=_read_csv(os.path.join(outdir,"int_channel.csv")); return outdir,_payload_hash_channel(ch),_raw_sha256(os.path.join(outdir,"int_channel.csv")),thr,src,nfold


def main():
    parser=argparse.ArgumentParser(description="Sensors analysis pipeline v2")
    parser.add_argument("--base-data-dir",default=os.environ.get("SENSORS_BASE_DATA_DIR"))
    parser.add_argument("--only-good-cut",type=float,choices=[0.70,0.80],default=None,help="post-process one version; heavy run still starts from 0.70 when no cache is supplied")
    args=parser.parse_args()
    if args.base_data_dir: config.update_paths(args.base_data_dir)
    cuts=[float(x) for x in getattr(config,"GOOD_CUT_VERSIONS",[0.70,0.80])]
    if args.only_good_cut is not None: cuts=[float(args.only_good_cut)]
    base_cut=0.70 if 0.70 in cuts else cuts[0]
    d0,h0,r0,t0,s0,n0=run_one(base_cut,heavy=True)
    results=[(base_cut,d0,h0,r0,t0,s0,n0)]
    for c in cuts:
        if c==base_cut: continue
        d,h,r,t,src,nf=run_one(c,source_dir=d0,heavy=False,operational_fixed_thr=t0); results.append((c,d,h,r,t,src,nf))
    cross=[]
    for c,d,h,r,t,src,nf in results:
        df=_read_csv(os.path.join(d,"int_channel.csv")); gs=_read_csv(os.path.join(d,"int_good_sensitivity.csv")).iloc[0]
        cross.append({"good_cut":c,"threshold":t,"threshold_source":src,"n_fold_used":nf,"n_good_ch":int(gs["n_good_ch"]),"n_bad_ch":int(gs["n_bad_ch"]),"n_pass_ch":int(gs["n_pass_ch"]),"n_pass_mice":int(gs["n_pass_mice"]),"PPV":gs["PPV"],"sensitivity":gs["sensitivity"],"specificity":gs["specificity"],"par_auc":gs["par_auc"],"QC_after_F1":gs["f1_qc_post"],"int_channel_payload_sha256":h,"int_channel_raw_sha256":r})
    drift_ok=len(set(x["int_channel_payload_sha256"] for x in cross))==1
    for _,d,_,_,_,_,_ in results:
        _write_csv(pd.DataFrame(cross),os.path.join(d,"int_version_crosswalk.csv"))
        _make_audit(d,float(_read_csv(os.path.join(d,"int_channel.csv"))["good_cut"].iloc[0]),cross_rows=cross)
        open(os.path.join(d,"VERSION_DRIFT_CHECK.txt"),"w",encoding="utf-8").write(f"analysis_payload_hash_match={drift_ok}\nraw_hash_match={len(set(x['int_channel_raw_sha256'] for x in cross))==1}\n")
    print(f"[version drift] normalized int_channel payload hash match = {drift_ok}",flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb=traceback.format_exc(); print("!!!!!! stage1 v2 exception !!!!!!",flush=True); print(tb,flush=True)
        with open("stage1_error.log","w",encoding="utf-8") as f: f.write(tb)
        raise
