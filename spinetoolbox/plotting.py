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
from itertools import starmap
from bokeh.embed import file_html
from bokeh.layouts import gridplot, column
from bokeh.resources import INLINE
from bokeh.models import ColumnDataSource, FactorRange, HoverTool, Legend, RangeTool, SaveTool, CustomAction, CustomJS
from bokeh.palettes import TolRainbow
from bokeh.plotting import figure
from contextlib import contextmanager
from dataclasses import dataclass, field
import datetime
from enum import auto, Enum, unique
import functools
from operator import attrgetter, methodcaller
import re
import pandas as pd
from typing import Dict, Iterable, List, Literal, Optional, TypeVar, Union
import numpy as np
from PySide6.QtCore import QSize, Qt
from spinedb_api import DateTime, IndexedValue
from spinedb_api.dataframes import to_dataframe
from .mvcmodels.shared import PARAMETER_VALUE_ROLE, PARSED_ROLE
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
_LINE_PLOT_SETTINGS = {"linestyle": "solid"}


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


# NOTE: POD types like int, float, & str covers extension
# ExtensionDtypes like Int64Dtype, Float64Dtype, or StringDtype,
# since: Int64Dtype().type == int
compat_types = {
    int: "integer",
    np.int32: "integer",
    np.int64: "integer",
    float: "number",
    np.float32: "number",
    np.float64: "number",
    datetime.datetime: "timestamp",
    datetime.date: "timestamp",
    datetime.time: "timestamp",
    np.datetime64: "timestamp",
    pd.Timestamp: "timestamp",
    str: "string",
    object: "string",
    np.object_: "string",
}

# Regex pattern to indentify numerical sequences encoded as string
SEQ_PAT = re.compile(r"^(t|p)([0-9]+)$")


def parse_time(df: pd.DataFrame) -> pd.DataFrame:
    """Parse 'time' or 'period' columns to integers for plotting."""
    for col, _type in df.dtypes.items():
        if _type in (object, pd.StringDtype()) and (groups := df[col].str.extract(SEQ_PAT)).notna().all(axis=None):
            df[col] = groups[1].astype(int)
    return df


def squeeze_df(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove dataframe columns that have a single value, and return name, value as dict."""
    # last 2 columns are required for all plots, and may have duplicates
    counts = df.iloc[:, :-1].nunique(axis=0, dropna=True)

    if counts.empty:
        return df, {}

    common_idxs = {c: df[c].iloc[0] for c, v in counts.items() if v == 1}
    cols = [c for c in df.columns if c not in common_idxs]
    return df.loc[:, cols], common_idxs


def check_columns(dfs: Iterable[pd.DataFrame], _raise: bool = False) -> bool:
    """Check if list of dataframes have matching x-label and compatible column types.

    If `_raise` is `True`, `ValueError` is raised on failure.

    """

    # check if column types match
    def _get_type(i) -> str:
        if isinstance(i, pd.CategoricalDtype):
            return compat_types[i.categories.dtype.type]
        else:
            return compat_types[i.type]

    col_types = pd.concat(map(attrgetter("dtypes"), dfs), axis=1).map(_get_type, na_action="ignore")
    type_count = col_types.nunique(axis=1, dropna=True)

    # TODO: fallback, try dropping DFs to find a working set
    stringified = col_types.loc[type_count != 1].astype(str)
    # type_counts = stringified.agg(Counter, axis=1).apply(pd.Series).astype("Int64").fillna(0)

    # check if all column names match
    cols = np.array([df.columns.values for df in dfs])
    cols_neq = cols[:-1] != cols[1:]
    mismatched_cols = cols[:, cols_neq.any(axis=0)].T
    # NOTE: when column names mismatch, in the resulting concatenated
    # DF, any differing column from the 2nd DF onwards are appended
    # after the set of columns from the 1st DF.

    if not _raise:
        return (type_count == 1).all() and bool(mismatched_cols.any())

    if (type_count != 1).any():
        msgs = stringified.apply(lambda r: f"{r.name}: " + ", ".join([i for i in r if i != "nan"]), axis=1)
        raise PlottingError("\n".join(["incompatible column types:", *msgs]))
    elif mismatched_cols.any():
        msgs = [", ".join(col) for col in mismatched_cols]
        raise PlottingError("\n".join(["mismatched column names:", *msgs]))
    return True


def check_shapes(dfs: Iterable[pd.DataFrame], _raise: bool = False) -> bool:
    # check if shapes match
    shapes = [d.shape for d in dfs]
    if functools.reduce(lambda i, j: i if i == j else False, shapes):
        return True
    elif _raise:
        raise PlottingError(f"incompatible shapes: {shapes}")
    else:
        return False


seq_t = TypeVar("seq_t", int, pd.Timestamp, datetime.datetime)


def is_sequence(col_dtype: np.dtype) -> bool:
    # FIXME: for some mad reason `True` for string `object` type!
    # if col_dtype.kind == "O":
    #     return col_dtype == datetime.datetime

    # sequence, timestamp; to include raw timestamp, add "f" below
    return col_dtype.kind in ("i", "M")


def get_variants(sdf: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Determine all possible plots that are possible.

    The different plot variants are determined by looking at the
    intersection of the columns present in the squeezed dataframe and
    the complete list of index columns.  This comparison identifies
    the number of index columns that have more than one unique values.

    TODO: do more fine grained plot types based on data types

    """
    # last column has values (y axis)
    idx_cols = sdf.columns[:-1]
    idx_cols_df = sdf.loc[:, idx_cols].drop_duplicates()
    # TODO: check for implicit sequence: no explicit sequential
    # x-axis; in this case len(sdf) != len(idx_cols_df)
    seq_col_indexer = idx_cols_df.dtypes.apply(is_sequence)
    if seq_col_indexer.sum() > 1:
        raise PlottingError(f"multiple sequence columns (x axis): {', '.join(seq_col_indexer.index)}")
    nplots = idx_cols_df.loc[:, idx_cols_df.columns[~seq_col_indexer]].drop_duplicates().reset_index(drop=True)
    # NOTE: seq_cols will be as long as the longest seq for any non-seq index value
    seq_cols = idx_cols_df.loc[:, seq_col_indexer].drop_duplicates().reset_index(drop=True)
    return nplots, seq_cols


def plot_data(dfs, plot_widget: PlotWidget | None = None):
    """
    Returns a plot widget with plots of the given data.

    Args:
        data_list (list of XYData): data to plot
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget
        plot_type (PlotType, optional): plot type

    Returns:
        a PlotWidget object
    """
    if plot_widget is None:
        plot_widget = PlotWidget()

    dfs = [parse_time(df) for df in dfs]
    check_columns(dfs, _raise=True)

    pprint(dfs, max_length=5)
    # combine all dfs to determine type of plot we need
    df_combined = pd.concat(dfs, axis=0)
    sdf, common = squeeze_df(df_combined)

    if sdf.empty:
        return plot_widget

    nplots, seq_cols = get_variants(sdf)

    plot_title = "|".join(starmap(lambda k, v: f"{k}={v}", common.items()))

    match nplots.empty, nplots.shape, seq_cols.empty, seq_cols.shape:
        case True, _, False, (seq_len, _):
            plot = plot_overlayed(sdf, nplots, plot_title)
        case False, (_, ncols), False, (seq_len, _) if seq_len > 5:
            plot = plot_overlayed(sdf, nplots, plot_title)
        case False, (_, ncols), False, (seq_len, _):
            plot = plot_barchart(sdf, plot_title)
        case False, (_, ncols), True, _:
            plot = plot_barchart(sdf, plot_title)
        case _:
            raise ValueError(f"unhandled case:\n{nplots=}\n{seq_cols=}")

    plot_widget.set_download_data(sdf)
    plot_widget.write(file_html(plot, INLINE, plot_title))
    if plot.width and plot.height:
        plot_widget.resize(QSize(plot.width + 50, plot.height + 50))

    return plot_widget


class Palette:
    """A palette that cycles through colours."""

    def __init__(self, nplots: int):
        if nplots < 3:
            palette: tuple[str, ...] = TolRainbow[3]
        elif nplots <= 23:
            palette: tuple[str, ...] = TolRainbow[nplots]
        else:
            palette: tuple[str, ...] = TolRainbow[23]
        self._palette = palette
        self._len = len(palette)

    def __getitem__(self, num: int) -> str:
        return self._palette[num % self._len]


def pad_num(num: float | int, frac: float = 0.05) -> float:
    return num * ((1 + frac) if num > 0 else (1 - frac))


def get_ranges(
    sdf: pd.DataFrame, idxcols: list, max_points: int = 1_000
) -> tuple[tuple[seq_t, seq_t], tuple[float, float]]:
    """Calculate a common range that includes all ranges.

    Parameters
    ----------
    sdf: pd.DataFrame
       DataFrame with the data.

    idxcols: list[str]
        List of column names that are treated as categorical indices.

    max_points: int
        Maximum number of points visible at a time on the default plot.

    """
    x_label: str
    col: str
    x_label, col = sdf.columns[-2:]
    agg_fns = {x_label: ["min", "max", "count"], col: ["min", "max"]}
    if len(idxcols) > 0:
        range_df = sdf.groupby(idxcols).agg(agg_fns)
    else:
        range_df = pd.DataFrame([sdf.agg(agg_fns).unstack(level=0)])
    # tolerance = 0.01% of min
    empty = np.less(np.abs((range_df[col]["max"] - range_df[col]["min"])), 1e-4 * range_df[col]["min"])

    def _y_range() -> tuple[float, float]:
        y_ranges = range_df[~empty][col]
        lo = pad_num(np.min(y_ranges["min"]), -0.05)
        if (_hi := np.max(y_ranges["max"])) <= 1:
            hi = 1
        else:
            hi = pad_num(_hi, 0.05) + 1
        return np.floor_divide(lo, 1), np.floor_divide(hi, 1)

    def _x_range() -> tuple[seq_t, seq_t]:
        x_ranges = range_df[~empty][x_label]
        lo = np.min(x_ranges["min"])
        hi = np.max(x_ranges["max"])
        if (points := np.max(x_ranges["count"])) > max_points:
            return lo, lo + (hi - lo) * (max_points / points)
        else:
            return lo, hi

    return _x_range(), _y_range()


def get_window_selector(
    fig: figure, x_label: str, y_label: str, x_axis_type: Literal["linear"] | Literal["datetime"], cds: ColumnDataSource
) -> figure:
    # TODO: get width from `fig`
    select = figure(
        title="Select time range",
        y_axis_type=None,
        height=100,
        width=800,
        tools="",
        toolbar_location=None,
        y_range=(0, 100),
        x_axis_type=x_axis_type,
    )
    range_tool = RangeTool(x_range=fig.x_range, start_gesture="pan")
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.line(x_label, y_label, source=cds)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    return select


def plot_overlayed(sdf: pd.DataFrame, nplots: pd.DataFrame, title: str, *, max_points: int = 1_000):
    match sdf.shape:
        case _, 2:
            sources = {"value": ColumnDataSource(data=sdf)}
        case _, 3:
            col = sdf.columns[0]
            grouped = sdf.groupby(col)
            sources = {
                f"{col}={v}": ColumnDataSource(data=sdf.loc[idx, sdf.columns[1:]]) for v, idx in grouped.groups.items()
            }
        case _, ncols if ncols > 3:
            # FIXME: probably doesn't work for ncols == 4
            grouped = sdf.groupby(sdf.columns[:-3].to_list())
            figs = [
                plot_overlayed(
                    sdf.loc[idx, sdf.columns[-3:]],
                    nplots,
                    "|".join([title, *(f"{k}={v}" for k, v in zip(sdf.columns[:-3], vals))]),
                    max_points=max_points,
                )
                for vals, idx in grouped.groups.items()
            ]
            return gridplot(figs, ncols=2)
        case _:
            raise RuntimeError()

    x_label, y_label = sdf.columns[-2:]
    x_axis_type = "datetime" if sdf[x_label].dtype.kind == "M" else "linear"
    x_range, y_range = get_ranges(sdf, nplots.columns.to_list(), max_points)
    fig = figure(
        title=title,
        width=800,
        height=400,
        x_axis_label=x_label,
        y_axis_label=y_label,
        x_range=x_range,
        y_range=y_range,
        x_axis_type=x_axis_type,
        tools="pan,box_zoom,wheel_zoom,save,reset",
    )
    save_tool: SaveTool = fig.select_one(SaveTool)
    # TODO Generate file name based on data, instead of hard-coding
    save_tool.filename = "plot.jpg"  # default filename, suppress file name dialog from bokeh

    palette = Palette(len(nplots))

    def _draw(cds: ColumnDataSource, idx: int):
        line = fig.line(x_label, y_label, source=cds, color=palette[idx])
        point = fig.scatter(x_label, y_label, source=cds, color=palette[idx], size=3)
        return [line, point]

    legend_items = [(key, _draw(cds, idx)) for idx, (key, cds) in enumerate(sources.items())]
    legend = Legend(items=legend_items)
    fig.add_layout(legend, "right")
    fig.legend.click_policy = "hide"

    # Download data as file via QWebChannel bridge (CSV is generated on demand in Python).
    # The callback inspects legend item visibility so that only data series currently
    # shown in the plot (not toggled off via legend click) are included in the export.
    download_callback: CustomJS = CustomJS(args={"legend": legend}, code="""
    var visibleKeys = [];
    for (var i = 0; i < legend.items.length; i++) {
        var item = legend.items[i];
        if (item.renderers[0].visible) {
            visibleKeys.push(item.label.value);
        }
    }
    if (window.bridge) {
        window.bridge.downloadFilteredCsv(JSON.stringify(visibleKeys));
    } else {
        console.error("QWebChannel bridge not available");
    }
""")
    download_action: CustomAction = CustomAction(
        # Opacity is currently hard-coded to match the other icons
        # TODO Find a way to match icon colors automatically.
        icon="""data:image/svg+xml;utf8,
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" opacity="0.4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="m 4,17 v 2 a 2,2 0 0 0 2,2 h 12 a 2,2 0 0 0 2,-2 v -2" />
        <polyline points="7 11 12 16 17 11" transform="translate(0,1.1807315)" />
        <line x1="12" y1="5.1807313" x2="12" y2="17.180731" />
        <path d="M 7.9021726,8.7586207 V 4" id="path4" />
        <path d="M 7.9021726,4 6.1435519,5.7586207" />
        <ellipse cx="16.87956" cy="6.3793101" rx="1.715098" ry="2.3953953" />
        </svg>
        """,
        callback=download_callback,
        description="Download Data as CSV"       # tooltip on hover
    )

    # Add the data download button _under_ the graph save button.
    tools = fig.toolbar.tools
    save_tool = next(t for t in tools if isinstance(t, SaveTool))
    save_index = tools.index(save_tool)
    tools.insert(save_index+1, download_action)

    longest: ColumnDataSource = functools.reduce(
        lambda i, j: max(i, j, key=lambda d: len(d.data["index"])), sources.values()
    )
    select = get_window_selector(fig, x_label, y_label, x_axis_type, longest)
    return column(fig, select)


def plot_barchart(sdf: pd.DataFrame, title: str):
    # NOTE: {x,y}_label is also used to refer to the data in the
    # source (df, grouped df, cds)
    y_label = sdf.columns[-1]
    tooltips = [(col.capitalize(), f"@{col}") for col in sdf.columns]
    fig_opts = {
        "y_axis_label": y_label,
        "title": title,
        "height": 600,
        "width": 800,
        "tooltips": tooltips,
    }
    match sdf.shape:
        case _, 2:
            x_label = sdf.columns[0]
            source = sdf
            fig = figure(x_axis_label=x_label, x_range=sdf.iloc[:, 0].to_list(), **fig_opts)
            # major_label_orientation: "vertical" or angle in radians
            fig.xaxis.major_label_orientation = np.pi / 3
        case _, 3:
            x_label = "_".join(sdf.columns[:-1])
            _data = {
                x_label: [tuple(map(str, row)) for row in sdf.iloc[:, :-1].values],
                str(y_label): sdf[y_label].to_list(),
            }
            source = ColumnDataSource(data=_data)
            x_range = FactorRange(*sorted(_data[x_label], key=lambda i: i[0]))
            fig = figure(x_range=x_range, **fig_opts)
            fig.xaxis.group_label_orientation = np.pi / 2
        case _, ncols if ncols > 3:
            # FIXME: probably doesn't work for ncols == 4
            grouped = sdf.groupby(sdf.columns[:-3].to_list())
            figs = [
                plot_barchart(
                    sdf.loc[idx, sdf.columns[-3:]],
                    "|".join([title, *(f"{k}={v}" for k, v in zip(sdf.columns[:-3], vals))]),
                )
                for vals, idx in grouped.groups.items()
            ]
            return gridplot(figs, ncols=2)
        case _:
            raise RuntimeError()

    fig.vbar(x=str(x_label), top=str(y_label), source=source)
    fig.y_range.start = -10
    return fig


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
    pprint(header_columns)
    pprint(table_header_sections)
    dfs = [
        to_dataframe(model.index(i.row(), i.column()).data(PARAMETER_VALUE_ROLE))
        for i in sorted(model_indexes, key=methodcaller("row"))
    ]
    return plot_data(dfs, plot_widget)


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
    dfs = [
        to_dataframe(model.index(i.row(), i.column()).data(PARAMETER_VALUE_ROLE))
        for i in sorted(model_indexes, key=methodcaller("row"))
    ]
    return plot_data(dfs, plot_widget)


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
    dfs = [
        to_dataframe(model.index(i.row(), i.column()).data(PARAMETER_VALUE_ROLE))
        for i in sorted(model_indexes, key=methodcaller("row"))
    ]
    return plot_data(dfs, plot_widget)


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
    dfs = [
        to_dataframe(model.index(i.row(), i.column()).data(PARAMETER_VALUE_ROLE))
        for i in sorted(model_indexes, key=methodcaller("row"))
    ]
    return plot_data(dfs, plot_widget)


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
