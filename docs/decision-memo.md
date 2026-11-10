# Decision Memo — Foundation Reserve Portfolio

> **AI use:** built with Claude Code (Claude Opus 5.5); the analysis and the decision are mine.
> **Education, not investment advice.**

**To:** Foundation investment committee · **From:** Drew Scheiderer, portfolio analyst ·
**Decision date:** 2026-10-30 · **Universe:** BIL / IEF / LQD / VT

## Recommendation

> **TODO (Drew):** your action (adopt, allocate to, rebalance, pilot, or reject), the allocation range,
> the condition, and the committee ask. Use the numbers below; keep them the same as `output/report.txt`.

## The mandate

Expected return at least CPI inflation as known on the decision date plus 4%: **3.72% + 4% = 7.72%**.
Annual volatility at most 10%; at least 3% in BIL for twelve months of payouts; no fund above 70%;
long-only. Benchmark: 60% VT / 40% LQD.

## What the process found

| Portfolio | BIL / IEF / LQD / VT | Expected return | Volatility | Verdict |
|---|---|---:|---:|---|
| Equal weight | 25 / 25 / 25 / 25 | 6.05% | 7.49% | fail: below the objective |
| Benchmark 60/40 | 0 / 0 / 40 / 60 | 8.21% | 12.23% | fail: volatility cap; no BIL reserve |
| **Constrained portfolio** | **35 / 0 / 0 / 65** | **7.80%** | **9.69%** | **pass** |

The constrained portfolio is the lowest-volatility long-only mix, in 5-point steps, that passes every rule.
It clears the objective by 0.08 points and the volatility cap by 0.31 points. Over the last 60 months,
held with monthly rebalancing, it returned 7.95% a year with a maximum drawdown of 16.93%. That is history,
not a forecast.

## How fragile it is

| Stress (one change) | Result |
|---|---|
| Equity risk premium 1 point lower | **no mix meets the mandate** |
| Equity risk premium 1 point higher | 45 / 0 / 0 / 55 (10 points move) |
| Inflation 1 point higher | **no mix meets the mandate** |
| Risk from the last 36 months only | unchanged |
| Extra 0.25% a year in costs | **no mix meets the mandate** |
| Volatility cap 1 point tighter | **no mix meets the mandate** |
| Largest fund at most 60% | 25 / 5 / 10 / 60 (10 points move) |
| BIL reserve at least 10% | unchanged |

**Allocation range** across the cases that still have a mix: BIL 25–45%, IEF 0–5%, LQD 0–10%, VT 55–65%.

**Stop conditions (computed):** no mix passes if the equity risk premium is below **4.85%** or CPI
inflation is above **3.82%**. Inflation is 3.72% today.

## Monitor and reversal triggers

> **TODO (Drew):** confirm or edit. Suggested: each monthly CPI release (inflation above 3.82% stops the
> process); the 10-year Treasury yield and your equity risk premium view; realized 12-month volatility
> above 10%; BIL below 3% after any rebalance.

## Limits of this analysis

Expected returns are estimates built from yields known on the decision date, and the equity risk
premium is a judgment. Risk comes from 60 months that include the 2022 rate shock. LQD's yield is not
reduced for credit losses. Full detail: `docs/validation-and-ai-use.md`.

*Any remaining errors are my own.*
