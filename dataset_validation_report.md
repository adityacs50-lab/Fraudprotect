# PaySim Post-Import Validation Report

This report verifies that the PaySim dataset import is correct, believable, and operationally useful.

## 1. Data Mapping Sanity
| Field | Source (PaySim) | Mapped (FraudShield) | Validation |
| :--- | :--- | :--- | :--- |
| **Identity** | `nameOrig` | `user_id` | 1:1 mapping preserved. 100k unique users verified in first 100k rows. |
| **Time** | `step` | `timestamp` | Monotonic 1-hour steps converted to UTC ISO strings starting 2026-03-01. |
| **Amount** | `amount` | `amount` | Float precision preserved. No truncation or coercion issues. |
| **Categorical** | `type` | `merchant_category` | `PAYMENT` -> `online_shopping`, `CASH_OUT` -> `electronics`. |
| **Location** | - | `city`, `lat`, `lon` | Synthesized based on user-city mapping for stability. |
| **Device** | - | `device_id` | Stabilized per-user to prevent "new device" spam on every transaction. |

## 2. Global Metrics
- **Total Transactions**: 100,000
- **True Fraud Labels**: 116 (0.12%)
- **System Alerts Generated**: 34,255 (Initial: 71,195)
- **Caught Fraud (Recall)**: 76.7% (at 0.5 threshold)

## 3. Performance Analysis
### Confusion Matrix (Threshold 0.5)
| | Predicted Negative | Predicted Positive |
| :--- | :--- | :--- |
| **Actual Negative** | 98,690 (TN) | 1,194 (FP) |
| **Actual Positive** | 27 (FN) | 89 (TP) |

### Key Metrics
- **ROC-AUC**: 0.9673
- **PR-AUC**: 0.1420
- **Precision**: 6.94%
- **Recall**: 76.72%
- **F1 Score**: 0.1272

## 4. Threshold Sweep & Operational Tuning
The system default threshold (0.5) produces a 1.28% alert rate from the ML model, but rules drive total alerts higher.

| Threshold | Precision | Recall | Alert Rate | False Positives |
| :--- | :--- | :--- | :--- | :--- |
| 0.30 | 4.13% | 90.52% | 2.54% | 2,436 |
| 0.40 | 5.03% | 86.21% | 1.99% | 1,886 |
| 0.50 | 6.94% | 76.72% | 1.28% | 1,194 |
| 0.60 | 10.80% | 33.62% | 0.36% | 322 |

> [!TIP]
> **Operational Recommendation**: 
> - Set **Review Threshold** to **0.40** to capture 86% of fraud with a manageable 2% queue rate.
> - Set **Block Threshold** to **0.80** for near-zero false positives.

## 5. Feature Engineering Audit
- **`is_new_device`**: Corrected logic to only flag *subsequent* new devices for a known user. Since every user in the first 100k rows is new, `is_new_device` is currently 0% for this batch.
- **`amount_zscore`**: Correctly identifies outliers for users with multiple transactions.
- **Rule Engine**: Dominant rule is `high_merchant_risk` (electronics > 5000), triggering on ~30% of rows. This reflects PaySim's high-value cash-out nature and should be calibrated (e.g., increase amount threshold to 15,000).

## 6. System Integrity
- **Database Persistence**: 100k transactions and 34k alerts successfully persisted.
- **Dashboard Consistency**: UI counts match database totals.
- **Explainability**: SHAP reasons for `CASH_OUT` correctly highlight high amount and merchant risk.
