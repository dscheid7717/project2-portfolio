"""Project 2 app: the foundation reserve's mandate verdicts, the constrained portfolio and its stress run.

Every number comes from engine.py; nothing is computed here. Run: streamlit run app.py
"""

import html

import altair as alt
import pandas as pd
import streamlit as st

import analysis
import engine

BASE = analysis.BASE_INPUTS
ACCENT, INK_3, LINE = "#D9481C", "#6E6A66", "#CFCBC3"

# Tokens follow the design systems in my other repos (BlastOff, TrueForm, DitchList, Stack):
# warm paper and ink, Bricolage + Geist + Geist Mono, one accent, status never shown by color alone.
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap');
:root {
  --base: #FAF8F4; --surface: #FFFFFF; --raised: #F3F0EA; --line: #E5E2DC; --line-strong: #CFCBC3;
  --ink: #1B1A17; --ink-2: #45423C; --ink-3: #6E6A66; --accent: #D9481C;
  --ok: #1F7A4D; --ok-soft: #E4F3EA; --bad: #B3261E; --bad-soft: #FBE9E7;
  --shadow-card: 0 1px 2px rgba(27,26,23,.05), 0 4px 16px rgba(27,26,23,.05);
  --font-heading: 'Bricolage Grotesque', 'Geist', sans-serif; --font-sans: 'Geist', 'Segoe UI', sans-serif;
  --font-mono: 'Geist Mono', Consolas, monospace;
}
.stApp { background: var(--base); color: var(--ink); font-family: var(--font-sans); }
.stApp p, .stApp li, .stApp label { font-family: var(--font-sans); }
.block-container { max-width: 1180px; padding: 2.5rem 1.5rem 4rem; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: var(--raised); border-right: 1px solid var(--line); }
[class*="st-key-card"] { background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
  box-shadow: var(--shadow-card); padding: 20px 24px; }
[data-testid="stHorizontalBlock"]:has([class*="st-key-card"]) { align-items: stretch; }
[data-testid="stColumn"]:has([class*="st-key-card"]) > div,
[data-testid="stColumn"]:has([class*="st-key-card"]) [data-testid="stLayoutWrapper"],
[data-testid="stColumn"] [class*="st-key-card"] { height: 100%; }
.page-title { font-family: var(--font-heading); font-size: 34px; font-weight: 600; line-height: 1.1;
  letter-spacing: -.02em; margin: 0 0 6px; }
.page-sub { font-size: 14px; line-height: 1.5; color: var(--ink-3); margin: 0; max-width: 80ch; }
.panel-title { font-family: var(--font-heading); font-size: 16px; font-weight: 600; margin: 0 0 2px; color: var(--ink); }
.panel-sub { font-size: 13px; color: var(--ink-3); margin: 0 0 12px; line-height: 1.45; }
.eyebrow { font-size: 14px; font-weight: 500; color: var(--ink-3); margin: 0 0 6px; }
.verdict { font-family: var(--font-heading); font-size: 28px; font-weight: 600; line-height: 1.15;
  letter-spacing: -.02em; margin: 0 0 8px; color: var(--ink); }
.lead { font-size: 16px; line-height: 1.55; color: var(--ink-2); margin: 0; max-width: 78ch; }
.chip { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 3px 10px;
  font-size: 13px; font-weight: 500; white-space: nowrap; }
.chip-pass { background: var(--ok-soft); color: var(--ok); }
.chip-fail { background: var(--bad-soft); color: var(--bad); }
.chip-quiet { background: var(--raised); color: var(--ink-3); }
.mix { font-family: var(--font-mono); font-size: 15px; color: var(--ink); margin: 6px 0 4px; }
.readout { font-family: var(--font-heading); font-size: 24px; font-weight: 600; font-variant-numeric: tabular-nums; }
.label { font-size: 13px; color: var(--ink-3); }
.stats { display: flex; gap: 22px; margin: 10px 0; }
.fails { font-size: 13px; color: var(--bad); margin: 6px 0 0; line-height: 1.45; }
.table-wrap { overflow-x: auto; }
table.grid { border-collapse: collapse; width: 100%; font-size: 14px; }
table.grid th, table.grid td { padding: 9px 12px; border: 0; border-top: 1px solid var(--line); text-align: right;
  white-space: nowrap; color: var(--ink-2); vertical-align: middle; }
table.grid thead th { border-top: 0; font-weight: 500; font-size: 13px; color: var(--ink-3); }
table.grid th[scope=row], table.grid thead th:first-child { text-align: left; color: var(--ink); font-weight: 500; white-space: normal; }
table.grid th[scope=row] { min-width: 150px; }
table.grid thead th.left { text-align: left; }
table.grid td.num { font-family: var(--font-mono); font-size: 13.5px; color: var(--ink); }
table.grid td.word { font-size: 13px; color: var(--ink-3); text-align: left; white-space: normal; }
.note { border-radius: 10px; padding: 10px 14px; font-size: 14px; line-height: 1.45; margin: 0 0 4px; }
.note-quiet { background: var(--raised); color: var(--ink-2); }
.note-bad { background: var(--bad-soft); color: var(--bad); }
dl.card { padding: 0 !important; display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; margin: 0; font-size: 14px; }
dl.card dt { color: var(--ink-3); } dl.card dd { margin: 0; color: var(--ink-2); }
@media (max-width: 640px) {
  .block-container { padding: 1.5rem 1rem 3rem; } .page-title { font-size: 28px; }
  [class*="st-key-card"] { padding: 16px; } dl.card { grid-template-columns: 1fr; }
}
</style>
"""

CHIP = {True: '<span class="chip chip-pass">&#10003; passes every rule</span>',
        False: '<span class="chip chip-fail">&#10005; fails the mandate</span>'}


def esc(value):
    return html.escape(str(value))


def note(kind, message):
    st.html(f'<div class="note note-{kind}">{message}</div>')


@st.cache_data(show_spinner=False)
def cached_data(decision_date):
    return engine.load_data({**BASE, "decision_date": decision_date})


@st.cache_data(show_spinner=False)
def compute(inputs_items):
    """The base run, the stress run, the range and the stop conditions for one set of inputs."""
    inputs = dict(inputs_items)
    return analysis.build(inputs)


# ---------------------------------------------------------------- page

st.set_page_config(page_title="Foundation Reserve Portfolio", layout="wide")
st.html(STYLE)
st.html('<h1 class="page-title">Foundation reserve portfolio</h1>'
        '<p class="page-sub">Built with Claude Code (Claude Opus 5.5); the analysis and the decision are Drew '
        'Scheiderer\'s. Education, not investment advice. Data from Yahoo Finance and FRED/ALFRED as of the '
        f'decision date, {BASE["decision_date"]}.</p>')

with st.sidebar:
    st.markdown("**What if?**")
    st.caption("Each control reruns the engine. Reset returns to the frozen base case.")
    if st.button("Reset to base case", width="stretch"):
        for key in ("erp", "real", "cap", "maxw", "reserve", "window", "cost"):
            st.session_state.pop(key, None)
    erp = st.slider("Equity risk premium (%)", 3.0, 7.0, BASE["erp"], 0.05, key="erp",
                    help="Judgment. VT expected return = 10-year Treasury + this premium.")
    real = st.slider("Real return target over CPI (%)", 3.0, 5.0, BASE["real_return_target"], 0.05, key="real")
    cap = st.slider("Volatility cap (%)", 7.0, 14.0, BASE["vol_cap"], 0.5, key="cap")
    maxw = st.slider("Largest single fund (%)", 40.0, 100.0, BASE["max_weight"], 5.0, key="maxw")
    reserve = st.slider("BIL reserve minimum (%)", 0.0, 20.0, BASE["reserve_min"], 1.0, key="reserve")
    window = st.radio("Risk estimated from", ["All 60 months", "Last 36 months"], key="window")
    cost = st.slider("Extra costs (% a year)", 0.0, 1.0, BASE["extra_cost"], 0.05, key="cost")

inputs = {**BASE, "erp": erp, "real_return_target": real, "vol_cap": cap, "max_weight": maxw,
          "reserve_min": reserve, "window_months": 36 if window == "Last 36 months" else None, "extra_cost": cost}
is_base = inputs == BASE
built = compute(tuple(sorted(inputs.items(), key=lambda kv: kv[0])))
result, tickers = built["base"], built["base"]["tickers"]
m = result["mandate"]

if not is_base:
    note("quiet", "What-if view: these inputs differ from the frozen base case. Reset in the sidebar.")

# ---------------------------------------------------------------- the answer
constrained = result["portfolios"].get("Constrained portfolio")
with st.container(key="card_hero"):
    if constrained:
        w = constrained["weights"]
        headline = f"A mandate-passing mix exists: {' / '.join(f'{t} {x:.0f}' for t, x in zip(tickers, w))}"
        margin = f"{m['vol_cap'] - constrained['volatility']:.2f} points under the volatility cap"
        lead = (f"Expected return {constrained['expected_return']:.2f}% against a {m['objective']:.2f}% objective, "
                f"volatility {constrained['volatility']:.2f}% ({margin}). Neither baseline passes. "
                f"The process stops if the equity risk premium falls below "
                f"{analysis.pct(built['erp_floor'])} or CPI inflation rises above "
                f"{analysis.pct(built['inflation_ceiling'])}.")
    else:
        headline = "No mix meets the mandate"
        lead = (f"No long-only mix in 5-point steps reaches {m['objective']:.2f}% with volatility at most "
                f"{m['vol_cap']:.1f}%, BIL at least {m['reserve_min']:.0f}% and no fund above {m['max_weight']:.0f}%. "
                "That is the answer, not a reason to lower the objective.")
    st.html(f'<p class="eyebrow">Committee action: {esc(analysis.PENDING)}</p>'
            f'<h2 class="verdict">{esc(headline)}</h2><p class="lead">{esc(lead)}</p>')

# ---------------------------------------------------------------- the three portfolios
cols = st.columns(len(result["portfolios"]) if constrained else 3)
order = ["Constrained portfolio", "Benchmark 60/40 VT/LQD", "Equal weight"]
for col, name in zip(cols, order):
    with col, st.container(key=f"card_{name.split()[0].lower()}"):
        p = result["portfolios"].get(name)
        if p is None:
            st.html(f'<p class="panel-title">{esc(name)}</p><p class="panel-sub">No mix meets every rule.</p>'
                    '<span class="chip chip-quiet">&#9675; none</span>')
            continue
        mix = " / ".join(f"{t} {x:.0f}" for t, x in zip(tickers, p["weights"]))
        fails = "" if not p["failed"] else f'<p class="fails">Fails: {esc("; ".join(p["failed"]))}</p>'
        h = p["history"]
        st.html(f'<p class="panel-title">{esc(name)}</p><p class="mix">{esc(mix)}</p>'
                f'<div class="stats"><div><div class="readout">{p["expected_return"]:.2f}%</div>'
                f'<div class="label">expected return</div></div><div><div class="readout">{p["volatility"]:.2f}%</div>'
                f'<div class="label">volatility</div></div></div>{CHIP[not p["failed"]]}{fails}'
                f'<p class="panel-sub" style="margin-top:12px">History, 60 months, monthly rebalanced: '
                f'{h["annual_return"]:.2f}% a year, max drawdown {h["max_drawdown"]:.2f}%.</p>')

# ---------------------------------------------------------------- mandate table and chart
left, right = st.columns([1.35, 1])
with left, st.container(key="card_mandate"):
    short = {"Equal weight": "Equal", "Benchmark 60/40 VT/LQD": "60/40", "Constrained portfolio": "Constrained"}
    head = "".join(f'<th scope="col">{esc(short[n])}</th>' for n in result["portfolios"])
    body = []
    for i, (rule, _, limit, _) in enumerate(next(iter(result["portfolios"].values()))["checks"]):
        cells = []
        for p in result["portfolios"].values():
            _, value, _, passed = p["checks"][i]
            mark = "&#10003;" if passed else "&#10005;"
            colour = "var(--ok)" if passed else "var(--bad)"
            cells.append(f'<td class="num"><span style="color:{colour}">{mark}</span> {value:.1f}</td>')
        body.append(f'<tr><th scope="row">{esc(rule)}<div class="label">{esc(limit)}</div></th>{"".join(cells)}</tr>')
    st.html('<p class="panel-title">Mandate check</p>'
            f'<p class="panel-sub">Objective = CPI inflation as known on {BASE["decision_date"]} '
            f'({result["inflation"]:.2f}%) + {inputs["real_return_target"]:.2f}%. Values in percent.</p>'
            f'<div class="table-wrap"><table class="grid"><thead><tr><th scope="col">Rule</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')

with right, st.container(key="card_chart"):
    points = [{"name": t, "kind": "fund", "vol": v, "ret": r}
              for t, v, r in zip(tickers, result["vols"], result["expected_returns"])]
    points += [{"name": n.replace(" VT/LQD", ""), "kind": "constrained" if n == "Constrained portfolio" else "baseline",
                "vol": p["volatility"], "ret": p["expected_return"]} for n, p in result["portfolios"].items()]
    df = pd.DataFrame(points)
    x = alt.X("vol:Q", title="Volatility, % a year", scale=alt.Scale(zero=True))
    y = alt.Y("ret:Q", title="Expected return, % a year", scale=alt.Scale(zero=False))
    colour = alt.Color("kind:N", scale=alt.Scale(domain=["constrained", "baseline", "fund"],
                                                 range=[ACCENT, "#45423C", INK_3]), legend=None)
    tip = [alt.Tooltip("name:N", title="Portfolio or fund"), alt.Tooltip("ret:Q", title="Expected return %", format=".2f"),
           alt.Tooltip("vol:Q", title="Volatility %", format=".2f")]
    dots = alt.Chart(df).mark_point(size=110, filled=True, opacity=1, stroke="#FFFFFF", strokeWidth=2).encode(
        x=x, y=y, color=colour, shape=alt.Shape("kind:N", legend=None, scale=alt.Scale(
            domain=["constrained", "baseline", "fund"], range=["circle", "circle", "diamond"])), tooltip=tip)
    labels = alt.Chart(df).mark_text(align="left", dx=9, dy=-8, fontSize=12, color="#45423C").encode(
        x=x, y=y, text="name:N")
    # Reference lines drawn from constants (datum), so the chart carries one dataset.
    base_chart = alt.Chart(df)
    cap_line = base_chart.mark_rule(color=LINE, strokeWidth=1.5).encode(x=alt.datum(m["vol_cap"]))
    goal_line = base_chart.mark_rule(color=LINE, strokeWidth=1.5).encode(y=alt.datum(m["objective"]))
    cap_text = base_chart.mark_text(align="left", dx=4, fontSize=11, color=INK_3, baseline="top").encode(
        x=alt.datum(m["vol_cap"]), y=alt.value(4), text=alt.value(f"cap {m['vol_cap']:.1f}%"))
    goal_text = base_chart.mark_text(align="left", dx=4, dy=-7, fontSize=11, color=INK_3).encode(
        y=alt.datum(m["objective"]), x=alt.value(4), text=alt.value(f"objective {m['objective']:.2f}%"))
    dots = base_chart.mark_point(size=110, filled=True, opacity=1, stroke="#FFFFFF", strokeWidth=2).encode(
        x=x, y=y, color=colour, shape=alt.Shape("kind:N", legend=None, scale=alt.Scale(
            domain=["constrained", "baseline", "fund"], range=["circle", "circle", "diamond"])), tooltip=tip)
    labels = base_chart.mark_text(align="left", dx=9, dy=-8, fontSize=12, color="#45423C").encode(
        x=x, y=y, text="name:N")
    chart = (alt.layer(cap_line, goal_line, dots, labels, cap_text, goal_text).properties(height=330)
             .configure_view(strokeWidth=0).configure(background="transparent", font="Geist, Segoe UI, sans-serif")
             .configure_axis(labelColor=INK_3, titleColor=INK_3, titleFontWeight="normal", gridColor="#EFECE6",
                             domainColor=LINE, tickColor=LINE, labelFontSize=12, titleFontSize=12))
    st.html('<p class="panel-title">Risk and expected return</p>'
            '<p class="panel-sub">Up and to the left is better. A passing mix sits above the objective line and left '
            'of the cap.</p>')
    st.altair_chart(chart, width="stretch", theme=None)

# ---------------------------------------------------------------- stress run
with st.container(key="card_stress"):
    rows = []
    for r in built["stress"]:
        mix = (" / ".join(f"{t} {x:.0f}" for t, x in zip(tickers, r["weights"])) if r["weights"]
               else "no mix meets the mandate")
        chip = ('<span class="chip chip-pass">&#10003; mix</span>' if r["weights"]
                else '<span class="chip chip-fail">&#10005; stops</span>')
        moved = "" if r["largest_change"] is None else f'{r["largest_change"]:.0f}'
        rows.append(f'<tr><td class="word">{esc(r["group"])}</td><th scope="row">{esc(r["label"])}</th>'
                    f'<td>{chip}</td><td class="num">{esc(mix)}</td><td class="num">{moved}</td></tr>')
    stopped = sum(1 for r in built["stress"] if not r["weights"])
    st.html('<p class="panel-title">Stress run</p>'
            f'<p class="panel-sub">One change at a time from the inputs above. {stopped} of {len(built["stress"])} '
            'cases leave no mix that meets the mandate.</p>'
            '<div class="table-wrap"><table class="grid"><thead><tr><th scope="col">Group</th><th scope="col" class="left">Change</th>'
            '<th scope="col" class="left">Result</th><th scope="col">Mix (BIL / IEF / LQD / VT)</th><th scope="col">Largest move, points</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')

# ---------------------------------------------------------------- range, stop conditions, data card
left, right = st.columns(2)
with left, st.container(key="card_range"):
    if built["range"]:
        items = "".join(f'<dt>{esc(t)}</dt><dd><span class="mix">{lo:.0f}% to {hi:.0f}%</span></dd>'
                        for t, (lo, hi) in built["range"].items())
    else:
        items = "<dt>Range</dt><dd>none: no case has a mix</dd>"
    st.html('<p class="panel-title">Allocation range and stop conditions</p>'
            '<p class="panel-sub">Range across the base case and every stress case that still has a mix.</p>'
            f'<dl class="card">{items}<dt>Stop if</dt><dd>equity risk premium below {analysis.pct(built["erp_floor"])}</dd>'
            f'<dt>Stop if</dt><dd>CPI inflation above {analysis.pct(built["inflation_ceiling"])}</dd></dl>')
with right, st.container(key="card_signal"):
    st.html('<p class="panel-title">Point-in-time signal: CPI</p>'
            '<p class="panel-sub">Sets the objective. Only the vintage published by the decision date is used.</p>'
            '<dl class="card"><dt>Source</dt><dd>BLS via FRED/ALFRED, series CPIAUCSL</dd>'
            f'<dt>Known on {BASE["decision_date"]}</dt><dd>{esc(result["cpi_month"][:7])}, inflation '
            f'{result["inflation"]:.2f}% a year</dd>'
            '<dt>Publication lag</dt><dd>about two weeks after the month ends</dd>'
            '<dt>Revisions</dt><dd>seasonal factors revised each February for five years</dd>'
            '<dt>Gap</dt><dd>October 2025 never published (2025 shutdown)</dd></dl>')

with st.expander("Estimates behind the numbers"):
    est = pd.DataFrame({"Expected return %": result["expected_returns"], "History mean % (not used)": result["historical_mean"],
                        "Volatility %": result["vols"]}, index=tickers).round(2)
    st.dataframe(est)
    st.caption("Expected returns: yields known on the decision date, net of expense ratios; VT = 10-year Treasury + "
               "the equity risk premium. History means are shown to explain why they are not used: the 60 months "
               "start just before the 2022 rate shock.")
