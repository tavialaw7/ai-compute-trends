"""Render the findings page (docs/index.html) from findings.json numbers."""

from html import escape

REPO = "https://github.com/tavialaw7/ai-compute-trends"

CSS = """
:root { --ink:#1d2a33; --muted:#5b6b76; --line:#e3e7ea; --accent:#2a6f97; --warn:#c1440e; }
* { box-sizing: border-box; }
body { margin:0; color:var(--ink); background:#f7f9fa; font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:820px; margin:0 auto; padding:48px 20px 80px; }
h1 { font-size:2.1rem; line-height:1.2; margin:0 0 12px; }
h2 { font-size:1.35rem; margin:48px 0 8px; }
.lede { color:var(--muted); font-size:1.1rem; margin:0 0 28px; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:28px 0; }
.stat { background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
.stat b { display:block; font-size:1.7rem; color:var(--accent); line-height:1.2; }
.stat span { color:var(--muted); font-size:.88rem; }
figure { margin:16px 0; background:#fff; border:1px solid var(--line); border-radius:10px; padding:10px; }
figure img { width:100%; height:auto; display:block; }
.caveat { border-left:4px solid var(--warn); background:#fff; padding:10px 16px; border-radius:0 8px 8px 0; margin:16px 0; }
table { border-collapse:collapse; width:100%; background:#fff; font-size:.92rem; }
th, td { border:1px solid var(--line); padding:7px 10px; text-align:left; }
th { background:#eef2f4; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
code { background:#eef2f4; padding:1px 5px; border-radius:4px; font-size:.9em; }
a { color:var(--accent); }
footer { color:var(--muted); font-size:.88rem; margin-top:56px; border-top:1px solid var(--line); padding-top:16px; }
"""


def sci(value):
    mantissa, exponent = f"{value:.1e}".split("e")
    return f"{mantissa} × 10<sup>{int(exponent)}</sup>"


def row(label, fit):
    return (f"<tr><td>{escape(label)}</td><td class='num'>{fit['n']}</td>"
            f"<td class='num'>{fit['doubling_months']:.1f}</td>"
            f"<td class='num'>{fit['ci_low']:.1f} to {fit['ci_high']:.1f}</td>"
            f"<td class='num'>{fit['growth_per_year']:.1f}×</td></tr>")


def write_report(findings, path):
    totals, fits, queries = findings["totals"], findings["fits"], findings["queries"]
    sector = findings["sector_share"]
    by_year = {r["year"]: r for r in queries["open_weights_by_year"]}
    coverage = {r["year"]: r for r in queries["coverage_by_year"]}
    by_sector = {r["sector"]: r for r in queries["open_weights_by_sector"]}
    country = {(r["period"], r["country_group"]): r["pct"] for r in queries["country_share_by_period"]}
    top = queries["top_compute"][0]
    cost = queries["top_cost"][0]
    mid, late = fits["2010 to 2022"], fits["2023 to 2026"]
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Who builds frontier AI? Compute, sectors and openness</title>
<style>{CSS}</style></head><body><main>
<h1>Who builds frontier AI?</h1>
<p class="lede">A SQL and Python analysis of {totals['models']:,} notable AI models from Epoch AI: how fast training compute grew, which sectors build the models, and how open they are.</p>

<div class="stats">
<div class="stat"><b>{mid['doubling_months']:.1f} mo</b><span>compute doubling time, 2010 to 2022</span></div>
<div class="stat"><b>{sector['2025']['Industry']:.0f}%</b><span>of 2025 notable models built by industry alone</span></div>
<div class="stat"><b>{by_year[2025]['pct_open']:.0f}%</b><span>open weights in 2025, down from {by_year[2020]['pct_open']:.0f}% in 2020</span></div>
<div class="stat"><b>{totals['with_compute']}/{totals['models']:,}</b><span>models have a compute estimate</span></div>
</div>

<h2>1. Compute grew by orders of magnitude</h2>
<figure><img src="img/compute-over-time.png" alt="Scatter plot of training compute for notable AI models on a log scale from 1990 to 2026, with fitted growth lines for 2010 to 2022 and 2023 to 2026"></figure>
<p>From 2010 to 2022, training compute doubled about every {mid['doubling_months']:.1f} months (95% bootstrap interval {mid['ci_low']:.1f} to {mid['ci_high']:.1f}, {mid['n']} models), roughly {mid['growth_per_year']:.1f}× per year. Before 2010 the doubling time was about {fits['Before 2010']['doubling_months']:.0f} months. Models that were at the frontier of compute when released doubled every {fits['Frontier models, 2010 on']['doubling_months']:.1f} months.</p>
<table><thead><tr><th>Group</th><th>Models</th><th>Doubling time (months)</th><th>95% interval</th><th>Growth per year</th></tr></thead><tbody>
{row('Before 2010', fits['Before 2010'])}{row('2010 to 2022', mid)}{row('2023 to 2026 (partial)', late)}{row('Frontier models, 2010 on', fits['Frontier models, 2010 on'])}
</tbody></table>
<div class="caveat"><b>Treat the 2023 on figure as fragile.</b> It is a short window that includes a partial 2026, it rests on {late['n']} models, and the share of models with a compute estimate fell from {coverage[2021]['pct_with_compute']:.0f}% in 2021 to {coverage[2025]['pct_with_compute']:.0f}% in 2025 (section 4). The frontier interval is narrow because frontier status is defined by compute, so that subset is selected on the outcome.</div>
<p>The largest run in the data is {escape(top['model'])} ({escape(top['organization'])}, {top['pub_date'][:4]}) at about {sci(top['compute_flop'])} FLOP. Of the {totals['with_cost']} models with a cost estimate, the costliest is {escape(cost['model'])} at roughly ${cost['cost_usd_2023'] / 1e6:,.0f} million (2023 USD).</p>

<h2>2. Industry took over</h2>
<figure><img src="img/sector-share.png" alt="Stacked area chart of the share of notable AI models by developer type from 2010 to 2025"></figure>
<p>Academia built {sector['2015']['Academia']:.0f}% of notable models in 2015, but only {sector['2025']['Academia']:.0f}% in 2025. Industry alone built {sector['2025']['Industry']:.0f}%, and industry-academia collaborations {sector['2025']['Collaboration']:.0f}%. The earliest years have few models each, so read the direction and not single points.</p>

<h2>3. Openness is lower where industry leads</h2>
<figure><img src="img/open-weights.png" alt="Line chart of the share of notable AI models with open weights by year from 2018 to 2025"></figure>
<p>Among models where Epoch records weight availability, the open share was {by_year[2020]['pct_open']:.0f}% in 2020 and {by_year[2025]['pct_open']:.0f}% in 2025. From 2022 to 2025, {by_sector['Industry']['pct_open']:.0f}% of industry-built models had open weights ({by_sector['Industry']['known']} models), compared with {by_sector['Academia']['pct_open']:.0f}% for academia ({by_sector['Academia']['known']}) and {by_sector['Collaboration']['pct_open']:.0f}% for collaborations ({by_sector['Collaboration']['known']}). Sector and year are mixed together here, so this describes the pattern and does not isolate a cause.</p>

<h2>4. How complete is the compute data?</h2>
<figure><img src="img/coverage.png" alt="Bar chart of the share of notable AI models per year that have a training compute estimate, 2010 to 2025"></figure>
<p>Only {totals['with_compute']} of {totals['models']:,} models ({100 * totals['with_compute'] / totals['models']:.0f}%) have a compute estimate, and coverage varies a lot by year. Labs that publish less about their models make estimation harder, so missing values are probably not random. Every growth rate above describes models with estimates only.</p>

<h2>5. Where the models come from</h2>
<figure><img src="img/country-share.png" alt="Grouped bar chart of the share of notable AI models by country group across three periods"></figure>
<p>US-based developers account for {country[('2022-2025', 'United States')]:.0f}% of notable models from 2022 to 2025. China rose from {country[('2018-2021', 'China')]:.0f}% in 2018 to 2021 to {country[('2022-2025', 'China')]:.0f}% in 2022 to 2025. Country is the first one listed for the developing organizations, which simplifies multinational teams.</p>

<h2>Method and limits</h2>
<ul>
<li><b>Data.</b> Epoch AI's notable AI models table ({totals['models']:,} rows, {totals['first_year']} to {totals['last_year']}; {totals['in_2026']} models in 2026, a partial year). It is released under CC BY 4.0. The copy in this repo is a snapshot taken from a public GitHub mirror, not downloaded from Epoch directly, so it may differ from Epoch's current release. See <a href="{REPO}/blob/main/data/README.md">data/README.md</a>.</li>
<li><b>Notable is Epoch's judgment.</b> The dataset does not cover every model, and its inclusion rules shape every share shown here.</li>
<li><b>Growth fits.</b> Ordinary least squares of log<sub>2</sub> compute on publication date. Intervals come from a 2,000-draw bootstrap over models with a fixed seed. They capture sampling noise only, not estimate error or selection. Era boundaries (2010, 2023) are my choices.</li>
<li><b>Shares count models, not importance.</b> A frontier model and a small research model each count once.</li>
</ul>

<footer>Code and SQL: <a href="{REPO}">{REPO.removeprefix('https://')}</a>. Data: Epoch AI, "Data on AI models", CC BY 4.0. Built by <a href="https://github.com/tavialaw7">Tavia</a>.</footer>
</main></body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
