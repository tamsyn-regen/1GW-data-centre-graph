"""
Regen — "Emissions of a 1GW data centre"
==========================================

Generates a single, self-contained, interactive HTML file with a grouped bar
chart comparing GHG emissions across four power-supply scenarios, clustered
by load factor (low 45% / high 95%). Built with Plotly so it's interactive
out of the box (hover tooltips, zoom, PNG export) and drops straight into a
blog via an <iframe> — see embed-snippet.html in this folder.

Requirements:
    pip install plotly pillow

Usage:
    python emissions_chart.py

Output:
    emissions-1gw-datacentre.html

Branding
--------
Colours are Regen's exact brand hex codes (text #134448, background #F1EEE2,
and the four series colours below) — this is a single fixed theme, not an
auto light/dark toggle, since only one palette was supplied.

The Regen logo ships as "regen-logo.png" next to this script (background
already keyed to transparent) and is inlined into the page as a base64 data
URI, so the output HTML has no external file dependency. Drop in a different
file — SVG or raster — named per LOGO_CANDIDATES below to swap it; an SVG is
inlined as markup, a raster image is base64-embedded. If no logo file is
found, a plain text "Regen" wordmark in the brand text colour is used
instead, so the script still produces a complete, working page.
"""

import base64
import json
import mimetypes
from pathlib import Path

import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# 1. Data
# ---------------------------------------------------------------------------

LOAD_FACTOR_SCENARIOS = ["Low load factor scenario", "High load factor scenario"]
LOAD_FACTOR_LABELS = ["Low load factor\n(45%)", "High load factor\n(95%)"]

POWER_SCENARIOS = [
    "Grid renewable PPA",
    "Average grid intensity",
    "CCGT",
    "Reciprocating engine",
]

# Mt CO2e — one value per entry in LOAD_FACTOR_SCENARIOS, in that order
EMISSIONS = {
    "Grid renewable PPA": [0.3, 0.5],
    "Average grid intensity": [0.7, 1.1],
    "CCGT": [2.7, 3.8],
    "Reciprocating engine": [3.3, 5.7],
}

# Short, stable name — used for the browser tab title and the table caption.
PAGE_TITLE = "Emissions of a 1GW data centre"

# The big on-page headline (can be a full sentence; wraps to multiple lines).
HEADLINE = (
    "In its first year of operations, a 1GW fossil fueled data center could "
    "consume from 2.7 to 5.7 Mt CO₂e"
)
SUBTITLE = (
    "Illustrative emissions of a theoretical 1GW data centre in the UK under "
    "different power providers and load factors. The low load factor "
    "scenario assumes 45%, while the high load factor scenario assumes 95%."
)
FOOTNOTE = (
    "Note: Renewables PPA assumed to guarantee a maximum carbon intensity of "
    "50g per kWh."
)
SOURCE_NOTE = "Source: Regen analysis. Figures are illustrative, not a forecast."

LOGO_CANDIDATES = [
    "regen-logo.png",
    "regen-logo.svg",
    "Regen logo - Green.svg",
    "regen-logo.jpg",
    "regen-logo.jpeg",
    "regen_logo.svg",
]
OUTPUT_FILENAME = "emissions-1gw-datacentre.html"

# ---------------------------------------------------------------------------
# 2. Regen brand colours (exact hex, as supplied)
# ---------------------------------------------------------------------------

TEXT_COLOR = "#134448"
BG_COLOR = "#F1EEE2"

# One hue family, light -> dark, ordered by emissions intensity
# (cleanest scenario lightest, most emissions-intensive scenario darkest)
COLORS = {
    "Grid renewable PPA": "#E9C5E0",
    "Average grid intensity": "#D38BC0",
    "CCGT": "#A23C87",
    "Reciprocating engine": "#501E43",
}

# Secondary/muted text is the brand text colour at reduced opacity, so
# hierarchy comes from weight, not from inventing extra brand colours.
TEXT_SECONDARY = "rgba(19, 68, 72, 0.72)"
TEXT_MUTED = "rgba(19, 68, 72, 0.55)"
GRIDLINE = "rgba(19, 68, 72, 0.12)"
BASELINE = "rgba(19, 68, 72, 0.30)"
BORDER_HAIRLINE = "rgba(19, 68, 72, 0.16)"

FONT_STACK = 'Aptos, "Aptos Display", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'


# ---------------------------------------------------------------------------
# 3. Build the Plotly figure
# ---------------------------------------------------------------------------


def build_figure() -> go.Figure:
    fig = go.Figure()

    for scenario in POWER_SCENARIOS:
        values = EMISSIONS[scenario]
        fig.add_trace(
            go.Bar(
                name=scenario,
                x=LOAD_FACTOR_LABELS,
                y=values,
                marker=dict(color=COLORS[scenario]),
                text=[f"{v:.1f}" for v in values],
                textposition="outside",
                textfont=dict(size=15, color=TEXT_SECONDARY),
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "%{x}<br>"
                    "%{y:.1f} Mt CO₂e"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        barmode="group",
        bargap=0.32,
        bargroupgap=0.12,
        font=dict(family=FONT_STACK, size=15, color=TEXT_COLOR),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color=TEXT_SECONDARY),
        ),
        yaxis=dict(
            title=dict(
                text="GHG emissions (Mt CO₂e)",
                font=dict(size=15, color=TEXT_SECONDARY),
            ),
            gridcolor=GRIDLINE,
            zerolinecolor=BASELINE,
            zerolinewidth=1,
            rangemode="tozero",
            tickfont=dict(size=14, color=TEXT_SECONDARY),
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(size=30, color=TEXT_COLOR),
            showgrid=False,
        ),
        plot_bgcolor=BG_COLOR,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=64, r=24, t=16, b=100),
        hoverlabel=dict(
            bgcolor=TEXT_COLOR,
            font_color=BG_COLOR,
            font_size=13,
            font_family=FONT_STACK,
        ),
        height=540,
    )
    return fig


# ---------------------------------------------------------------------------
# 4. Logo — inline the real file (SVG markup or base64 raster), else a
#    text wordmark fallback
# ---------------------------------------------------------------------------


def load_logo_markup(base_dir: Path) -> str:
    for candidate in LOGO_CANDIDATES:
        path = base_dir / candidate
        if not path.exists():
            continue
        if path.suffix.lower() == ".svg":
            svg = path.read_text(encoding="utf-8")
            return f'<span class="logo logo--svg">{svg}</span>'
        mime, _ = mimetypes.guess_type(path.name)
        mime = mime or "image/png"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return (
            '<span class="logo logo--raster">'
            f'<img src="data:{mime};base64,{b64}" alt="Regen">'
            "</span>"
        )
    # Fallback: no logo file found — plain brand-colour text wordmark
    return '<span class="logo logo--text">Regen</span>'


# ---------------------------------------------------------------------------
# 5. Accessible data table (the "view as table" toggle)
# ---------------------------------------------------------------------------


def build_table_html() -> str:
    header_cells = "".join(f"<th scope=\"col\">{s}</th>" for s in LOAD_FACTOR_SCENARIOS)
    rows = []
    for scenario in POWER_SCENARIOS:
        values = EMISSIONS[scenario]
        cells = "".join(f"<td>{v:.1f}</td>" for v in values)
        rows.append(f'<tr><th scope="row">{scenario}</th>{cells}</tr>')
    rows_html = "\n          ".join(rows)
    return f"""
        <table class="data-table">
          <caption>{PAGE_TITLE} — GHG emissions, Mt CO₂e</caption>
          <thead>
            <tr><th scope="col">Power scenario</th>{header_cells}</tr>
          </thead>
          <tbody>
          {rows_html}
          </tbody>
        </table>
    """.strip()


# ---------------------------------------------------------------------------
# 6. Assemble the page
# ---------------------------------------------------------------------------

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  .regen-viz {{
    --surface: {bg_color};
    --text-primary: {text_color};
    --text-secondary: {text_secondary};
    --text-muted: {text_muted};
    --gridline: {gridline};
    --baseline: {baseline};
    --border-hairline: {border_hairline};
  }}

  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    background: var(--surface);
    font-family: {font_stack};
  }}
  .regen-viz {{
    background: var(--surface);
    color: var(--text-primary);
    max-width: 900px;
    margin: 0 auto;
    padding: 24px 28px 20px;
  }}
  .viz-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 4px;
  }}
  .viz-header h1 {{ text-align: left; }}
  .logo {{ display: inline-flex; align-items: center; flex-shrink: 0; margin-top: 2px; }}
  .logo--svg svg {{ height: 26px; width: auto; display: block; }}
  .logo--raster img {{ height: 26px; width: auto; display: block; }}
  .logo--text {{
    font-weight: 700;
    font-size: 20px;
    letter-spacing: 0.02em;
    color: var(--text-primary);
  }}
  h1 {{
    font-size: 21px;
    line-height: 1.25;
    margin: 0;
    font-weight: 700;
    color: var(--text-primary);
  }}
  .subtitle {{
    font-size: 13.5px;
    line-height: 1.5;
    color: var(--text-secondary);
    max-width: 66ch;
    margin: 4px 0 18px;
  }}
  .chart-container {{ width: 100%; }}
  .footnote {{
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-muted);
    margin: 10px 0 16px;
  }}
  .viz-footer {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 6px;
    padding-top: 12px;
    border-top: 1px solid var(--border-hairline);
    font-size: 11.5px;
    color: var(--text-muted);
  }}
  .viz-footer a {{ color: var(--text-muted); }}
  .table-toggle {{
    appearance: none;
    background: transparent;
    border: 1px solid var(--baseline);
    color: var(--text-secondary);
    font-size: 11.5px;
    font-family: inherit;
    padding: 4px 10px;
    border-radius: 999px;
    cursor: pointer;
  }}
  .table-toggle:hover {{ border-color: var(--text-primary); }}
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 14px;
    font-size: 13px;
  }}
  .data-table[hidden] {{ display: none; }}
  .data-table caption {{
    text-align: left;
    font-size: 11.5px;
    color: var(--text-muted);
    margin-bottom: 6px;
  }}
  .data-table th, .data-table td {{
    text-align: right;
    padding: 6px 10px;
    border-bottom: 1px solid var(--gridline);
    font-variant-numeric: tabular-nums;
  }}
  .data-table th[scope="row"] {{ text-align: left; font-weight: 500; }}
  .data-table thead th {{ color: var(--text-secondary); font-weight: 600; }}

  @media (max-width: 520px) {{
    .regen-viz {{ padding: 18px 14px 16px; }}
    h1 {{ font-size: 18px; }}
    .viz-footer {{ flex-direction: column; align-items: flex-start; gap: 6px; }}
  }}
</style>
</head>
<body>
  <div class="regen-viz">
    <div class="viz-header">
      <h1>{headline}</h1>
      {logo_markup}
    </div>
    <p class="subtitle">{subtitle}</p>

    <div id="chart" class="chart-container"></div>

    <p class="footnote">{footnote}</p>

    <button class="table-toggle" id="table-toggle-btn" aria-expanded="false" aria-controls="data-table">
      View as table
    </button>
    <div id="data-table">
      {table_html}
    </div>

    <div class="viz-footer">
      <span>{source_note}</span>
      <a href="https://www.regen.co.uk" target="_blank" rel="noopener">regen.co.uk</a>
    </div>
  </div>

  <script>
    const FIG = {fig_json};
    const CONFIG = {{
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
      toImageButtonOptions: {{ filename: 'regen-1gw-datacentre-emissions' }}
    }};

    const chartEl = document.getElementById('chart');
    Plotly.newPlot(chartEl, FIG.data, FIG.layout, CONFIG);

    // The x-axis category labels are deliberately large on desktop; on a
    // narrow (mobile) viewport that same size forces Plotly to rotate them
    // 90 degrees and eats most of the chart's height, so step it down below
    // 520px — matching the .regen-viz mobile breakpoint above.
    let lastNarrow = null;
    function applyResponsiveTickSize() {{
      const narrow = window.innerWidth < 520;
      if (narrow === lastNarrow) return;
      lastNarrow = narrow;
      Plotly.relayout(chartEl, {{ 'xaxis.tickfont.size': narrow ? 16 : 30 }});
    }}
    applyResponsiveTickSize();
    window.addEventListener('resize', applyResponsiveTickSize);

    const tableEl = document.getElementById('data-table');
    const toggleBtn = document.getElementById('table-toggle-btn');
    tableEl.hidden = true;
    toggleBtn.addEventListener('click', () => {{
      const showing = !tableEl.hidden;
      tableEl.hidden = showing;
      toggleBtn.setAttribute('aria-expanded', String(!showing));
      toggleBtn.textContent = showing ? 'View as table' : 'Hide table';
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    base_dir = Path(__file__).resolve().parent

    fig = build_figure()

    html = PAGE_TEMPLATE.format(
        page_title=PAGE_TITLE,
        headline=HEADLINE,
        subtitle=SUBTITLE,
        footnote=FOOTNOTE,
        source_note=SOURCE_NOTE,
        logo_markup=load_logo_markup(base_dir),
        table_html=build_table_html(),
        font_stack=FONT_STACK,
        bg_color=BG_COLOR,
        text_color=TEXT_COLOR,
        text_secondary=TEXT_SECONDARY,
        text_muted=TEXT_MUTED,
        gridline=GRIDLINE,
        baseline=BASELINE,
        border_hairline=BORDER_HAIRLINE,
        fig_json=json.dumps(fig.to_plotly_json()),
    )

    out_path = base_dir / OUTPUT_FILENAME
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
