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

**Changed since these runs:** the app was redesigned as a terminal-style interface on 2026-11-17
(commit `5348ae0`): a status bar, five function tabs and a decision panel. The README, the commands
and every number are unchanged, so my partner's cold run uses the same steps.

## I — the cold run, by my partner

> **TODO (partner writes):** the command they ran, the first failure, the elapsed time, and where they
> found the result.

## V — one changed input, predicted first

My prediction is in the **Locked Changed-Input Record** in
[`validation-and-ai-use.md`](validation-and-ai-use.md#locked-changed-input-record), written with AI
closed and committed **before** the run.

| Step | Record |
|---|---|
| Prediction commit | `b5ead91`, pushed 2026-11-17 before the run |
| Command run | `python analysis.py --set vol_cap=11` (volatility cap 10.0% → 11.0%) |
| Before output | `output/report.txt` (base case, frozen) |
| After output | [`output/changed-input-run.txt`](../output/changed-input-run.txt) |
| What happened, whether the decision changes, and why | I predicted more VT, a higher return and higher volatility; **the mix did not change** (BIL 35 / VT 65, 7.80%, 9.69%). The cap was not binding: the search takes the lowest-risk mix that meets the 7.72% objective, and it already sat under 10%. The pilot decision did not change, as I predicted. The cap did widen the safety margin: stress stops fell from 4 of 8 to 2 of 8. **Realization after the run:** the mix was already at 9.69%, below the 10% cap; the 11% cap could come into effect during the 12-month pilot if the mix's volatility increases. |

## Explain the code (no AI)

The block that produces my decision number is `lowest_risk_mix` in [`engine.py`](../engine.py) (line
185), which uses `mandate_check` (line 166). `run` (line 218) calls both for the three portfolios.

> **TODO (Drew):** your partner's question and your answer from the code.

## E — fix one thing

> **TODO (Drew):** the first failure your partner hit and the fix you pushed, or "Clean cold run; no fix
> needed."

## My decision line

**Pilot the constrained portfolio with 20% of the reserve for 12 months, reviewed quarterly. Stop the pilot and return the sleeve to the current policy if CPI inflation exceeds 3.82% or my equity risk premium falls below 4.85%, since either leaves no mix that can satisfy the mandate. Reconsider adopting if it holds through 4 quarterly reviews with realized volatility under 10%.**

## Reflect

> **TODO (Drew):** 1. What did the cold run find that you could not see? 2. What will you not touch
> before the deadline?

---

*AI assistance: the repository, the cold runs before class and this page's factual sections were
produced with Claude Code (Claude Opus 5.5). The prediction, the partner's cold-run note, the decision
line and the reflection are mine. Any remaining errors are my own.*
