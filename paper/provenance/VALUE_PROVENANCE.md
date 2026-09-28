# VALUE_PROVENANCE — 数値の出所対応表

2026-09-13 改訂。照合対象 224 値について、**4 桁の数字が一致するか**ではなく
**その文が言っている量の出所か**という基準で再照合した。

- SM の表セルにしか現れない 132 値（208 出現）は docx の表構造を復元し、
  キャプションと同じ番号の `TableS*.csv` の同じ行と全数照合した（不一致 0）。
  これらの出所は `int_*.csv` ではなく表 CSV である。
- 本文に現れる 92 値は前後の文と列名を 1 件ずつ突き合わせた。
- `TableS1.csv`（good_cut 掃引 6 行）は `int_good_sensitivity_grid.csv` から生成されており、
  全 78 セルの厳密一致を確認済み（`stage2_tables.py:374-395`）。

判定: ✓ 出所確定 / ○ 候補複数 / ▲ 要注意

| 値 | 出現箇所 | 出所 | 集約 | 判定 |
|---|---|---|---|---|
| -23.026 | 本文§2.6.1 , 本文§3.7 | int_calibration_60s_summary.csv[channel_median_min] | 平均 ほか候補 13 件 | ○ |
| -19.50 | 本文§3.7 , 本文§4.6 | int_calibration_60s.csv[log_lp_var] | 生値 ほか候補 19 件 | ○ |
| -13.96 | 本文§3.7 | int_calibration.csv[log_lp_var] | 生値 ほか候補 120 件 | ○ |
| -13.71 | SMFigure S1 | int_calibration.csv[log_lp_var] | 生値 ほか候補 105 件 | ○ |
| -13.2798 | 本文Figure 4 , 本文§3.4 | int_channel.csv[nano_rest_mu_mean] | 生値 ほか候補 1 件 | ✓ |
| -13.2364 | 本文Figure 4 , 本文§3.4 | int_channel.csv[gmm_rest_mu] | 生値 ほか候補 4 件 | ○ |
| -12.93 | SMFigure S1 | int_calibration.csv[log_lp_var] | 生値 ほか候補 216 件 | ○ |
| -10.62 | 本文§3.7 , 本文§4.6 | int_calibration.csv[log_lp_var] | 生値 ほか候補 116 件 | ○ |
| -10.09 | SMFigure S1 | int_calibration.csv[log_lp_var] | 生値 ほか候補 80 件 | ○ |
| -1.2471 | 本文§3.6 | int_bland_altman.csv[bias] | 最小 ほか候補 1 件 | ✓ |
| -0.372 | 本文表本体 | int_qc_anatomy.csv[par_minus_true] | 最小 ほか候補 7 件 | ○ |
| -0.29 | 本文§3.6 | int_sensor_retest.csv[icc2_1] | 最小 ほか候補 20 件 | ○ |
| -0.28 | 本文表本体 | int_qc_anatomy.csv[par_minus_true] | 中央値 ほか候補 20 件 | ○ |
| -0.151 | 本文表本体 | int_bland_altman_pairs.csv[diff_ab] | 生値 ほか候補 4 件 | ○ |
| -0.10 | 本文§3.6 | int_sensor_retest.csv[spearman] | 最小 ほか候補 77 件 | ○ |
| -0.0372 | 本文§3.3 | int_placebo_pairs.csv[placebo_r] | same_session=True（n=96）の最小 | ✓ |
| 0.0000 | 本文§3.4 | int_seed_state_stability.csv[f1_state] | ch ごとシード間 SD の中央値（32 ch） | ✓ |
| 0.0002 | 本文§3.7 , 本文§4.6 | int_channel.csv[pai_near_floor_rate] | 最小 ほか候補 5 件 | ○ |
| 0.001 | 本文§3.3 | int_channel.csv[phase_shuffle_p] | config.N_PHASE_PERM=1000 による下限 1/1001=0.000999 | ✓ |
| 0.0010 | 本文§3.4 | int_seed_state_stability.csv[pir_active_rate] | ch ごとシード間 SD の最大（0.001030） | ✓ |
| 0.0012 | 本文§3.4 , 本文§4.1 | int_seed_state_stability.csv[f1_state] | ch ごとシード間 SD の最大（0.001166） | ✓ |
| 0.0040 | 本文§3.4 | int_seed_stability.csv[rest_mu]（bin_sec = 60） | ch ごとシード間 SD の最大（260629_ch1、0.003995） | ✓ |
| 0.0014 | 本文§3.1 , 本文Figure 3 , 本文§3.3 … | TableS6.csv[Point estimate]（Random-permutation control r の行） | セル値 | ✓ |
| 0.0030 | 本文§3.1 | int_channel.csv[F1_state_rawvar] | 平均 ほか候補 7 件 | ○ |
| 0.01 | 本文§2.3 , 本文§3.7 , 本文Table 1 … | int_adc_diagnostic.csv[min] | 最小 ほか候補 235 件 | ○ |
| 0.0139 | 本文Figure 6 , 本文§3.6 | int_raw_trace.csv[raw_value_lpf] | 生値 | ✓ |
| 0.0142 | SM(前付け) | TableS4.csv[SD]（260626 の行） / TableS4.csv[Slope (per day)]（260626 の行） | セル値 | ✓ |
| 0.0171 | 本文§3.4 | int_seed_state_stability.csv[gmm_boundary] | ch ごとシード間 SD の最大（0.017147） | ✓ |
| 0.0194 | 本文§2.6.5 , 本文§3.5 , SMFigure S6 | int_loso_thr.csv[qc1_threshold] | fold 間 SD（8 fold） | ✓ |
| 0.0248 | SM(前付け) | TableS4.csv[Slope (per day)]（260702 の行） | セル値 | ✓ |
| 0.0255 | SM(前付け) | TableS4.csv[SD]（260702 の行） | セル値 | ✓ |
| 0.0284 | SM(前付け) | TableS4.csv[Delta (last - first)]（260626 の行） | セル値 | ✓ |
| 0.0285 | 本文Figure 6 , 本文§3.6 | int_sensor_retest.csv[abs_diff_mean] | 最小 ほか候補 8 件 | ○ |
| 0.0363 | SM(前付け) | TableS4.csv[Slope (per day)]（260629 の行） | セル値 | ✓ |
| 0.0434 | 本文Figure 4 , 本文§3.4 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値（ch=260626_ch6） | ✓ |
| 0.0471 | SM(前付け) | TableS4.csv[SD]（260629 の行） | セル値 | ✓ |
| 0.0496 | SM(前付け) | TableS4.csv[Delta (last - first)]（260702 の行） | セル値 | ✓ |
| 0.0510 | SM(前付け) | TableS4.csv[Slope (per day)]（260706 の行） | セル値 | ✓ |
| 0.0579 | 本文Figure 4 , 本文§3.4 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値の中央値（QC 通過 15 ch） | ✓ |
| 0.0699 | 本文§3.1 | int_channel.csv[F1_state_band25] | 平均 ほか候補 3 件 | ○ |
| 0.0714 | 本文Figure 4 , 本文§3.4 , 本文§4.5 | int_channel.csv[gmm_rest_mu] − [nano_rest_mu_mean] | 差の絶対値の中央値（全 32 ch） | ✓ |
| 0.0722 | SM(前付け) | TableS4.csv[SD]（260706 の行） | セル値 | ✓ |
| 0.0726 | SM(前付け) | TableS4.csv[Delta (last - first)]（260629 の行） | セル値 | ✓ |
| 0.0864 | 本文§3.5 | int_auc_boot.csv[diff_ci_lower] | comparison=pir_active_rate - snr の生値 | ✓ |
| 0.0886 | 本文§3.1 | int_feature_bench.csv[mean_r] | 生値 | ✓ |
| 0.1020 | SM(前付け) | TableS4.csv[Delta (last - first)]（260706 の行） | セル値 | ✓ |
| 0.108 | 本文§3.1 | int_state_confusion_perch.csv[npv] | 個体平均のSD ほか候補 13 件 | ○ |
| 0.1132 | 本文§3.3 | int_placebo_pairs.csv[placebo_r] | same_session=True（n=96）の中央値 | ✓ |
| 0.1468 | SM(前付け) | TableS3.csv[par]（260702_ch2 の行） | セル値 | ✓ |
| 0.1491 | 本文(前付け) , 本文Figure 3 , 本文§3.3 … | TableS6.csv[Point estimate]（Mismatched-pairing control r の行） | セル値 | ✓ |
| 0.15 | 本文§3.5 | config.py PAR_THRESHOLD_SWEEP | 設定値（掃引下限） | ✓ |
| 0.1660 | 本文Figure 5 , 本文§3.5 | int_auc_metrics_cluster.csv[auc_observed] | metric=gmm_separation の生値 | ✓ |
| 0.1667 | 本文§3.5 | int_error_bydist_perch.csv[error_rate] | db=>3 のチャンネル平均（n=32） | ✓ |
| 0.1678 | SM(前付け) | TableS3.csv[par]（260626_ch3 の行） | セル値 | ✓ |
| 0.1731 | SM(前付け) | TableS3.csv[par]（260702_ch6 の行） | セル値 | ✓ |
| 0.1750 | SM(前付け) | TableS1.csv[LOMO threshold (par)]（0.55 の行） / TableS3.csv[par]（260629_ch7 の行） / TableS3.csv[par]（260702_ch1 の行） | セル値 | ✓ |
| 0.1769 | SM(前付け) | TableS3.csv[par]（260706_ch7 の行） | セル値 | ✓ |
| 0.1806 | 本文§3.7 | int_label_sweep.csv[algebraic_lower_mean] | 最小 ほか候補 3 件 | ○ |
| 0.181 | 本文表本体 | int_channel.csv[mcc] | 最小 ほか候補 12 件 | ○ |
| 0.1965 | SM(前付け) | TableS3.csv[par]（260702_ch4 の行） | セル値 | ✓ |
| 0.1968 | SM(前付け) | TableS2.csv[Sweep threshold (Youden)]（3 の行） / TableS3.csv[par]（260626_ch8 の行） | セル値 | ✓ |
| 0.2046 | SM(前付け) | TableS2.csv[Sweep threshold (Youden)]（2 の行） / TableS3.csv[par]（260626_ch7 の行） | セル値 | ✓ |
| 0.2133 | SM 表本体 | TableS1.csv[LOMO threshold (par)]（0.6 の行） | セル値 | ✓ |
| 0.2201 | SM(前付け) | TableS3.csv[par]（260706_ch6 の行） | セル値 | ✓ |
| 0.2238 | SM(前付け) | TableS3.csv[par]（260702_ch5 の行） | セル値 | ✓ |
| 0.2316 | 本文§3.1 | int_channel.csv[F1_state_band515] | 平均 ほか候補 3 件 | ○ |
| 0.2357 | 本文§3.1 | int_channel.csv[F1_state_band01] | 平均 ほか候補 1 件 | ✓ |
| 0.2544 | SM(前付け) | TableS3.csv[par]（260702_ch7 の行） | セル値 | ✓ |
| 0.2602 | SM(前付け) | TableS3.csv[par]（260702_ch3 の行） | セル値 | ✓ |
| 0.2658 | SM 表本体 | TableS1.csv[LOMO threshold (par)]（0.65 の行） | セル値 | ✓ |
| 0.2674 | SM(前付け) | TableS3.csv[par]（260706_ch3 の行） | セル値 | ✓ |
| 0.2706 | SM(前付け) | TableS3.csv[par]（260629_ch5 の行） | セル値 | ✓ |
| 0.2757 | 本文§3.5 , SMFigure S6 , SM(前付け) | int_loso_thr.csv[qc1_threshold] | 生値（6 fold で同値） | ✓ |
| 0.276 | 本文表本体 | int_error_bydist_perch.csv[error_rate] | 中央値 ほか候補 34 件 | ○ |
| 0.28 | 本文§3.5 | 本文§3.5 内で導出 | 0.624 − 0.344（Record 4 ch4 の実測 − par） | ✓ |
| 0.2831 | SM(前付け) | TableS3.csv[par]（260629_ch4 の行） | セル値 | ✓ |
| 0.2852 | 本文§2.6.5 , 本文§2.7.1 , 本文§2.7.5 … | TableS1.csv[LOMO threshold (par)]（0.7 の行） / TableS6.csv[Point estimate]（QC threshold (par) の行） | セル値 | ✓ |
| 0.2981 | 本文§3.5 , SM(前付け) | int_loso_thr.csv[qc1_threshold] | 生値（fold=mouse_8） | ✓ |
| 0.2996 | 本文§3.5 | int_auc_boot.csv[diff_observed] | comparison=pir_active_rate - snr の生値 | ✓ |
| 0.3023 | SM(前付け) | int_channel.csv[pir_active_rate] | 平均 ほか候補 18 件 | ○ |
| 0.3275 | SM(前付け) | TableS3.csv[par]（260629_ch3 の行） | セル値 | ✓ |
| 0.328 | 本文§3.5 , 本文表本体 | int_channel.csv[pir_active_rate] | 生値（Record 2 ch3） | ✓ |
| 0.3292 | 本文§3.5 , SMFigure S6 , SM(前付け) | int_loso_thr.csv[qc1_threshold] | 生値（fold=mouse_5、0.329155） | ✓ |
| 0.33 | 本文§4.2 | int_auc_metrics_cluster.csv[ci_lower] | SD ほか候補 93 件 | ○ |
| 0.3313 | SM 表本体 | TableS1.csv[LOMO threshold (par)]（0.75 の行） | セル値 | ✓ |
| 0.3355 | SM(前付け) | TableS2.csv[nar (mean)]（3 の行） | セル値 | ✓ |
| 0.344 | 本文§3.5 , 本文表本体 | int_channel.csv[pir_active_rate] | 生値（Record 4 ch4） | ✓ |
| 0.3440 | SM(前付け) | TableS3.csv[par]（260706_ch4 の行） | セル値 | ✓ |
| 0.3463 | SM(前付け) | TableS3.csv[par]（260706_ch2 の行） | セル値 | ✓ |
| 0.35 | 本文§3.6 | int_adc_diagnostic.csv[range] | 最小 ほか候補 134 件 | ○ |
| 0.3505 | SM(前付け) | TableS3.csv[par]（260626_ch5 の行） | セル値 | ✓ |
| 0.3538 | SM(前付け) | TableS3.csv[par]（260706_ch1 の行） | セル値 | ✓ |
| 0.3558 | SM(前付け) | TableS1.csv[LOMO threshold (par)]（0.8 の行） | セル値 | ✓ |
| 0.3699 | SM(前付け) | TableS3.csv[par]（260626_ch2 の行） | セル値 | ✓ |
| 0.3739 | 本文§3.5 | int_error_bydist_perch.csv[error_rate] | db=0-0.5 のチャンネル平均（n=32） | ✓ |
| 0.375 | 本文§3.4 | int_channel.csv[pir_active_rate] | 生値（ch=260626_ch6） | ✓ |
| 0.3755 | SM(前付け) | TableS3.csv[par]（260626_ch6 の行） | セル値 | ✓ |
| 0.3771 | 本文§3.5 | int_error_bydist_perch.csv[error_rate] | db=0.5-1 のチャンネル平均（n=32） | ✓ |
| 0.3777 | 本文§3.3 | int_placebo_pairs.csv[placebo_r] | same_session=True（n=96）の最大 | ✓ |
| 0.3796 | SM(前付け) | TableS3.csv[par]（260629_ch2 の行） | セル値 | ✓ |
| 0.3916 | SM(前付け) | TableS2.csv[nar (mean)]（2 の行） | セル値 | ✓ |
| 0.4153 | SM(前付け) | TableS3.csv[par]（260626_ch4 の行） | セル値 | ✓ |
| 0.4255 | SM(前付け) | TableS3.csv[par]（260629_ch8 の行） | セル値 | ✓ |
| 0.427 | 本文§3.5 , 本文表本体 | int_session_mouse_control.csv[nanotag_active_rate_260702] | 最小 ほか候補 13 件 | ○ |
| 0.4326 | 本文§3.1 | int_channel.csv[F1_state_logband12] | 平均 ほか候補 2 件 | ○ |
| 0.4421 | SM(前付け) | TableS3.csv[par]（260629_ch1 の行） | セル値 | ✓ |
| 0.45 | 本文§3.5 | config.py PAR_THRESHOLD_SWEEP | 設定値（掃引上限） | ✓ |
| 0.468 | 本文§3.5 , 本文表本体 , 本文§4.3 | int_channel.csv[nanotag_active_rate] | 生値（Record 4 ch5） | ✓ |
| 0.4684 | 本文§3.7 | int_qc_anatomy.csv[nanotag_active_rate] | 最小 ほか候補 3 件 | ○ |
| 0.4716 | 本文§2.6.2 , 本文§4.3 , SM(前付け) | TableS2.csv[nar (mean)]（1 の行） | セル値 | ✓ |
| 0.474 | 本文§3.5 | int_session_mouse_control.csv[nanotag_active_rate_260702] | 最大 ほか候補 16 件 | ○ |
| 0.4822 | 本文§3.1 | int_channel.csv[F1_state_logband25] | 平均 ほか候補 1 件 | ✓ |
| 0.4831 | 本文§3.1 | int_feature_bench.csv[mean_r] | 生値 ほか候補 1 件 | ✓ |
| 0.4982 | SM(前付け) | TableS3.csv[State F1]（260702_ch2 の行） | セル値 | ✓ |
| 0.5128 | SM(前付け) | TableS4.csv[Detection ratio, block 1]（260702 の行） | セル値 | ✓ |
| 0.5243 | SM(前付け) | TableS3.csv[State F1]（260702_ch6 の行） | セル値 | ✓ |
| 0.5273 | SM(前付け) | TableS4.csv[Detection ratio, block 2 (mid)]（260702 の行） | セル値 | ✓ |
| 0.529 | 本文§3.5 | 本文§3.5 内で導出 | PPV 7/8 の Wilson 95% CI 下限（0.5291） | ✓ |
| 0.5292 | 本文§3.5 | int_auc_boot.csv[diff_ci_upper] | comparison=pir_active_rate - snr の生値 | ✓ |
| 0.5334 | 本文§3.1 | int_channel.csv[F1_state_logband515] | 平均 ほか候補 1 件 | ✓ |
| 0.5341 | SM(前付け) | TableS4.csv[Mean]（260702 の行） | セル値 | ✓ |
| 0.5420 | SM(前付け) | TableS3.csv[State F1]（260626_ch3 の行） | セル値 | ✓ |
| 0.548 | 本文§3.5 | 本文§3.5 内で導出 | PPV 12/15 の Wilson 95% CI 下限（0.5481） | ✓ |
| 0.55 | 本文§2.6.5 , 本文§3.5 | TableS1.csv[good definition (state F1 >=)] | 掃引下限（表の最小行） | ✓ |
| 0.5624 | SM(前付け) | TableS4.csv[Detection ratio, block 3]（260702 の行） | セル値 | ✓ |
| 0.5631 | SM(前付け) | TableS3.csv[State F1]（260629_ch4 の行） | セル値 | ✓ |
| 0.5646 | SM(前付け) | TableS3.csv[State F1]（260706_ch7 の行） | セル値 | ✓ |
| 0.5648 | SM(前付け) | TableS3.csv[State F1]（260702_ch1 の行） | セル値 | ✓ |
| 0.5702 | SM(前付け) | TableS3.csv[State F1]（260706_ch3 の行） | セル値 | ✓ |
| 0.573 | 本文§3.1 | int_channel.csv[F1_state_std] | 生値 ほか候補 14 件 | ○ |
| 0.574 | 本文§3.5 , 本文表本体 | int_channel.csv[F1_state] | 生値（Record 2 ch3） | ✓ |
| 0.5744 | SM(前付け) | TableS3.csv[State F1]（260629_ch3 の行） | セル値 | ✓ |
| 0.5758 | 本文§3.1 | int_channel.csv[F1_state_logvar_nolpf] | 平均 ほか候補 2 件 | ○ |
| 0.5853 | SM(前付け) | TableS3.csv[State F1]（260702_ch4 の行） | セル値 | ✓ |
| 0.5880 | SM(前付け) | TableS3.csv[State F1]（260629_ch7 の行） | セル値 | ✓ |
| 0.5909 | 本文表本体 | int_permouse_values.csv[F1_state] | 最小 ほか候補 2 件 | ○ |
| 0.5978 | SM(前付け) | TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_2 の行） | セル値 | ✓ |
| 0.5979 | SM(前付け) | TableS3.csv[par]（260629_ch6 の行） | セル値 | ✓ |
| 0.60 | SM 表本体 | TableS1.csv[good definition (state F1 >=)]（0.6 の行） | セル値 | ✓ |
| 0.61 | 本文§4.4 | int_channel.csv[intensity_r_lightonly] | 個体中央値 ほか候補 144 件 | ○ |
| 0.6152 | 本文表本体 | int_channel.csv[F1_state_raw_amp] | 最大 ほか候補 4 件 | ○ |
| 0.6215 | SM(前付け) | TableS3.csv[State F1]（260706_ch5 の行） | セル値 | ✓ |
| 0.622 | 本文§3.5 , 本文表本体 | int_channel.csv[F1_state] | 生値（Record 4 ch5） | ✓ |
| 0.6235 | 本文Figure 5 , 本文§3.5 , 本文§4.1 | int_auc_metrics_cluster.csv[auc_observed] | metric=snr の平均 ほか候補 6 件 | ○ |
| 0.624 | 本文§3.5 , 本文表本体 | int_channel.csv[nanotag_active_rate] | 生値（Record 4 ch4） | ✓ |
| 0.6271 | SM(前付け) | TableS3.csv[State F1]（260706_ch6 の行） | セル値 | ✓ |
| 0.6282 | SM(前付け) | TableS3.csv[State F1]（260702_ch5 の行） | セル値 | ✓ |
| 0.6312 | 本文§3.3 | int_channel.csv[intensity_r_lightonly] | 平均 ほか候補 2 件 | ○ |
| 0.6351 | 本文§3.1 | int_bin_sweep_agg.csv[f1_all_mean] | 最小 ほか候補 6 件 | ○ |
| 0.6382 | SM(前付け) | TableS3.csv[State F1]（260626_ch8 の行） | セル値 | ✓ |
| 0.6444 | SM(前付け) | TableS3.csv[State F1]（260626_ch7 の行） | セル値 | ✓ |
| 0.649 | 本文§3.5 , 本文表本体 | int_channel.csv[pir_active_rate] | 最大 ほか候補 15 件 | ○ |
| 0.6490 | 本文Figure 6 , 本文§3.7 , SM(前付け) | TableS3.csv[par]（260706_ch5 の行） | セル値 | ✓ |
| 0.65 | SM 表本体 | TableS1.csv[good definition (state F1 >=)]（0.65 の行） | セル値 | ✓ |
| 0.6516 | 本文§3.4 , 本文Figure 5 , 本文§3.5 … | TableS6.csv[95% CI lower]（State F1 (all channels) の行） | セル値 | ✓ |
| 0.6526 | 本文§3.1 | int_bin_sweep_agg.csv[f1_all_mean] | 中央値 ほか候補 4 件 | ○ |
| 0.6558 | 本文表本体 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.6560 | SM(前付け) | TableS3.csv[State F1]（260706_ch4 の行） | セル値 | ✓ |
| 0.656 | 本文§3.5 , 本文表本体 | int_channel.csv[F1_state] | 生値（Record 4 ch4） | ✓ |
| 0.658 | 本文§3.7 | int_bin_sweep.csv[f1_state] | 生値 ほか候補 14 件 | ○ |
| 0.6655 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_1 の行） | セル値 | ✓ |
| 0.6690 | 本文表本体 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.6697 | 本文§3.1 | int_channel.csv[F1_state_logband01] | 平均 ほか候補 1 件 | ✓ |
| 0.6709 | 本文表本体 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.6720 | SM(前付け) | TableS4.csv[Detection ratio, block 2 (mid)]（260706 の行） | セル値 | ✓ |
| 0.6729 | 本文Figure 6 , 本文§3.7 , SMFigure S4 | int_channel.csv[intensity_r] | 最小 ほか候補 10 件 | ○ |
| 0.673 | 本文§3.5 | int_channel.csv[intensity_r] | 最小 ほか候補 27 件 | ○ |
| 0.6760 | 本文表本体 | int_mouse.csv[mean_f1] | 生値 ほか候補 1 件 | ✓ |
| 0.6773 | SM(前付け) | TableS3.csv[State F1]（260629_ch5 の行） | セル値 | ✓ |
| 0.6793 | SM(前付け) | TableS4.csv[Mean of the other recordings]（260626 の行） | セル値 | ✓ |
| 0.6803 | SM(前付け) | TableS4.csv[Mean of the other recordings]（260629 の行） | セル値 | ✓ |
| 0.6814 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_4 の行） | セル値 | ✓ |
| 0.6825 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_3 の行） | セル値 | ✓ |
| 0.6840 | 本文§3.1 , 本文§3.4 , 本文Figure 5 … | TableS2.csv[State F1 (mean of animal means)]（1 の行） / TableS6.csv[Point estimate]（State F1 (all channels) の行） | セル値 | ✓ |
| 0.6851 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_8 の行） | セル値 | ✓ |
| 0.6857 | SM(前付け) | TableS3.csv[State F1]（260702_ch3 の行） | セル値 | ✓ |
| 0.6858 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_7 の行） | セル値 | ✓ |
| 0.6861 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_6 の行） | セル値 | ✓ |
| 0.6862 | 本文Figure 5 , 本文§3.5 | int_auc_metrics_cluster.csv[auc_observed] | metric=floor_rate の平均 ほか候補 5 件 | ○ |
| 0.6880 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_5 の行） | セル値 | ✓ |
| 0.6881 | 本文§3.1 | int_lpf_sweep_agg.csv[f1_qc_mean_of_means] | 最小 ほか候補 2 件 | ○ |
| 0.6943 | SM(前付け) | TableS4.csv[Mean of the other recordings]（260706 の行） | セル値 | ✓ |
| 0.6944 | 本文表本体 | int_permouse_values.csv[F1_state] | 生値 ほか候補 1 件 | ✓ |
| 0.6973 | SM(前付け) | TableS5.csv[LOSO state F1, all channels (remaining animals)]（mouse_2 の行） | セル値 | ✓ |
| 0.6988 | SM(前付け) | TableS3.csv[State F1]（260702_ch7 の行） | セル値 | ✓ |
| 0.699 | 本文§3.5 , 本文表本体 , 本文§4.3 | int_channel.csv[nanotag_active_rate] | 最大 ほか候補 21 件 | ○ |
| 0.6998 | 本文Figure 5 , 本文§3.5 , SM(前付け) | TableS6.csv[95% CI lower]（State F1 (QC-passing channels) の行） | セル値 | ✓ |
| 0.7000 | SM 表本体 | TableS1.csv[Specificity]（0.6 の行） | セル値 | ✓ |
| 0.70 | 本文§2.6.5 , 本文Figure 5 , 本文§3.5 … | config.py QC1_GOOD_F1 | 設定値（good 定義の主基準） | ✓ |
| 0.7001 | SM(前付け) | TableS3.csv[State F1]（260626_ch5 の行） | セル値 | ✓ |
| 0.7017 | 本文表本体 | int_permouse_values.csv[F1_state] | 生値 | ✓ |
| 0.7019 | SM 表本体 | TableS1.csv[State F1 after QC]（0.55 の行） | セル値 | ✓ |
| 0.7095 | SM(前付け) | TableS4.csv[Detection ratio, block 1]（260706 の行） | セル値 | ✓ |
| 0.7167 | SM(前付け) | TableS2.csv[State F1 (mean of animal means)]（2 の行） | セル値 | ✓ |
| 0.7192 | SM(前付け) | TableS4.csv[Detection ratio, block 1]（260629 の行） | セル値 | ✓ |
| 0.722 | 本文表本体 | int_bin_sweep_agg.csv[f1_qc_mean_of_means] | 最小 ほか候補 11 件 | ○ |
| 0.7225 | 本文§3.5 , SM(前付け) | int_channel.csv[F1_state] | 生値（Record 3 ch8） | ✓ |
| 0.7239 | 本文§3.1 | int_bin_sweep_agg.csv[f1_qc_mean_of_means] | 生値 | ✓ |
| 0.7310 | SM(前付け) | TableS4.csv[Mean]（260706 の行） | セル値 | ✓ |
| 0.7333 | SM 表本体 | TableS1.csv[Specificity]（0.65 の行） | セル値 | ✓ |
| 0.7339 | 本文§3.4 , 本文Figure 5 , 本文§3.5 … | TableS6.csv[95% CI upper]（State F1 (all channels) の行） | セル値 | ✓ |
| 0.7356 | 本文§3.1 | int_lpf_sweep_agg.csv[f1_qc_mean_of_means] | 生値 | ✓ |
| 0.7361 | SM(前付け) | TableS2.csv[State F1 (mean of animal means)]（3 の行） | セル値 | ✓ |
| 0.7365 | 本文表本体 , SM(前付け) | TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_3 の行） | セル値 | ✓ |
| 0.7388 | SM 表本体 | TableS1.csv[State F1 after QC]（0.6 の行） | セル値 | ✓ |
| 0.7456 | SM(前付け) | TableS3.csv[State F1]（260626_ch1 の行） | セル値 | ✓ |
| 0.750 | SM 表本体 | TableS1.csv[PPV]（0.75 の行） | セル値 | ✓ |
| 0.75 | 本文§3.5 | int_qc_threshold_sweep.csv[PPV] | par_threshold=0.28 の行 | ✓ |
| 0.7562 | 本文(前付け) , 本文§3.5 , 本文§3.7 … | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_6 の行） | セル値 | ✓ |
| 0.7571 | 本文§3.3 | int_permouse_values.csv[intensity_r_trendremoved] | 個体別の最小 | ○ |
| 0.7599 | SM(前付け) | TableS1.csv[State F1 after QC]（0.65 の行） / TableS4.csv[Mean of the other recordings]（260702 の行） | セル値 | ✓ |
| 0.7617 | SM(前付け) | TableS4.csv[Detection ratio, block 1]（260626 の行） | セル値 | ✓ |
| 0.7622 | SM(前付け) | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_4 の行） | セル値 | ✓ |
| 0.7623 | 本文§4.3 | int_state_baseline.csv[f1_state] | method=fixed_quantile の平均 ほか候補 4 件 | ○ |
| 0.7646 | SM(前付け) | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_1 の行） | セル値 | ✓ |
| 0.7652 | 本文§3.1 | int_lpf_sweep_agg.csv[f1_qc_mean_of_means] | 生値 ほか候補 2 件 | ○ |
| 0.7656 | 本文表本体 , SM(前付け) | TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_7 の行） | セル値 | ✓ |
| 0.7690 | 本文§3.5 | int_qc_threshold_sweep.csv[f1_qc_post] | 生値 | ✓ |
| 0.7701 | SM(前付け) | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_5 の行） | セル値 | ✓ |
| 0.7715 | 本文(前付け) , 本文§3.1 , 本文Figure 5 … | TableS1.csv[State F1 after QC]（0.7 の行） / TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_8 の行） / TableS6.csv[Point estimate]（State F1 (QC-passing channels) の行） | セル値 | ✓ |
| 0.7725 | SM(前付け) | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_7 の行） | セル値 | ✓ |
| 0.7729 | SM(前付け) | TableS4.csv[Mean]（260629 の行） | セル値 | ✓ |
| 0.7739 | 本文(前付け) , 本文§3.5 , 本文§3.7 … | int_holdout_f1.csv[holdout_f1] | 平均 | ✓ |
| 0.7754 | SM(前付け) | TableS2.csv[AUC (par)]（3 の行） / TableS4.csv[Detection ratio, block 2 (mid)]（260626 の行） | セル値 | ✓ |
| 0.7757 | SM(前付け) | TableS4.csv[Mean]（260626 の行） | セル値 | ✓ |
| 0.7764 | 本文§3.5 | int_qc_threshold_sweep.csv[f1_qc_post] | 生値 | ✓ |
| 0.7773 | SM(前付け) | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_3 の行） | セル値 | ✓ |
| 0.7801 | 本文表本体 | int_aggregation_summary.csv[median_of_medians] | metric=F1_state の中央値 ほか候補 7 件 | ○ |
| 0.7848 | SM(前付け) | TableS3.csv[State F1]（260706_ch8 の行） | セル値 | ✓ |
| 0.7883 | SM 表本体 | TableS1.csv[State F1 after QC]（0.75 の行） | セル値 | ✓ |
| 0.789 | SM 表本体 | TableS1.csv[PPV]（0.65 の行） | セル値 | ✓ |
| 0.7896 | 本文§3.6 , 本文§3.7 | int_channel.csv[snr] | 最小 ほか候補 3 件 | ○ |
| 0.79 | 本文§3.5 , 本文表本体 | int_qc_threshold_sweep.csv[PPV] | par_threshold=0.30 の行（0.7857） | ✓ |
| 0.7901 | SM(前付け) | TableS4.csv[Detection ratio, block 3]（260626 の行） | セル値 | ✓ |
| 0.7908 | 本文(前付け) , 本文Figure 3 , 本文§3.3 … | TableS3.csv[State F1]（260706_ch2 の行） / TableS6.csv[Point estimate]（Residual intensity r (60-min envelope removed) の行） | セル値 | ✓ |
| 0.7919 | SM(前付け) | TableS4.csv[Detection ratio, block 3]（260629 の行） | セル値 | ✓ |
| 0.7975 | 本文(前付け) , 本文§3.5 , 本文§3.7 … | TableS5.csv[LOSO state F1 after QC (remaining animals)]（mouse_2 の行） | セル値 | ✓ |
| 0.7995 | 本文§4.3 | int_state_baseline.csv[f1_state] | method=median_split かつ QC 通過の個体平均 | ✓ |
| 0.800 | 本文§3.5 , 本文§4.5 , SM(前付け) | int_qc_threshold_sweep.csv[PPV] | par_threshold=0.29（運用閾値）の行 | ✓ |
| 0.80 | 本文§2.6.5 , 本文§3.5 , SM(前付け) | TableS1.csv[good definition (state F1 >=)] | 掃引上限（表の最大行） | ✓ |
| 0.8004 | SM(前付け) | TableS3.csv[State F1]（260706_ch1 の行） | セル値 | ✓ |
| 0.8042 | 本文§3.1 | int_bin_sweep_agg.csv[intensity_r_mean_of_means] | 最小 ほか候補 1 件 | ✓ |
| 0.807 | 本文§3.6 | int_sensor_swap.csv[set1_r] | 最小 ほか候補 9 件 | ○ |
| 0.8075 | SM(前付け) | TableS4.csv[Detection ratio, block 2 (mid)]（260629 の行） | セル値 | ✓ |
| 0.8085 | SM(前付け) | TableS3.csv[State F1]（260629_ch2 の行） | セル値 | ✓ |
| 0.8115 | SM(前付け) | TableS4.csv[Detection ratio, block 3]（260706 の行） | セル値 | ✓ |
| 0.8130 | 本文表本体 , SM(前付け) | TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_1 の行） | セル値 | ✓ |
| 0.8141 | 本文Figure 5 , 本文§3.5 , SM(前付け) | TableS6.csv[95% CI upper]（State F1 (QC-passing channels) の行） | セル値 | ✓ |
| 0.8146 | SM(前付け) | TableS3.csv[State F1]（260626_ch2 の行） / TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_5 の行） | セル値 | ✓ |
| 0.8210 | 本文§3.1 , 本文§3.3 | int_feature_bench.csv[mean_r] | 生値 ほか候補 1 件 | ✓ |
| 0.8241 | 本文§3.5 , SM Table S1 | TableS1.csv[State F1 after QC]（0.8 の行） | セル値 | ✓ |
| 0.8254 | 本文Figure 5 , SM(前付け) | TableS6.csv[95% CI lower]（AUC (par) の行） | セル値 | ✓ |
| 0.8270 | 本文表本体 , SM(前付け) | TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_4 の行） | セル値 | ✓ |
| 0.831 | 本文§3.4 | int_channel.csv[F1_state] | 生値（ch=260626_ch6） | ✓ |
| 0.8312 | SM(前付け) | TableS3.csv[State F1]（260626_ch6 の行） | セル値 | ✓ |
| 0.8340 | 本文Figure 5 | 本文 Figure 5 キャプション内で導出 | 1 − 0.1660（GMM 分離度の AUC） | ✓ |
| 0.8421 | SM(前付け) | TableS1.csv[Specificity]（0.7 の行） | セル値 | ✓ |
| 0.8462 | SM(前付け) | TableS2.csv[AUC (par)]（2 の行） | セル値 | ✓ |
| 0.8515 | 本文§3.4 , 本文§3.7 , SM(前付け) | int_channel.csv[F1_state] | 生値（Record 2 ch6） | ✓ |
| 0.8524 | SM(前付け) | TableS3.csv[State F1]（260629_ch1 の行） | セル値 | ✓ |
| 0.8525 | 本文§3.3 | int_channel.csv[intensity_r_lightincl] | 平均 ほか候補 1 件 | ✓ |
| 0.8630 | 本文表本体 , SM(前付け) | TableS3.csv[State F1]（260626_ch4 の行） / TableS5.csv[Hold-out state F1 (held-out animal)]（mouse_6 の行） | セル値 | ✓ |
| 0.8636 | SM 表本体 | TableS1.csv[Specificity]（0.75 の行） | セル値 | ✓ |
| 0.8692 | SM(前付け) | TableS3.csv[State F1]（260629_ch8 の行） | セル値 | ✓ |
| 0.87 | 本文§4.2 | int_bin_sweep_agg.csv[intensity_r_median_of_medians] | 平均 ほか候補 120 件 | ○ |
| 0.870 | SM 表本体 | TableS1.csv[PPV]（0.6 の行） | セル値 | ✓ |
| 0.8721 | 本文§3.3 , 本文表本体 , SMFigure S4 | int_permouse_values.csv[intensity_r] | 最小 ほか候補 2 件 | ○ |
| 0.875 | 本文§3.5 , SM(前付け) | TableS1.csv[PPV] | good_cut=0.80 の行 | ✓ |
| 0.8750 | SM(前付け) | TableS1.csv[Sensitivity]（0.8 の行） | セル値 | ✓ |
| 0.8824 | SM 表本体 | TableS1.csv[Sensitivity]（0.65 の行） | セル値 | ✓ |
| 0.8875 | 本文§3.6 | int_darkdef_sensitivity.csv[intensity_r] | 生値 ほか候補 3 件 | ○ |
| 0.89 | 本文§3.5 | TableS1.csv[AUC (par)] | 全 6 条件の最小（0.8902） | ✓ |
| 0.8902 | SM 表本体 | TableS1.csv[AUC (par)]（0.65 の行） | セル値 | ✓ |
| 0.8955 | SM 表本体 | TableS1.csv[AUC (par)]（0.6 の行） | セル値 | ✓ |
| 0.8986 | 本文Figure 3 , 本文§3.3 , SM(前付け) | TableS6.csv[95% CI lower]（Intensity r (mean of mouse means) の行） | セル値 | ✓ |
| 0.9000 | SM 表本体 | TableS1.csv[Sensitivity]（0.75 の行） | セル値 | ✓ |
| 0.9091 | SM 表本体 | TableS1.csv[Sensitivity]（0.6 の行） | セル値 | ✓ |
| 0.9092 | 本文§3.7 | int_darkdef_sensitivity_agg.csv[mean_of_mouse_means] | 最小 ほか候補 7 件 | ○ |
| 0.9096 | 本文§3.7 | int_darkdef_sensitivity_agg.csv[mean_of_mouse_means] | 中央値 ほか候補 1 件 | ✓ |
| 0.9131 | 本文表本体 , SMFigure S4 | int_lpf_sweep.csv[intensity_r] | 生値 ほか候補 1 件 | ✓ |
| 0.9133 | 本文§3.3 , 本文§3.7 , SMFigure S6 | int_loso_r.csv[r_test] | 最小 ほか候補 2 件 | ○ |
| 0.9155 | 本文Figure 3 , 本文§3.3 , 本文§4.1 | int_channel.csv[intensity_r_activeonly] | 平均 ほか候補 3 件 | ○ |
| 0.9157 | 本文§3.7 | int_bin_sweep.csv[intensity_r] | 生値 ほか候補 3 件 | ○ |
| 0.9159 | 本文表本体 , SMFigure S4 | int_lpf_sweep_agg.csv[intensity_r_mean_of_means] | 中央値 ほか候補 3 件 | ○ |
| 0.9171 | 本文(前付け) , 本文§3.1 , 本文§3.2 … | TableS6.csv[Point estimate]（Intensity r (mean of mouse means) の行） | セル値 | ✓ |
| 0.9172 | 本文§3.2 , 本文§3.7 , 本文表本体 … | int_darkdef_sensitivity_agg.csv[mean_of_mouse_means] | 最大 ほか候補 3 件 | ○ |
| 0.9174 | 本文§3.7 | int_learning_curve.csv[intensity_r] | 個体中央値 | ✓ |
| 0.9177 | 本文§3.7 , 本文§4.6 | int_loso_r.csv[r_test] | 生値 ほか候補 1 件 | ✓ |
| 0.9178 | 本文§3.1 | int_feature_bench.csv[mean_r] | 最大 ほか候補 2 件 | ○ |
| 0.9207 | 本文§3.6 | int_sensor_retest.csv[setB_r] | 平均 ほか候補 15 件 | ○ |
| 0.9226 | 本文§3.6 | int_darkdef_sensitivity.csv[intensity_r] | 個体中央値 ほか候補 15 件 | ○ |
| 0.9231 | 本文(前付け) , 本文Figure 5 , 本文§3.5 … | TableS1.csv[AUC (par)]（0.7 の行） / TableS1.csv[Sensitivity]（0.7 の行） / TableS2.csv[AUC (par)]（1 の行） / TableS6.csv[Point estimate]（AUC (par) の行） | セル値 | ✓ |
| 0.9236 | 本文§3.3 , 本文§3.7 , SMFigure S6 | int_loso_r.csv[r_test] | 最大 ほか候補 2 件 | ○ |
| 0.9238 | 本文表本体 , SMFigure S4 | int_permouse_values.csv[intensity_r] | 生値 ほか候補 1 件 | ✓ |
| 0.9253 | 本文表本体 , SMFigure S4 | int_channel.csv[intensity_r_darkonly_24grid] | 中央値 ほか候補 4 件 | ○ |
| 0.9259 | 本文表本体 , SMFigure S4 | int_permouse_values.csv[intensity_r] | 生値 ほか候補 2 件 | ○ |
| 0.926 | 本文表本体 | int_channel.csv[gmm_separation] | 最小 ほか候補 40 件 | ○ |
| 0.9269 | 本文Figure 3 , 本文§3.3 , SM(前付け) | TableS6.csv[95% CI upper]（Intensity r (mean of mouse means) の行） | セル値 | ✓ |
| 0.930 | 本文§3.5 | 本文§3.5 内で導出 | PPV 12/15 の Wilson 95% CI 上限（0.9295） | ✓ |
| 0.938 | 本文§3.6 | int_bin_sweep.csv[intensity_r] | 生値 ほか候補 28 件 | ○ |
| 0.9390 | 本文§3.2 , 本文Figure 2 | int_bin_sweep.csv[intensity_r] | 生値 ほか候補 5 件 | ○ |
| 0.9409 | SM 表本体 | TableS1.csv[AUC (par)]（0.75 の行） | セル値 | ✓ |
| 0.9421 | 本文(前付け) , 本文§3.6 , 本文Figure 6 … | TableS6.csv[Point estimate]（Inter-sensor r の行） | セル値 | ✓ |
| 0.9437 | 本文§3.3 , 本文表本体 , SMFigure S4 | int_permouse_values.csv[intensity_r] | 最大 ほか候補 4 件 | ○ |
| 0.9583 | SM(前付け) | TableS1.csv[AUC (par)]（0.8 の行） / TableS1.csv[Specificity]（0.8 の行） | セル値 | ✓ |
| 0.9617 | 本文Figure 2 , 本文§3.2 | int_state_confusion_perch.csv[specificity] | 中央値 ほか候補 1 件 | ✓ |
| 0.978 | 本文§3.5 | 本文§3.5 内で導出 | PPV 7/8 の Wilson 95% CI 上限（0.9776） | ✓ |
| 0.9896 | 本文§3.6 | int_channel.csv[within_over_between] | 平均 ほか候補 2 件 | ○ |
| 0.99 | 本文§1 | int_auc_boot.csv[diff_ci_upper] | 最大 ほか候補 53 件 | ○ |
| 1.0000 | SM 表本体 | TableS1.csv[AUC (par)]（0.55 の行） / TableS1.csv[Sensitivity]（0.55 の行） / TableS1.csv[Specificity]（0.55 の行） | セル値 | ✓ |
| 1.000 | 本文Figure 5 , SM(前付け) | int_auc_metrics_cluster.csv[ci_upper] | metric=pir_active_rate の行 | ✓ |
| 1.17 | 本文§2.7.5 , 本文§3.7 | int_bland_altman.csv[loa_upper] | SD ほか候補 12 件 | ○ |
| 1.2217 | 本文§3.6 | int_bland_altman.csv[bias] | 最大 ほか候補 1 件 | ✓ |
| 1.25 | 本文§4.5 , 本文§4.6 | int_holdout_f1.csv[n_pass_ch] | SD ほか候補 10 件 | ○ |
| 1.29 | 本文表本体 | int_auc_boot.csv[diff_observed] | 合計 ほか候補 9 件 | ○ |
| 1.3875 | 本文§3.6 | int_channel.csv[snr] | 生値 | ✓ |
| 1.552 | 本文表本体 | int_channel.csv[gmm_separation] | 生値 | ✓ |
| 1.62 | 本文表本体 | int_qc_anatomy.csv[gmm_separation] | 最大 ほか候補 11 件 | ○ |
| 1.77 | 本文§3.6 | int_bland_altman.csv[sd_diff] | 最大 ほか候補 10 件 | ○ |
| 1.91 | 本文§3.7 | int_channel.csv[gmm_rest_sd] | 最大 ほか候補 6 件 | ○ |
| 2.15 | 本文§3.7 | int_channel.csv[pai_sd_active] | 生値 ほか候補 4 件 | ○ |
| 2.47 | 本文§3.5 | int_channel.csv[median_nb_fn] | ch ごとの中央値のチャンネル間平均 | ✓ |
| 2.87 | 本文§3.6 | int_channel.csv[snr] | 生値 ほか候補 4 件 | ○ |
| 3.13 | 本文§2.7.5 | — | 抽出の誤検出。「Python 3.13.14」のバージョン番号であり、データの値ではない | ✓ |
| 6.892 | 本文表本体 | int_qc_anatomy.csv[snr] | 中央値 | ✓ |
| 7.336 | 本文表本体 | int_qc_anatomy.csv[snr] | 最大 ほか候補 2 件 | ○ |
| 8.88 | 本文§4.6 | 本文§3.7 内で導出 | −10.62 −(−19.50) | ✓ |
| 9.17 | 本文§3.5 | int_channel.csv[median_nb_tp] / [median_nb_fn] | 比の中央値（9.1667、範囲 4.00–16.67） | ✓ |
| 15.174 | 本文表本体 | int_channel.csv[snr] | 生値 | ✓ |
| 24.69 | 本文§3.5 | int_channel.csv[median_nb_tp] | ch ごとの中央値のチャンネル間平均 | ✓ |
| 102.65 | 本文Figure 1 , 本文§3.1 | figure_values_good070.csv[fig1_variance_ratio_raw] | ch=260626_ch4 variant=high | ✓ |
| 1082.65 | 本文Figure 1 , 本文§3.1 | figure_values_good070.csv[fig1_variance_ratio_lpf] | ch=260626_ch4 variant=high | ✓ |

