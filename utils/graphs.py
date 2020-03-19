import networkx as nx
import pandas as pd
import plotly.graph_objs as go
from colour import Color
from datetime import datetime


def network_graph(year_range: tuple, account_to_search: str) -> dict:

    # read csv's for edges and nodes...
    edge1 = pd.read_csv('data/input/edge_sample.csv')
    node1 = pd.read_csv('data/input/node_sample.csv')

    # filter the record by datetime, to enable interactive control through the input box
    # add empty Datetime column to edge1 dataframe
    edge1['Datetime'] = ""

    # contain unique account
    account_set = set()
    for index in range(0, len(edge1)):
        edge1['Datetime'][index] = datetime.strptime(edge1['Date'][index], '%d/%m/%Y')
        year_i = edge1['Datetime'][index].year
        if year_i < year_range[0] or year_i > year_range[1]:
            edge1.drop(axis=0, index=index, inplace=True)
            continue
        account_set.add(edge1['Source'][index])
        account_set.add(edge1['Target'][index])

    # to define the centric point of the network layout
    shells = []
    shell1 = [account_to_search]
    shells.append(shell1)
    shell2 = []
    for account_ in account_set:
        if account_ != account_to_search:
            shell2.append(account_)
    shells.append(shell2)

    graph_ = nx.from_pandas_edgelist(edge1, 'Source', 'Target', ['Source', 'Target', 'TransactionAmt', 'Date'], create_using=nx.MultiDiGraph())
    nx.set_node_attributes(graph_, node1.set_index('Account')['CustomerName'].to_dict(), 'CustomerName')
    nx.set_node_attributes(graph_, node1.set_index('Account')['Type'].to_dict(), 'Type')
    # pos = nx.layout.spring_layout(G)
    # pos = nx.layout.circular_layout(G)
    # nx.layout.shell_layout only works for more than 3 nodes
    if len(shell2) > 1:
        pos = nx.drawing.layout.shell_layout(graph_, shells)
    else:
        pos = nx.drawing.layout.spring_layout(graph_)
    for node in graph_.nodes:
        graph_.nodes[node]['pos'] = list(pos[node])

    if len(shell2) == 0:
        trace_recode = []  # contains edge_trace, node_trace, middle_node_trace

        node_trace = go.Scatter(x=tuple([1]), y=tuple([1]),
                                text=tuple([str(account_to_search)]),
                                textposition="bottom center",
                                mode='markers+text',
                                marker={'size': 50, 'color': 'LightBlue'})
        trace_recode.append(node_trace)

        node_trace1 = go.Scatter(x=tuple([1]), y=tuple([1]),
                                mode='markers',
                                marker={'size': 50, 'color': 'LightBlue'},
                                opacity=0)
        trace_recode.append(node_trace1)

        figure = {
            "data": trace_recode,
            "layout": go.Layout(title='Interactive Transaction Visualization',
                                showlegend=False,
                                margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                                xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                height=600
                                )}
        return figure

    # contains edge_trace, node_trace, middle_node_trace
    trace_recode = []

    colors = list(Color('brown').range_to(Color('darkred'), len(graph_.edges())))
    colors = ['rgb' + str(x.rgb) for x in colors]

    index = 0
    for edge in graph_.edges:
        x0, y0 = graph_.nodes[edge[0]]['pos']
        x1, y1 = graph_.nodes[edge[1]]['pos']
        weight = float(graph_.edges[edge]['TransactionAmt']) / max(edge1['TransactionAmt']) * 10
        trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                           mode='lines',
                           line={'width': weight},
                           marker=dict(color=colors[index]),
                           line_shape='spline',
                           opacity=1)
        trace_recode.append(trace)
        index += 1

    node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[],
                            mode='markers+text',
                            textposition="bottom center",
                            hoverinfo="text",
                            marker={'size': 50, 'color': 'LightBlue'})

    index = 0
    for node in graph_.nodes():
        x, y = graph_.nodes[node]['pos']
        hovertext = "CustomerName: " +\
                    str(graph_.nodes[node]['CustomerName']) +\
                    "<br>" + "AccountType: " +\
                    str(graph_.nodes[node]['Type'])
        text = node1['Account'][index]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['hovertext'] += tuple([hovertext])
        node_trace['text'] += tuple([text])
        index += 1

    trace_recode.append(node_trace)

    middle_hover_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers', hoverinfo="text",
                                    marker={'size': 20, 'color': 'LightBlue'},
                                    opacity=0)
    index = 0
    for edge in graph_.edges:
        x0, y0 = graph_.nodes[edge[0]]['pos']
        x1, y1 = graph_.nodes[edge[1]]['pos']
        hovertext = "From: " + str(graph_.edges[edge]['Source']) + "<br>" + "To: " + str(
            graph_.edges[edge]['Target']) + "<br>" + "TransactionAmt: " + str(
            graph_.edges[edge]['TransactionAmt']) + "<br>" + "TransactionDate: " + str(graph_.edges[edge]['Date'])
        middle_hover_trace['x'] += tuple([(x0 + x1) / 2])
        middle_hover_trace['y'] += tuple([(y0 + y1) / 2])
        middle_hover_trace['hovertext'] += tuple([hovertext])
        index += 1

    trace_recode.append(middle_hover_trace)

    figure = {
        "data": trace_recode,
        "layout": go.Layout(title='Interactive Transaction Visualization', showlegend=False, hovermode='closest',
                            margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                            xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            height=600,
                            clickmode='event+select',
                            annotations=[
                                dict(
                                    ax=(graph_.nodes[edge[0]]['pos'][0] + graph_.nodes[edge[1]]['pos'][0]) / 2,
                                    ay=(graph_.nodes[edge[0]]['pos'][1] + graph_.nodes[edge[1]]['pos'][1]) / 2, axref='x', ayref='y',
                                    x=(graph_.nodes[edge[1]]['pos'][0] * 3 + graph_.nodes[edge[0]]['pos'][0]) / 4,
                                    y=(graph_.nodes[edge[1]]['pos'][1] * 3 + graph_.nodes[edge[0]]['pos'][1]) / 4, xref='x', yref='y',
                                    showarrow=True,
                                    arrowhead=3,
                                    arrowsize=4,
                                    arrowwidth=1,
                                    opacity=1
                                ) for edge in graph_.edges]
                            )}
    return figure
