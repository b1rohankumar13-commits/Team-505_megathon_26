# Lloyds ML results

Cutoff: 2025-12-31. Outcome window: 6 months.

## Data sizes

| table | rows |
| --- | --- |
| customers | 1000 |
| transactions | 84112 |
| products | 1563 |
| vehicles | 803 |
| energy | 12000 |
| digital | 12000 |
| labels_transactions | 84112 |
| labels_takeup | 4000 |

## Customers and positives

| split | product | customers | positive | negative |
| --- | --- | --- | --- | --- |
| train | GP01 | 700 | 184 | 516 |
| train | GP02 | 700 | 117 | 583 |
| train | GP03 | 700 | 67 | 633 |
| train | GP04 | 700 | 156 | 544 |
| val | GP01 | 150 | 41 | 109 |
| val | GP02 | 150 | 22 | 128 |
| val | GP03 | 150 | 10 | 140 |
| val | GP04 | 150 | 39 | 111 |
| test | GP01 | 150 | 40 | 110 |
| test | GP02 | 150 | 25 | 125 |
| test | GP03 | 150 | 17 | 133 |
| test | GP04 | 150 | 37 | 113 |

## categoriser validation

| partition | model | macro_f1 | accuracy | unseen_merchants_rows | unseen_merchant_accuracy |
| --- | --- | --- | --- | --- | --- |
| val | ml_only | 1.00000 | 1.00000 | 0 | N/A |
| val | hybrid | 0.95085 | 0.95345 | 0 | N/A |
| val | rules | 0.53208 | 0.63815 | 0 | N/A |

### ml_only per-class results

| category | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| Fuel | 1.00000 | 1.00000 | 1.00000 | 1152 |
| Electricity | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Gas | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Public Transport | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Home Improvement | 1.00000 | 1.00000 | 1.00000 | 229 |
| Automotive | 1.00000 | 1.00000 | 1.00000 | 280 |
| Utilities | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Other | 1.00000 | 1.00000 | 1.00000 | 3600 |

Boundary confusions

| actual | predicted | errors |
| --- | --- | --- |
| Fuel | Automotive | 0 |
| Automotive | Fuel | 0 |
| Electricity | Utilities | 0 |
| Utilities | Electricity | 0 |
| Gas | Utilities | 0 |
| Utilities | Gas | 0 |

### hybrid per-class results

| category | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| Fuel | 0.66513 | 1.00000 | 0.79889 | 1152 |
| Electricity | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Gas | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Public Transport | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Home Improvement | 1.00000 | 1.00000 | 1.00000 | 229 |
| Automotive | 1.00000 | 1.00000 | 1.00000 | 280 |
| Utilities | 1.00000 | 0.67778 | 0.80795 | 1800 |
| Other | 1.00000 | 1.00000 | 1.00000 | 3600 |

Boundary confusions

| actual | predicted | errors |
| --- | --- | --- |
| Fuel | Automotive | 0 |
| Automotive | Fuel | 0 |
| Electricity | Utilities | 0 |
| Utilities | Electricity | 0 |
| Gas | Utilities | 0 |
| Utilities | Gas | 0 |

### rules per-class results

| category | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| Fuel | 0.66513 | 1.00000 | 0.79889 | 1152 |
| Electricity | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Gas | 1.00000 | 0.33000 | 0.49624 | 1800 |
| Public Transport | 1.00000 | 0.34333 | 0.51117 | 1800 |
| Home Improvement | 0.00000 | 0.00000 | 0.00000 | 229 |
| Automotive | 1.00000 | 0.67143 | 0.80342 | 280 |
| Utilities | 0.00000 | 0.00000 | 0.00000 | 1800 |
| Other | 0.47815 | 1.00000 | 0.64696 | 3600 |

Boundary confusions

| actual | predicted | errors |
| --- | --- | --- |
| Fuel | Automotive | 0 |
| Automotive | Fuel | 0 |
| Electricity | Utilities | 0 |
| Utilities | Electricity | 0 |
| Gas | Utilities | 0 |
| Utilities | Gas | 0 |

## categoriser test

| partition | model | macro_f1 | accuracy | unseen_merchants_rows | unseen_merchant_accuracy |
| --- | --- | --- | --- | --- | --- |
| test | ml_only | 1.00000 | 1.00000 | 0 | N/A |
| test | hybrid | 0.95637 | 0.95645 | 0 | N/A |
| test | rules | 0.53634 | 0.64256 | 0 | N/A |

### ml_only per-class results

| category | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| Fuel | 1.00000 | 1.00000 | 1.00000 | 1380 |
| Electricity | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Gas | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Public Transport | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Home Improvement | 1.00000 | 1.00000 | 1.00000 | 243 |
| Automotive | 1.00000 | 1.00000 | 1.00000 | 298 |
| Utilities | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Other | 1.00000 | 1.00000 | 1.00000 | 3600 |

Boundary confusions

| actual | predicted | errors |
| --- | --- | --- |
| Fuel | Automotive | 0 |
| Automotive | Fuel | 0 |
| Electricity | Utilities | 0 |
| Utilities | Electricity | 0 |
| Gas | Utilities | 0 |
| Utilities | Gas | 0 |

### hybrid per-class results

| category | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| Fuel | 0.71355 | 1.00000 | 0.83283 | 1380 |
| Electricity | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Gas | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Public Transport | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Home Improvement | 1.00000 | 1.00000 | 1.00000 | 243 |
| Automotive | 1.00000 | 1.00000 | 1.00000 | 298 |
| Utilities | 1.00000 | 0.69222 | 0.81812 | 1800 |
| Other | 1.00000 | 1.00000 | 1.00000 | 3600 |

Boundary confusions

| actual | predicted | errors |
| --- | --- | --- |
| Fuel | Automotive | 0 |
| Automotive | Fuel | 0 |
| Electricity | Utilities | 0 |
| Utilities | Electricity | 0 |
| Gas | Utilities | 0 |
| Utilities | Gas | 0 |

### rules per-class results

| category | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| Fuel | 0.71355 | 1.00000 | 0.83283 | 1380 |
| Electricity | 1.00000 | 1.00000 | 1.00000 | 1800 |
| Gas | 1.00000 | 0.34444 | 0.51240 | 1800 |
| Public Transport | 1.00000 | 0.31389 | 0.47780 | 1800 |
| Home Improvement | 0.00000 | 0.00000 | 0.00000 | 243 |
| Automotive | 1.00000 | 0.70134 | 0.82446 | 298 |
| Utilities | 0.00000 | 0.00000 | 0.00000 | 1800 |
| Other | 0.47412 | 1.00000 | 0.64326 | 3600 |

Boundary confusions

| actual | predicted | errors |
| --- | --- | --- |
| Fuel | Automotive | 0 |
| Automotive | Fuel | 0 |
| Electricity | Utilities | 0 |
| Utilities | Electricity | 0 |
| Gas | Utilities | 0 |
| Utilities | Gas | 0 |

## Validation ablation metrics

| product | variant | model | pr_auc | roc_auc | brier | lift_top10 | precision_at_k | k | customers | positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GP01 | all_train | xgb | 0.60034 | 0.82435 | 0.15362 | 2.19512 | 0.60000 | 15 | 150 | 41 |
| GP01 | all_train | logreg | 0.53428 | 0.80533 | 0.16711 | 1.70732 | 0.46667 | 15 | 150 | 41 |
| GP01 | all_train | rule | 0.49598 | 0.76740 | 0.20053 | 1.70732 | 0.46667 | 15 | 150 | 41 |
| GP01 | inliers_only | xgb | 0.60201 | 0.83061 | 0.15063 | 2.68293 | 0.73333 | 15 | 150 | 41 |
| GP01 | inliers_only | logreg | 0.52610 | 0.80622 | 0.16817 | 1.95122 | 0.53333 | 15 | 150 | 41 |
| GP01 | inliers_only | rule | 0.49550 | 0.76717 | 0.20100 | 1.70732 | 0.46667 | 15 | 150 | 41 |
| GP02 | all_train | xgb | 0.43215 | 0.80646 | 0.10633 | 3.63636 | 0.53333 | 15 | 150 | 22 |
| GP02 | all_train | logreg | 0.38521 | 0.78161 | 0.16344 | 2.27273 | 0.33333 | 15 | 150 | 22 |
| GP02 | all_train | rule | 0.32214 | 0.74876 | 0.29751 | 1.81818 | 0.26667 | 15 | 150 | 22 |
| GP02 | inliers_only | xgb | 0.37015 | 0.81534 | 0.10986 | 1.81818 | 0.26667 | 15 | 150 | 22 |
| GP02 | inliers_only | logreg | 0.38368 | 0.77450 | 0.16512 | 2.27273 | 0.33333 | 15 | 150 | 22 |
| GP02 | inliers_only | rule | 0.32214 | 0.74876 | 0.29763 | 1.81818 | 0.26667 | 15 | 150 | 22 |
| GP03 | all_train | xgb | 0.22204 | 0.77429 | 0.05887 | 3.00000 | 0.20000 | 15 | 150 | 10 |
| GP03 | all_train | logreg | 0.22956 | 0.75143 | 0.16351 | 2.00000 | 0.13333 | 15 | 150 | 10 |
| GP03 | all_train | rule | 0.10809 | 0.66214 | 0.33138 | 1.00000 | 0.06667 | 15 | 150 | 10 |
| GP03 | inliers_only | xgb | 0.30260 | 0.69107 | 0.06073 | 3.00000 | 0.20000 | 15 | 150 | 10 |
| GP03 | inliers_only | logreg | 0.22932 | 0.75071 | 0.16364 | 2.00000 | 0.13333 | 15 | 150 | 10 |
| GP03 | inliers_only | rule | 0.10809 | 0.66214 | 0.33117 | 1.00000 | 0.06667 | 15 | 150 | 10 |
| GP04 | all_train | xgb | 0.49360 | 0.81370 | 0.14282 | 2.56410 | 0.66667 | 15 | 150 | 39 |
| GP04 | all_train | logreg | 0.50797 | 0.79972 | 0.18511 | 2.05128 | 0.53333 | 15 | 150 | 39 |
| GP04 | all_train | rule | 0.33595 | 0.68815 | 0.27184 | 0.76923 | 0.20000 | 15 | 150 | 39 |
| GP04 | inliers_only | xgb | 0.56244 | 0.83576 | 0.13930 | 2.82051 | 0.73333 | 15 | 150 | 39 |
| GP04 | inliers_only | logreg | 0.49797 | 0.79834 | 0.18688 | 2.05128 | 0.53333 | 15 | 150 | 39 |
| GP04 | inliers_only | rule | 0.33595 | 0.68815 | 0.27348 | 0.76923 | 0.20000 | 15 | 150 | 39 |

## Selected ablations

| product | selected | selection_rule | all_train_n | inlier_train_n |
| --- | --- | --- | --- | --- |
| GP01 | inliers_only | validation Pareto dominance | 700 | 695 |
| GP02 | all_train | validation dominance or tie | 700 | 695 |
| GP03 | inliers_only | validation AP minus Brier trade-off (declared before evaluation) | 700 | 695 |
| GP04 | inliers_only | validation Pareto dominance | 700 | 695 |

## GP01 final test (before exclusions)

| model | pr_auc | roc_auc | brier | lift_top10 | precision_at_k | k | customers | positive | threshold | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb | 0.45110 | 0.74682 | 0.16657 | 2.00000 | 0.53333 | 15 | 150 | 40 | 0.18405 | 0.38776 | 0.95000 | 0.55072 |
| logreg | 0.49176 | 0.74886 | 0.21629 | 2.50000 | 0.66667 | 15 | 150 | 40 | 0.42802 | 0.38824 | 0.82500 | 0.52800 |
| rule | 0.46691 | 0.69523 | 0.25507 | 2.00000 | 0.53333 | 15 | 150 | 40 | 0.17553 | 0.35088 | 1.00000 | 0.51948 |

## GP01 confidence

C = D**3 * S; selected S=calibrated_certainty. D=mean observed coverage of four data blocks; ensemble agreement=1-2*std(seed probabilities); certainty=1-binary_entropy(p)/log(2); margin=abs(2*p-1); blend weights={'ensemble_spread': 0.25, 'calibrated_certainty': 0.35, 'data_completeness': 0.2, 'margin': 0.2}. Percentiles use training customers only. If no method passes validation, the runner stops and saves the comparison table.

| method | spearman | brier_low | brier_middle | brier_high | n_low | n_middle | n_high | eligible | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ensemble_spread | -0.30662 | 0.06111 | 0.21617 | 0.17461 | 50 | 50 | 50 | False | False |
| calibrated_certainty | 0.64356 | 0.24299 | 0.11113 | 0.09205 | 50 | 65 | 35 | True | True |
| data_completeness | -0.63393 | 0.15063 | N/A | N/A | 150 | 0 | 0 | False | False |
| blend | -0.19186 | 0.05054 | 0.24739 | 0.15396 | 50 | 50 | 50 | False | False |

## GP02 final test (before exclusions)

| model | pr_auc | roc_auc | brier | lift_top10 | precision_at_k | k | customers | positive | threshold | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb | 0.30311 | 0.73952 | 0.12746 | 2.40000 | 0.40000 | 15 | 150 | 25 | 0.28115 | 0.31429 | 0.44000 | 0.36667 |
| logreg | 0.23272 | 0.66976 | 0.22926 | 1.60000 | 0.26667 | 15 | 150 | 25 | 0.47112 | 0.23810 | 0.60000 | 0.34091 |
| rule | 0.37879 | 0.71040 | 0.31079 | 2.40000 | 0.40000 | 15 | 150 | 25 | 0.80295 | 0.29730 | 0.44000 | 0.35484 |

## GP02 confidence

C = D**3 * S; selected S=calibrated_certainty. D=mean observed coverage of four data blocks; ensemble agreement=1-2*std(seed probabilities); certainty=1-binary_entropy(p)/log(2); margin=abs(2*p-1); blend weights={'ensemble_spread': 0.25, 'calibrated_certainty': 0.35, 'data_completeness': 0.2, 'margin': 0.2}. Percentiles use training customers only. If no method passes validation, the runner stops and saves the comparison table.

| method | spearman | brier_low | brier_middle | brier_high | n_low | n_middle | n_high | eligible | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ensemble_spread | 0.23805 | 0.09641 | 0.16113 | 0.06146 | 50 | 50 | 50 | True | False |
| calibrated_certainty | 0.77060 | 0.19619 | 0.08609 | 0.03672 | 50 | 50 | 50 | True | True |
| data_completeness | -0.14312 | 0.10633 | N/A | N/A | 150 | 0 | 0 | False | False |
| blend | 0.39958 | 0.11645 | 0.16581 | 0.03674 | 50 | 50 | 50 | True | False |

## GP03 final test (before exclusions)

| model | pr_auc | roc_auc | brier | lift_top10 | precision_at_k | k | customers | positive | threshold | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb | 0.22307 | 0.74856 | 0.09450 | 2.35294 | 0.26667 | 15 | 150 | 17 | 0.27749 | 0.14286 | 0.05882 | 0.08333 |
| logreg | 0.19594 | 0.70323 | 0.20484 | 1.17647 | 0.13333 | 15 | 150 | 17 | 0.55672 | 0.16667 | 0.47059 | 0.24615 |
| rule | 0.30418 | 0.71473 | 0.30310 | 2.35294 | 0.26667 | 15 | 150 | 17 | 0.67538 | 0.16949 | 0.58824 | 0.26316 |

## GP03 confidence

C = D**3 * S; selected S=calibrated_certainty. D=mean observed coverage of four data blocks; ensemble agreement=1-2*std(seed probabilities); certainty=1-binary_entropy(p)/log(2); margin=abs(2*p-1); blend weights={'ensemble_spread': 0.25, 'calibrated_certainty': 0.35, 'data_completeness': 0.2, 'margin': 0.2}. Percentiles use training customers only. If no method passes validation, the runner stops and saves the comparison table.

| method | spearman | brier_low | brier_middle | brier_high | n_low | n_middle | n_high | eligible | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ensemble_spread | 0.29203 | 0.08162 | 0.08053 | 0.02003 | 50 | 50 | 50 | True | False |
| calibrated_certainty | 0.65441 | 0.10238 | 0.05959 | 0.02021 | 50 | 50 | 50 | True | True |
| data_completeness | 0.03857 | 0.06073 | N/A | N/A | 150 | 0 | 0 | False | False |
| blend | 0.57710 | 0.09906 | 0.07988 | 0.00324 | 50 | 50 | 50 | True | False |

## GP04 final test (before exclusions)

| model | pr_auc | roc_auc | brier | lift_top10 | precision_at_k | k | customers | positive | threshold | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| xgb | 0.47566 | 0.78833 | 0.14461 | 2.70270 | 0.66667 | 15 | 150 | 37 | 0.37049 | 0.41176 | 0.75676 | 0.53333 |
| logreg | 0.50611 | 0.80244 | 0.19847 | 2.16216 | 0.53333 | 15 | 150 | 37 | 0.12402 | 0.38144 | 1.00000 | 0.55224 |
| rule | 0.28048 | 0.61217 | 0.31024 | 1.08108 | 0.26667 | 15 | 150 | 37 | 0.45827 | 0.36559 | 0.91892 | 0.52308 |

## GP04 confidence

C = D**3 * S; selected S=calibrated_certainty. D=mean observed coverage of four data blocks; ensemble agreement=1-2*std(seed probabilities); certainty=1-binary_entropy(p)/log(2); margin=abs(2*p-1); blend weights={'ensemble_spread': 0.25, 'calibrated_certainty': 0.35, 'data_completeness': 0.2, 'margin': 0.2}. Percentiles use training customers only. If no method passes validation, the runner stops and saves the comparison table.

| method | spearman | brier_low | brier_middle | brier_high | n_low | n_middle | n_high | eligible | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ensemble_spread | 0.42314 | 0.15995 | 0.22610 | 0.02374 | 50 | 52 | 48 | True | False |
| calibrated_certainty | 0.81002 | 0.23283 | 0.13818 | 0.00000 | 66 | 40 | 44 | True | True |
| data_completeness | -0.00874 | 0.13930 | N/A | N/A | 150 | 0 | 0 | False | False |
| blend | 0.46254 | 0.15030 | 0.22987 | 0.03772 | 50 | 50 | 50 | True | False |

## Reproducibility

{"features": "identical", "probabilities": "identical", "validation_metrics": "identical", "test_repeated": false}

## Scenario tests

{"profiles": 9, "predictions": 36, "assertions": "passed"}

## Runtimes

| stage | seconds | success |
| --- | --- | --- |
| 1/load and clean | 0.48071 | True |
| 2/shared stratified customer split | 0.03611 | True |
| 3/train-only energy RANSAC flags | 0.04140 | True |
| 4/categoriser training and validation | 81.45883 | True |
| 5/OOF categories, Customer 360 and customer RANSAC | 17.78613 | True |
| 6/ablation/GP01/all_train | 4.40343 | True |
| 6/ablation/GP01/inliers_only | 1.08494 | True |
| 6/ablation/GP02/all_train | 1.19642 | True |
| 6/ablation/GP02/inliers_only | 1.17814 | True |
| 6/ablation/GP03/all_train | 1.97341 | True |
| 6/ablation/GP03/inliers_only | 0.48433 | True |
| 6/ablation/GP04/all_train | 2.28271 | True |
| 6/ablation/GP04/inliers_only | 0.44128 | True |
| 6/propensity ablation on validation | 13.28368 | True |
| 6/reproducibility/GP01/all_train | 4.31576 | True |
| 6/reproducibility/GP01/inliers_only | 1.07201 | True |
| 6/reproducibility/GP02/all_train | 1.25215 | True |
| 6/reproducibility/GP02/inliers_only | 1.14984 | True |
| 6/reproducibility/GP03/all_train | 1.86542 | True |
| 6/reproducibility/GP03/inliers_only | 0.47774 | True |
| 6/reproducibility/GP04/all_train | 2.17048 | True |
| 6/reproducibility/GP04/inliers_only | 0.42179 | True |
| 11/reproduce steps 5–6 before opening TEST | 30.56712 | True |
| 7–8/GP01/confidence, thresholds and reason checks | 0.57226 | True |
| 7–8/GP02/confidence, thresholds and reason checks | 0.67617 | True |
| 7–8/GP03/confidence, thresholds and reason checks | 0.22329 | True |
| 7–8/GP04/confidence, thresholds and reason checks | 0.21139 | True |
| 10/scenario tests before final TEST evaluation | 0.19220 | True |
| lock all selections | 0.00550 | True |
| final TEST/GP01 | 0.68169 | True |
| final TEST/GP02 | 0.69017 | True |
| final TEST/GP03 | 0.65960 | True |
| final TEST/GP04 | 0.64225 | True |
| final TEST evaluation; no selection beyond this point | 7.28594 | True |
| 9/prediction exports after exclusions | 1.02454 | True |
| 12/summary and model inventory | 0.01586 | True |

## Model file sizes

| file | bytes |
| --- | --- |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP01\all_train\propensity_GP01.joblib | 876051 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP01\inliers_only\propensity_GP01.joblib | 691987 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP02\all_train\propensity_GP02.joblib | 713395 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP02\inliers_only\propensity_GP02.joblib | 698979 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP03\all_train\propensity_GP03.joblib | 809523 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP03\inliers_only\propensity_GP03.joblib | 594803 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP04\all_train\propensity_GP04.joblib | 887907 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\ablation\GP04\inliers_only\propensity_GP04.joblib | 595891 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\categoriser.joblib | 108041 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\categoriser_kind.joblib | 21 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\categoriser_use_rules.joblib | 110 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\customer_360.joblib | 695168 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\explain_GP01.joblib | 302133 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\explain_GP02.joblib | 361381 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\explain_GP03.joblib | 90117 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\explain_GP04.joblib | 82293 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\propensity_GP01.joblib | 691987 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\propensity_GP02.joblib | 713395 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\propensity_GP03.joblib | 594803 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\propensity_GP04.joblib | 595891 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP01\all_train\propensity_GP01.joblib | 876051 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP01\inliers_only\propensity_GP01.joblib | 691987 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP02\all_train\propensity_GP02.joblib | 713395 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP02\inliers_only\propensity_GP02.joblib | 698979 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP03\all_train\propensity_GP03.joblib | 809523 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP03\inliers_only\propensity_GP03.joblib | 594803 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP04\all_train\propensity_GP04.joblib | 887907 |
| C:\Users\Asus\Desktop\Team-505_megathon_26\artifacts\reproducibility\GP04\inliers_only\propensity_GP04.joblib | 595891 |

## Limitations

- Synthetic-data metrics measure recovery of the simulator, not real-world performance.
- The supplied labels/splits were inspected in earlier preprocessing; this is not a never-seen external benchmark.
- The requested stratified split is generated anew; it can differ from the earlier split_manifest.csv.
- The same validation set selects early stopping, calibration, ablation, thresholds and confidence; selection estimates are optimistic.
- Confidence is a validation-tested heuristic, not a guarantee or a calibrated correctness probability.
- SHAP describes the deployed XGBoost tree's raw margin, before its monotone calibration transform.
- Rule baseline scores are heuristics, not calibrated adoption probabilities.
- Unseen-merchant accuracy is null when no such merchants occur; 10 errors means up to 10 actual errors.
- Non-vehicle ownership and unrecorded vehicle data are not distinguished by these existing feature modules.
- No source distance unit is declared; annual mileage is used on its supplied scale without km conversion.
- No carbon, lending eligibility or text-generation functionality is included.