# VALUE_PROVENANCE — 数値の出所対応表 / Value-to-source map

**English summary.** This table maps each decimal value printed in the article and in the
Supplementary Materials (final versions of 2026-10-06) to the file and column in this repository
from which it is computed, and to the aggregation used. Locations follow the numbering of the
article (main-text sections §, Figures and Tables; Supplementary Figures S, Tables S and Text S).
File names such as `TableS1.csv` are the names emitted by the frozen code; their numbers in the
article are given in `NOTES.md` (Section 1). "文献値" marks a value quoted from a cited work,
"…内で導出" a value computed from other values in the same passage. Integer counts (bins, channels,
pairs, folds) and integer percentages are not listed. Judgement: ✓ source confirmed;
▲ see the note in the row.

## 表について

- 対象は、論文の最終版（本文・補足資料、2026-10-06）に現れる小数を含む値（374 行）。件数（整数）と整数のパーセントは含まない。
- 「出現箇所」は論文の番号で示す（本文の節 §・Figure・Table、補足資料の Figure S・Table S・Text S）。
- 「出所」の `TableS*.csv` はコードが出力するファイル名で、論文の番号と一部異なる（`NOTES.md` の Section 1）。
  これらの行は、README の手順で再生成した表 CSV の該当セルと照合した。
- 同じ数字が別の量として複数箇所に現れる場合は、量ごとに行を分けた（例：0.0014、0.0194、0.8210、0.9172）。
- 判定：✓ 出所確定 ／ ▲ 要注意（行内の注記を参照）。

| 値 | 出現箇所 | 出所 | 集約 | 判定 |
|---|---|---|---|---|
| -23.03 | 本文§3.7, 本文§4.6 | int_calibration_60s_summary.csv[channel_median_min] | 空箱 60 秒ビンの ch 別中央値の最小（−23.0259。260629_ch6 と 260702_ch6） | ✓ |
| -23.026 | 本文§2.6.1, 本文§3.7, SM Text S2.6 | 定数 ln(ε)、ε = 1e-10（数値安定化定数） | −23.02585（PAI の下限） | ✓ |
| -14.18 | 本文§3.7 | int_calibration_60s_summary.csv[channel_median_mean] | 空箱 60 秒ビン（セット A 33 個、セット B 39 個）の ch 別中央値の平均（32 ch） | ✓ |
| -13.71 | SM Figure S1 | figure_values_good070.csv[figS1_median_empty] | 空箱 10 分ビンの中央値（n = 128） | ✓ |
| -13.2798 | 本文§3.4, 本文 Figure 4 | int_channel.csv[nano_rest_mu_mean] | 生値（260626_ch6） | ✓ |
| -13.2364 | 本文§3.4, 本文 Figure 4 | int_channel.csv[gmm_rest_mu] | 生値（ch=260626_ch6） | ✓ |
| -12.93 | SM Figure S1 | figure_values_good070.csv[figS1_median_active_rest] | 占有 Rest 10 分ビンの中央値（n = 172） | ✓ |
| -10.67 | 本文§3.7, 本文§4.6 | int_calibration_60s_summary.csv[channel_median_max] | 空箱 60 秒ビンの ch 別中央値の最大（−10.6674） | ✓ |
| -10.09 | SM Figure S1 | figure_values_good070.csv[figS1_median_active_move] | 占有 Active 10 分ビンの中央値（n = 6,692） | ✓ |
| -1.2471 | 本文§3.6 | int_bland_altman.csv[bias] | 最小（16 ペア） | ✓ |
| -0.372 | 本文 Table 3 | int_qc_anatomy.csv[par_minus_true] | 生値（260629_ch3） | ✓ |
| -0.29 | 本文§3.6 | int_sensor_retest.csv[icc2_1] | metric = intensity_r の行（−0.2868） | ✓ |
| -0.280 | 本文 Table 3 | int_channel.csv[pir_active_rate] − [nanotag_active_rate] ／ int_qc_anatomy.csv[par_minus_true] | 生値（260706_ch4、−0.2802） | ✓ |
| -0.151 | 本文 Table 3 | int_channel.csv[pir_active_rate] − [nanotag_active_rate] | 生値（260702_ch8、−0.1509） | ✓ |
| -0.10 | 本文§3.6 | int_sensor_retest.csv[spearman] | metric = intensity_r の行（−0.0952） | ✓ |
| -0.0372 | 本文§3.3 | int_placebo_pairs.csv[placebo_r] | same_session=True（n=96）の最小 | ✓ |
| < 0.0001 | 本文§3.4 | int_seed_stability.csv[rest_mu]（bin_sec = 60） ／ int_seed_state_stability.csv[f1_state] | ch ごとシード間 SD の中央値（Rest 成分平均 0.000016、state F1 0.000000） | ✓ |
| 0.0002 | 本文§4.6 | int_channel.csv[noise_sigma] | 最小（260629_ch6、0.000245 V） | ✓ |
| 0.0002 | SM Figure S3 | int_seed_stability.csv[rest_mu]（bin_sec = 60） | シードごとに 32 ch の Rest 成分平均を平均し、そのシード間 SD（0.000165） | ✓ |
| 0.0005 | SM Figure S3 | int_seed_stability.csv[active_mu]（bin_sec = 60） | シードごとに 32 ch の Active 成分平均を平均し、そのシード間 SD（0.000544） | ✓ |
| 0.001 | 本文§3.3 | int_channel.csv[phase_shuffle_p] | config.N_PHASE_PERM=1000 による下限 1/1001=0.000999 | ✓ |
| 0.0010 | 本文§3.4 | int_seed_state_stability.csv[pir_active_rate] | ch ごとシード間 SD の最大（0.001030） | ✓ |
| 0.0012 | 本文§3.4 | int_seed_state_stability.csv[f1_state] | ch ごとシード間 SD の最大（0.001166） | ✓ |
| 0.0014 | 本文§3.1 | int_channel.csv[F1_state_band12] | 平均（1–2 Hz 帯、対数変換なし） | ✓ |
| 0.0014 | 本文§3.3, 本文§5, SM Table S2 | TableS6.csv[Point estimate]（Random-permutation control r の行） | セル値 | ✓ |
| 0.0030 | 本文§3.1, SM Figure S1 | int_channel.csv[F1_state_rawvar] | 平均（個体平均の平均も同値） | ✓ |
| 0.0040 | 本文§3.4 | int_seed_stability.csv[rest_mu]（bin_sec = 60） | ch ごとシード間 SD の最大（260629_ch1、0.003985） | ✓ |
| 0.01 | 本文§2.3, 本文§3.7, 本文§4.6, 本文§4.7, 本文 Table 1, SM Text S2.6 | int_adc_diagnostic.csv[smallest_step] ／ 記録設定（LabVIEW、小数 2 桁で保存） | 全 32 ch で 0.01（記録分解能） | ✓ |
| 0.0139 | 本文§3.6 | int_sensor_swap.csv[abs_diff_r] | mouse_3 を除いた 7 個体の平均 | ✓ |
| 0.0142 | SM Table S4 | TableS4.csv[SD]（260626 の行） / TableS4.csv[Slope (per day)]（260626 の行） | セル値 | ✓ |
| 0.0171 | 本文§3.4 | int_seed_state_stability.csv[gmm_boundary] | ch ごとシード間 SD の最大（0.017147） | ✓ |
| 0.0194 | SM Text S2.7 | int_channel.csv[pir_active_rate] − [nanotag_active_rate] | 生値（260629_ch8） | ✓ |
| 0.0194 | 本文§3.5, SM Figure S6, SM Text S1.3, SM Text S2.2 | int_loso_thr.csv[qc1_threshold] | fold 間 SD（8 fold、不偏 SD） | ✓ |
| 0.0248 | SM Table S4 | TableS4.csv[Slope (per day)]（260702 の行） | セル値 | ✓ |
| 0.0255 | SM Table S4 | TableS4.csv[SD]（260702 の行） | セル値 | ✓ |
| 0.0284 | SM Table S4 | TableS4.csv[Delta (last - first)]（260626 の行） | セル値 | ✓ |
| 0.0285 | 本文§3.6 | int_sensor_swap.csv[abs_diff_r] ／ int_sensor_retest.csv[abs_diff_mean] | 8 個体の平均 | ✓ |
| 0.0363 | SM Table S4 | TableS4.csv[Slope (per day)]（260629 の行） | セル値 | ✓ |
| 0.0434 | 本文§3.4, 本文 Figure 4 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値（ch=260626_ch6） | ✓ |
| 0.0471 | SM Table S4 | TableS4.csv[SD]（260629 の行） | セル値 | ✓ |
| 0.0496 | SM Table S4 | TableS4.csv[Delta (last - first)]（260702 の行） | セル値 | ✓ |
| 0.0510 | SM Table S4 | TableS4.csv[Slope (per day)]（260706 の行） | セル値 | ✓ |
| 0.0579 | 本文§3.4 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値の中央値（QC 通過 15 ch） | ✓ |
| 0.0699 | 本文§3.1 | int_channel.csv[F1_state_band25] | 平均（個体平均の平均も同値） | ✓ |
| 0.0714 | 本文§3.4, 本文§4.5, 本文 Figure 4 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値の中央値（全 32 ch） | ✓ |
| 0.0722 | SM Table S4 | TableS4.csv[SD]（260706 の行） | セル値 | ✓ |
| 0.0726 | SM Table S4 | TableS4.csv[Delta (last - first)]（260629 の行） | セル値 | ✓ |
| 0.0864 | 本文§3.5 | int_auc_boot.csv[diff_ci_lower] | comparison=pir_active_rate - snr の生値 | ✓ |
| 0.0886 | 本文§3.1 | int_feature_bench.csv[mean_r] | 生値（feature = band_5_15Hz。stage3 の表示名は High-Pass (>5Hz)） | ✓ |
| 0.1 | SM Text S1.1 | 文献値（[18]） | 焦電素子の公称周波数応答の極大（Hz） | ✓ |
| 0.1020 | SM Table S4 | TableS4.csv[Delta (last - first)]（260706 の行） | セル値 | ✓ |
| 0.108 | 本文§3.1 | 本文§3.1 内で導出 | 0.6840 − 0.5758（int_channel.csv[F1_state] − [F1_state_logvar_nolpf] の個体平均の差、0.1081） | ✓ |
| 0.1132 | 本文§3.3 | int_placebo_pairs.csv[placebo_r] | same_session=True（n=96）の中央値 | ✓ |
| 0.1296 | SM Text S2.7 | int_channel.csv[pir_active_rate] − [nanotag_active_rate] | 生値（260629_ch6） | ✓ |
| 0.1468 | SM Table S5 | TableS3.csv[par]（260702_ch2 の行） | セル値 | ✓ |
| 0.1491 | 本文 Abstract, 本文§3.3, 本文§5, SM Table S2 | TableS6.csv[Point estimate]（Mismatched-pairing control r の行） | セル値 | ✓ |
| 0.15 | SM Text S2.2 | config.py PAR_THRESHOLD_SWEEP | 設定値（掃引下限） | ✓ |
| 0.1660 | 本文§3.5, 本文 Figure 5, 本文 Table 3, SM Text S2.1 | int_auc_metrics_cluster.csv[auc_observed] | metric=gmm_separation の生値 | ✓ |
| 0.1678 | SM Table S5 | TableS3.csv[par]（260626_ch3 の行） | セル値 | ✓ |
| 0.1708 | SM Text S2.3 | int_error_bydist_perch.csv[n, n_error] | 距離帯 >3：個体ごとに n_error と n を合算した誤り率の 8 個体平均 | ✓ |
| 0.1731 | SM Table S5 | TableS3.csv[par]（260702_ch6 の行） | セル値 | ✓ |
| 0.1750 | SM Table S5, SM Table S6 | TableS1.csv[LOMO threshold (par)]（0.55 の行） / TableS3.csv[par]（260629_ch7 の行） / TableS3.csv[par]（260702_ch1 の行） | セル値 | ✓ |
| 0.1769 | SM Table S5 | TableS3.csv[par]（260706_ch7 の行） | セル値 | ✓ |
| 0.1806 | SM Text S2.7 | int_channel.csv[pir_active_rate] − [nanotag_active_rate] ／ int_qc_anatomy.csv[par_minus_true] | 生値（260706_ch5） | ✓ |
| 0.181 | 本文 Table 3 | int_channel.csv[pir_active_rate] − [nanotag_active_rate] ／ int_qc_anatomy.csv[par_minus_true] | 生値（260706_ch5、0.1806） | ✓ |
| 0.1965 | SM Table S5 | TableS3.csv[par]（260702_ch4 の行） | セル値 | ✓ |
| 0.1968 | SM Table S1, SM Table S5 | TableS2.csv[Sweep threshold (Youden)]（3 の行） / TableS3.csv[par]（260626_ch8 の行） | セル値 | ✓ |
| 0.2 | 本文§4.4 | 文献値（[10] RAD） | 歩行を伴わない行動との R²（< 0.2） | ✓ |
| 0.2046 | SM Table S1, SM Table S5 | TableS2.csv[Sweep threshold (Youden)]（2 の行） / TableS3.csv[par]（260626_ch7 の行） | セル値 | ✓ |
| 0.2133 | SM Table S6 | TableS1.csv[LOMO threshold (par)]（0.6 の行） | セル値 | ✓ |
| 0.2201 | SM Table S5 | TableS3.csv[par]（260706_ch6 の行） | セル値 | ✓ |
| 0.2238 | SM Table S5 | TableS3.csv[par]（260702_ch5 の行） | セル値 | ✓ |
| 0.2316 | 本文§3.1 | int_channel.csv[F1_state_band515] | 平均（個体平均の平均も同値） | ✓ |
| 0.2357 | 本文§3.1 | int_channel.csv[F1_state_band01] | 平均（個体平均の平均も同値） | ✓ |
| 0.2544 | SM Table S5 | TableS3.csv[par]（260702_ch7 の行） | セル値 | ✓ |
| 0.2602 | SM Table S5 | TableS3.csv[par]（260702_ch3 の行） | セル値 | ✓ |
| 0.2658 | SM Table S6 | TableS1.csv[LOMO threshold (par)]（0.65 の行） | セル値 | ✓ |
| 0.2674 | SM Table S5 | TableS3.csv[par]（260706_ch3 の行） | セル値 | ✓ |
| 0.2706 | SM Table S5 | TableS3.csv[par]（260629_ch5 の行） | セル値 | ✓ |
| 0.2757 | 本文§3.5, SM Figure S6, SM Table S1, SM Table S3, SM Table S5, SM Text S2.2 | int_loso_thr.csv[qc1_threshold] | 生値（6 fold で同値） | ✓ |
| 0.276 | 本文 Table 3 | int_channel.csv[pir_active_rate] | 生値（260702_ch8、0.2757） | ✓ |
| 0.2831 | SM Table S5 | TableS3.csv[par]（260629_ch4 の行） | セル値 | ✓ |
| 0.2852 | 本文§2.6.5, 本文§2.7.1, 本文§3.5, 本文 Figure 5, SM Figure S6, SM Figure S8, SM Table S1, SM Table S2, SM Table S3, SM Table S5, SM Table S6, SM Text S1.3, SM Text S2.2 | TableS1.csv[LOMO threshold (par)]（0.7 の行） / TableS6.csv[Point estimate]（QC threshold (par) の行） | セル値 | ✓ |
| 0.2981 | 本文§3.5, SM Table S3, SM Table S5, SM Text S2.2 | int_loso_thr.csv[qc1_threshold] | 生値（fold=mouse_8） | ✓ |
| 0.2996 | 本文§3.5 | int_auc_boot.csv[diff_observed] | comparison=pir_active_rate - snr の生値 | ✓ |
| 0.3 | 本文§2.2 | 文献値（[12] BISS0001） | 双方向レベル検出の下側閾値（0.3 Vdd） | ✓ |
| 0.3023 | SM Table S1 | int_channel.csv[pir_active_rate] | 平均（32 ch） | ✓ |
| 0.3275 | SM Table S5 | TableS3.csv[par]（260629_ch3 の行） | セル値 | ✓ |
| 0.328 | 本文 Table 3 | int_channel.csv[pir_active_rate] | 生値（Record 2 ch3） | ✓ |
| 0.3292 | 本文§3.5, SM Figure S6, SM Table S3, SM Table S5, SM Text S2.2 | int_loso_thr.csv[qc1_threshold] | 生値（fold=mouse_5、0.329155） | ✓ |
| 0.33 | 本文§4.2 | 文献値（[10] RAD） | 1 s ビンでの R² | ✓ |
| 0.3313 | SM Table S6 | TableS1.csv[LOMO threshold (par)]（0.75 の行） | セル値 | ✓ |
| 0.3355 | SM Table S1 | TableS2.csv[nar (mean)]（3 の行） | セル値 | ✓ |
| 0.344 | 本文 Table 3 | int_channel.csv[pir_active_rate] | 生値（Record 4 ch4） | ✓ |
| 0.3440 | SM Table S5 | TableS3.csv[par]（260706_ch4 の行） | セル値 | ✓ |
| 0.3463 | SM Table S5 | TableS3.csv[par]（260706_ch2 の行） | セル値 | ✓ |
| 0.35 | 本文§3.6 | int_bland_altman.csv[sd_diff] | 最小（0.3545） | ✓ |
| 0.3503 | SM Text S2.3 | int_error_bydist_perch.csv[n, n_error] | 距離帯 0–0.5：個体ごとに n_error と n を合算した誤り率の 8 個体平均（stage3 figS3 パネル c と同じ計算） | ✓ |
| 0.3505 | SM Table S5, SM Text S2.7 | TableS3.csv[par]（260626_ch5 の行） | セル値 | ✓ |
| 0.3538 | SM Table S5 | TableS3.csv[par]（260706_ch1 の行） | セル値 | ✓ |
| 0.3558 | SM Table S6 | TableS1.csv[LOMO threshold (par)]（0.8 の行） | セル値 | ✓ |
| 0.3694 | SM Text S2.3 | int_error_bydist_perch.csv[n, n_error] | 距離帯 0.5–1：個体ごとに n_error と n を合算した誤り率の 8 個体平均 | ✓ |
| 0.3699 | SM Table S5 | TableS3.csv[par]（260626_ch2 の行） | セル値 | ✓ |
| 0.3755 | 本文§3.4 | int_channel.csv[pir_active_rate] | 生値（ch=260626_ch6、0.375463） | ✓ |
| 0.3755 | SM Table S5 | TableS3.csv[par]（260626_ch6 の行） | セル値 | ✓ |
| 0.3777 | 本文§3.3 | int_placebo_pairs.csv[placebo_r] | same_session=True（n=96）の最大 | ✓ |
| 0.3796 | SM Table S5 | TableS3.csv[par]（260629_ch2 の行） | セル値 | ✓ |
| 0.3916 | SM Table S1 | TableS2.csv[nar (mean)]（2 の行） | セル値 | ✓ |
| 0.41 | 本文§2.6.5 | int_channel.csv[nanotag_active_rate] | 32 ch の最小（0.4060） | ✓ |
| 0.4153 | SM Table S5 | TableS3.csv[par]（260626_ch4 の行） | セル値 | ✓ |
| 0.4255 | SM Table S5 | TableS3.csv[par]（260629_ch8 の行） | セル値 | ✓ |
| 0.427 | 本文§3.5, 本文 Table 3 | int_channel.csv[nanotag_active_rate]（260702 の 8 ch） ／ int_session_mouse_control.csv[nanotag_active_rate_260702] | 最小（260702_ch8、0.4266） | ✓ |
| 0.4326 | 本文§3.1 | int_channel.csv[F1_state_logband12] | 平均（個体平均の平均も同値） | ✓ |
| 0.4421 | SM Table S5 | TableS3.csv[par]（260629_ch1 の行） | セル値 | ✓ |
| 0.45 | SM Text S2.2 | config.py PAR_THRESHOLD_SWEEP | 設定値（掃引上限） | ✓ |
| 0.468 | 本文§3.5, 本文 Table 3 | int_channel.csv[nanotag_active_rate] | 生値（Record 4 ch5） | ✓ |
| 0.4684 | SM Text S2.7 | int_channel.csv[nanotag_active_rate] | 生値（260706_ch5） | ✓ |
| 0.4716 | 本文§2.6.2, 本文§4.3, SM Table S1 | TableS2.csv[nar (mean)]（1 の行） | セル値 | ✓ |
| 0.474 | 本文§3.5 | int_channel.csv[nanotag_active_rate]（260702 の 8 ch） | 最大（0.4741） | ✓ |
| 0.4822 | 本文§3.1 | int_channel.csv[F1_state_logband25] | 平均（個体平均の平均も同値） | ✓ |
| 0.4831 | 本文§3.1 | int_feature_bench.csv[mean_r] | 生値（feature = band_2_5Hz） | ✓ |
| 0.4982 | SM Table S5 | TableS3.csv[State F1]（260702_ch2 の行） | セル値 | ✓ |
| 0.5 | 本文§3.1, 本文 Data Availability, SM Figure S1 | config.py LPF_SWEEP_HZ | 設定値（カットオフ掃引 0.5 / 1.0 / 2.0 / 5.0 Hz） | ✓ |
| 0.5 | SM Text S1.3 | stage1_compute.py（floor_rate の定義） | 設定値（floor_rate = 生分散の対数が ch 最小値 + 0.5 以下となる 60 秒ビンの割合 %） | ✓ |
| 0.50 | SM Text S2.5 | config.py TEMPORAL_PAR_RANGE_THRESHOLD | 設定値（補助的な範囲基準。int_qc_temporal_compare.csv[temporal_pass] には含まれるが、論文の時間分解ガード（stage2 の Table S5 生成：飽和またはフロアシフト）には含めない） | ✓ |
| 0.5128 | SM Table S4 | TableS4.csv[Detection ratio, block 1]（260702 の行） | セル値 | ✓ |
| 0.5243 | SM Table S5 | TableS3.csv[State F1]（260702_ch6 の行） | セル値 | ✓ |
| 0.5273 | SM Table S4 | TableS4.csv[Detection ratio, block 2 (mid)]（260702 の行） | セル値 | ✓ |
| 0.529 | SM Text S2.4 | SM Text S2.4 内で導出 | PPV 7/8 の Wilson 95% CI 下限（0.5291） | ✓ |
| 0.5292 | 本文§3.5 | int_auc_boot.csv[diff_ci_upper] | comparison=pir_active_rate - snr の生値 | ✓ |
| 0.5334 | 本文§3.1 | int_channel.csv[F1_state_logband515] | 平均（個体平均の平均も同値） | ✓ |
| 0.5341 | SM Table S4 | TableS4.csv[Mean]（260702 の行） | セル値 | ✓ |
| 0.5420 | SM Table S5 | TableS3.csv[State F1]（260626_ch3 の行） | セル値 | ✓ |
| 0.548 | SM Text S2.4 | SM Text S2.4 内で導出 | PPV 12/15 の Wilson 95% CI 下限（0.5481） | ✓ |
| 0.55 | 本文§2.6.5, 本文§3.5, SM Table S6, SM Text S2.4 | TableS1.csv[good definition (state F1 >=)] | 掃引下限（表の最小行） | ✓ |
| 0.5624 | SM Table S4 | TableS4.csv[Detection ratio, block 3]（260702 の行） | セル値 | ✓ |
| 0.5631 | SM Table S5 | TableS3.csv[State F1]（260629_ch4 の行） | セル値 | ✓ |
| 0.5646 | SM Table S5 | TableS3.csv[State F1]（260706_ch7 の行） | セル値 | ✓ |
| 0.5648 | SM Table S5 | TableS3.csv[State F1]（260702_ch1 の行） | セル値 | ✓ |
| 0.5702 | SM Table S5 | TableS3.csv[State F1]（260706_ch3 の行） | セル値 | ✓ |
| 0.573 | 本文§3.1 | 本文§3.1 内で導出 | 0.5758 − 0.0030（[F1_state_logvar_nolpf] − [F1_state_rawvar] の個体平均の差、0.5729） | ✓ |
| 0.574 | 本文 Table 3 | int_channel.csv[F1_state] | 生値（Record 2 ch3） | ✓ |
| 0.5744 | SM Table S5 | TableS3.csv[State F1]（260629_ch3 の行） | セル値 | ✓ |
| 0.5758 | 本文§3.1 | int_channel.csv[F1_state_logvar_nolpf] | 平均（個体平均の平均も同値） | ✓ |
| 0.5853 | SM Table S5 | TableS3.csv[State F1]（260702_ch4 の行） | セル値 | ✓ |
| 0.5880 | SM Table S5 | TableS3.csv[State F1]（260629_ch7 の行） | セル値 | ✓ |
| 0.5909 | 本文 Table 2 | int_permouse_values.csv[F1_state] | 生値（mouse_2） | ✓ |
| 0.5978 | 本文§3.5, SM Table S3 | TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_2 の行） | セル値 | ✓ |
| 0.5979 | SM Table S5 | TableS3.csv[par]（260629_ch6 の行） | セル値 | ✓ |
| 0.60 | SM Table S6, SM Text S2.4 | TableS1.csv[good definition (state F1 >=)]（0.6 の行） | セル値 | ✓ |
| 0.61 | 本文§4.4 | 文献値（[10] RAD） | 歩行との R² | ✓ |
| 0.6152 | 本文§3.5, 本文 Table 2 | Table2.csv[State F1 (QC-passing channels)]（int_channel.csv[F1_state] の qc1_pass = 1 の個体平均） | mouse_2 の値 | ✓ |
| 0.6215 | SM Table S5 | TableS3.csv[State F1]（260706_ch5 の行） | セル値 | ✓ |
| 0.622 | 本文 Table 3 | int_channel.csv[F1_state] | 生値（Record 4 ch5） | ✓ |
| 0.6235 | 本文§3.5, 本文 Figure 5 | int_auc_metrics_cluster.csv[auc_observed] | metric = snr の生値 | ✓ |
| 0.624 | 本文 Table 3 | int_channel.csv[nanotag_active_rate] | 生値（Record 4 ch4） | ✓ |
| 0.6271 | SM Table S5 | TableS3.csv[State F1]（260706_ch6 の行） | セル値 | ✓ |
| 0.6282 | SM Table S5 | TableS3.csv[State F1]（260702_ch5 の行） | セル値 | ✓ |
| 0.6312 | 本文§3.3, 本文§4.6 | int_channel.csv[intensity_r_lightonly] | 個体平均の平均 | ✓ |
| 0.6351 | 本文§3.1 | int_bin_sweep_agg.csv[f1_all_mean_of_means] | bin_sec = 300 の行（最小） | ✓ |
| 0.6382 | SM Table S5 | TableS3.csv[State F1]（260626_ch8 の行） | セル値 | ✓ |
| 0.6444 | SM Table S5 | TableS3.csv[State F1]（260626_ch7 の行） | セル値 | ✓ |
| 0.649 | 本文 Table 3, SM Text S2.5 | int_channel.csv[pir_active_rate] | 生値（260706_ch5、0.6490） | ✓ |
| 0.6490 | 本文§3.6, SM Table S5, SM Text S2.7, SM Text S2.5 | TableS3.csv[par]（260706_ch5 の行） | セル値 | ✓ |
| 0.65 | SM Table S6 | TableS1.csv[good definition (state F1 >=)]（0.65 の行） | セル値 | ✓ |
| 0.6516 | 本文§3.4, 本文§3.5, 本文 Figure 5, SM Table S2 | TableS6.csv[95% CI lower]（State F1 (all channels) の行） | セル値 | ✓ |
| 0.6526 | 本文§3.1 | int_bin_sweep_agg.csv[f1_all_mean_of_means] | bin_sec = 600 の行 | ✓ |
| 0.6558 | 本文 Table 2 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.656 | 本文 Table 3 | int_channel.csv[F1_state] | 生値（Record 4 ch4） | ✓ |
| 0.6560 | SM Table S5 | TableS3.csv[State F1]（260706_ch4 の行） | セル値 | ✓ |
| 0.6579 | 本文§3.7 | int_channel.csv[pir_active_rate, intensity_r] | 32 チャンネルの par と強度 r の Spearman 相関（0.657868） | ✓ |
| 0.66 | 本文§4.2 | 文献値（[10] RAD） | ホームケージ上方設置での R² | ✓ |
| 0.6655 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_1 の行） | セル値 | ✓ |
| 0.6690 | 本文 Table 2 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.6697 | 本文§3.1, SM Figure S1 | int_channel.csv[F1_state_logband01] | 平均（個体平均の平均も同値） | ✓ |
| 0.6709 | 本文 Table 2 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.6720 | SM Table S4 | TableS4.csv[Detection ratio, block 2 (mid)]（260706 の行） | セル値 | ✓ |
| 0.6729 | 本文§3.6, SM Figure S4, SM Text S2.7, SM Text S2.5 | int_channel.csv[intensity_r] | 生値（260706_ch5、最小） | ✓ |
| 0.673 | SM Text S2.5 | int_channel.csv[intensity_r] | 生値（260706_ch5、最小） | ✓ |
| 0.6760 | 本文 Table 2 | int_mouse.csv[mean_f1] | 生値（mouse_8） | ✓ |
| 0.6773 | SM Table S5 | TableS3.csv[State F1]（260629_ch5 の行） | セル値 | ✓ |
| 0.6793 | SM Table S4 | TableS4.csv[Mean of the other recordings]（260626 の行） | セル値 | ✓ |
| 0.6803 | SM Table S4 | TableS4.csv[Mean of the other recordings]（260629 の行） | セル値 | ✓ |
| 0.6814 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_4 の行） | セル値 | ✓ |
| 0.6825 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_3 の行） | セル値 | ✓ |
| 0.6840 | 本文§3.1, 本文§3.4, 本文§3.5, 本文§4.3, 本文 Figure 5, 本文 Table 2, SM Table S1, SM Table S2, SM Figure S1 | TableS2.csv[State F1 (mean of animal means)]（1 の行） / TableS6.csv[Point estimate]（State F1 (all channels) の行） | セル値 | ✓ |
| 0.6851 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_8 の行） | セル値 | ✓ |
| 0.6857 | SM Table S5 | TableS3.csv[State F1]（260702_ch3 の行） | セル値 | ✓ |
| 0.6858 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_7 の行） | セル値 | ✓ |
| 0.6861 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_6 の行） | セル値 | ✓ |
| 0.6862 | 本文§3.5, 本文 Figure 5 | int_auc_metrics_cluster.csv[auc_observed] | metric = floor_rate の生値 | ✓ |
| 0.6880 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_5 の行） | セル値 | ✓ |
| 0.6881 | 本文§3.1 | int_lpf_sweep_agg.csv[f1_qc_mean_of_means] | cutoff_hz = 5.0 の行 | ✓ |
| 0.6943 | SM Table S4 | TableS4.csv[Mean of the other recordings]（260706 の行） | セル値 | ✓ |
| 0.6944 | 本文 Table 2 | int_permouse_values.csv[F1_state] | 生値（mouse_3） | ✓ |
| 0.6973 | SM Table S3 | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_2 の行） | セル値 | ✓ |
| 0.6988 | SM Table S5 | TableS3.csv[State F1]（260702_ch7 の行） | セル値 | ✓ |
| 0.699 | 本文§3.5, 本文 Table 3 | int_channel.csv[nanotag_active_rate] | 生値（260629_ch3、0.6993） | ✓ |
| 0.6998 | 本文§3.5, 本文 Figure 5, SM Table S2 | TableS6.csv[95% CI lower]（State F1 (QC-passing channels) の行） | セル値 | ✓ |
| 0.7 | 本文§2.2 | 文献値（[12] BISS0001） | 双方向レベル検出の上側閾値（0.7 Vdd） | ✓ |
| 0.70 | 本文§2.6.5, 本文§3.5, 本文§4.6, 本文 Figure 5, SM Figure S7, SM Figure S8, SM Table S3, SM Table S6, SM Text S1.3, SM Text S2.4 | config.py QC1_GOOD_F1 | 設定値（good 定義の主基準） | ✓ |
| 0.7000 | SM Table S6 | TableS1.csv[Specificity]（0.6 の行） | セル値 | ✓ |
| 0.70 | 本文§2.6.5 | int_channel.csv[nanotag_active_rate] | 32 ch の最大（0.6993）。good 基準の 0.70 とは別の量 | ✓ |
| 0.7001 | SM Table S5 | TableS3.csv[State F1]（260626_ch5 の行） | セル値 | ✓ |
| 0.7017 | 本文 Table 2 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.7019 | SM Table S6 | TableS1.csv[State F1 after QC]（0.55 の行） | セル値 | ✓ |
| 0.7095 | SM Table S4 | TableS4.csv[Detection ratio, block 1]（260706 の行） | セル値 | ✓ |
| 0.7167 | SM Table S1 | TableS2.csv[State F1 (mean of animal means)]（2 の行） | セル値 | ✓ |
| 0.7192 | SM Table S4 | TableS4.csv[Detection ratio, block 1]（260629 の行） | セル値 | ✓ |
| 0.7215 | 本文§3.1 | int_bin_sweep_agg.csv[f1_qc_mean_of_means] | bin_sec = 300 の行 | ✓ |
| 0.722 | 本文 Table 3 | int_channel.csv[F1_state] | 生値（260702_ch8、0.7225） | ✓ |
| 0.7225 | 本文§3.5, SM Table S5 | int_channel.csv[F1_state] | 生値（Record 3 ch8） | ✓ |
| 0.7239 | 本文§3.1 | int_bin_sweep_agg.csv[f1_qc_mean_of_means] | bin_sec = 600 の行 | ✓ |
| 0.7310 | SM Table S4 | TableS4.csv[Mean]（260706 の行） | セル値 | ✓ |
| 0.7333 | SM Table S6 | TableS1.csv[Specificity]（0.65 の行） | セル値 | ✓ |
| 0.7339 | 本文§3.4, 本文§3.5, 本文 Figure 5, SM Table S2 | TableS6.csv[95% CI upper]（State F1 (all channels) の行） | セル値 | ✓ |
| 0.7356 | 本文§3.1 | int_lpf_sweep_agg.csv[f1_qc_mean_of_means] | cutoff_hz = 2.0 の行 | ✓ |
| 0.7361 | SM Table S1 | TableS2.csv[State F1 (mean of animal means)]（3 の行） | セル値 | ✓ |
| 0.7365 | 本文 Table 2, SM Table S3 | Table2.csv[State F1 (QC-passing channels)]（mouse_3） ／ TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_3 の行） | セル値 | ✓ |
| 0.7388 | SM Table S6, SM Text S2.4 | TableS1.csv[State F1 after QC]（0.6 の行） | セル値 | ✓ |
| 0.74 | 本文§4.2 | 文献値（[10] RAD） | ホームケージ側方設置での R² | ✓ |
| 0.7456 | SM Table S5 | TableS3.csv[State F1]（260626_ch1 の行） | セル値 | ✓ |
| 0.75 | SM Text S2.2 | int_qc_threshold_sweep.csv[PPV] | par_threshold = 0.28 の行 | ✓ |
| 0.75 | SM Table S6 | TableS1.csv[good definition (state F1 >=)] | 0.75 の行（good 定義の掃引値） | ✓ |
| 0.7500 | SM Table S6（表と注） | TableS1.csv[PPV]（0.75 の行） | セル値（9/12 を 4 桁で表示） | ✓ |
| 0.7562 | 本文§3.7, SM Table S2, SM Table S3, SM Text S2.2 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_6 の行） | セル値 | ✓ |
| 0.7571 | 本文§3.3 | int_channel.csv[intensity_r_trendrm_sym] | 個体平均の最小（mouse_3） | ✓ |
| 0.7599 | SM Table S4, SM Table S6 | TableS1.csv[State F1 after QC]（0.65 の行） / TableS4.csv[Mean of the other recordings]（260702 の行） | セル値 | ✓ |
| 0.7617 | SM Table S4 | TableS4.csv[Detection ratio, block 1]（260626 の行） | セル値 | ✓ |
| 0.7622 | SM Table S3 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_4 の行） | セル値 | ✓ |
| 0.7623 | 本文§4.3 | int_state_baseline.csv[f1_state] | method = median_split の個体平均の平均（fixed_quantile = 0.5 も同値） | ✓ |
| 0.7646 | SM Table S3 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_1 の行） | セル値 | ✓ |
| 0.7652 | 本文§3.1 | int_lpf_sweep_agg.csv[f1_qc_mean_of_means] | cutoff_hz = 0.5 の行 | ✓ |
| 0.7656 | 本文 Table 2, SM Table S3 | Table2.csv[State F1 (QC-passing channels)]（mouse_7） ／ TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_7 の行） | セル値 | ✓ |
| 0.7690 | SM Text S2.2 | int_qc_threshold_sweep.csv[f1_qc_post] | 生値 | ✓ |
| 0.7701 | SM Table S3 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_5 の行） | セル値 | ✓ |
| 0.7715 | 本文 Abstract, 本文§3.1, 本文§3.5, 本文§4.3, 本文§5, 本文 Figure 5, 本文 Table 2, SM Figure S6, SM Table S2, SM Table S3, SM Table S6, SM Text S2.2 | TableS1.csv[State F1 after QC]（0.7 の行） / TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_8 の行） / TableS6.csv[Point estimate]（State F1 (QC-passing channels) の行） | セル値 | ✓ |
| 0.7725 | SM Table S3 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_7 の行） | セル値 | ✓ |
| 0.7729 | SM Table S4 | TableS4.csv[Mean]（260629 の行） | セル値 | ✓ |
| 0.7739 | 本文§3.5, SM Figure S6, SM Table S3 | int_holdout_f1.csv[holdout_f1] | 平均 | ✓ |
| 0.7754 | SM Table S1, SM Table S4 | TableS2.csv[AUC (par)]（3 の行） / TableS4.csv[Detection ratio, block 2 (mid)]（260626 の行） | セル値 | ✓ |
| 0.7757 | SM Table S4 | TableS4.csv[Mean]（260626 の行） | セル値 | ✓ |
| 0.7764 | SM Text S2.2 | int_qc_threshold_sweep.csv[f1_qc_post] | 生値 | ✓ |
| 0.7773 | SM Table S3 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_3 の行） | セル値 | ✓ |
| 0.7801 | 本文§3.5, 本文 Table 2 | Table2.csv[State F1 (QC-passing channels)]（int_channel.csv[F1_state] の qc1_pass = 1 の個体平均） | mouse_5 の値 | ✓ |
| 0.7848 | SM Table S5 | TableS3.csv[State F1]（260706_ch8 の行） | セル値 | ✓ |
| 0.7883 | SM Table S6 | TableS1.csv[State F1 after QC]（0.75 の行） | セル値 | ✓ |
| 0.7895 | SM Table S6 | TableS1.csv[PPV]（0.65 の行） | セル値（15/19 を 4 桁で表示） | ✓ |
| 0.7896 | 本文§3.6, SM Text S2.7 | int_channel.csv[snr] | 最小（260706_ch5） | ✓ |
| 0.79 | SM Text S2.2 | int_qc_threshold_sweep.csv[PPV] | par_threshold=0.30 の行（0.7857） | ✓ |
| 0.790 | 本文 Table 3 | int_channel.csv[snr] | 生値（260706_ch5、0.7896） | ✓ |
| 0.7901 | SM Table S4 | TableS4.csv[Detection ratio, block 3]（260626 の行） | セル値 | ✓ |
| 0.7908 | 本文 Abstract, 本文§3.3, 本文§5, SM Table S2, SM Table S5 | TableS3.csv[State F1]（260706_ch2 の行） / TableS6.csv[Point estimate]（Residual intensity r (60-min envelope removed) の行） | セル値 | ✓ |
| 0.7919 | SM Table S4 | TableS4.csv[Detection ratio, block 3]（260629 の行） | セル値 | ✓ |
| 0.7975 | 本文§3.7, SM Table S2, SM Table S3, SM Text S2.2 | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_2 の行） | セル値 | ✓ |
| 0.7995 | 本文§4.3 | int_state_baseline.csv[f1_state] | method=median_split かつ QC 通過の個体平均 | ✓ |
| 0.80 | SM Text S2.2 | int_qc_threshold_sweep.csv[PPV] | par_threshold = 0.29 の行（0.8000） | ✓ |
| 0.80 | 本文§2.6.5, 本文§3.5, SM Table S6, SM Text S2.4 | TableS1.csv[good definition (state F1 >=)] | 掃引上限（表の最大行） | ✓ |
| 0.800 | SM Table S2（注）, SM Text S2.4 | TableS1.csv[PPV]（0.7 の行） | 陽性的中率 12/15 | ✓ |
| 0.8000 | 本文§3.5, SM Table S6（表と注。TableS1.csv[PPV] 0.7 の行と同値） | int_qc_threshold_sweep.csv[PPV]（par_threshold = 0.29 の行） | 運用閾値での陽性的中率 12/15 | ✓ |
| 0.8004 | SM Table S5 | TableS3.csv[State F1]（260706_ch1 の行） | セル値 | ✓ |
| 0.8042 | 本文§3.1 | int_bin_sweep_agg.csv[intensity_r_mean_of_means] | bin_sec = 60 の行 | ✓ |
| 0.8068 | 本文§3.6 | int_sensor_swap.csv[set1_r] | mouse_3 の行（セット A、0.806751） | ✓ |
| 0.8075 | SM Table S4 | TableS4.csv[Detection ratio, block 2 (mid)]（260629 の行） | セル値 | ✓ |
| 0.8085 | SM Table S5 | TableS3.csv[State F1]（260629_ch2 の行） | セル値 | ✓ |
| 0.8115 | SM Table S4 | TableS4.csv[Detection ratio, block 3]（260706 の行） | セル値 | ✓ |
| 0.8130 | 本文 Table 2, SM Table S3 | Table2.csv[State F1 (all channels)] と [State F1 (QC-passing channels)]（mouse_1） ／ TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_1 の行） | セル値 | ✓ |
| 0.8141 | 本文§3.5, 本文 Figure 5, SM Table S2 | TableS6.csv[95% CI upper]（State F1 (QC-passing channels) の行） | セル値 | ✓ |
| 0.8146 | 本文§3.5, SM Table S3, SM Table S5 | TableS3.csv[State F1]（260626_ch2 の行） / TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_5 の行） | セル値 | ✓ |
| 0.8210 | 本文§3.1 | int_feature_bench.csv[mean_r] | 生値（feature = band_1_2Hz） | ✓ |
| 0.8210 | 本文§3.3 | int_channel.csv[intensity_r_trendrm_sym] | 個体平均の最大（mouse_4） | ✓ |
| 0.8241 | SM Table S6, SM Text S2.4 | TableS1.csv[State F1 after QC]（0.8 の行） | セル値 | ✓ |
| 0.8254 | 本文 Figure 5, SM Table S2 | TableS6.csv[95% CI lower]（AUC (par) の行） | セル値 | ✓ |
| 0.8270 | 本文 Table 2, SM Table S3 | Table2.csv[State F1 (QC-passing channels)]（mouse_4） ／ TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_4 の行） | セル値 | ✓ |
| 0.8312 | 本文§3.4 | int_channel.csv[F1_state] | 生値（ch=260626_ch6、0.831205） | ✓ |
| 0.8312 | SM Table S5 | TableS3.csv[State F1]（260626_ch6 の行） | セル値 | ✓ |
| 0.8340 | 本文 Figure 5 | 本文 Figure 5 キャプション内で導出 | 1 − 0.1660（GMM 分離度の AUC） | ✓ |
| 0.8421 | SM Table S6 | TableS1.csv[Specificity]（0.7 の行） | セル値 | ✓ |
| 0.8462 | SM Table S1 | TableS2.csv[AUC (par)]（2 の行） | セル値 | ✓ |
| 0.8515 | 本文§3.4, SM Table S5, SM Text S2.6 | int_channel.csv[F1_state] | 生値（Record 2 ch6） | ✓ |
| 0.8524 | SM Table S5 | TableS3.csv[State F1]（260629_ch1 の行） | セル値 | ✓ |
| 0.8525 | 本文§3.3, 本文§4.6 | int_channel.csv[intensity_r_lightincl] | 個体平均の平均 | ✓ |
| 0.8630 | 本文§3.5, 本文 Table 2, SM Table S3, SM Table S5 | Table2.csv[State F1 (QC-passing channels)]（mouse_6） ／ TableS3.csv[State F1]（260626_ch4 の行） ／ TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_6 の行） | セル値 | ✓ |
| 0.8636 | SM Table S6 | TableS1.csv[Specificity]（0.75 の行） | セル値 | ✓ |
| 0.8692 | SM Table S5 | TableS3.csv[State F1]（260629_ch8 の行） | セル値 | ✓ |
| 0.8696 | SM Table S6 | TableS1.csv[PPV]（0.6 の行） | セル値（20/23 を 4 桁で表示） | ✓ |
| 0.87 | 本文§4.2 | 文献値（[10] RAD） | 1 分ビンでの R²（専用チャンバー） | ✓ |
| 0.8721 | 本文§3.3, 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 最小（mouse_3） | ✓ |
| 0.875 | SM Text S2.4 | TableS1.csv[PPV] | good_cut=0.80 の行 | ✓ |
| 0.8750 | SM Table S6, SM Table S6 の PPV（表と注。TableS1.csv[PPV] 0.8 の行） | TableS1.csv[Sensitivity]（0.8 の行） | セル値 | ✓ |
| 0.8824 | SM Table S6 | TableS1.csv[Sensitivity]（0.65 の行） | セル値 | ✓ |
| 0.8896 | 本文§3.6 | int_binned.csv[log_lp_var]（stage3_figures.py の fig6(a) と同じ対応づけ。16 ペア、3,432 ビン） | 全ビンをプールした Spearman r（0.889619） | ✓ |
| 0.89 | 本文§3.5, SM Text S2.4 | TableS1.csv[AUC (par)] | 全 6 条件の最小（0.8902） | ✓ |
| 0.8902 | SM Table S6 | TableS1.csv[AUC (par)]（0.65 の行） | セル値 | ✓ |
| 0.8955 | SM Table S6 | TableS1.csv[AUC (par)]（0.6 の行） | セル値 | ✓ |
| 0.8986 | 本文§3.3, 本文 Figure 3, SM Table S2 | TableS6.csv[95% CI lower]（Intensity r (mean of mouse means) の行） | セル値 | ✓ |
| 0.9000 | SM Table S6 | TableS1.csv[Sensitivity]（0.75 の行） | セル値 | ✓ |
| 0.9091 | SM Table S6 | TableS1.csv[Sensitivity]（0.6 の行） | セル値 | ✓ |
| 0.9092 | 本文§3.7 | int_darkdef_sensitivity_agg.csv[mean_of_mouse_means] | shift_h = −1 の行 | ✓ |
| 0.9096 | 本文§3.7 | int_darkdef_sensitivity_agg.csv[mean_of_mouse_means] | shift_h = +1 の行 | ✓ |
| 0.9102 | 本文§3.1, SM Figure S1 | int_lpf_sweep_agg.csv[intensity_r_mean_of_means] | 最小（cutoff_hz = 5.0 の行） | ✓ |
| 0.9127 | 本文§3.6 | int_sensor_swap.csv[set1_r] | 8 個体の平均（セット A） | ✓ |
| 0.9131 | 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 生値（mouse_8） | ✓ |
| 0.9133 | 本文§3.7, SM Figure S6 | int_loso_r.csv[r_test] | 最小（fold = mouse_1） | ✓ |
| 0.9155 | 本文§3.3 | int_channel.csv[intensity_r_activeonly] | 個体平均の平均 | ✓ |
| 0.9157 | 本文§3.7, SM Figure S7 | int_channel.csv[intensity_r] | qc1_pass = 0 の ch の個体平均の平均（7 個体） | ✓ |
| 0.9159 | 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 生値（mouse_5） | ✓ |
| 0.9171 | 本文 Abstract, 本文§3.1, 本文§3.2, 本文§3.3, 本文§3.7, 本文§5, 本文 Figure 3, 本文 Table 2, SM Figure S6, SM Table S2, SM Figure S1, SM Figure S7 | TableS6.csv[Point estimate]（Intensity r (mean of mouse means) の行） | セル値 | ✓ |
| 0.9172 | 本文§3.2, 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 生値（mouse_6、0.917152） | ✓ |
| 0.9172 | 本文§3.7 | int_darkdef_sensitivity_agg.csv[mean_of_mouse_means] | shift_h = 0 の行（0.917247）。24 時間の連続信号から暗期ビンを抽出する計算のため、主解析値 0.9171 とは一致しない（本文に明記） | ✓ |
| 0.9174 | 本文§3.7, SM Figure S7 | int_channel.csv[intensity_r] | qc1_pass = 1 の ch の個体平均の平均（7 個体）。§3.7 の「mouse_8 を除き ch 単位の QC を適用」も同値（mouse_8 に QC 通過 ch が無いため） | ✓ |
| 0.9177 | 本文§3.7 | int_loso_r.csv[r_test] | fold = mouse_8 の行 | ✓ |
| 0.9178 | 本文§3.1, SM Figure S1 | int_feature_bench.csv[mean_r] | 生値（feature = band_0_1Hz） | ✓ |
| 0.9181 | 本文§3.1, SM Figure S1 | int_lpf_sweep_agg.csv[intensity_r_mean_of_means] | 最大（cutoff_hz = 0.5 の行） | ✓ |
| 0.9215 | 本文§3.6 | int_sensor_swap.csv[set2_r] | 8 個体の平均（セット B） | ✓ |
| 0.9231 | 本文 Abstract, 本文§3.5, 本文§4.3, 本文§5, 本文 Figure 5, SM Table S1, SM Table S2, SM Table S6 | TableS1.csv[AUC (par)]（0.7 の行） / TableS1.csv[Sensitivity]（0.7 の行） / TableS2.csv[AUC (par)]（1 の行） / TableS6.csv[Point estimate]（AUC (par) の行） | セル値 | ✓ |
| 0.9236 | 本文§3.7, SM Figure S6 | int_loso_r.csv[r_test] | 最大（fold = mouse_3） | ✓ |
| 0.9238 | 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 生値（mouse_7） | ✓ |
| 0.9253 | 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 生値（mouse_2） | ✓ |
| 0.9259 | 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 生値（mouse_4） | ✓ |
| 0.926 | 本文 Table 3 | int_channel.csv[gmm_separation] | 生値（260629_ch3、0.9264） | ✓ |
| 0.9269 | 本文§3.3, 本文 Figure 3, SM Table S2 | TableS6.csv[95% CI upper]（Intensity r (mean of mouse means) の行） | セル値 | ✓ |
| 0.930 | SM Text S2.4 | SM Text S2.4 内で導出 | PPV 12/15 の Wilson 95% CI 上限（0.9295） | ✓ |
| 0.9337 | 本文§3.6, SM Text S2.7 | int_channel.csv[intensity_r] | 生値（260626_ch5） | ✓ |
| 0.9375 | 本文§3.6 | int_sensor_swap.csv[set2_r] | mouse_3 の行（セット B、0.937543） | ✓ |
| 0.9390 | 本文§3.2, 本文 Figure 2 | int_channel.csv[intensity_r] | 生値（260626_ch4、0.938967）。Figure 2(a) の r も stage3 がこの列を表示 | ✓ |
| 0.9409 | SM Table S6 | TableS1.csv[AUC (par)]（0.75 の行） | セル値 | ✓ |
| 0.9421 | 本文 Abstract, 本文§3.6, 本文§4.5, 本文 Figure 6, SM Table S2 | TableS6.csv[Point estimate]（Inter-sensor r の行） | セル値 | ✓ |
| 0.9437 | 本文§3.3, 本文 Table 2, SM Figure S4 | int_permouse_values.csv[intensity_r] | 最大（mouse_1） | ✓ |
| 0.95 | SM Text S2.5 | config.py TEMPORAL_PAR_SATURATION_THRESHOLD ／ SESSION_BLOCK_MIN_PAI_FRAC | 設定値（par 飽和の判定値、およびブロック採用に必要な 60 秒ビンの存在率） | ✓ |
| 0.9583 | SM Table S6 | TableS1.csv[AUC (par)]（0.8 の行） / TableS1.csv[Specificity]（0.8 の行） | セル値 | ✓ |
| 0.9617 | 本文§3.2, 本文 Figure 2 | int_circadian.csv[pir_norm, nano_norm] | 両系列の Spearman r（stage3 が算出） | ✓ |
| 0.978 | SM Text S2.4 | SM Text S2.4 内で導出 | PPV 7/8 の Wilson 95% CI 上限（0.9776） | ✓ |
| 0.9896 | 本文§3.6 | int_channel.csv[within_over_between] | 32 ch の平均 | ✓ |
| 0.99 | 本文§1 | 文献値（[13]、学会抄録） | センサー由来と動画由来の活動量の相関係数 | ✓ |
| 1.0 | SM Text S2.6 | int_channel.csv[pai_floor_rate] | 生値 %（260706_ch1、0.0104） | ✓ |
| 1.0 | 本文 Table 3 | config.py QC1_MULTI_GMM_SEP_MIN | 設定値（Table 3 最終列「Separation ≥ 1.0」） | ✓ |
| 1.0 | SM Table S6, SM Text S2.4 | TableS1.csv[PPV] / [AUC (par)]（0.55 の行） | 縮退した値（AUC = 1.0、PPV = 1.0） | ✓ |
| 1.000 | 本文 Figure 5, SM Table S2 | int_auc_metrics_cluster.csv[ci_upper] | metric=pir_active_rate の行 | ✓ |
| 1.0000 | SM Table S6（PPV） | TableS1.csv[PPV]（0.55 の行） | セル値（29/29 を 4 桁で表示） | ✓ |
| 1.0000 | SM Table S6 | TableS1.csv[AUC (par)]（0.55 の行） / TableS1.csv[Sensitivity]（0.55 の行） / TableS1.csv[Specificity]（0.55 の行） | セル値 | ✓ |
| 1.1 | SM Text S1.1 | 文献値（[14]） | LiTaO₃ 素子の熱時定数に対応するコーナー周波数（Hz） | ✓ |
| 1.2217 | 本文§3.6 | int_bland_altman.csv[bias] | 最大（16 ペア） | ✓ |
| 1.25 | 本文§4.5, 本文§4.6 | int_bland_altman.csv[bias] | 絶対値の最大（1.2471） | ✓ |
| 1.290 | 本文 Table 3 | int_channel.csv[gmm_separation] | 生値（260706_ch4、1.2902） | ✓ |
| 1.3875 | 本文§3.6, SM Text S2.7 | int_channel.csv[snr] | 生値（260626_ch5） | ✓ |
| 1.552 | 本文 Table 3 | int_channel.csv[gmm_separation] | 生値 | ✓ |
| 1.620 | 本文 Table 3 | int_channel.csv[gmm_separation] ／ int_qc_anatomy.csv[gmm_separation] | 生値（260706_ch5、1.6196） | ✓ |
| 1.77 | 本文§3.6 | int_bland_altman.csv[sd_diff] | 最大（1.7681） | ✓ |
| 1.91 | SM Text S2.6 | int_channel.csv[gmm_rest_sd] | 最大（260629_ch6、1.907） | ✓ |
| 2.0 | SM Text S2.5 | config.py TEMPORAL_PAI_REST_JUMP_THRESHOLD | 設定値（隣接ブロック間の Rest 成分平均の変化、対数分散単位） | ✓ |
| 2.24 | SM Text S2.6 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値（260629_ch6、2.2407） | ✓ |
| 2.46 | SM Text S2.5 | int_channel_stability.csv[pai_rest_jump_max] | 生値（260706_ch5、2.4624） | ✓ |
| 2.47 | SM Text S2.3 | int_channel.csv[median_nb_fn] | ch ごとの中央値のチャンネル間平均 | ✓ |
| 2.81 | 本文§3.7 | int_calibration_60s_summary.csv[channel_median_sd] | 空箱 60 秒ビンの ch 別中央値の SD（32 ch） | ✓ |
| 2.87 | 本文§3.6 | int_channel.csv[snr] | SNR の小さい順で 3 番目（2.871） | ✓ |
| 3.2 | 本文§3.7, SM Figure S8 | int_qc_learning.csv[approx_hours] | n_active_bins_state = 150 における 32 ch の最小（3.23 h） | ✓ |
| 3.5 | 本文§3.6 | 本文§3.6 内で導出 | exp(1.2471) = 3.48（Bland–Altman の系統差の最大を生の分散の比に換算） | ✓ |
| 4.9 | 本文§3.7, SM Figure S8 | int_qc_learning.csv[approx_hours] | n_active_bins_state = 150 における 32 ch の中央値（4.925 h） | ✓ |
| 5.9 | 本文§3.7, SM Figure S8 | int_qc_learning.csv[approx_hours] | n_active_bins_state = 150 における 32 ch の最大（5.93 h） | ✓ |
| 6.892 | 本文 Table 3 | int_qc_anatomy.csv[snr] | 生値（260706_ch4） | ✓ |
| 7.336 | 本文 Table 3 | int_qc_anatomy.csv[snr] | 生値（260629_ch3） | ✓ |
| 8.7 | 本文§3.4 | int_gmm_bic.csv[bic] | K ごとの ch 間中央値の差（K = 4 → 5、15,037.49 − 15,028.80） | ✓ |
| 9.17 | SM Text S2.3 | int_channel.csv[median_nb_tp] / [median_nb_fn] | 比の中央値（9.1667、範囲 4.00–16.67） | ✓ |
| 12.36 | 本文§4.6 | 本文§4.6 内で導出 | −10.67 − (−23.03) | ✓ |
| 14.5 | SM Text S2.3 | figure_values_good070.csv[fig5_fn_share_pct] | 100 − 85.5（FP の割合 %） | ✓ |
| 15.174 | 本文 Table 3 | int_channel.csv[snr] | 生値 | ✓ |
| 24.69 | SM Text S2.3 | int_channel.csv[median_nb_tp] | ch ごとの中央値のチャンネル間平均 | ✓ |
| 28.8 | SM Text S2.6 | int_channel.csv[pai_floor_rate] | 生値 %（260629_ch6、0.2882） | ✓ |
| 48.1 | 本文§3.4 | int_gmm_bic.csv[bic] | K ごとの ch 間中央値の差（K = 3 → 4、15,085.58 − 15,037.49） | ✓ |
| 85.5 | 本文§3.5, SM Text S2.3 | figure_values_good070.csv[fig5_fn_share_pct] | 全誤り中の FN の割合 %（FN 28,168 / FP 4,775） | ✓ |
| 102.65 | 本文§3.1 | figure_values_good070.csv[fig1_variance_ratio_raw] | ch=260626_ch4 variant=high | ✓ |
| 176.2 | 本文§3.6 | int_channel.csv[snr] | 最大（176.25） | ✓ |
| 1,082.65 | 本文§3.1 | figure_values_good070.csv[fig1_variance_ratio_lpf] | ch=260626_ch4 variant=high | ✓ |
