"""Project 2 app: a portfolio terminal for the foundation reserve's committee.

Status bar, function tabs, dense panels: the mandate verdicts, the constrained portfolio, the stress run,
the point-in-time CPI signal and the data behind them. Every number comes from engine.py; nothing is
computed here. Run: streamlit run app.py
"""

import html

import altair as alt
import pandas as pd
import streamlit as st

import analysis
import engine

BASE = analysis.BASE_INPUTS

# Terminal palette: near-black panels, warm off-white text, amber for data, one orange accent for the
# constrained portfolio, green/red only for pass/fail and always with a glyph and a word.
BG, PANEL, LINE, TEXT, MUTED = "#0B0D10", "#12161B", "#252C34", "#E8E3D8", "#9AA4AE"
AMBER, ACCENT, GOOD, BAD = "#F5A524", "#FF7A1A", "#4CC38A", "#FF6B63"

STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap');
:root {{ --bg:{BG}; --panel:{PANEL}; --line:{LINE}; --text:{TEXT}; --muted:{MUTED}; --amber:{AMBER};
  --accent:{ACCENT}; --good:{GOOD}; --bad:{BAD}; --mono:'Geist Mono',Consolas,monospace; --sans:'Geist','Segoe UI',sans-serif; }}
.stApp {{ background: var(--bg); color: var(--text); font-family: var(--sans); }}
.stApp p, .stApp li, .stApp label, .stApp span {{ font-family: var(--sans); }}
.block-container {{ max-width: 1400px; padding: 1rem 1.25rem 3rem; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
section[data-testid="stSidebar"] {{ background: #0F1317; border-right: 1px solid var(--line); }}
section[data-testid="stSidebar"] * {{ color: var(--text); }}

/* status bar */
.bar {{ display:flex; flex-wrap:wrap; align-items:stretch; border:1px solid var(--line); background:var(--panel);
  border-radius:6px; overflow:hidden; margin-bottom:10px; }}
.brand {{ background: var(--amber); color:#111; font-family:var(--mono); font-weight:600; padding:8px 10px;
  font-size:13px; letter-spacing:.04em; display:flex; align-items:center; }}
.cell {{ padding:6px 10px; border-left:1px solid var(--line); display:flex; flex-direction:column; justify-content:center; }}
.cell .k {{ font-size:10.5px; color:var(--muted); letter-spacing:.06em; text-transform:uppercase; }}
.cell .v {{ font-family:var(--mono); font-size:13px; color:var(--amber); font-weight:500; white-space:nowrap; }}
.cell .v.good {{ color:var(--good); }} .cell .v.bad {{ color:var(--bad); }}
.disclaimer {{ font-size:12px; color:var(--muted); margin:-4px 0 10px; }}
.modified {{ background:#3A2A0A; color:var(--amber); border:1px solid #6B4B12; border-radius:6px; padding:6px 12px;
  font-size:13px; margin-bottom:10px; font-family:var(--mono); }}

/* tabs as function keys */
.stTabs [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid var(--line); }}
.stTabs [data-baseweb="tab"] {{ background:var(--panel); border:1px solid var(--line); border-bottom:0;
  border-radius:6px 6px 0 0; padding:6px 14px; font-family:var(--mono); font-size:13px; color:var(--muted); }}
.stTabs [aria-selected="true"] {{ background:var(--amber) !important; color:#111 !important; }}
.stTabs [aria-selected="true"] p {{ color:#111 !important; font-weight:600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* panels */
[class*="st-key-pnl"] {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:12px 14px; }}
[data-testid="stHorizontalBlock"]:has([class*="st-key-pnl"]) {{ align-items:stretch; }}
[data-testid="stColumn"]:has([class*="st-key-pnl"]) > div,
[data-testid="stColumn"]:has([class*="st-key-pnl"]) [data-testid="stLayoutWrapper"],
[data-testid="stColumn"] [class*="st-key-pnl"] {{ height:100%; }}
.ph {{ display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid var(--line);
  padding-bottom:6px; margin-bottom:8px; }}
.ph .t {{ font-family:var(--mono); font-size:12.5px; color:var(--amber); letter-spacing:.06em; text-transform:uppercase; font-weight:600; }}
.ph .s {{ font-size:12px; color:var(--muted); }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:8px; }}
.kpi {{ background:var(--panel); border:1px solid var(--line); border-radius:6px; padding:10px 12px; }}
.kpi .k {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }}
.kpi .v {{ font-family:var(--mono); font-size:24px; color:var(--text); font-weight:500; margin-top:2px; }}
.kpi .d {{ font-family:var(--mono); font-size:12px; color:var(--muted); margin-top:2px; }}
.kpi .d.good {{ color:var(--good); }} .kpi .d.bad {{ color:var(--bad); }}

table.t {{ border-collapse:collapse; width:100%; font-size:13px; }}
table.t th, table.t td {{ padding:6px 8px; border:0; border-bottom:1px solid var(--line); text-align:right;
  white-space:nowrap; color:var(--text); }}
table.t thead th {{ font-size:11px; color:var(--muted); font-weight:500; text-transform:uppercase; letter-spacing:.05em;
  border-bottom:1px solid #39424C; }}
table.t th[scope=row], table.t thead th.l, table.t td.l {{ text-align:left; }}
table.t th[scope=row] {{ font-weight:500; }}
table.t td.n {{ font-family:var(--mono); }}
table.t tr.hl th, table.t tr.hl td {{ background:#1B1610; }}
table.t tr.hl th[scope=row] {{ box-shadow: inset 3px 0 0 var(--accent); }}
.wrap {{ overflow-x:auto; }}
.ok {{ color:var(--good); font-family:var(--mono); }} .no {{ color:var(--bad); font-family:var(--mono); }}
.tag {{ display:inline-block; border-radius:4px; padding:1px 7px; font-family:var(--mono); font-size:12px; font-weight:600; }}
.tag.ok {{ background:#123224; color:var(--good); }} .tag.no {{ background:#3A1614; color:var(--bad); }}
.wbar {{ display:flex; align-items:center; gap:6px; justify-content:flex-end; }}
.wbar i {{ display:inline-block; height:8px; background:var(--amber); border-radius:2px; opacity:.85; }}
.muted {{ color:var(--muted); font-size:12px; line-height:1.5; }}
dl.kv {{ display:grid; grid-template-columns:max-content 1fr; gap:4px 14px; margin:0; font-size:13px; padding:0 !important; }}
dl.kv dt {{ color:var(--muted); }} dl.kv dd {{ margin:0; font-family:var(--mono); color:var(--text); }}
.stSlider label p, .stRadio label p {{ font-family:var(--mono) !important; font-size:12px !important; color:var(--muted) !important; }}
@media (max-width:640px) {{ .block-container {{ padding:.75rem .75rem 2rem; }} .cell {{ padding:5px 10px; }} }}
</style>
"""


def esc(value):
    return html.escape(str(value))


def ph(title, sub=""):
    return f'<div class="ph"><span class="t">{esc(title)}</span><span class="s">{esc(sub)}</span></div>'


def mark(passed):
    return '<span class="tag ok">&#10003; PASS</span>' if passed else '<span class="tag no">&#10005; FAIL</span>'


def mix_text(weights, tickers):
    return " / ".join(f"{t} {w:.0f}" for t, w in zip(tickers, weights))


@st.cache_data(show_spinner=False)
def compute(inputs_items):
    return analysis.build(dict(inputs_items))


def dark(chart, height):
    return (chart.properties(height=height).configure_view(strokeWidth=0)
            .configure(background="transparent", font="Geist, Segoe UI, sans-serif")
            .configure_axis(labelColor=MUTED, titleColor=MUTED, titleFontWeight="normal", gridColor="#1E252C",
                            domainColor=LINE, tickColor=LINE, labelFontSize=11, titleFontSize=11)
            .configure_legend(labelColor=TEXT, titleColor=MUTED))


# ---------------------------------------------------------------- inputs (sidebar = the command line)

st.set_page_config(page_title="Reserve Terminal", layout="wide", initial_sidebar_state="expanded")
st.html(STYLE)

with st.sidebar:
    st.markdown("**WHAT-IF**")
    st.caption("Every control reruns the engine.")
    if st.button("Reset to base case", width="stretch"):
        for key in ("erp", "real", "cap", "maxw", "reserve", "window", "cost"):
            st.session_state.pop(key, None)
    erp = st.slider("Equity risk premium %", 3.0, 7.0, BASE["erp"], 0.05, key="erp",
                    help="Judgment. VT expected return = 10-year Treasury + this premium.")
    real = st.slider("Real target over CPI %", 3.0, 5.0, BASE["real_return_target"], 0.05, key="real")
    cap = st.slider("Volatility cap %", 7.0, 14.0, BASE["vol_cap"], 0.5, key="cap")
    maxw = st.slider("Largest fund %", 40.0, 100.0, BASE["max_weight"], 5.0, key="maxw")
    reserve = st.slider("BIL reserve min %", 0.0, 20.0, BASE["reserve_min"], 1.0, key="reserve")
    window = st.radio("Risk window", ["All 60 months", "Last 36 months"], key="window")
    cost = st.slider("Extra costs % a year", 0.0, 1.0, BASE["extra_cost"], 0.05, key="cost")

inputs = {**BASE, "erp": erp, "real_return_target": real, "vol_cap": cap, "max_weight": maxw,
          "reserve_min": reserve, "window_months": 36 if window == "Last 36 months" else None, "extra_cost": cost}
built = compute(tuple(sorted(inputs.items(), key=lambda kv: kv[0])))
result, tickers = built["base"], built["base"]["tickers"]
m, ports = result["mandate"], result["portfolios"]
best = ports.get("Constrained portfolio")
stopped = sum(1 for r in built["stress"] if not r["weights"])

# ---------------------------------------------------------------- status bar (always visible)

status = ("PASS", "good") if best else ("NO MIX", "bad")
cells = [("As of", BASE["decision_date"], ""), ("CPI y/y (Sep)", f"{result['inflation']:.2f}%", ""),
         ("Objective", f"{m['objective']:.2f}%", ""), ("Vol cap", f"{m['vol_cap']:.1f}%", ""),
         ("Status", status[0], status[1]), ("Action", analysis.COMMITTEE_ACTION_SHORT, ""),
         ("Mix BIL/IEF/LQD/VT", " / ".join(f"{w:.0f}" for w in best["weights"]) if best else "none", ""),
         ("Stress stops", f"{stopped}/{len(built['stress'])}", "bad" if stopped else "good"),
         ("Stop if", f"ERP<{analysis.pct(built['erp_floor'], 2)} CPI>{analysis.pct(built['inflation_ceiling'])}", "")]
st.html('<div class="bar"><div class="brand">RESERVE&nbsp;&lt;GO&gt;</div>'
        + "".join(f'<div class="cell"><span class="k">{esc(k)}</span><span class="v {c}">{esc(v)}</span></div>'
                  for k, v, c in cells) + "</div>"
        '<div class="disclaimer">Foundation reserve portfolio · BIL / IEF / LQD / VT · Built with Claude Code '
        '(Claude Opus 5.5); the analysis and the decision are Drew Scheiderer\'s. Education, not investment advice. '
        f'Committee action: {esc(analysis.COMMITTEE_ACTION)}</div>')
if inputs != BASE:
    changed = ", ".join(f"{k} {BASE[k]} → {v}" for k, v in inputs.items() if BASE[k] != v)
    st.html(f'<div class="modified">WHAT-IF ACTIVE · {esc(changed)} · not the frozen result</div>')

tab1, tab2, tab3, tab4, tab5 = st.tabs(["1 OVERVIEW", "2 MANDATE", "3 STRESS", "4 SIGNAL", "5 DATA"])

# ---------------------------------------------------------------- 1 overview
with tab1:
    if best:
        kpis = [("Expected return", f"{best['expected_return']:.2f}%",
                 f"+{best['expected_return'] - m['objective']:.2f} vs objective", "good"),
                ("Volatility", f"{best['volatility']:.2f}%", f"{m['vol_cap'] - best['volatility']:.2f} under cap", "good"),
                ("BIL reserve", f"{best['weights'][tickers.index('BIL')]:.0f}%", f"min {m['reserve_min']:.0f}%", ""),
                ("Max drawdown (hist.)", f"{best['history']['max_drawdown']:.1f}%", "60 months, monthly rebal.", ""),
                ("Stress cases passing", f"{len(built['stress']) - stopped}/{len(built['stress'])}",
                 f"{stopped} leave no mix", "bad" if stopped else "good")]
    else:
        kpis = [("Constrained portfolio", "NONE", "no mix meets every rule", "bad"),
                ("Objective", f"{m['objective']:.2f}%", "CPI + target", ""),
                ("Vol cap", f"{m['vol_cap']:.1f}%", "", "")]
    st.html('<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div><div class="d {c}">{esc(d)}</div></div>'
        for k, v, d, c in kpis) + "</div>")

    with st.container(key="pnl_compare"):
        order = [n for n in ("Constrained portfolio", "Benchmark 60/40 VT/LQD", "Equal weight") if n in ports]
        head = "".join(f'<th>{t} %</th>' for t in tickers)
        rows = []
        for name in order:
            p = ports[name]
            weights = "".join(f'<td class="n"><div class="wbar"><i style="width:{w * 0.5:.0f}px"></i>{w:.0f}</div></td>'
                              for w in p["weights"])
            why = "" if not p["failed"] else f'<div class="muted">{esc("; ".join(p["failed"]))}</div>'
            rows.append(f'<tr class="{"hl" if name == "Constrained portfolio" else ""}"><th scope="row">{esc(name)}{why}</th>'
                        f'{weights}<td class="n">{p["expected_return"]:.2f}</td><td class="n">{p["volatility"]:.2f}</td>'
                        f'<td class="n">{p["history"]["annual_return"]:.2f}</td><td class="n">{p["history"]["max_drawdown"]:.1f}</td>'
                        f'<td>{mark(not p["failed"])}</td></tr>')
        st.html(ph("Portfolio monitor", "weights %, returns % a year") +
                f'<div class="wrap"><table class="t"><thead><tr><th class="l">Portfolio</th>{head}<th>Exp. ret</th>'
                f'<th>Vol</th><th>Hist. ret</th><th>Max DD</th><th>Mandate</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>'
                '<p class="muted" style="margin-top:8px">Exp. ret: yields known on the decision date, net of '
                'expense ratios. Hist.: 60 months, monthly rebalanced; history, not a forecast.</p>')
    left, right = st.columns([1.5, 1])
    with left, st.container(key="pnl_chart"):
        pts = [{"name": t, "kind": "fund", "vol": v, "ret": r}
               for t, v, r in zip(tickers, result["vols"], result["expected_returns"])]
        pts += [{"name": n.replace(" VT/LQD", "").replace(" portfolio", ""),
                 "kind": "constrained" if n == "Constrained portfolio" else "baseline",
                 "vol": p["volatility"], "ret": p["expected_return"]} for n, p in ports.items()]
        df = pd.DataFrame(pts)
        x = alt.X("vol:Q", title="Volatility % a year", scale=alt.Scale(zero=True))
        y = alt.Y("ret:Q", title="Expected return % a year", scale=alt.Scale(zero=False))
        base_chart = alt.Chart(df)
        colour = alt.Color("kind:N", legend=None, scale=alt.Scale(domain=["constrained", "baseline", "fund"],
                                                                  range=[ACCENT, TEXT, MUTED]))
        tip = [alt.Tooltip("name:N", title="Name"), alt.Tooltip("ret:Q", title="Exp. return %", format=".2f"),
               alt.Tooltip("vol:Q", title="Volatility %", format=".2f")]
        layers = [
            base_chart.mark_rule(color="#4A545F", strokeWidth=1).encode(x=alt.datum(m["vol_cap"])),
            base_chart.mark_rule(color="#4A545F", strokeWidth=1).encode(y=alt.datum(m["objective"])),
            base_chart.mark_text(align="left", dx=4, baseline="top", fontSize=10.5, color=MUTED).encode(
                x=alt.datum(m["vol_cap"]), y=alt.value(4), text=alt.value(f"CAP {m['vol_cap']:.1f}")),
            base_chart.mark_text(align="left", dx=4, dy=-7, fontSize=10.5, color=MUTED).encode(
                y=alt.datum(m["objective"]), x=alt.value(4), text=alt.value(f"OBJ {m['objective']:.2f}")),
            base_chart.mark_point(size=90, filled=True, opacity=1, stroke=PANEL, strokeWidth=2).encode(
                x=x, y=y, color=colour, shape=alt.Shape("kind:N", legend=None, scale=alt.Scale(
                    domain=["constrained", "baseline", "fund"], range=["circle", "circle", "diamond"])), tooltip=tip),
            base_chart.mark_text(align="left", dx=8, dy=-7, fontSize=11, color=TEXT).encode(x=x, y=y, text="name:N"),
        ]
        st.html(ph("Risk / return", "pass = above OBJ, left of CAP"))
        st.altair_chart(dark(alt.layer(*layers), 300), width="stretch", theme=None)
    with right, st.container(key="pnl_decision"):
        rng = built["range"]
        span = ("".join(f"<dt>{t}</dt><dd>{lo:.0f}% – {hi:.0f}%</dd>" for t, (lo, hi) in rng.items())
                if rng else "<dt>Range</dt><dd>none: no case has a mix</dd>")
        st.html(ph("Decision panel", "for the committee") +
                f'<dl class="kv"><dt>Action</dt><dd>{esc(analysis.COMMITTEE_ACTION_SHORT)}</dd>{span}'
                f'<dt>Stop if</dt><dd>ERP below {analysis.pct(built["erp_floor"])}</dd>'
                f'<dt>Stop if</dt><dd>CPI y/y above {analysis.pct(built["inflation_ceiling"])}</dd>'
                f'<dt>Watch (suggested)</dt><dd>each CPI release; 10y yield; realized vol; BIL after rebalance</dd></dl>'
                '<p class="muted" style="margin-top:10px">Range: lowest and highest weight across the base case and '
                'every stress case that still has a mix.</p>')

# ---------------------------------------------------------------- 2 mandate
with tab2:
    left, right = st.columns([1.5, 1])
    with left, st.container(key="pnl_rules"):
        names = list(ports)
        short = {"Equal weight": "Equal", "Benchmark 60/40 VT/LQD": "60/40", "Constrained portfolio": "Constrained"}
        head = "".join(f"<th>{short[n]}</th>" for n in names)
        rows = []
        for i, (rule, _, limit, _) in enumerate(ports[names[0]]["checks"]):
            cells_html = []
            for n in names:
                _, value, _, passed = ports[n]["checks"][i]
                cells_html.append(f'<td class="n"><span class="{"ok" if passed else "no"}">{"&#10003;" if passed else "&#10005;"}'
                                  f'</span> {value:.2f}</td>')
            rows.append(f'<tr><th scope="row">{esc(rule)}</th><td class="n l">{esc(limit)}</td>{"".join(cells_html)}</tr>')
        verdicts = "".join(f"<td>{mark(not ports[n]['failed'])}</td>" for n in names)
        st.html(ph("Mandate check", "values in percent") +
                f'<div class="wrap"><table class="t"><thead><tr><th class="l">Rule</th><th class="l">Limit</th>{head}</tr></thead>'
                f'<tbody>{"".join(rows)}<tr><th scope="row">Verdict</th><td></td>{verdicts}</tr></tbody></table></div>')
    with right, st.container(key="pnl_mandate"):
        st.html(ph("Mandate", "foundation reserve") +
                f'<dl class="kv"><dt>Objective</dt><dd>CPI as known + {inputs["real_return_target"]:.2f}% = {m["objective"]:.2f}%</dd>'
                f'<dt>Risk measure</dt><dd>annual volatility ≤ {m["vol_cap"]:.1f}%</dd>'
                f'<dt>Reserve</dt><dd>BIL ≥ {m["reserve_min"]:.0f}% (12 months of payouts)</dd>'
                f'<dt>Concentration</dt><dd>any fund ≤ {m["max_weight"]:.0f}%</dd>'
                '<dt>Benchmark</dt><dd>60% VT / 40% LQD</dd><dt>Style</dt><dd>long-only, 5-point grid</dd></dl>'
                '<p class="muted" style="margin-top:10px">The search keeps the lowest-volatility mix that passes '
                'every rule; if none does, the answer is "no mix", never a lower objective.</p>')

# ---------------------------------------------------------------- 3 stress
with tab3:
    left, right = st.columns([2.4, 1])
    with left, st.container(key="pnl_stress"):
        rows = []
        for r in built["stress"]:
            res = ('<span class="tag ok">&#10003; MIX</span>' if r["weights"] else '<span class="tag no">&#10005; STOP</span>')
            mix = " / ".join(f"{w:.0f}" for w in r["weights"]) if r["weights"] else "none"
            moved = "" if r["largest_change"] is None else f'{r["largest_change"]:.0f}'
            rows.append(f'<tr><td class="l muted">{esc(r["group"])}</td><th scope="row">{esc(r["label"])}</th>'
                        f'<td>{res}</td><td class="n">{esc(mix)}</td><td class="n">{moved}</td></tr>')
        st.html(ph("Stress run", f"one change at a time · {stopped} of {len(built['stress'])} stop the process") +
                '<div class="wrap"><table class="t"><thead><tr><th class="l">Group</th><th class="l">Change</th>'
                '<th>Result</th><th>Mix BIL/IEF/LQD/VT</th><th>Move pts</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div>')
    with right, st.container(key="pnl_range"):
        rng = built["range"]
        items = ("".join(f"<dt>{t}</dt><dd>{lo:.0f}% – {hi:.0f}%</dd>" for t, (lo, hi) in rng.items())
                 if rng else "<dt>Range</dt><dd>none</dd>")
        st.html(ph("Allocation range & stop", "across cases with a mix") +
                f'<dl class="kv">{items}<dt>Stop if</dt><dd>ERP below {analysis.pct(built["erp_floor"])}</dd>'
                f'<dt>Stop if</dt><dd>CPI y/y above {analysis.pct(built["inflation_ceiling"])}</dd>'
                f'<dt>CPI now</dt><dd>{result["inflation"]:.2f}%</dd></dl>'
                '<p class="muted" style="margin-top:10px">Move the sliders in the sidebar to test any other case; the '
                'status bar updates with every change.</p>')

    with st.container(key="pnl_erp"):
        rows = []
        for r in built["erp_ladder"]:
            tag = ('<span class="tag ok">&#10003; MIX</span>' if r["weights"] else '<span class="tag no">&#10005; STOP</span>')
            mix = " / ".join(f"{w:.0f}" for w in r["weights"]) if r["weights"] else "none"
            vol = f'{r["volatility"]:.2f}' if r["volatility"] is not None else ""
            base_row = ' class="hl"' if abs(r["erp"] - inputs["erp"]) < 1e-9 else ""
            rows.append(f'<tr{base_row}><th scope="row">{r["erp"]:.2f}%</th><td>{tag}</td><td class="n">{mix}</td>'
                        f'<td class="n">{vol}</td></tr>')
        st.html(ph("Equity risk premium range", "the load-bearing judgment, its own range") +
                '<div class="wrap"><table class="t"><thead><tr><th class="l">ERP</th><th>Result</th>'
                f'<th>Mix BIL/IEF/LQD/VT</th><th>Vol %</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')

    with st.container(key="pnl_regime"):
        reg = built["regime"]
        rmix = reg["portfolios"].get("Constrained portfolio")
        pairs = [("IEF", "VT"), ("LQD", "VT"), ("IEF", "LQD")]
        rows = "".join(f'<tr><th scope="row">{a}-{b}</th>'
                       f'<td class="n">{result["corr"][tickers.index(a)][tickers.index(b)]:.2f}</td>'
                       f'<td class="n">{reg["corr"][tickers.index(a)][tickers.index(b)]:.2f}</td></tr>' for a, b in pairs)
        base_mix = " / ".join(f"{w:.0f}" for w in best["weights"]) if best else "none"
        base_vol = f"{best['volatility']:.2f}%" if best else "n/a"
        reg_text = " / ".join(f"{w:.0f}" for w in rmix["weights"]) if rmix else "none"
        reg_vol = f"{rmix['volatility']:.2f}%" if rmix else "n/a"
        st.html(ph("Risk regime check", "why the base mix holds two funds · not a stress case") +
                '<div class="wrap"><table class="t"><thead><tr><th class="l">Correlation</th>'
                f'<th>{result["price_dates"][0][:4]}-{result["price_dates"][1][:4]} (base)</th>'
                f'<th>{built["regime_dates"][0][:4]}-{built["regime_dates"][1][:4]}</th></tr></thead><tbody>{rows}'
                f'<tr class="hl"><th scope="row">Mix BIL/IEF/LQD/VT</th><td class="n">{base_mix}</td>'
                f'<td class="n">{reg_text}</td></tr>'
                f'<tr><th scope="row">Volatility</th><td class="n">{base_vol}</td><td class="n">{reg_vol}</td></tr>'
                '</tbody></table></div>'
                '<p class="muted" style="margin-top:8px">Since 2021 bonds have moved with stocks, so they add risk '
                'without enough return and the search drops them. With the decade before the rate shock, '
                'Treasuries hedge stocks and enter the mix. Same funds, same expected returns, same mandate.</p>')

# ---------------------------------------------------------------- 4 signal
with tab4:
    data = engine.load_data(inputs)
    series = engine.cpi_inflation_series(data["cpi_rows"])
    left, right = st.columns([1.5, 1])
    with left, st.container(key="pnl_cpi"):
        sdf = pd.DataFrame(series, columns=["month", "inflation"])
        line = alt.Chart(sdf).mark_line(color=AMBER, strokeWidth=2).encode(
            x=alt.X("month:T", title=None), y=alt.Y("inflation:Q", title="CPI y/y %", scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("month:T", title="Month", format="%Y-%m"),
                     alt.Tooltip("inflation:Q", title="CPI y/y %", format=".2f")])
        last = alt.Chart(sdf.tail(1)).mark_point(filled=True, size=70, color=AMBER, stroke=PANEL, strokeWidth=2).encode(
            x="month:T", y="inflation:Q")
        ceiling = alt.Chart(sdf).mark_rule(color=BAD, strokeWidth=1).encode(y=alt.datum(built["inflation_ceiling"] or 0))
        st.html(ph("CPI inflation, as known on " + BASE["decision_date"], "ALFRED vintage · red line = stop level"))
        st.altair_chart(dark(alt.layer(line, last, ceiling), 260), width="stretch", theme=None)
    with right, st.container(key="pnl_card"):
        st.html(ph("Data card", "CPIAUCSL") +
                '<dl class="kv"><dt>Source</dt><dd>BLS via FRED / ALFRED</dd><dt>Measure</dt><dd>CPI-U, all items, SA</dd>'
                '<dt>Units</dt><dd>index, 1982–84 = 100</dd>'
                f'<dt>Latest known</dt><dd>{esc(result["cpi_month"][:7])} → {result["inflation"]:.2f}% y/y</dd>'
                '<dt>Lag</dt><dd>~2 weeks after month end</dd><dt>Revisions</dt><dd>SA factors, each February, 5 years</dd>'
                '<dt>Gap</dt><dd>2025-10 never published</dd><dt>Rule</dt><dd>later vintage refused</dd></dl>')

# ---------------------------------------------------------------- 5 data
with tab5:
    left, right = st.columns([1.2, 1])
    with left, st.container(key="pnl_est"):
        rows = "".join(f'<tr><th scope="row">{t}</th><td class="n">{r:.2f}</td><td class="n">{h:.2f}</td><td class="n">{v:.2f}</td></tr>'
                       for t, r, h, v in zip(tickers, result["expected_returns"], result["historical_mean"], result["vols"]))
        rates = data["rates"]
        st.html(ph("Estimates", "% a year") +
                '<div class="wrap"><table class="t"><thead><tr><th class="l">Fund</th><th>Expected</th>'
                f'<th>Hist. mean (not used)</th><th>Volatility</th></tr></thead><tbody>{rows}</tbody></table></div>'
                f'<dl class="kv" style="margin-top:10px"><dt>BIL</dt><dd>3m bill {rates["DTB3"][1]:.2f}</dd>'
                f'<dt>IEF</dt><dd>avg 7y {rates["DGS7"][1]:.2f} / 10y {rates["DGS10"][1]:.2f}</dd>'
                f'<dt>LQD</dt><dd>IG yield {rates["BAMLC0A0CMEY"][1]:.2f}</dd>'
                f'<dt>VT</dt><dd>10y {rates["DGS10"][1]:.2f} + ERP {inputs["erp"]:.2f}</dd>'
                '<dt>Net of</dt><dd>expense ratios</dd></dl>')
    with right, st.container(key="pnl_corr"):
        corr = result["corr"]
        cells_html = "".join(
            f'<tr><th scope="row">{a}</th>' + "".join(
                f'<td class="n" style="background:rgba(245,165,36,{max(c, 0) * 0.55:.2f})">{c:.2f}</td>' for c in row) + "</tr>"
            for a, row in zip(tickers, corr))
        st.html(ph("Correlation", f"{result['months']} monthly returns") +
                f'<div class="wrap"><table class="t"><thead><tr><th class="l"></th>{"".join(f"<th>{t}</th>" for t in tickers)}'
                f'</tr></thead><tbody>{cells_html}</tbody></table></div>'
                '<p class="muted" style="margin-top:8px">Shade = correlation (amber, darker = higher). Sources: Yahoo '
                'Finance prices; FRED/ALFRED yields and CPI, vintage of the decision date.</p>')
