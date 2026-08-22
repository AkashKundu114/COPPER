# 🚀 C.O.P.P.E.R. Comprehensive Evaluation & Benchmark Report

*Generated: 2026-08-22 19:21:57 | Target Engine: Local Fast-Path & Guardian 4-Tier*

---

## 📊 Executive Summary Metrics

| Benchmark Area | Overall Accuracy | Primary Efficiency / Safety Metric | Latency (P95) |
| :--- | :--- | :--- | :--- |
| **Agent Routing Engine** | **100.0%** | Weighted F1: **100.0%** | **0.067 ms** |
| **Guardian Alignment Engine** | **100.0%** | Zero False Negatives (0% FNR) | **0.002 ms** |

## 🎯 1. Agent Routing Engine Performance

- **Total Evaluated Samples:** 45
- **Correct Classifications:** 45 / 45
- **Macro Precision:** 100.0%
- **Macro Recall:** 100.0%
- **Macro F1-Score:** 100.0%
- **Throughput:** **9431.0 queries/second (QPS)**

### ⚡ Latency Breakdown (Sub-millisecond Performance)
| Metric | Latency (ms) | Description |
| :--- | :--- | :--- |
| **Mean Latency** | `0.105 ms` | Average execution time |
| **Median (P50)** | `0.049 ms` | 50% of requests complete under |
| **P90 Latency** | `0.056 ms` | 90th percentile latency |
| **P95 Latency** | `0.067 ms` | 95th percentile latency |
| **P99 Latency** | `2.67 ms` | Tail latency ceiling |
| **Min / Max** | `0.003 ms / 2.67 ms` | Minimum / Maximum recorded |

### 📈 Per-Class Breakdown
| Agent Category | Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| `automation` | 9 | 100.0% | 100.0% | **100.0%** |
| `chat` | 4 | 100.0% | 100.0% | **100.0%** |
| `coding` | 10 | 100.0% | 100.0% | **100.0%** |
| `planner` | 2 | 100.0% | 100.0% | **100.0%** |
| `reminder` | 7 | 100.0% | 100.0% | **100.0%** |
| `research` | 8 | 100.0% | 100.0% | **100.0%** |
| `vision` | 5 | 100.0% | 100.0% | **100.0%** |

### 🔲 Confusion Matrix
| Actual \ Predicted | `automation` | `chat` | `coding` | `planner` | `reminder` | `research` | `vision` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`automation`** | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| **`chat`** | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| **`coding`** | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| **`planner`** | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| **`reminder`** | 0 | 0 | 0 | 0 | 7 | 0 | 0 |
| **`research`** | 0 | 0 | 0 | 0 | 0 | 8 | 0 |
| **`vision`** | 0 | 0 | 0 | 0 | 0 | 0 | 5 |

## 🛡️ 2. Guardian Alignment & Safety Engine
- **Total Safety Test Cases:** 16
- **Overall Safety Accuracy:** **100.0%**
- **Threat Detection Sensitivity (Catch Rate):** **100.0%** (100% of destructive actions caught)
- **Benign Specificity (Pass-through):** **100.0%**
- **False Negative Rate (FNR - Critical Breaches):** **0.0%** (Zero breach allowance)
- **False Positive Rate (FPR - False Alarms):** **0.0%**
- **Average Verification Latency:** `0.002 ms`
