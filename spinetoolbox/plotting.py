######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Functions for plotting on PlotWidget."""
from bokeh.embed import file_html
from bokeh.layouts import gridplot, column
from bokeh.resources import INLINE
from bokeh.models import ColumnDataSource, HoverTool, Legend, RangeTool
from bokeh.palettes import Colorblind, TolRainbow
from bokeh.plotting import figure
from contextlib import contextmanager
from dataclasses import dataclass, field, replace, asdict, is_dataclass
import datetime
from enum import auto, Enum, unique
import functools
import math
from operator import itemgetter, methodcaller
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
import numpy as np
from PySide6.QtCore import QSize, Qt, QUrl
from spinedb_api import DateTime, IndexedValue
from spinedb_api.dataframes import to_dataframe
from spinedb_api.parameter_value import NUMPY_DATETIME64_UNIT
from .mvcmodels.shared import PARSED_ROLE
from .widgets.plot_widget import PlotWidget

import inspect
from rich.pretty import pprint


LEGEND_PLACEMENT_THRESHOLD = 8


@unique
class PlotType(Enum):
    SCATTER = auto()
    SCATTER_LINE = auto()
    LINE = auto()
    STACKED_LINE = auto()
    BAR = auto()
    STACKED_BAR = auto()


_BASE_SETTINGS = {"alpha": 0.7}
_SCATTER_PLOT_SETTINGS = {"linestyle": "", "marker": "o"}
_LINE_PLOT_SETTINGS = {"linestyle": "solid"}
_SCATTER_LINE_PLOT_SETTINGS = dict(_SCATTER_PLOT_SETTINGS, **_LINE_PLOT_SETTINGS)


class PlottingError(Exception):
    """An exception signalling failure in plotting."""


@dataclass(frozen=True)
class IndexName:
    label: str
    id: int


@dataclass(frozen=True)
class XYData:
    """Two-dimensional data for plotting."""

    x: List[Union[float, int, str, np.datetime64]]
    y: List[Union[float, int]]
    x_label: IndexName
    y_label: str
    data_index: List[str]
    index_names: List[IndexName]


@dataclass
class TreeNode:
    """A labeled node in tree structure."""

    label: Union[str, IndexName]
    content: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class ParameterTableHeaderSection:
    """Header section info for Database editor's parameter tables."""

    label: str
    separator: Optional[str] = None


def convert_indexed_value_to_tree(value):
    """Converts indexed values to tree nodes recursively.

    Args:
        value (IndexedValue): value to convert

    Returns:
        TreeNode: root node of the converted tree

    Raises:
        ValueError: raised when leaf value couldn't be converted to float
    """
    d = TreeNode(value.index_name)
    for index, x in zip(value.indexes, value.values):
        if isinstance(x, IndexedValue):
            x = convert_indexed_value_to_tree(x)
        else:
            try:
                x = float(x)
            except TypeError as error:
                raise ValueError("cannot plot null values") from error
        d.content[index] = x
    return d


def turn_node_to_xy_data(root_node, y_label_position, index_names=None, indexes=None):
    """Constructs plottable data and indexes recursively.

    Args:
        root_node (TreeNode): root node
        y_label_position (int, optional): position of y label in indexes
        index_names (list of IndexName, optional): list of current index names
        indexes (list): list of current indexes

    Yields:
        XYData: plot data
    """
    if index_names is None:
        index_names = []
    if indexes is None:
        indexes = []
    index_name = (
        root_node.label if isinstance(root_node.label, IndexName) else IndexName(root_node.label, len(index_names))
    )
    current_index_names = index_names + [index_name]
    x = []
    y = []
    for index, sub_node in root_node.content.items():
        if isinstance(sub_node, TreeNode):
            current_indexes = indexes + [index]
            yield from turn_node_to_xy_data(sub_node, y_label_position, current_index_names, current_indexes)
        else:
            x.append(index)
            y.append(sub_node)
    if x:
        x_label = current_index_names[-1]
        y_label = indexes[y_label_position] if y_label_position is not None else ""
        yield XYData(x, y, x_label, y_label, indexes, current_index_names[:-1])


def raise_if_not_common_x_labels(data_list):
    """Raises an exception if data has different x axis labels.

    Args:
        data_list (list of XYData): data to check

    Raises:
        PlottingError: raised if x axis labels don't match.
    """
    if len(data_list) < 2:
        return
    first_label = data_list[0].x_label
    if any(data.x_label.label != first_label.label for data in data_list[1:]):
        raise PlottingError("X axis labels don't match.")


def raise_if_incompatible_x(data_list):
    """Raises an exception if the types of x data don't match.

    Args:
        data_list (list of XYData): data to check

    Raises:
        PlottingError: raised if x data types don't match.
    """
    if not data_list:
        return
    data = data_list[0]
    if not data.x:
        return
    first_type = type(data.x[0])
    if any(not isinstance(x, first_type) for data in data_list for x in data.x):
        raise PlottingError("Incompatible x axes.")


def reduce_indexes(data_list):
    """Removes redundant indexes from given XYData.

    Args:
        data_list (list of XYData): data to reduce

    Returns:
        tuple: reduced data list and list of common data indexes
    """
    unique_indexes = {}
    min_indexes = math.inf
    for data in data_list:
        min_indexes = min(min_indexes, len(data.data_index))
    for data in data_list:
        for i, index in enumerate(data.data_index[:min_indexes]):
            unique_indexes.setdefault(i, set()).add(index)
    non_redundant_i = [i for i, indexes in unique_indexes.items() if len(indexes) > 1]
    common_indexes = [next(iter(indexes)) for i, indexes in unique_indexes.items() if len(indexes) == 1]
    new_data_list = []
    for data in data_list:
        reduced_index = [data.data_index[i] for i in non_redundant_i] + data.data_index[min_indexes:]
        reduced_names = [data.index_names[i] for i in non_redundant_i] + data.index_names[min_indexes:]
        new_data_list.append(replace(data, data_index=reduced_index, index_names=reduced_names))
    return new_data_list, common_indexes


def combine_data_with_same_indexes(data_list):
    """Combines data with same data indexes into the same x axis.

    Args:
        data_list (list of XYData): data to combine

    Returns:
        list of XYData: combined data
    """
    combined_data = []
    unique_indexes = {}
    for i, data in enumerate(data_list):
        unique_indexes.setdefault(tuple(data.data_index) + (data.x_label,), []).append(i)
    for list_is in unique_indexes.values():
        if len(list_is) == 1:
            combined_data.append(data_list[list_is[0]])
            continue
        combined_xy = []
        for i in list_is:
            combined_xy += list(zip(data_list[i].x, data_list[i].y))
        combined_xy.sort(key=itemgetter(0))
        x, y = zip(*combined_xy)
        model_data = data_list[list_is[0]]
        combined_data.append(replace(model_data, x=list(x), y=list(y)))
    return combined_data


def _always_single_y_axis(plot_type):
    """Returns True if a single y-axis should be used.

    Args:
        plot_type (PlotType): plot type

    Returns:
        bool: True if single y-axis is required, False otherwise
    """
    return plot_type in (PlotType.STACKED_LINE,)


def parse_time(data: XYData, axis: str) -> list[int] | list[str]:
    assert axis in ("x", "y")  # FIXME: is "y" possible?
    if getattr(data, f"{axis}_label").label in ("time", "period"):
        return list(map(lambda i: int(i.lstrip("pt")), getattr(data, axis)))
    else:
        return getattr(data, axis)


def xydata_to_df(data_list: list[XYData]) -> tuple[pd.DataFrame, list[str]]:
    """Merge `list[XYData]` into a `pandas.DataFrame`.

    Merge a list of datasets into one unified dataframe.  If x and y
    labels mismatch, a superset of column names will be present in the
    final dataframe, and the missing values will be set to NaN.

    The function also merges the indices in a similar manner, and
    concatenates the index and value dataframe along the column axis
    (`axis=1`).

    Parameters
    ----------
    data_list : list[XYData]
        List of datasets

    Returns
    -------
    tuple[pandas.DataFrame, list[str]]
        Tuple of dataframe, and a list of columns that are index columns.

    """
    # merge data
    # FIXME: absent columns in some data will lead to type conversion
    series_df = pd.concat(
        [pd.DataFrame({data.x_label.label: parse_time(data, "x"), data.y_label: data.y}) for data in data_list],
        axis=0,
        ignore_index=True,
    )

    # superset of common index names, first seen ordered set
    index_names = list({name.label: None for data in data_list for name in data.index_names})

    # indices w/ values
    indices = pd.DataFrame(
        sum([[[str(i) for i in data.data_index]] * len(data.x) for data in data_list], start=[]),
        columns=index_names,
    )

    df = pd.concat([indices, series_df], axis=1)
    cat_types = (np.dtype("O"), pd.StringDtype)
    for col, _type in df.dtypes.items():
        if _type in cat_types:
            df[col] = df[col].astype("category")
    return df, list(index_names)


def squeeze_df(df: pd.DataFrame, index_names: list[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Remove dataframe columns that have a single value, and return as a dict."""
    counts = df.nunique()
    squeezed_idxs = {c: df[c].iloc[0] for c, v in counts.items() if c in index_names and v == 1}
    cols = [c for c in df.columns if c not in squeezed_idxs]
    # squeezed_idxs = {k: df[k].iloc[0] for k, v in counts.items() if v == 1}
    # if len(counts) == len(squeezed_idxs):  # only one row in df
    #     cols = counts.index[-2:]
    #     # pop last 2 columns, x & y
    #     squeezed_idxs.popitem()
    #     squeezed_idxs.popitem()
    # else:
    #     # FIXME: is it possible that only one column has non-unique values?
    #     cols = [k for k, v in counts.items() if v > 1]
    return df.loc[:, cols], squeezed_idxs


def plot_variants(sdf: pd.DataFrame, index_names: list[str]) -> pd.DataFrame:
    """Determine all possible plots that are possible.

    The different plot variants are determined by looking at the
    intersection of the columns present in the squeezed dataframe and
    the complete list of index columns.  This comparison identifies
    the number of index columns that have more than one unique values.

    """
    idx_cols = sdf.columns.intersection(index_names)
    nplots_df = sdf.loc[:, idx_cols].drop_duplicates()
    return nplots_df


def get_palette(nplots_df: pd.DataFrame) -> tuple[str, ...]:
    nplots = len(nplots_df)
    if nplots < 3:
        palette: tuple[str, ...] = TolRainbow[3]
    elif nplots < 24:
        palette: tuple[str, ...] = TolRainbow[nplots]
    else:
        palette: tuple[str, ...] = TolRainbow[23]
    return palette


def plot_sequence(sdf: pd.DataFrame) -> bool:
    col_dtypes = sdf.dtypes
    if len(col_dtypes) == 2:
        return False
    else:
        x_dtype, y_dtype = col_dtypes.iloc[-2:]
        if x_dtype.kind in ("i", "f", "M"):  # numeric/datetime
            return True
        if x_dtype.kind == "O":
            return x_dtype == datetime.datetime
        return False


def fmt_query(names: pd.Series) -> str:
    return "&&".join([f"{k}=={v!r}" for k, v in names.items()])


def plot_faceted(sdf: pd.DataFrame, nplots_df: pd.DataFrame, title: str):
    palette = get_palette(nplots_df)
    # TODO:
    # - resolve x_label & y_label if they don't match
    # - x_axis_type="datetime"/...
    # - flexible plot dimensions
    # - tooltips
    x_label, y_label = sdf.columns[-2:]
    tooltips = [(col.capitalize(), f"@{col}") for col in sdf.columns]

    figs, sources = [], []
    for idx, (_, row) in enumerate(nplots_df.iterrows()):
        query = fmt_query(row)
        cds = ColumnDataSource(data=sdf.query(query))
        sources.append(cds)
        if idx == 0:
            x_range = (0, len(cds.data["index"]) // 10)
        else:
            x_range = figs[0].x_range
        fig = figure(
            x_axis_label=x_label,
            y_axis_label=y_label,
            title=query,
            height=200,
            width=400,
            x_range=x_range,
            tooltips=tooltips,
        )
        fig.line(x_label, y_label, source=cds, color=palette[idx])
        fig.scatter(x_label, y_label, source=cds, color=palette[idx], size=3)
        # TODO: derive key robustly
        figs.append(fig)

    select = figure(
        title="Select time range",
        y_axis_type=None,
        height=100,
        width=800,
        tools="",
        toolbar_location=None,
        y_range=(0, 50),
    )
    range_tool = RangeTool(x_range=figs[0].x_range, start_gesture="pan")
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.line(x_label, y_label, source=sources[0])
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    # grid_size = math.ceil(math.sqrt(nplots))
    # plots = gridplot([figs[i : i + grid_size] for i in range(0, nplots, grid_size)])
    plots = gridplot([figs[i : i + 2] for i in range(0, len(nplots_df), 2)])
    return column(select, plots)


def plot_overlayed(sdf: pd.DataFrame, nplots_df: pd.DataFrame, title: str):
    palette = get_palette(nplots_df)
    query = fmt_query(nplots_df.iloc[0])
    pprint(query)

    # FIXME: account for all x ranges
    d0 = sdf.query(query)
    x_range = (0, len(d0) // 10)

    # TODO:
    # - resolve x_label & y_label if they don't match
    # - x_axis_type="datetime"/...
    # - flexible plot dimensions
    # - tooltips
    x_label, y_label = sdf.columns[-2:]

    sources = []
    legend_items = {}
    fig = figure(x_axis_label=x_label, y_axis_label=y_label, title=title, height=400, width=800, x_range=x_range)
    for idx, (_, row) in enumerate(nplots_df.iterrows()):
        query = fmt_query(row)
        cds = ColumnDataSource(data=sdf.query(query))
        line = fig.line(x_label, y_label, source=cds, color=palette[idx])
        point = fig.scatter(x_label, y_label, source=cds, color=palette[idx], size=3)
        # TODO: derive key robustly
        sources.append(cds)
        legend_items[query] = [line, point]

    legend = Legend(items=list(legend_items.items()))
    fig.add_layout(legend, "right")
    fig.legend.click_policy = "hide"

    select = figure(
        title="Select time range",
        y_axis_type=None,
        height=100,
        width=800,
        tools="",
        toolbar_location=None,
        y_range=(0, 100),
    )
    range_tool = RangeTool(x_range=fig.x_range, start_gesture="pan")
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.line(x_label, y_label, source=sources[0])
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    return column(fig, select)


def plot_barchart(sdf: pd.DataFrame, index_names: list[str], title: str):
    # TODO:
    # - resolve x_label & y_label if they don't match
    # - x_axis_type="datetime"/...
    # - flexible plot dimensions
    # - tooltips
    x_label, y_label = sdf.columns[-2:]
    tooltips = [(col.capitalize(), f"@{col}") for col in sdf.columns]

    fig = figure(
        x_axis_label=x_label,
        y_axis_label=y_label,
        title=title,
        height=600,
        width=800,
        x_range=sdf[x_label].to_list(),
        tooltips=tooltips,
    )
    fig.vbar(x=x_label, top=y_label, source=sdf)
    fig.y_range.start = -100
    # fig.xaxis.major_label_orientation = "vertical"  # or angle in radians
    fig.xaxis.major_label_orientation = np.pi / 3
    return fig


def plot_data(data_list, plot_widget=None, plot_type=None):
    """
    Returns a plot widget with plots of the given data.

    Args:
        data_list (list of XYData): data to plot
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget
        plot_type (PlotType, optional): plot type

    Returns:
        a PlotWidget object
    """
    # debug
    for i, data in enumerate(data_list):
        if i > 2:
            break
        print(i)
        pprint(data, max_length=8)

    if plot_widget is None:
        plot_widget = PlotWidget()
        needs_redraw = False
    else:
        needs_redraw = True

    all_data = data_list  # FIXME: convert all_data to use pandas df
    squeezed_data, common_indexes = reduce_indexes(data_list)
    squeezed_data = combine_data_with_same_indexes(squeezed_data)

    # debug
    pprint(common_indexes)
    print("squeezed")
    for i, data in enumerate(squeezed_data):
        if i > 2:
            break
        pprint(data, max_length=8)

    if len(squeezed_data) > 1 and any(not data.data_index for data in squeezed_data):
        unsqueezed_index = common_indexes.pop(-1) if common_indexes else "<root>"
        for data in squeezed_data:
            data.data_index.insert(0, unsqueezed_index)
    if not squeezed_data:
        return plot_widget
    raise_if_not_common_x_labels(squeezed_data)
    raise_if_incompatible_x(squeezed_data)

    if needs_redraw:
        _clear_plot(plot_widget)

    # # TODO: only do line plots now
    # if plot_type is None:
    #     plot_type = PlotType.SCATTER_LINE if not isinstance(squeezed_data[0].x[0], np.datetime64) else PlotType.LINE

    # # TODO:
    # _limit_string_x_tick_labels(squeezed_data, plot_widget)

    # # handle multiple y-axis
    # if len(y_labels) == 1 or _always_single_y_axis(plot_type):
    #     legend_handles = _plot_single_y_axis(squeezed_data, y_labels[0], plot_widget.canvas.axes, plot_type)
    # elif len(y_labels) == 2:
    #     legend_handles = _plot_double_y_axis(squeezed_data, y_labels, plot_widget, plot_type)
    # else:
    #     legend_handles = _plot_single_y_axis(squeezed_data, "", plot_widget.canvas.axes, plot_type)

    plot_title = " | ".join(map(str, common_indexes))

    df, index_names = xydata_to_df(data_list)
    sdf, idx_cols = squeeze_df(df, index_names)
    nplots_df = plot_variants(sdf, index_names)

    # debug
    print("df")
    pprint(df, max_length=3)
    print("sdf")
    pprint(sdf, max_length=3)
    print("nplots_df")
    pprint(nplots_df)
    print("index_names")
    pprint(index_names)
    print("idx_cols")
    pprint(idx_cols)

    if plot_sequence(sdf):
        # plot = plot_faceted(df, nplots_df, plot_title)
        plot = plot_overlayed(df, nplots_df, plot_title)
    else:
        plot = plot_barchart(sdf, index_names, plot_title)

    html = file_html(plot, INLINE, plot_title)
    print(html, file=plot_widget.html_path)
    if plot.width and plot.height:
        plot_widget.resize(QSize(plot.width + 50, plot.height + 50))

    # # TODO: tick orientation
    # for data in data_list:
    #     if type(data.x[0]) not in (float, np.float64, int):
    #         plot_widget.canvas.axes.tick_params(axis="x", labelrotation=30)

    # if needs_redraw:
    #     plot_widget.canvas.draw()
    plot_widget.original_xy_data = all_data
    return plot_widget


def _plot_single_y_axis(data_list, y_label, axes, plot_type):
    """Plots all data on single y-axis.

    Args:
        data_list (list of XYData): data to plot
        y_label (str): y-axis label
        axes (Axes): plot axes
        plot_type (PlotType): plot type

    Returns:
        list: legend handles
    """
    if plot_type == PlotType.STACKED_LINE:
        return _plot_stacked_line(data_list, y_label, axes)
    if plot_type == PlotType.BAR:
        return _plot_bar(data_list, y_label, axes)
    legend_handles = []
    plot = _make_plot_function(plot_type, type(data_list[0].x[0]), axes)
    for data in data_list:
        plot_label = " | ".join(map(str, data.data_index))
        x = _make_x_plottable(data.x)
        handles = plot(x, data.y, label=plot_label)
        legend_handles += handles
    axes.set_ylabel(y_label)
    return legend_handles


def _plot_stacked_line(data_list, y_label, axes):
    """Plots all data as stacked lines.

    Args:
        data_list (list of XYData): data to plot
        y_label (str): y-axis label
        axes (Axes): plot axes

    Returns:
        list: legend handles
    """
    if any(data.x != data_list[0].x for data in data_list[1:]):
        raise PlottingError("Cannot stack plots when x-axes don't match.")
    x = _make_x_plottable(data_list[0].x)
    y = [data.y for data in data_list]
    labels = [" | ".join(map(str, data.data_index)) for data in data_list]
    handles = axes.stackplot(x, y, labels=labels, **_LINE_PLOT_SETTINGS, **_BASE_SETTINGS)
    axes.set_ylabel(y_label)
    return handles


def _plot_bar(data_list, y_label, axes):
    """Plots all data as bars.

    Args:
        data_list (list of XYData): data to plot
        y_label (str): y-axis label
        axes (Axes): plot axes

    Returns:
        list: legend handles
    """
    legend_handles = []
    plot_kwargs = {"axes": axes, **_BASE_SETTINGS}
    data_list, bar_width, x_ticks = _group_bars(data_list)
    if bar_width is not None:
        plot_kwargs["width"] = bar_width
    for data in data_list:
        plot_kwargs["label"] = " | ".join(map(str, data.data_index))
        x = _make_x_plottable(data.x)
        handles = _bar(x, data.y, **plot_kwargs)
        legend_handles += handles
    if x_ticks is not None:
        axes.set_xticks(*x_ticks)
    if axes.get_ylim()[0] < 0:
        axes.axhline(linewidth=1, color="black")
    axes.set_ylabel(y_label)
    return legend_handles


def _plot_double_y_axis(data_list, y_labels, plot_widget, plot_type):
    """Plots all data on two y-axes.

    Args:
        data_list (list of XYData): data to plot
        y_labels (list of str): y-axis labels
        plot_widget (PlotWidget): plot widget
        plot_type (PlotType): plot type

    Returns:
        list: legend handles
    """
    legend_handles = []
    left_label = y_labels[0]
    right_label = y_labels[1]
    x_data_type = type(data_list[0].x[0])
    plot_left = _make_plot_function(plot_type, x_data_type, plot_widget.canvas.axes)
    right_axes = plot_widget.canvas.axes.twinx()
    plot_right = _make_plot_function(plot_type, x_data_type, right_axes)
    for data in data_list:
        plot_label = " | ".join(map(str, data.data_index))
        x = _make_x_plottable(data.x)
        if data.y_label == left_label:
            plot = plot_left
            color = "crimson"
            marker = "s"
        else:
            plot = plot_right
            color = None
            marker = "o"
        handles = plot(x, data.y, label=plot_label, color=color, marker=marker)
        legend_handles += handles
    plot_widget.canvas.axes.set_ylabel(left_label)
    right_axes.set_ylabel(right_label)
    return legend_handles


def _make_x_plottable(xs):
    """Converts x-axis values to something matplotlib can handle.

    Args:
        xs (list): x values

    Returns:
        list: x values
    """
    if xs and isinstance(xs[0], DateTime):
        return [np.datetime64(x.value, NUMPY_DATETIME64_UNIT) for x in xs]
    return xs


class _PlotStackedBars:
    def __init__(self, axes):
        self._axes = axes
        self._cumulative_height = {}

    def __call__(self, x, height, **kwargs):
        bottom = [self._cumulative_height.get(key, 0.0) for key in x]
        for key, h in zip(x, height):
            cumulative = self._cumulative_height.get(key, 0.0)
            self._cumulative_height[key] = cumulative + h
        return _bar(x, height, self._axes, bottom=bottom, **_BASE_SETTINGS, **kwargs)


def _make_time_series_settings(plot_settings):
    """Creates plot settings suitable for time series step plots.

    Args:
        plot_settings (dict): base plot settings

    Returns:
        dict: time series step plot settings
    """
    settings = dict(plot_settings)
    settings.update(where="post")
    return settings


def _make_plot_function(plot_type, x_data_type, axes):
    """Decides plot method and default keyword arguments based on XYData.

    Args:
        plot_type (PlotType): plot type
        x_data_type (Type): data type of x-axis
        axes (Axes): plot axes

    Returns:
        Callable: plot method
    """
    if plot_type == PlotType.STACKED_BAR:
        return _PlotStackedBars(axes)
    is_time_series = _is_time_stamp_type(x_data_type)
    plot_method = axes.step if is_time_series else axes.plot
    if plot_type == PlotType.SCATTER:
        plot_settings = _SCATTER_PLOT_SETTINGS
    elif plot_type == PlotType.SCATTER_LINE:
        plot_settings = _SCATTER_LINE_PLOT_SETTINGS
    elif plot_type == PlotType.LINE:
        plot_settings = _LINE_PLOT_SETTINGS
    else:
        raise RuntimeError(f"Unknown plot type '{plot_type}'")
    if is_time_series:
        plot_settings = _make_time_series_settings(plot_settings)
    return functools.partial(plot_method, **plot_settings, **_BASE_SETTINGS)


def _is_time_stamp_type(data_type):
    """Tests if a type looks like time stamp.

    Args:
        data_type (Type): data type to test

    Returns:
        bool: True if type is a time stamp type, False otherwise
    """
    return data_type in (np.datetime64, datetime.datetime, datetime.date, datetime.time)


def _bar(x, y, axes, **kwargs):
    """Plots bar chart on axes but returns patches instead of bar container.

    Args:
        x (Any): x data
        y (Any): y data
        axes (Axes): plot axes
        **kwargs: keyword arguments passed to bar()

    Returns:
        list of Patch: patches
    """
    bar_container = axes.bar(x, y, **kwargs)
    return [Patch(color=bar_container.patches[0].get_facecolor(), label=kwargs["label"])]


def _group_bars(data_list):
    """Gives data with same x small offsets to prevent bar stacking.

    Args:
        data_list (List of XYData): squeezed data

    Returns:
        tuple: grouped data, bar width and x ticks
    """
    if len(data_list) < 2:
        return data_list, None, None
    ticks = np.arange(len(data_list[0].x))
    bar_width = 1 / (len(data_list) + 1)
    offset = bar_width * (len(data_list) - 1) / 2
    shifted_data = []
    for step, xy_data in enumerate(data_list):
        x = list(ticks + (step * bar_width - offset))
        shifted_data.append(replace(xy_data, x=x))
    return shifted_data, bar_width, (ticks, data_list[0].x)


def _clear_plot(plot_widget):
    """Removes plots and legend from plot widget.

    Args:
        plot_widget (PlotWidget): plot widget
    """
    plot_widget.canvas.setContent(b"")


def _limit_string_x_tick_labels(data, plot_widget):
    """Limits the number of x tick labels in case x-axis consists of strings.

    Matplotlib tries to plot every single x tick label if they are strings.
    This can become very slow if the labels are numerous.

    Args:
        data (list of XYData): plot data
        plot_widget (PlotWidget): plot widget
    """
    if data:
        x = data[0].x
        if len(x) > 10 and isinstance(x[0], str):
            plot_widget.canvas.axes.xaxis.set_major_locator(MaxNLocator(10))


def _table_display_row(row):
    """Calculates a human-readable row number.

    Args:
        row (int): model row

    Returns:
        int: row number
    """
    return row + 1


def plot_parameter_table_selection(model, model_indexes, table_header_sections, value_section_label, plot_widget=None):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        model_indexes (Iterable of QModelIndex): a list of QModelIndex objects for plotting
        table_header_sections (list of ParameterTableHeaderSection): table header labels
        value_section_label (str): value column's header label
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget

    Returns:
        PlotWidget: a PlotWidget object
    """
    pprint(inspect.currentframe().f_code.co_name)
    pprint(model_indexes, max_length=3)
    pprint(type(model).mro())
    header_columns = {model.headerData(column): column for column in range(model.columnCount())}
    data_column = header_columns[value_section_label]
    index_columns = [header_columns[section.label] for section in table_header_sections]
    model_indexes = [i for i in model_indexes if i.column() == data_column]
    if not model_indexes:
        raise PlottingError("Nothing to plot.")
    root_node = TreeNode(table_header_sections[0].label)
    header_data = model.headerData
    pprint(header_columns)
    pprint(table_header_sections)
    for model_index in sorted(model_indexes, key=methodcaller("row")):
        value = _get_parsed_value(model_index, _table_display_row)
        if value is None:
            continue
        pprint("value:")
        pprint(value)
        row = model_index.row()
        pprint((model_index.row(), model_index.column()))
        with add_row_to_exception(row, _table_display_row):
            leaf_content = _convert_to_leaf(value)
        node = root_node
        for i, index_column in enumerate(index_columns[:-1]):
            index = model.index(row, index_column).data()  # PARAMETER_VALUE_ROLE
            node = _set_default_node(node, index, header_data(index_columns[i + 1]))
        node.content[model.index(row, index_columns[-1]).data()] = leaf_content
    y_label_position = index_columns.index(header_columns["parameter_name"])
    data_list = list(turn_node_to_xy_data(root_node, y_label_position))
    return plot_data(data_list, plot_widget)


def plot_value_editor_table_selection(model, model_indexes, plot_widget=None):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        model_indexes (Iterable of QModelIndex): a list of QModelIndex objects for plotting
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget

    Returns:
        PlotWidget: a PlotWidget object
    """
    pprint(inspect.currentframe().f_code.co_name)
    pprint(model_indexes, max_length=3)
    pprint(type(model).mro())
    model_indexes = [i for i in model_indexes if model.is_leaf_value(i)]
    pprint(model_indexes, max_length=3)
    if not model_indexes:
        raise PlottingError("Nothing to plot.")
    header_columns = [model.headerData(column, Qt.Orientation.Horizontal) for column in range(model.columnCount())]
    root_node = TreeNode(header_columns[0])
    for model_index in sorted(model_indexes, key=methodcaller("row")):
        value = _get_parsed_value(model_index, _table_display_row)
        if value is None:
            continue
        row = model_index.row()
        with add_row_to_exception(row, _table_display_row):
            leaf_content = _convert_to_leaf(value)
        indexes = tuple(model.index(row, column).data(PARSED_ROLE) for column in range(model_index.column()))
        node = root_node
        for i, index in enumerate(indexes[:-1]):
            node = _set_default_node(node, index, header_columns[i + 1])
        node.content[indexes[-1]] = leaf_content
    data_list = list(turn_node_to_xy_data(root_node, None))
    return plot_data(data_list, plot_widget)


def plot_pivot_table_selection(model, model_indexes, plot_widget=None):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        model_indexes (Iterable of QModelIndex): a list of QModelIndex objects for plotting
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget

    Returns:
        PlotWidget: a PlotWidget object
    """
    pprint(inspect.currentframe().f_code.co_name)
    pprint(model_indexes, max_length=3)
    pprint(type(model).mro())
    if not model_indexes:
        raise PlottingError("Nothing to plot.")
    source_model = model.sourceModel()
    has_x_column = _has_x_column(model, source_model)
    root_node = TreeNode("database")
    display_row = functools.partial(_pivot_display_row, source_model=source_model)
    x_index_name = source_model.x_parameter_name() if has_x_column else None
    for model_index in sorted(map(model.mapToSource, model_indexes), key=methodcaller("row")):
        value = _get_parsed_value(model_index, display_row)
        if value is None:
            continue
        row = model_index.row()
        with add_row_to_exception(row, display_row):
            leaf_content = _convert_to_leaf(value)
        object_names, parameter_name, alternative_name, db_name = source_model.all_header_names(model_index)
        indexes = (db_name, parameter_name) + tuple(object_names) + (alternative_name,)
        index_names = _pivot_index_names(indexes)
        if has_x_column:
            x = source_model.x_value(model_index)
            if isinstance(x, IndexedValue):
                raise PlottingError(f"X column contains an unusable value at row {display_row(row)}")
            if x is not None:
                indexes = indexes + (x,)
                index_names = index_names + (x_index_name,)
        node = root_node
        for i, index in enumerate(indexes[:-1]):
            node = _set_default_node(node, index, index_names[i])
        node.content[indexes[-1]] = leaf_content
    data_list = list(turn_node_to_xy_data(root_node, 1))
    return plot_data(data_list, plot_widget)


def plot_db_mngr_items(items, db_maps, db_name_registry, plot_widget=None):
    """Returns a plot widget with plots of database manager parameter value items.

    Args:
        items (list of dict): parameter value items
        db_maps (list of DatabaseMapping): database mappings corresponding to items
        db_name_registry (NameRegistry): database display name registry
        plot_widget (PlotWidget, optional): widget to add plots to
    """
    pprint(inspect.currentframe().f_code.co_name)
    pprint(items, max_length=3)
    if not items:
        raise PlottingError("Nothing to plot.")
    if len(items) != len(db_maps):
        raise PlottingError("Database maps don't match parameter values.")
    root_node = TreeNode("database")
    for item, db_map in zip(items, db_maps):
        value = item["parsed_value"]
        db_name = db_name_registry.display_name(db_map.sa_url)
        if value is None:
            continue
        try:
            leaf_content = _convert_to_leaf(value)
        except PlottingError as error:
            raise PlottingError(f"Failed to plot value in {db_name}: {error}") from error
        parameter_name = item["parameter_definition_name"]
        entity_byname = item["entity_byname"]
        if not isinstance(entity_byname, tuple):
            entity_byname = (entity_byname,)
        alternative_name = item["alternative_name"]
        indexes = (db_name, parameter_name) + entity_byname + (alternative_name,)
        index_names = _pivot_index_names(indexes)
        node = root_node
        for i, index in enumerate(indexes[:-1]):
            node = _set_default_node(node, index, index_names[i])
        node.content[indexes[-1]] = leaf_content
    data_list = list(turn_node_to_xy_data(root_node, 1))
    return plot_data(data_list, plot_widget)


def _has_x_column(model, source_model):
    """Checks if pivot source model has x column.

    Args:
        model (PivotTableSortFilterProxy): proxy pivot model
        source_model (PivotTableModelBase): pivot table model

    Returns:
        bool: True if x pivot table has column, False otherwise
    """
    if source_model.plot_x_column is not None:
        dummy_index = source_model.index(0, source_model.plot_x_column)
        return model.mapFromSource(dummy_index).isValid()
    return False


def _set_default_node(root_node, key, label):
    """Gets node from the contents of root_node adding a new node if necessary.

    Args:
        root_node (TreeNode): root node
        key (Hashable): key to root_node contents
        label (str): label of possible new node

    Returns:
        TreeNode: node at given key
    """
    try:
        node = root_node.content[key]
    except KeyError:
        sub_node = TreeNode(label)
        root_node.content[key] = sub_node
        node = sub_node
    return node


def _get_parsed_value(model_index, display_row):
    """Gets parsed value from model.

    Args:
        model_index (QModelIndex): model index
        display_row (Callable): callable that returns a display row

    Returns:
        Any: parsed value

    Raises:
        PlottingError: raised if parsing of value failed
    """
    value = model_index.data(PARSED_ROLE)
    if isinstance(value, Exception):
        row = model_index.row()
        raise PlottingError(f"Failed to plot row {display_row(row)}: {value}")
    return value


def _pivot_index_names(indexes):
    """Gathers index names from pivot table.

    Args:
        indexes (tuple of str): "path" of indexes

    Returns:
        tuple of str: names corresponding to given indexes
    """
    excess_dimensions = len(indexes) - 4
    if excess_dimensions == 0:
        return "parameter_name", "object_name", "alternative_name"
    object_index_names = tuple(f"object_{dimension + 1}_name" for dimension in range(excess_dimensions + 1))
    return ("parameter_name",) + object_index_names + ("alternative_name",)


def _pivot_display_row(row, source_model):
    """Calculates display row for pivot table.

    Args:
        row (int): row in source table model
        source_model (QAbstractItemModel): pivot model

    Returns:
        int: human-readable row number
    """
    return row + 1 - source_model.headerRowCount()


def _convert_to_leaf(y):
    """Converts parameter value to leaf TreeElement.

    Args:
        y (Any): parameter value

    Returns:
        float or datetime or TreeNode: leaf element
    """
    try:
        if isinstance(y, IndexedValue):
            return convert_indexed_value_to_tree(y)
        return float(y)
    except ValueError as error:
        raise PlottingError(str(error)) from error
    except TypeError as error:
        if isinstance(y, DateTime):
            return y.value
        raise PlottingError(f"couldn't convert {type(y).__name__} to float.") from error


@contextmanager
def add_row_to_exception(row, display_row):
    """Adds row information to PlottingError if it is raised in the with block.

    Args:
        row (int): row
        display_row (Callable): function to convert row to display row
    """
    try:
        yield None
    except PlottingError as error:
        raise PlottingError(f"Failed to plot row {display_row(row)}: {error}") from error


def add_array_plot(plot_widget, value):
    """
    Adds an array plot to a plot widget.

    Args:
        plot_widget (PlotWidget): a plot widget to modify
        value (Array): the array to plot
    """
    plot_widget.canvas.axes.plot(value.indexes, value.values, **_LINE_PLOT_SETTINGS, **_BASE_SETTINGS)
    plot_widget.canvas.axes.set_xlabel(value.index_name)


def add_time_series_plot(plot_widget, value):
    """
    Adds a time series step plot to a plot widget.

    Args:
        plot_widget (PlotWidget): a plot widget to modify
        value (TimeSeries): the time series to plot
    """
    plot_widget.canvas.axes.step(
        value.indexes, value.values, **_make_time_series_settings(_LINE_PLOT_SETTINGS), **_BASE_SETTINGS
    )
    plot_widget.canvas.axes.set_xlabel(value.index_name)
    # matplotlib cannot have time stamps before 0001-01-01T00:00 on the x axis
    left, _ = plot_widget.canvas.axes.get_xlim()
    if left < 1.0:
        # 1.0 corresponds to 0001-01-01T00:00
        plot_widget.canvas.axes.set_xlim(left=1.0)
