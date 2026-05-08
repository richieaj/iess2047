from itertools import cycle
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import plotly.graph_objects as go
from .Model import init_vals

# ─── Design tokens ────────────────────────────────────────────────────────────
CHART_FONT        = "Inter, 'Helvetica Neue', Roboto, Arial, sans-serif"
CHART_TITLE_COLOR = "#0f172a"
CHART_AXIS_COLOR  = "#475569"
CHART_GRID_COLOR  = "rgba(15, 23, 42, 0.06)"
CHART_ZERO_COLOR  = "rgba(15, 23, 42, 0.12)"
CHART_LINE_COLOR  = "rgba(15, 23, 42, 0.15)"
CHART_BG          = "#ffffff"
CHART_PAPER_BG    = "#ffffff"
TOTAL_LINE_COLOR  = "#0f172a"

# ─── Energy-sector colour map ─────────────────────────────────────────────────
# Each entry: (fill_hex, line_hex)  — fill gets 0.85 alpha added in stacked area
_EC = {
    "coal_noncoking":    ("#64748b", "#475569"),
    "coal_coking":       ("#334155", "#1e293b"),
    "coal":              ("#64748b", "#475569"),
    "transport":         ("#0369a1", "#075985"),
    "industry":          ("#6d28d9", "#4c1d95"),
    "cooking":           ("#b45309", "#92400e"),
    "buildings":         ("#c2410c", "#9a3412"),
    "telecom":           ("#be123c", "#9f1239"),
    "agriculture":       ("#15803d", "#166534"),
    "others":            ("#1d4ed8", "#1e40af"),
    "pump":              ("#4338ca", "#3730a3"),
    "renewable":         ("#65a30d", "#4d7c0f"),
    "electricity_imports": ("#dc2626", "#b91c1c"),
    "bioenergy":         ("#16a34a", "#15803d"),
    "biomass":           ("#22c55e", "#16a34a"),
    "cross_border":      ("#84cc16", "#65a30d"),
    "natural_gas":       ("#7c3aed", "#6d28d9"),
    "oil":               ("#ea580c", "#c2410c"),
    "gas":               ("#9333ea", "#7e22ce"),
    "ccs":               ("#0891b2", "#0e7490"),
    "electricity":       ("#e11d48", "#be123c"),
    "fossil_non":        ("#4d7c0f", "#365314"),
    "fossil":            ("#78716c", "#57534e"),
    "solar_distributed": ("#eab308", "#ca8a04"),
    "solar_csp":         ("#f97316", "#ea580c"),
    "solar_pv":          ("#fbbf24", "#f59e0b"),
    "solar":             ("#f59e0b", "#d97706"),
    "wind_onshore":      ("#0284c7", "#0369a1"),
    "wind_offshore":     ("#06b6d4", "#0891b2"),
    "wind":              ("#0ea5e9", "#0284c7"),
    "hydro_large":       ("#0f766e", "#115e59"),
    "hydro_small":       ("#0d9488", "#0f766e"),
    "hydro":             ("#14b8a6", "#0d9488"),
    "nuclear":           ("#ef4444", "#dc2626"),
    "default":           ("#94a3b8", "#64748b"),
}

def _sector_color(name):
    """Return (fill_hex, line_hex) for a sector name."""
    n = name.lower()
    if "non-coking" in n or "noncoking" in n: return _EC["coal_noncoking"]
    if "coking" in n:                          return _EC["coal_coking"]
    if "coal" in n:                            return _EC["coal"]
    if "transport" in n:                       return _EC["transport"]
    if "industry" in n:                        return _EC["industry"]
    if "cooking" in n:                         return _EC["cooking"]
    if "buildings" in n:                       return _EC["buildings"]
    if "telecom" in n:                         return _EC["telecom"]
    if "agriculture" in n:                     return _EC["agriculture"]
    if "others" in n:                          return _EC["others"]
    if "pump" in n:                            return _EC["pump"]
    if "electricity imports" in n:             return _EC["electricity_imports"]
    if "bioenergy" in n:                       return _EC["bioenergy"]
    if "biomass" in n:                         return _EC["biomass"]
    if "cross border" in n:                    return _EC["cross_border"]
    if "natural gas" in n:                     return _EC["natural_gas"]
    if "oil" in n:                             return _EC["oil"]
    if "gas" in n:                             return _EC["gas"]
    if "ccs" in n:                             return _EC["ccs"]
    if "electricity" in n:                     return _EC["electricity"]
    if "fossil" in n:
        return _EC["fossil_non"] if "non" in n else _EC["fossil"]
    if "distributed solar pv" in n:            return _EC["solar_distributed"]
    if "csp" in n:                             return _EC["solar_csp"]
    if "solar pv" in n:                        return _EC["solar_pv"]
    if "solar" in n:                           return _EC["solar"]
    if "onshore" in n:                         return _EC["wind_onshore"]
    if "offshore" in n:                        return _EC["wind_offshore"]
    if "wind" in n:                            return _EC["wind"]
    if "large" in n and "hydro" in n:          return _EC["hydro_large"]
    if "small" in n and "hydro" in n:          return _EC["hydro_small"]
    if "hydro" in n:                           return _EC["hydro"]
    if "nuclear" in n:                         return _EC["nuclear"]
    if "renewable" in n:                       return _EC["renewable"]
    return _EC["default"]


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _prepare_rows(data, x):
    for row in data[::-1]:
        name = row[0]
        trace = row[1:]
        yield name, trace


def _round_y(y):
    return [round(v, 2) if isinstance(v, float) else v for v in y]


def _scatter(x, y, name, **kwargs):
    y = _round_y(y)
    tmpl = "<b>%{x}</b><br>" + name + ":  <b>%{y}</b><extra></extra>"
    return go.Scatter(x=x[-len(y):], name=name, y=y,
                      hovertemplate=tmpl, **kwargs)


def _bar(x, y, name, width=0.35, **kwargs):
    fill, line = _sector_color(name)
    return go.Bar(
        x=x[-len(y):], y=_round_y(y), name=name, width=width,
        marker=dict(color=fill, line=dict(color=line, width=0.8)),
        hovertemplate="<b>%{x}</b><br>" + name + ": <b>%{y}</b><extra></extra>",
        **kwargs,
    )


# ─── Shared layout helpers ────────────────────────────────────────────────────

def format_plot(plot, title):
    """Apply clean, professional light-theme base layout."""
    layout = plot.layout
    layout.paper_bgcolor = CHART_PAPER_BG
    layout.plot_bgcolor  = CHART_BG
    layout.margin        = dict(t=76, b=56, l=72, r=16)
    layout.title = dict(
        text=f"<b>{title}</b>",
        x=0.5, xanchor="center",
        font=dict(color=CHART_TITLE_COLOR, size=14.5, family=CHART_FONT),
    )
    layout.font = dict(family=CHART_FONT, size=12, color=CHART_AXIS_COLOR)
    layout.legend = dict(
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(15,23,42,0.1)",
        borderwidth=1,
        font=dict(size=11, family=CHART_FONT, color=CHART_AXIS_COLOR),
        orientation="v",
        x=1.01, xanchor="left",
        y=1.0,  yanchor="top",
        tracegroupgap=2,
    )
    layout.hoverlabel = dict(
        bgcolor="white",
        bordercolor="rgba(15,23,42,0.12)",
        font=dict(family=CHART_FONT, size=12, color=CHART_TITLE_COLOR),
        namelength=-1,
    )


def _xaxis_cfg():
    return dict(
        title=dict(text="<b>Year</b>",
                   font=dict(size=12, color=CHART_AXIS_COLOR, family=CHART_FONT)),
        showline=True, linecolor=CHART_LINE_COLOR, linewidth=1,
        tick0=2022, dtick=1,
        showticklabels=True,
        tickangle=35,
        tickfont=dict(size=11, color=CHART_AXIS_COLOR, family=CHART_FONT),
        zeroline=False,
        showgrid=True, gridcolor=CHART_GRID_COLOR, gridwidth=1,
        showspikes=True, spikemode="across", spikedistance=-1,
        spikethickness=1, spikesnap="cursor", spikecolor="rgba(15,23,42,0.18)",
        type="category",
    )


def _yaxis_cfg(axis_unit, max_val, scale=1.3):
    return dict(
        title=dict(text=f"<b>{axis_unit}</b>",
                   font=dict(size=12, color=CHART_AXIS_COLOR, family=CHART_FONT)),
        showline=True, linecolor=CHART_LINE_COLOR, linewidth=1,
        tick0=0, range=[0, max_val * scale],
        showgrid=True, gridcolor=CHART_GRID_COLOR, gridwidth=1,
        zeroline=True, zerolinecolor=CHART_ZERO_COLOR, zerolinewidth=1,
        tickfont=dict(size=11, color=CHART_AXIS_COLOR, family=CHART_FONT),
        showspikes=True, spikemode="across", spikedistance=-1,
        spikethickness=1, spikesnap="cursor", spikecolor="rgba(15,23,42,0.18)",
    )


def _max_val(model_output):
    m = 0
    for row in model_output:
        for v in row[1:]:
            if isinstance(v, (int, float)) and v > m:
                m = v
    return m or 1


# ─── Plot functions ───────────────────────────────────────────────────────────

def plot_stacked_area(plot, model_solution, output, title, axis_unit):
    """Stacked area chart with optional total overlay line."""
    format_plot(plot, title)
    plot.layout.xaxis = _xaxis_cfg()

    model_output = model_solution[output]
    x = model_solution["x"]
    top = _max_val(model_output)
    plot.layout.yaxis = _yaxis_cfg(axis_unit, top, scale=1.28)

    traces = []
    total  = None
    for name, y in _prepare_rows(model_output, x):
        if ("total" in name.lower()) or ("overall" in name.lower()):
            total = _scatter(
                x, y, name,
                mode="lines+markers",
                line=dict(width=2.5, color=TOTAL_LINE_COLOR, dash="solid"),
                marker=dict(size=5, color=TOTAL_LINE_COLOR,
                            line=dict(width=1, color="white")),
            )
        else:
            fill, line = _sector_color(name)
            traces.append(_scatter(
                x, y, name,
                mode="markers",
                marker=dict(size=3, opacity=0),
                stackgroup="one",
                fillcolor=fill + "D6",
                line=dict(width=1.2, color=line),
            ))
    if total:
        traces.append(total)
    plot.data = traces


def plot_line(plot, model_solution, output, title, axis_unit):
    """Multi-line chart with markers."""
    format_plot(plot, title)
    model_output = model_solution[output]
    x = model_solution["x"]
    plot.layout.xaxis = _xaxis_cfg()
    top = _max_val(model_output)
    plot.layout.yaxis = _yaxis_cfg(axis_unit, top, scale=1.35)

    traces = []
    for name, y in _prepare_rows(model_output, x):
        fill, line = _sector_color(name)
        traces.append(_scatter(
            x, y, name,
            mode="lines+markers",
            line=dict(width=2.5, color=line),
            marker=dict(size=6, color=fill,
                        line=dict(width=1.5, color=line)),
        ))
    plot.data = traces


def plot_sankey(plot, model_solution, output, title, valuesuffix):
    """Sankey / energy-flow diagram."""
    format_plot(plot, title)
    data_index = model_solution["x"].index(init_vals["sankey_data_year"])

    year_cols = {
        "output_flows_one":   2, "output_flows_two":   3,
        "output_flows_three": 4, "output_flows_four":  5,
        "output_flows_five":  6, "output_flows_six":   7,
        "output_flows_seven": 8,
    }
    if output in year_cols:
        col = year_cols[output]
        plot.layout.title.text = (
            f"<b>{title} {model_solution[output][0][col]}</b>"
        )
    plot.layout.title.x = 0.5
    plot.layout.margin  = dict(t=80, b=24, l=24, r=24)

    model_output = model_solution[output]
    sources, targets, values = [], [], []
    for source, target, *data_row in model_output[1:]:
        sources.append(source)
        targets.append(target)
        values.append(data_row[data_index])

    nodes = list(dict.fromkeys(sources + targets))
    src_i = [nodes.index(s) for s in sources]
    tgt_i = [nodes.index(t) for t in targets]

    node_palette = [
        "#1d4ed8","#15803d","#ea580c","#6d28d9","#0369a1",
        "#c2410c","#ca8a04","#0284c7","#0e7490","#7c3aed",
        "#16a34a","#dc2626","#d97706","#0f766e","#65a30d",
        "#b45309","#4338ca","#64748b","#e11d48","#0891b2",
        "#9333ea","#0d9488","#f97316","#4d7c0f","#1d4ed8",
    ]
    n_nodes = len(nodes)
    colors  = (node_palette * ((n_nodes // len(node_palette)) + 1))[:n_nodes]

    plot.data = [go.Sankey(
        valueformat=".1f",
        arrangement="fixed",
        valuesuffix=valuesuffix,
        node=dict(
            pad=18, thickness=16,
            line=dict(color="rgba(255,255,255,0.6)", width=0.5),
            label=nodes, color=colors,
            hovertemplate="%{label}: %{value:.1f}<extra></extra>",
        ),
        link=dict(
            source=src_i, target=tgt_i, value=values,
            color="rgba(15,23,42,0.06)",
            hovertemplate="%{source.label} → %{target.label}: "
                          "%{value:.1f}<extra></extra>",
        ),
    )]


def bar_chart(plot, model_solution, outputs, title, axis_unit):
    """Grouped bar chart."""
    format_plot(plot, title)
    plot.layout.xaxis = dict(
        title=dict(text="<b>Year</b>",
                   font=dict(size=12, color=CHART_AXIS_COLOR, family=CHART_FONT)),
        showline=True, linecolor=CHART_LINE_COLOR,
        dtick=0, showticklabels=True, zeroline=False,
        tickfont=dict(size=11, color=CHART_AXIS_COLOR),
        showgrid=True, gridcolor=CHART_GRID_COLOR,
        type="category",
    )
    plot.layout.yaxis = dict(
        title=dict(text=f"<b>{axis_unit}</b>",
                   font=dict(size=12, color=CHART_AXIS_COLOR, family=CHART_FONT)),
        showline=True, linecolor=CHART_LINE_COLOR,
        showgrid=True, gridcolor=CHART_GRID_COLOR,
        zeroline=True, zerolinecolor=CHART_ZERO_COLOR,
        tickfont=dict(size=11, color=CHART_AXIS_COLOR),
    )
    model_output = model_solution[outputs]
    x = model_solution["x"]
    plot.data = [_bar(x, y, name=name)
                 for name, y in _prepare_rows(model_output, x)]


def bar_chart_stacked(plot, model_solution, outputs, title, axis_unit):
    """Stacked bar chart by period."""
    format_plot(plot, title)
    plot.layout.barmode = "stack"
    plot.layout.xaxis = dict(
        title=dict(text="<b>Period</b>",
                   font=dict(size=12, color=CHART_AXIS_COLOR, family=CHART_FONT)),
        showline=True, linecolor=CHART_LINE_COLOR,
        dtick=0, showticklabels=True, zeroline=False,
        tickfont=dict(size=11, color=CHART_AXIS_COLOR),
        showgrid=True, gridcolor=CHART_GRID_COLOR,
        type="category",
    )
    plot.layout.yaxis = dict(
        title=dict(text=f"<b>{axis_unit}</b>",
                   font=dict(size=12, color=CHART_AXIS_COLOR, family=CHART_FONT)),
        showline=True, linecolor=CHART_LINE_COLOR,
        showgrid=True, gridcolor=CHART_GRID_COLOR,
        zeroline=True, zerolinecolor=CHART_ZERO_COLOR,
        tickfont=dict(size=11, color=CHART_AXIS_COLOR),
    )
    periods = ["2020–2022", "2022–2027", "2027–2032",
               "2032–2037", "2037–2042", "2042–2047"]
    model_output = model_solution[outputs]
    x = model_solution["x"]
    bars = []
    for name, y in _prepare_rows(model_output, x):
        cats = [periods[i] for i in range(len(y))]
        bars.append(_bar(cats, y, name=name, width=0.72))
    plot.data = bars


def plot_map(plot, model_solution, outputs, title, _=None):
    pass


# ─── Registry ─────────────────────────────────────────────────────────────────

PLOTS_REGISTRY = {
    "stacked area with overlying line(s)": plot_stacked_area,
    "line":         plot_line,
    "sankey/flow":  plot_sankey,
    "map":          plot_map,
    "bar_graphing": bar_chart,
    "bar_stacked":  bar_chart_stacked,
}
