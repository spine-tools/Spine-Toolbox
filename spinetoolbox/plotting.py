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
from bokeh.models import ColumnDataSource, HoverTool, Legend, RangeTool
from bokeh.palettes import TolRainbow
from bokeh.plotting import figure
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
import datetime
from enum import auto, Enum, unique
import functools
from operator import attrgetter, methodcaller
import re
import pandas as pd
from typing import Dict, Iterable, List, Optional, TypeAlias, TypeVar, Union, cast
import numpy as np
from PySide6.QtCore import QSize, Qt, QUrl
from spinedb_api import DateTime, IndexedValue
from spinedb_api.dataframes import to_dataframe
from spinedb_api.parameter_value import NUMPY_DATETIME64_UNIT
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
    counts = df.nunique(axis=0, dropna=True)
    common_idxs = {c: df[c].iloc[0] for c, v in counts.items() if v == 1}
    cols = [c for c in df.columns if c not in common_idxs]
    return df.loc[:, cols], common_idxs


def check_dimensions(dfs: Iterable[pd.DataFrame], _raise: bool = False) -> bool:
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


def is_sequence(col_dtype: np.dtype) -> bool:
    if col_dtype.kind in ("i", "f", "M"):  # sequence, raw timestamp, timestamp
        return True

    # FIXME: for some mad reason `True` for string `object` type!
    # if col_dtype.kind == "O":
    #     return col_dtype == datetime.datetime

    return False


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
    nplots = idx_cols_df.loc[:, idx_cols_df.columns[~seq_col_indexer]].drop_duplicates().reset_index(drop=True)
    # NOTE: seq_cols will be as long as the longest seq for any non-seq index value
    seq_cols = idx_cols_df.loc[:, seq_col_indexer].drop_duplicates().reset_index(drop=True)
    return nplots, seq_cols


def plot_data(dfs, plot_widget=None, plot_type=None):
    """
    Returns a plot widget with plots of the given data.

    Args:
        data_list (list of XYData): data to plot
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget
        plot_type (PlotType, optional): plot type

    Returns:
        a PlotWidget object
    """
    dfs = [parse_time(df) for df in dfs]
    check_dimensions(dfs, _raise=True)

    pprint(dfs, max_length=5)
    # combine all dfs to determine type of plot we need
    df_combined = pd.concat(dfs, axis=0)
    sdf, common = squeeze_df(df_combined)

    if sdf.empty:
        return plot_widget

    nplots, seq_cols = get_variants(sdf)

    # debug
    print("sdf")
    sdf.info()
    pprint(sdf, max_length=3)
    print("nplots")
    pprint(nplots)
    print("common_indexes")
    pprint(common)

    if plot_widget is None:
        plot_widget = PlotWidget()
    else:
        # FIXME: redo for bokeh
        plot_widget.canvas.setContent(b"")

    plot_title = "|".join(starmap(lambda k, v: f"{k}={v}", common.items()))

    if seq_cols.empty:
        plot = plot_barchart(sdf, nplots, plot_title)
    else:
        # plot = plot_faceted(sdf, nplots, plot_title)
        plot = plot_overlayed(sdf, nplots, plot_title)

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


def get_yrange(sdf: pd.DataFrame, idxcols: list) -> tuple:
    """Calculate a common range that includes all ranges.

    `sdf` is a DataFrame with the data.

    `idxcols` is a list of column names that are treated as categorical indices.

    """
    col: str = sdf.columns[-1]
    ranges = sdf.groupby(idxcols).agg({col: ["min", "max"]})[col]
    # tolerance = 0.01% of min
    empty = (ranges["max"] - ranges["min"]).abs().lt(1e-4 * ranges["min"])
    ranges = ranges[~empty]

    lo = pad_num(ranges["min"].min(), -0.05)
    if (_hi := ranges["max"].max()) < 1:
        hi = 1
    else:
        hi = pad_num(_hi, 0.05) + 1

    return np.floor_divide(lo, 1), np.floor_divide(hi, 1)


def fmt_query(names: pd.Series, *, sep: str = "&&") -> str:
    return sep.join([f"{k}=={v!r}" for k, v in names.items()])


def plot_overlayed(sdf: pd.DataFrame, nplots: pd.DataFrame, title: str, *, max_points: int = 10_000):
    x_range = (0, max_points // len(nplots))
    y_range = get_yrange(sdf, nplots.columns.to_list())

    print("ranges:")
    print(x_range)
    print(y_range)

    # TODO:
    # - x_axis_type="datetime"/...
    # - flexible plot dimensions
    # - tooltips
    seq_cols = sdf.columns.difference(nplots.columns)
    if len(seq_cols) > 2:
        print(f"extra sequence columns: {seq_cols.tolist()}")
    x_label, y_label = sdf.columns[-2:]

    fig_options = {
        "title": title,
        "width": 800,
        "height": 400,
        "x_axis_label": x_label,
        "y_axis_label": y_label,
        "x_range": x_range,
        "y_range": y_range,
        "x_axis_type": "datetime" if sdf[x_label].dtype.kind == "M" else "linear",
    }
    fig = figure(**fig_options)

    palette = Palette(len(nplots))
    sources = []
    legend_items = {}
    for idx, (_, row) in enumerate(nplots.iterrows()):
        _df = sdf.query(fmt_query(row)).drop(row.index, axis=1)
        cds = ColumnDataSource(data=_df)
        line = fig.line(x_label, y_label, source=cds, color=palette[idx])
        point = fig.scatter(x_label, y_label, source=cds, color=palette[idx], size=3)
        sources.append(cds)
        # TODO: derive key robustly
        legend_items[fmt_query(row, sep="\n")] = [line, point]

    legend = Legend(items=list(legend_items.items()))
    fig.add_layout(legend, "right")
    fig.legend.click_policy = "hide"

    longest: ColumnDataSource = functools.reduce(lambda i, j: max(i, j, key=lambda d: len(d.data["index"])), sources)
    select = get_window_selector(fig, x_label, y_label, longest)
    return column(fig, select)


def get_window_selector(fig: figure, x_label: str, y_label: str, cds: ColumnDataSource) -> figure:
    # TODO: get width from `fig`
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
    select.line(x_label, y_label, source=cds)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    return select


def plot_faceted(sdf: pd.DataFrame, nplots: pd.DataFrame, title: str):
    palette = Palette(len(nplots))
    # TODO:
    # - resolve x_label & y_label if they don't match
    # - x_axis_type="datetime"/...
    # - flexible plot dimensions
    # - tooltips
    x_label, y_label = sdf.columns[-2:]
    tooltips = [(col.capitalize(), f"@{col}") for col in sdf.columns]

    figs, sources = [], []
    for idx, (_, row) in enumerate(nplots.iterrows()):
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

    select = get_window_selector(figs[0], x_label, y_label, sources[0])
    # grid_size = math.ceil(math.sqrt(nplots))
    # plots = gridplot([figs[i : i + grid_size] for i in range(0, nplots, grid_size)])
    plots = gridplot([figs[i : i + 2] for i in range(0, len(nplots), 2)])
    return column(select, plots)


def plot_barchart(sdf: pd.DataFrame, nplots: pd.DataFrame, title: str):
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
    # major_label_orientation: "vertical" or angle in radians
    fig.xaxis.major_label_orientation = np.pi / 3
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
