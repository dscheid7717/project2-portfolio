# Lab 20 — Project 2 Readiness

> **AI use:** built with Claude Code (Claude Opus 5.5); the analysis and the decision are mine.
> **Education, not investment advice.**

**Author:** Drew Scheiderer · **Date:** 2026-11-17 · **Repository:**
https://github.com/dscheid7717/project2-portfolio

**Question (D):** Could a committee member who has never met me reach my decision from my repository,
and does the decision survive one changed input?

---

## Cold runs before class (my own, not my partner's)

| Run | Command | First failure | Elapsed | Result |
|---|---|---|---|---|
| 2026-11-10, fresh clone, fresh venv, long folder path | `pip install -r requirements.txt`, then the tests, `analysis.py` and the app | `ModuleNotFoundError: No module named 'streamlit.proto'`: pip silently skipped part of Streamlit under a long Windows path | about 5 min | tests (23) and `analysis.py` ran; the app did not start |
| 2026-11-10, fresh clone, fresh venv, short path (`C:\Users\dsche\p2c`) | the same | none | about 50 min, almost all of it `pip install` | tests passed, the app started, result BIL 35 / IEF 0 / LQD 0 / VT 65 |

**Fix already pushed:** the README now says to clone to a short folder path on Windows (commit
`bb7b92d`).

## I — the cold run, by my partner

> **TODO (partner writes):** the command they ran, the first failure, the elapsed time, and where they
> found the result.

## V — one changed input, predicted first

My prediction is in the **Locked Changed-Input Record** in
[`validation-and-ai-use.md`](validation-and-ai-use.md#locked-changed-input-record), written with AI
closed and committed **before** the run.

| Step | Record |
|---|---|
| Prediction commit | **TODO (Drew)**: the commit hash after you push the prediction |
| Command run | **TODO (Drew)**, e.g. `python analysis.py --set vol_cap=11` |
| Before output | `output/report.txt` (base case, frozen) |
| After output | **TODO (Drew)**: paste the changed lines, or save as `output/changed-input-run.txt` |
| What happened, whether the decision changes, and why | **TODO (Drew)** |

## Explain the code (no AI)

The block that produces my decision number is `lowest_risk_mix` in [`engine.py`](../engine.py) (line
174), which uses `mandate_check` (line 155). `run` (line 207) calls both for the three portfolios.

> **TODO (Drew):** your partner's question and your answer from the code.

## E — fix one thing

> **TODO (Drew):** the first failure your partner hit and the fix you pushed, or "Clean cold run; no fix
> needed."

## My decision line

> **TODO (Drew):** one line: adopt, allocate to, rebalance, pilot or reject, with the condition that
> would reverse it.

## Reflect

> **TODO (Drew):** 1. What did the cold run find that you could not see? 2. What will you not touch
> before the deadline?

---

*AI assistance: the repository, the cold runs before class and this page's factual sections were
produced with Claude Code (Claude Opus 5.5). The prediction, the partner's cold-run note, the decision
line and the reflection are mine. Any remaining errors are my own.*
