from itertools import cycle
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import plotly.graph_objects as go
from .Model import init_vals

COLOUR_CYCLE = list([
    "rgba(31, 119, 180, 0.5)",
    "rgba(255, 127, 14, 0.5)",
    "rgba(44, 160, 44, 0.5)",
    "rgba(214, 39, 40, 0.5)",
    "rgba(148, 103, 189, 0.5)",
    "rgba(140, 86, 75, 0.5)",
    "rgba(227, 119, 194, 0.5)",
    "rgba(127, 127, 127, 0.5)",
    "rgba(188, 19, 34, 0.5)",
    "rgba(23, 190, 207, 0.5)",
    "rgba(112, 21, 163, 0.5)",
    "rgba(192, 19, 50, 0.5)",
    "rgba(71, 101, 238, 0.5)",
    "rgba(153, 31, 172, 0.5)",
    "rgba(213, 86, 13, 0.5)",
    "rgba(15, 232, 21, 0.5)",
    "rgba(229, 200, 14, 0.5)",
    "rgba(52, 44, 222, 0.5)",
    "rgba(36, 237, 222, 0.5)",
    "rgba(250, 116, 230, 0.5)",
    "rgba(232, 255, 0, 0.5)",
    "rgba(0, 217, 234, 0.5)",
    "rgba(252, 211, 57, 0.5)",
    "rgba(73, 235, 7, 0.5)",
    "rgba(37, 22, 225, 0.5)",
    "rgba(188, 0, 9, 0.5)",
    "rgba(170, 6, 193, 0.5)",
    "rgba(67, 0, 247, 0.5)",
    "rgba(33, 237, 185, 0.5)",
    "rgba(163, 136, 255, 0.5)",
    "rgba(0, 73, 73, 0.5)",
    "rgba(255, 201, 231, 0.5)",
    "rgba(89, 168, 133, 0.5)",
    "rgba(255, 41, 66, 0.5)",
    "rgba(25, 109, 187, 0.5)",
    "rgba(119, 101, 175, 0.5)",
    "rgba(100, 208, 219, 0.5)",
    "rgba(23, 190, 207, 0.5)",
    "rgba(31, 119, 10, 0.5)",
    "rgba(255, 127, 14, 0.5)",
    "rgba(44, 160, 44, 0.5)",
    "rgba(214, 39, 40, 0.5)",
    "rgba(148, 103, 189, 0.5)",
    "rgba(140, 86, 75, 0.5)",
    "rgba(227, 119, 194, 0.5)",
    "rgba(127, 27, 127, 0.5)",
    "rgba(188, 189, 34, 0.5)",
    "rgba(23, 190, 207, 0.5)",
    "rgba(31, 119, 180, 0.5)",
    "rgba(255, 127, 14, 0.5)",
    "rgba(44, 160, 44, 0.5)",
    "rgba(214, 39, 40, 0.5)",
    "rgba(148, 103, 189, 0.5)",
    "rgba(140, 86, 75, 0.5)",
    "rgba(227, 119, 194, 0.5)",
    "rgba(187, 127, 127, 0.5)",
    "rgba(188, 189, 34, 0.5)",
    "rgba(23, 190, 207, 0.5)",
    "rgba(31, 119, 180, 0.5)",
    "rgba(25, 127, 14, 0.5)",
    "rgba(44, 160, 44, 0.5)",
    "rgba(24, 39, 40, 0.5)",
    "rgba(148, 13, 189, 0.5)",
    "rgba(140, 86, 75, 0.5)",
    "rgba(227, 19, 194, 0.5)",
    "rgba(137, 17, 147, 0.5)",
    "rgba(148, 13, 89, 0.5)",
    "rgba(140, 86, 65, 0.5)",
    "rgba(27, 11, 194, 0.5)",
    "rgba(17, 127, 17, 0.5)",
    "rgba(18, 189, 4, 0.5)",
    "rgba(23, 190, 27, 0.5)",
    "rgba(31, 119, 10, 0.5)",
    "rgba(55, 127, 14, 0.5)",
    "rgba(44, 160, 44, 0.5)",
    "rgba(14, 39, 40, 0.5)",
    "rgba(148, 103, 189, 0.5)",
    "rgba(10, 86, 75, 0.5)",
    "rgba(227, 119, 194, 0.5)",
    "rgba(137, 127, 17, 0.5)",
])

def _prepare_rows(data, x):
    """Retrieve the name and data for each trace in a plot.

    Args:
        data (list): The data to be plotted, includes names and values
        x (list): The x axis. A list of years.

    Yields:
        tuple: A (name, trace) tuple. Where name is a string and trace is a list.
    """
    for row in data[::-1]:
        name = row[0] 
        trace = row[1 : ]
        yield name, trace

def _partial_scatter(x, y, name, **kwargs):

    for id, test in enumerate(y):
        if(type(test) is float):
            y[id] = round(y[id],2)

    hover_design = '<b>' + name + '</b> | <b>%{y}</b> in %{x} </b><extra></extra>'
    return go.Scatter(
    x=x[-len(y):], 
    name=name, 
    text=name, 
    y=y, 
    hovertemplate = hover_design, 
    **kwargs)

def _draw_bar(x, y, name, **kwargs):
    return go.Bar(x=x[-len(y):], y=y, name=name, width=.3,color='time', **kwargs)

def _draw_bar_stacked(x, y, name, **kwargs):
    return go.Bar(x=x[-len(y):], y=y, name=name, width=.8,color='time',**kwargs)


def format_plot(plot, title):
    """Apply standard formatting to plot. For Anvil `Plot` objects this must be
    called before the `data` attribute of the plot is set.
    """
    layout = plot.layout
    layout.margin = dict(t=120, b=80, l=60, r=30)
    layout.title = dict(text=f"<b>{title}</b>", x=0.5, font=dict(color='black',size=20, family="Arial"))

def plot_stacked_area(plot, model_solution, output, title, axis_unit):
    """Plots the stacked area type of plots.
    The traces stack on top of each other to make a total.

    Args:
        plot (plotly.graph_objects.Figure): The figure in the anvil app
        model_solution (dict): The solution returned by the model
        output (str): The named range corresponding to the output for this plot
        title (str): The title of the figure
        axis_unit (str): Unit to add as y-axis title
    """
    format_plot(plot, title)
    plot.layout.xaxis = dict(
        title=f"<b>Year</b>",
        showline = True,
        tick0=2022,
        range=[2022,6],
        dtick=1,
        showticklabels=True,
        zeroline=True,
        tickangle= 35,
        showspikes = True,
        spikemode  = 'across',
        spikedistance =  -1,
        spikethickness=1,
        spikesnap = 'cursor',
        type = 'category',
    )
    plot.layout.width = int(450)
    model_output = model_solution[output]
    #Count Array
    the_max_val = 0
    super_array_count = len(model_output)
    for t in range(super_array_count):
        for q in range(1,len(model_output[t])):
            if (model_output[t][q] > the_max_val):
                the_max_val = model_output[t][q]

    plot.layout.yaxis = dict(
        title=f"<b>{axis_unit}</b>",
        showline=True,
         tick0=0,
        range=[0,the_max_val * 1.3],
        showspikes = True,
        spikemode  = 'across',
        spikedistance =  -1,
        spikethickness=1,
        spikesnap = 'cursor',
        )
    x = model_solution["x"]
    # print("START")
    # print(model_solution)
    # print("END")
    data = []
    total = None
    for name, y in _prepare_rows(model_output, x):
    #code to eliminate less than 0 values in the graph - to cleanup plotly graphing
        # for id, test in enumerate(y):
        #     if(type(test) is float):
        #         if(test < 0 and test > -15 ):
        #             y[id] = 0
        #     y[id] = round(y[id],2)

        if ("total" or "overall") in name.lower():
            total = _partial_scatter(x, y, name, mode="lines+markers", line=dict(width=1, color="#000000"))
        # elif all(val <= 0 for val in y):
        #     data.append(_partial_scatter(x, y, name=name, mode="lines", stackgroup="two", line=dict(width=1, color="blue")))
        else:
            if "coal" in name.lower():
                if("non-coking" in name.lower()):
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1), stackgroup="one", fillcolor="#595959DD", line=dict(width=2, color="#595959")))
                elif("coking" in name.lower()):
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#222222DD", line=dict(width=2, color="#222222")))
                else:
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#595959DD", line=dict(width=2, color="#595959")))
            elif "transport" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#008f8aDD", line=dict(width=2, color="#008f8a")))
            elif "industry" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#731a65CC", line=dict(width=2, color="#731a65")))
            elif "cooking" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#bd8422DD", line=dict(width=2, color="#bd8422")))
            elif "buildings" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#c85020CC", line=dict(width=2, color="#c85020")))
            elif "telecom" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#ff0a1cDD", line=dict(width=2, color="#ff0a1c")))
            elif "agriculture" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#548235DD", line=dict(width=2, color="#548235")))
            elif "others" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#0070C0DD", line=dict(width=2, color="#0070C0")))
            elif "pump" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#482e6dDD", line=dict(width=2, color="#482e6d")))
            elif "renewable" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#a4e490DD", line=dict(width=2, color="#a4e490")))
            elif "electricity imports" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#FF0000DD", line=dict(width=2, color="#FF0000")))
            elif "bioenergy" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#68c44bDD", line=dict(width=2, color="#68c44b")))
            elif "biomass" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#85BD5FDD", line=dict(width=2, color="#85BD5F")))
            elif "cross border" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#8ab927DD", line=dict(width=2, color="#8ab927")))
            elif "natural gas" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#7030A0DD", line=dict(width=2, color="#7030A0")))
            elif "oil" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#bd8422DD", line=dict(width=2, color="#bd8422")))
            elif "gas" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#682992DD", line=dict(width=2, color="#682992")))
            elif "ccs" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#bcdcaeDD", line=dict(width=2, color="#bcdcae")))
            elif "electricity" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#f8535fDD", line=dict(width=2, color="#f8535f")))
            elif "fossil" in name.lower():
                if "non" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#548235DD", line=dict(width=2, color="#548235")))
                else:
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#595959DD", line=dict(width=2, color="#595959")))
            elif "solar" in name.lower():
                if "distributed solar pv" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#fcf265DD", line=dict(width=2, color="#ffff3c")))
                elif "csp" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#948f3dDD", line=dict(width=2, color="#bcdcae")))
                elif "solar pv" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#ffff1fDD", line=dict(width=2, color="#bcdcae")))
                else:
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#ffff1fDD", line=dict(width=2, color="#595959")))
            elif "wind" in name.lower():
                if "onshore" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#027cb5DD", line=dict(width=2, color="#ffff3c")))
                elif "offshore" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#04b3bdDD", line=dict(width=2, color="#bcdcae")))
                else:
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#00c6c5DD", line=dict(width=2, color="#00c6c5")))
            elif "hydro" in name.lower():
                if "large" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#037c82DD", line=dict(width=2, color="#ffff3c")))
                elif "small" in name.lower():
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#06599cDD", line=dict(width=2, color="#bcdcae")))
                else:
                    data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#41a0ecDD", line=dict(width=2, color="#41a0ec")))
            elif "nuclear" in name.lower():
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", fillcolor="#ff9596DD", line=dict(width=2, color="#ff9596")))
            else:
                data.append(_partial_scatter(x, y, name=name, mode="markers", marker=dict(size=4,opacity=1.0), stackgroup="one", line=dict(width=2)))
    if total:
        data.append(total)
    plot.data = data


def plot_line(plot, model_solution, output, title, axis_unit):
    """Plots the line plot type of plots.
    The traces are plotted as individual line plots with markers.

    Args:
        plot (plotly.graph_objects.Figure): The figure in the anvil app
        model_solution (dict): The solution returned by the model
        output (str): The named range corresponding to the output for this plot
        title (str): The title of the figure
        axis_unit (str): Unit to add as y-axis title
    """
    format_plot(plot, title)
    model_output = model_solution[output]
    x = model_solution["x"]
    # print("START")
    # print(model_solution)
    # print("END")
    plot.layout.xaxis = dict(
        title=f"<b>Year</b>",
        showline = True,
        tick0=2022,
        range=[2022,6],
        dtick=1,
        showticklabels=True,
        zeroline=True,
        tickangle= 35,
        showspikes = True,
        spikemode  = 'across',
        spikedistance =  -1,
        spikethickness=1,
        spikesnap = 'cursor',
        type = 'category',
    )

    #Count Array
    the_max_val = 0
    super_array_count = len(model_output)
    for t in range(super_array_count):
        for q in range(1,len(model_output[t])):
            if (model_output[t][q] > the_max_val):
                the_max_val = model_output[t][q]

    plot.layout.yaxis = dict(
        title=f"<b>{axis_unit}</b>",
        showline=True,
        tick0=0,
        range=[0,the_max_val * 1.4],
        showspikes = True,
        spikemode  = 'across',
        spikedistance =  -1,
        spikethickness=1,
        spikesnap = 'cursor',
    )
    data2 = []
    for name, y in _prepare_rows(model_output, x):
        for id, test in enumerate(y):
            y[id] = round(y[id],2)

        if "coal" in name.lower():
            if("non-coking" in name.lower()):
                data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#595959")))
            elif("coking" in name.lower()):
                data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#222222")))
            else:
                data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#595959")))
        elif "transport" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#008f8a")))
        elif "industry" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#731a65")))
        elif "cooking" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#bd8422")))
        elif "buildings" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#c85020")))
        elif "telecom" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#ff0a1c")))
        elif "agriculture" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#548235")))
        elif "others" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#0070C0")))
        elif "pump" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#482e6d")))
        elif "renewable" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#a4e490")))
        elif "electricity imports" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#FF0000")))
        elif "bioenergy" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#68c44b")))
        elif "biomass" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#85BD5F")))
        elif "cross border" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#8ab927")))
        elif "natural gas" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#7030A0")))
        elif "oil" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#bd8422")))
        elif "gas" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#682992")))
        elif "ccs" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#bcdcae")))
        elif "electricity" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#f8535f")))
        elif "fossil" in name.lower():
            if "non" in name.lower():
                data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#447734")))
            else:
                data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#777777")))
        elif "solar" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#ffff3c")))
        elif "wind" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#00c6c5")))
        elif "hydro" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#41a0ec")))
        elif "nuclear" in name.lower():
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2, color="#ff9596")))
        else:
            data2.append(_partial_scatter(x, y, name=name, mode="lines+markers",  line=dict(width=2)))
    plot.data = data2

def plot_sankey(plot, model_solution, output, title, valuesuffix):
    """Creates and plots a Sankey flow diagram.

    Args:
        plot (plotly.graph_objects.Figure): The figure in the anvil app
        model_solution (dict): The solution returned by the model
        output (str): The named range corresponding to the output for this plot
        title (str): The title of the figure
        valuesuffice (str): Value passed as valuesuffix to Go.Sankey
    """
    format_plot(plot, title)
    # Manipulation of Title
    data_index = model_solution["x"].index(init_vals["sankey_data_year"])
    # Dynamic Title
    if(output == "output_flows_one"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][2]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    elif(output == "output_flows_two"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][3]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    elif(output == "output_flows_three"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][4]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    elif(output == "output_flows_four"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][5]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    elif(output == "output_flows_five"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][6]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    elif(output == "output_flows_six"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][7]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    elif(output == "output_flows_seven"):
        plot.layout.title = dict(text=f"<b>{title} {model_solution[output][0][8]}</b>", x=-0.5, font=dict(color='black',size=20, family="Arial"))
    model_output = model_solution[output]
    sources = []
    targets = []
    values = []
    for source, target, *data_row in model_output[1::]:
        sources.append(source)
        targets.append(target)
        values.append(data_row[data_index])
    nodes = list(set(sources + targets))
    sources = [nodes.index(source) for source in sources]
    targets = [nodes.index(target) for target in targets]
    
    plot.data = [
        go.Sankey(
            valueformat=".0f",
            arrangement="fixed",
            valuesuffix=valuesuffix,
            node=dict(
                pad=15,
                thickness=15,
                line=dict(color="black", width=0.5),
                label=nodes,
                color=COLOUR_CYCLE,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=COLOUR_CYCLE
            ),
        )
    ]

def bar_chart (plot, model_solution, outputs, title, axis_unit):
    """This function helps in making a bar chart."""
    format_plot(plot, title)
    plot.layout.yaxis.title = f"{axis_unit}"

    plot.layout.xaxis = dict(
        title=f"<b>Year</b>",
        showline = True,
        tick0=2022,
        range=[2022,6],
        dtick=0,
        showticklabels=True,
        zeroline=True,
        # tickangle= 35,
        showspikes = True,
        # spikemode  = 'across',
        # spikedistance =  -1,
        # spikethickness=1,
        # spikesnap = 'cursor',
        type = 'category',
    )
    plot.layout.yaxis = dict(
        title=f"<b>{axis_unit}</b>",
        )

    # plot.layout.xaxis.title = "Year"
    model_output = model_solution[outputs]
    x = model_solution["x"]
    data_bar = []
    for name, y in _prepare_rows(model_output, x):
        for id, test in enumerate(y):
            y[id] = round(y[id],2)
        data_bar.append(_draw_bar(x, y, name=name))
    plot.data = data_bar

def bar_chart_stacked (plot, model_solution, outputs, title, axis_unit):
    """This function helps in making a bar chart."""
    format_plot(plot, title)
    plot.layout.barmode = 'stack'
    plot.layout.xaxis = dict(
        title=f"<b>Year</b>",
        # showline = True,
        # tick0=2022,
        # range=[2022,6],
        dtick=0,
        showticklabels=True,
        zeroline=True,
    #     # tickangle= 35,
        showspikes = True,
    #     # spikemode  = 'across',
    #     # spikedistance =  -1,
    #     # spikethickness=1,
    #     # spikesnap = 'cursor',
        type = 'category',
    )
    plot.layout.yaxis = dict(
        title=f"<b>{axis_unit}</b>",
        )
    
    # plot.layout.xaxis.title = "Year"
    model_output = model_solution[outputs]
    x = model_solution["x"]
    data_bar = []
    tr = []
    new_cat = ['2020-2022','2022-2027','2027-2032','2032-2037','2037-2042','2042-2047']
    for name, y in _prepare_rows(model_output, x):
        for id, test in enumerate(y):
            y[id] = round(y[id],2)
            tr.append(new_cat[id])
        data_bar.append(_draw_bar_stacked(tr, y, name=name))
    plot.data = data_bar
   
def plot_map(plot, model_solution, outputs, title, _=None):
    pass
    """Plot the Map type to show land areas over a map of the region.

    Args:
        plot (plotly.graph_objects.Figure): The figure in the anvil app
        model_solution (dict): The solution returned by the model
        outputs (str): The named ranges corresponding to the outputs for this plot
        title (str): The title of the figure
        _: dummy argument to match interface of other plotting routines
    """
    index = model_solution["x"].index(init_vals["maps_data_year"])
    data = {}
    for output in outputs.split(","):
        if "area" in output:
            key = "area"
        elif "distance" in output:
            key = "distance"
        else:
            continue
        data.setdefault(key, []).extend(
            [line[0], line[index]] for line in model_solution[output]
        )
    fig = anvil.server.call("map", data)
    format_plot(fig, title)
    plot.figure = fig


PLOTS_REGISTRY = {
    "stacked area with overlying line(s)": plot_stacked_area,
    "line": plot_line,
    "sankey/flow": plot_sankey,
    "map": plot_map,
    "bar_graphing":bar_chart,
    "bar_stacked":bar_chart_stacked,
}
"""Dictionary mapping plot type names to their functions."""
