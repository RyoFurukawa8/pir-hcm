"""
config.py — 完全置換版（改良バッチ v3）
定数・パラメータ一元管理。stage1/legacy stage2 は本ファイルのみ参照（結果値のハードコード禁止）。

【数値の2分類】
  ・測定値（禁止）: 計算結果として得られる値。
                    コードに書かない。必ず int_*.csv から読む。
  ・設定（可）    : 計算前に人間が決める入力。識別子（どれを代表とするか／どの群をAと呼ぶか）と
                    掃引レンジ（どこを調べるか）。本ファイルに集約し、REVIEW.txt にも必ず印字する。

改良バッチ v3 で追加した設定（測定値には触れない）:
  ・PAPER_VALUES_MAX_CHARS / PAPER_VALUES_PRIORITY（監査出力の上限・収録順）
  ・セッション trend 判定閾値（stable_low / declining / improving）
  ・時間分解QC閾値（par飽和 / PAI rest成分ジャンプ / parレンジ）
  ・Fig1 は現行設定どおり 260626_ch4 / high / 150秒を使用する。
第4版からの継続:
  ・Old群を完全排除（RECORDS_OLD=[] 固定・stage1で在庫チェックを print）
  ・センサーセット識別を sensor_id 先頭文字（X/Y）に固定（SENSOR_SET_ORDER）
  ・good_cut 掃引を 0.70 の下側にも拡張（下限の正当化用）
  ・探索用計算 X1-X10 のフラグとレンジ
"""

import os

# =============================================================== 1. 物理・時間
FS = 30.0  # 実測30Hz固定（TS秒精度による1.0Hz誤認を排除）
DARK_HOURS = (20, 8)  # 暗期 20:00〜翌08:00

# 状態分類ビン（既定60s）と強度相関ビン（既定10min）
BIN_STATE_SEC = 60
BIN_STATE = "60s"
BIN_INTENSITY_SEC = 600
BIN_INTENSITY = "10min"

# ビン掃引: 各ビン幅で状態F1と強度rを実計算し「使い分け」を正当化（S1）
BIN_SWEEP_SEC = [60, 120, 180, 300, 600]

# NanoTag の時間分解能（実測12s）。raw_trace の付与に使用。
NANOTAG_RESOLUTION_SEC = 12


def sec_to_rule(sec):
    """秒 → pandas resample 文字列（秒指定で統一）"""
    return f"{int(sec)}s"


# =============================================================== 2. 信号処理
LOWPASS_CUTOFF_HZ = 1.0  # Butterworth 低域通過 (B0)
LOWPASS_ORDER = 4  # 実効値。stage1 は必ずこの値を参照
MAIN_FEATURE = "log_lp_var"  # PAI = log(1Hz-LPF後の分散)
CORR_METHOD = "spearman"  # 単調・非線形・分布歪みに頑健（直線回帰は引かない）
INTENSITY_TARGET_LABEL = "nanotag_count_paired"
STAT_UNIT = "mouse"  # 疑似反復回避: 代表値・検定は個体(8匹)単位

# =============================================================== 3. 品質管理
QC1_METRIC = "pir_active_rate"
QC1_THRESHOLD = float("nan")  # 測定値フォールバックは持たない。LOMO不能時はNaNとして明示
QC1_GOOD_F1 = 0.70  # good定義（AUC報告・閾値導出で同一値）

# ★good定義(F1閾値)の感度分析・混同行列で使う掃引リスト。
#   0.70より下は good/bad の区別自体が消えることを示す「下限の正当化」に使う。
#   （下側では n_bad_ch が枯渇し PPV が見かけ上跳ね上がるため、
#     int_good_sensitivity.csv の n_good_ch / n_bad_ch / n_fold_used を必ず併読すること）
GOOD_CUT_SWEEP = [0.70, 0.80]
GOOD_CUT_VERSIONS = [0.70, 0.80]

# ★多条件QCの各ガード閾値。par単独の qc1_pass / QC1_THRESHOLD とは別枠。
QC1_MULTI_SNR_MIN = 1.0
QC1_MULTI_GMM_SEP_MIN = 1.0

# ★QCルール梯子（stage1が int_qc_confusion.csv の rule 列に出す ASCII キー）
#   par_only    : par >= thr
#   par_snr     : + snr >= QC1_MULTI_SNR_MIN
#   par_sep     : + gmm_separation >= QC1_MULTI_GMM_SEP_MIN   （SNRガードなし）
#   par_snr_sep : + 両方（= qc1_pass_multi）
QC_RULE_KEYS = ["par_only", "par_snr", "par_sep", "par_snr_sep"]

# ★par閾値そのものの連続掃引（X10）。採用閾値近傍の安定性を確認する。
PAR_THRESHOLD_SWEEP = [round(0.15 + 0.01 * i, 3) for i in range(31)]  # 0.15〜0.45

# =============================================================== 4. 表示規則
# legacy stage2 の表示量。int_aggregation_summary.csv で両方計算した上で、表示のみ切替。
DISPLAY_R_AGG = "mean"  # 強度r: 'median'(=median-of-medians, 従来) / 'mean'
DISPLAY_F1_AGG = "mean"  # 状態F1: 'mean'(=mean-of-means, 現行) / 'median'
# S2補助ベンチ: median版・mean版の両方を出力して比較する（'both' / 'median' / 'mean'）
DISPLAY_S2_AGG = "both"

# ★Fig1(asset)・Fig2 で共有する代表ch固定（決定論・毎run不変）。
#   ※第6版: Fig4 の候補選定はこれとは切り離す（bimodality上位を全出力してユーザーが選ぶ）。
REPR_CH = "260626_ch4"
# ★代表(main)として出力する図の指定。ここで指定した1枚だけを本文用(main)に出し、
#   同じ図の他の候補は exploratory サブフォルダに回す。これは「どれを代表とするか」という
#   識別子(設定値)であり測定値ではない。存在しない指定は legacy stage2 がログを出して無視する。
FIG1_MAIN_CH = "260626_ch4"      # Fig1 代表チャンネル(REPR_CH と別に明示)
FIG1_MAIN_VARIANT = "high"       # Fig1 代表の窓variant(median/high/transition)
FIG4_MAIN_CH = "260626_ch6"      # Fig4 代表チャンネル
FIG4_MAIN_MODE = "restcount"     # Fig4 代表の描画モード(condnorm/global/restdens/restcount)

# ★第7版 Fig4a: 順位選抜(bimodality上位N)とは別に、必ず描画するchを指定する。
#   QC非通過でも描画し、パネルとCSVにQC状態（par単独/多条件・par値・F1）を注記する。
#   【要確認】"7/2 pir3" は 260702_ch3 として解決できるが、"7/9" に対応する記録 260709 は
#   RECORDS_YOUNG に無い（対象は 260626 / 260629 / 260702 / 260706）。
#   260709 を解析対象に加えると N が変わり確定ゲートが全て動くため、ここでは追加しない。
#   7/6 の誤記であれば "260706_ch3" / "260706_ch6" に書き換えること。
#   存在しないchは legacy stage2 が「見つからない」と明示ログを出して読み飛ばす（捏造しない）。
FIG4_FORCE_CH = ["260702_ch3", "260706_ch3", "260706_ch6"]
# Fig4a の順位選抜（bimodality_coef 降順）で出す本数。
FIG4_N_CANDIDATES = 10

# =============================================================== 5. GMM
GMM_N_COMPONENTS = 2
GMM_RANDOM_STATE = 42  # ※fit_gmm() は random_state=42 をハードコード（この値と一致）
GMM_N_INIT = 1  # 既存実効値を宣言。stage1 は必ずこの値を参照
GMM_SEED_LIST = list(range(1, 21))  # S3: シード非依存性を実フィットで検証
N_PHASE_PERM = 1000  # R11/提案3: 位相シャッフル帰無分布の置換回数(seed=42固定)。p下限=1/(N+1)。
#   本文の主張は個体単位(N=8)。チャンネル別pのBH補正はSupplementary用。
# 累積データ要件（S4: 学習曲線を実計算）
CUM_ACTIVE_BIN_GRID = [5, 10, 15, 20, 25, 30, 35, 40, 50, 60,
                       80, 100, 150, 200, 300, 400, 500]

# =============================================================== 6. センサー
# ★SetA/SetB の識別子。sensor_id（X1〜X8 / Y1〜Y8）の先頭1文字で判定する。
#   これは「どちらの群をAと呼ぶか」という命名の宣言であり測定値ではない。
#   ファイル名の連番署名は int_channel.sensor_set_sig に併記して照合可能にする。
SENSOR_SET_ORDER = ["X", "Y"]

# =============================================================== 7. 生波形(Fig1)
# ★第6版: stage1 が int_raw_trace.csv に保存する窓長。60 → 300 秒に延長。
#   この窓は描画専用（PAI/GMM/F1/強度r の計算には一切使われない）＝確定ゲート不変。
RAW_WINDOW_S = 150
# legacy stage2 は保存窓を丸ごと描くため実質未使用（互換のため残置）。
RAW_DRAW_WINDOW_S = 150
# ★第6版: Fig1 から NanoTag を削除。
FIG1_SHOW_NANOTAG = False

# ★第7版: Fig1の窓の選び方（stage1が int_raw_trace.variant に出す）。
#   median     … 従来と同一（active/rest それぞれ median-PAI のビン）。既存Fig1の再現性を保証。
#   high       … active=最大PAIビン / rest=最小PAIビン。活動差が最も大きい区間。
#   transition … rest→active の切替（PAI跳躍が最大の箇所）。変化そのものを見せる区間。
#   ※ どれを本文Fig1にするかは出力を見てユーザーが選ぶ（legacy stage2は全部出す）。
RAW_TRACE_VARIANTS = ["median", "high", "transition"]
# transition窓を切替の何ビン(=60s)手前から始めるか。2なら切替の2分前から。
RAW_TRACE_TRANSITION_LEAD_BINS = 2
# ★Fig1候補を REPR_CH 以外のchでも保存したい場合に ch_id を列挙する（例 "260702_ch3"）。
#   空リストなら REPR_CH のみ。ここに足しても計算結果（ゲート）は変わらない
#   （int_raw_trace は描画専用で PAI/GMM/F1/強度r には一切使われないため）。
#   第8版: Fig1 を Fig4 のように複数候補にするため、Fig4a で強制描画する3chを明示指定する。
#   これらは RECORDS_YOUNG（260626/260629/260702/260706）内に実在するため N もゲートも不変。
#   各chについて RAW_TRACE_VARIANTS の3通り（median/high/transition）が保存され、
#   legacy stage2 が (ch × variant) ごとに Fig1 を1枚ずつ描く。REPR_CH(260626_ch4) も従来どおり出力される。
RAW_TRACE_EXTRA_CH = ["260702_ch3", "260706_ch3", "260706_ch6"]

# =============================================================== 8. 探索計算 X1-X10
# 既定 True の軽量ブロック（既存中間物の再集計中心・数分）
RUN_SUPPLEMENTARY = True  # 既存: bin掃引 / Welch特徴 / 概日lv24
RUN_EXPLORATORY = True  # X2-X10

# ★X1 LPFカットオフ掃引は重い（全chのstate計算を約4セット＝+40〜60分）。
#   int_lpf_sweep.csv が既に存在する場合は FORCE=False なら再計算をスキップする。
RUN_LPF_SWEEP = False
FORCE_LPF_SWEEP = False
LPF_SWEEP_HZ = [0.5, 1.0, 2.0, 5.0]

# X8: 暗期定義の感度（時間シフト）
DARK_DEF_SHIFTS = [-1, 0, 1]

# X3: AUC差(par vs SNR)のブートストラップ（個体クラスタ復元抽出）
AUC_BOOT_N = 5000
AUC_BOOT_SEED = 7

# X4: 状態分類ベースライン比較で使う固定閾値の分位点（GMM不使用の素朴手法）
BASELINE_FIXED_QUANTILE = 0.5
LABEL_NB_SWEEP = [1, 2, 3]
SESSION_DIAGNOSTIC_RECORD = "260702"
SESSION_BLOCK_HOURS = 12
ADC_RANGE_OUTLIER_V = 2.0
BCa_N_RESAMPLES = 10000
BCa_RANDOM_STATE = 2024

# --- v3: session-trend / temporal-stability diagnostics (declared inputs, not results) ---
SESSION_STABLE_LOW_COHORT_MARGIN = 0.15
SESSION_TREND_DELTA_THRESHOLD = 0.10
SESSION_BLOCK_MIN_PAI_FRAC = 0.95
SESSION_BLOCK_MIN_NANO_FRAC = 0.50
TEMPORAL_PAR_SATURATION_THRESHOLD = 0.95
TEMPORAL_PAI_REST_JUMP_THRESHOLD = 2.0
TEMPORAL_PAR_RANGE_THRESHOLD = 0.50

# =============================================================== 9. レコード
# 若齢30Hzのみ。老齢10Hz予備データは論文対象外（空固定・stage1で在庫チェック）。
RECORDS_YOUNG = ["260626", "260629", "260702", "260706"]
RECORDS_OLD = []

# =============================================================== 10. 出力
FIG_DPI = 600

# PAPER_VALUES.md audit export.  These are report-size / ordering settings only.
PAPER_VALUES_MAX_CHARS = 1_200_000
PAPER_VALUES_PRIORITY = [
    "int_session_timecourse", "int_session_summary", "int_session_2x2",
    "int_session_exclusion", "int_channel_stability",
    "int_state_baseline", "int_holdout_f1", "int_label_sweep",
    "int_qc_corr", "int_qc_confusion", "int_qc_anatomy",
    "int_gmm_params", "int_bootstrap_ci", "int_auc_metrics_cluster",
    "int_permouse_values", "int_loso_thr", "int_good_sensitivity",
    "int_nanotag_integrity", "int_filter_mode_compare", "int_error_bydist_perch",
]
# Always summarize these large/redundant tables instead of embedding every row.
PAPER_VALUES_SUMMARY_ONLY = [
    "int_bin_coverage.csv", "int_binned.csv", "int_calibration.csv",
    "int_auc_boot_draws.csv", "int_placebo_pairs.csv", "int_bland_altman_pairs.csv",
]

# =============================================================== パス解決
PIPELINE_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PIPELINE_ROOT)
BASE_DATA_DIR = r"C:\path\to\data"
ANALYSIS_OUTPUTS_DIR = ""
INTERMEDIATE_DIR = ""
OUTPUTS_DIR = ""
FIGURES_DIR = ""
TABLES_DIR = ""
MAPPING_CSV_PATH = ""


def update_paths(base_dir):
    global \
        BASE_DATA_DIR, \
        ANALYSIS_OUTPUTS_DIR, \
        INTERMEDIATE_DIR, \
        OUTPUTS_DIR, \
        FIGURES_DIR, \
        TABLES_DIR, \
        MAPPING_CSV_PATH
    BASE_DATA_DIR = base_dir
    ANALYSIS_OUTPUTS_DIR = os.path.join(BASE_DATA_DIR, "paper_pipeline_outputs")
    INTERMEDIATE_DIR = os.path.join(ANALYSIS_OUTPUTS_DIR, "intermediate")
    OUTPUTS_DIR = os.path.join(ANALYSIS_OUTPUTS_DIR, "outputs")
    FIGURES_DIR = os.path.join(OUTPUTS_DIR, "figures")
    TABLES_DIR = os.path.join(OUTPUTS_DIR, "tables")
    MAPPING_CSV_PATH = os.path.join(ANALYSIS_OUTPUTS_DIR, "mapping.csv")


update_paths(os.environ.get("SENSORS_BASE_DATA_DIR", r"C:\path\to\data"))


# =============================================================== 設定の自己申告
def settings_report():
    """REVIEW.txt / stage1 print 用。設定値（＝測定値ではない）を明示的に開示する。"""
    return [
        "[config settings — declared inputs, NOT measured results]",
        f"  FS={FS} Hz  DARK_HOURS={DARK_HOURS}  BIN_STATE={BIN_STATE}  BIN_INTENSITY={BIN_INTENSITY}",
        f"  NANOTAG_RESOLUTION_SEC={NANOTAG_RESOLUTION_SEC}",
        f"  LOWPASS_CUTOFF_HZ={LOWPASS_CUTOFF_HZ}  LOWPASS_ORDER={LOWPASS_ORDER}  (sweep: {LPF_SWEEP_HZ})",
        f"  GMM_N_COMPONENTS={GMM_N_COMPONENTS}  GMM_RANDOM_STATE={GMM_RANDOM_STATE}  GMM_N_INIT={GMM_N_INIT}",
        f"  QC1_GOOD_F1={QC1_GOOD_F1}  GOOD_CUT_SWEEP={GOOD_CUT_SWEEP}  VERSIONS={GOOD_CUT_VERSIONS}",
        f"  LABEL_NB_SWEEP={LABEL_NB_SWEEP}  SESSION_BLOCK_HOURS={SESSION_BLOCK_HOURS}  ADC_RANGE_OUTLIER_V={ADC_RANGE_OUTLIER_V}",
        f"  SESSION_TREND: low_margin={SESSION_STABLE_LOW_COHORT_MARGIN}  delta={SESSION_TREND_DELTA_THRESHOLD}",
        f"  SESSION_BLOCK: min_pai_frac={SESSION_BLOCK_MIN_PAI_FRAC}  min_nano_frac={SESSION_BLOCK_MIN_NANO_FRAC}",
        f"  TEMPORAL_QC: par_saturation>={TEMPORAL_PAR_SATURATION_THRESHOLD}  rest_jump>={TEMPORAL_PAI_REST_JUMP_THRESHOLD}  par_range>={TEMPORAL_PAR_RANGE_THRESHOLD}",
        f"  PAPER_VALUES_MAX_CHARS={PAPER_VALUES_MAX_CHARS}  PRIORITY_N={len(PAPER_VALUES_PRIORITY)}",
        f"  QC1_MULTI_SNR_MIN={QC1_MULTI_SNR_MIN}  QC1_MULTI_GMM_SEP_MIN={QC1_MULTI_GMM_SEP_MIN}",
        f"  QC_RULE_KEYS={QC_RULE_KEYS}",
        f"  PAR_THRESHOLD_SWEEP={PAR_THRESHOLD_SWEEP[0]}..{PAR_THRESHOLD_SWEEP[-1]} (n={len(PAR_THRESHOLD_SWEEP)})",
        f"  SENSOR_SET_ORDER={SENSOR_SET_ORDER}  (SetA={SENSOR_SET_ORDER[0]}, SetB={SENSOR_SET_ORDER[1]})",
        f"  REPR_CH={REPR_CH}",
        f"  RAW_WINDOW_S={RAW_WINDOW_S} (stored)  RAW_DRAW_WINDOW_S={RAW_DRAW_WINDOW_S} (drawn)"
        f"  FIG1_SHOW_NANOTAG={FIG1_SHOW_NANOTAG}",
        f"  RAW_TRACE_VARIANTS={RAW_TRACE_VARIANTS}  "
        f"TRANSITION_LEAD_BINS={RAW_TRACE_TRANSITION_LEAD_BINS}  "
        f"RAW_TRACE_EXTRA_CH={RAW_TRACE_EXTRA_CH}",
        f"  FIG4_FORCE_CH={FIG4_FORCE_CH}  FIG4_N_CANDIDATES={FIG4_N_CANDIDATES}",
        f"  DISPLAY: r={DISPLAY_R_AGG}  F1={DISPLAY_F1_AGG}  S2={DISPLAY_S2_AGG}",
        f"  RECORDS_YOUNG={RECORDS_YOUNG}  RECORDS_OLD={RECORDS_OLD}",
        f"  RUN_SUPPLEMENTARY={RUN_SUPPLEMENTARY}  RUN_EXPLORATORY={RUN_EXPLORATORY}  "
        f"RUN_LPF_SWEEP={RUN_LPF_SWEEP} (force={FORCE_LPF_SWEEP})",
    ]
