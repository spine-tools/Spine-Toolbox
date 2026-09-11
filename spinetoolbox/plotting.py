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

import datetime
import functools
from importlib import resources
from itertools import starmap
from operator import attrgetter, methodcaller
import re
from typing import Iterable, Literal, NamedTuple, TypeVar, TYPE_CHECKING
from bokeh.core.properties import String
from bokeh.embed import file_html
from bokeh.layouts import column, gridplot, row
from bokeh.models import (
    Row,
    ColumnDataSource,
    CustomAction,
    CustomJS,
    DataTable,
    FactorRange,
    HoverTool,
    Legend,
    RangeTool,
    SaveTool,
    TableColumn,
)
from bokeh.palettes import TolRainbow
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.compiler import TypeScript
import numpy as np
import pandas as pd
from PySide6.QtCore import QSize
from spinedb_api.dataframes import to_dataframe
from .mvcmodels.shared import PARAMETER_VALUE_ROLE

if TYPE_CHECKING:
    from .widgets.plot_widget import PlotWidget


class PlottingError(Exception):
    """An exception signalling failure in plotting."""


PLOT_WIDTH = 800
PLOT_HEIGHT = 400

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
SEQ_PAT = re.compile(r"^([a-zA-Z])([0-9]+)$")
STR_TYPES = (
    object,
    pd.StringDtype(na_value=pd.NA),
    pd.StringDtype(na_value=np.nan),
)


def parse_time(df: pd.DataFrame) -> pd.DataFrame:
    """Parse 'time' or 'period' columns to integers for plotting."""
    for col, _type in df.dtypes.items():
        if _type in STR_TYPES and (groups := df[col].str.extract(SEQ_PAT)).notna().all(axis=None):
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

    # check if all column names match
    cols = np.array([df.columns.values for df in dfs])
    cols_neq = cols[:-1] != cols[1:]
    mismatched_cols = cols[:, cols_neq.any(axis=0)].T
    # NOTE: when column names mismatch, in the resulting concatenated
    # DF, any differing column from the 2nd DF onwards are appended
    # after the set of columns from the 1st DF.

    if not _raise:
        return (type_count == 1).all() and (mismatched_cols.size == 0)

    if (type_count != 1).any():
        # TODO: fallback, try dropping DFs to find a working set
        stringified = col_types.loc[type_count != 1].astype(str)
        # type_counts = stringified.agg(Counter, axis=1).apply(pd.Series).astype("Int64").fillna(0)
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


def plot_data(dfs: list[pd.DataFrame], plot_widget: "PlotWidget | None" = None, **selections):
    """
    Returns a plot widget with plots of the given data.

    Args:
        dfs (list[pd.DataFrame()]): data to plot
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget

    Returns:
        a PlotWidget object
    """
    if plot_widget is None:
        from .widgets.plot_widget import PlotWidget

        plot_widget = PlotWidget()

    dfs = [parse_time(df) for df in dfs]
    check_columns(dfs, _raise=True)

    # combine all dfs to determine type of plot we need
    df_combined = pd.concat(dfs, axis=0)
    sdf, common = squeeze_df(df_combined)

    if sdf.empty:
        return plot_widget

    nplots, seq_cols = get_variants(sdf)

    plot_title = "|".join(starmap(lambda k, v: f"{k}={v}", common.items()))
    match nplots.empty, seq_cols.empty, seq_cols.shape:
        case True, False, (seq_len, _):
            # seq-only line plot; array, ts, etc
            plot = plot_overlayed(sdf, nplots, plot_title, **selections)
        case False, False, (seq_len, _) if seq_len > 5:
            # categorical & seq, overlayed line plot: map w/ series (5+)
            plot = plot_overlayed(sdf, nplots, plot_title, **selections)
        case False, False, (seq_len, _):
            # categorical & seq, bar chart: map w/ short series
            plot = plot_barchart(sdf, plot_title, **selections)
        case False, True, _:
            # categorical-only, bar charts: map w/ single values
            plot = plot_barchart(sdf, plot_title, **selections)
        case _:
            raise ValueError(f"unhandled case:\n{nplots=}\n{seq_cols=}")

    size = plot_widget.size()
    # Resize to an absolute target, never relative to the current size, so
    # re-plotting (e.g. from the selector table) can't grow the widget without
    # bound and blow past QtWebEngine's max surface size (~16384px).
    match plot:
        case Row():
            target = QSize(1200 + 50, 600)
        case _:
            target = QSize(800 + 50, 600)
    plot_widget.set_target_size(QSize(max(size.width(), target.width()), max(size.height(), target.height())))
    plot_widget.resize(max(size.width(), target.width()), max(size.height(), target.height()))

    plot_widget.dataframe = sdf
    plot_widget.write(file_html(plot, INLINE, plot_title))

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


def get_dim_selector(nplots: pd.DataFrame):
    """Create a Bokeh table with row selection and column reordering.

    Parameters
    ----------
    nplots: pandas.DataFrame
        Dataframe with number of plots metadata; output by
        `get_variants(squeezed_df)`

    Returns
    -------
    bokeh.layouts.column
        A layout containing a widget to select column-order, and a
        DataTable and a

    """

    df = nplots.drop(nplots.columns[-1:], axis=1).drop_duplicates()
    columns = list(df.columns)
    source = ColumnDataSource(data=df)
    table_columns = [TableColumn(field=col, title=str(col)) for col in columns]
    data_table = DataTable(
        source=source,
        columns=table_columns,
        sizing_mode="scale_width",
        min_height=PLOT_HEIGHT,
        selectable=True,
    )

    # NOTE: to add more selection widgets, pass to CustomJS via `args`.
    # You'll also have to adapt the JS code, and the webchannel bridge.
    cb = CustomJS(args={"source": source}, code=get_resource("selector_cb.js"))
    source.selected.js_on_change("indices", cb)

    return column(data_table, sizing_mode="scale_width")


def get_window_selector(
    fig: figure,
    x_label: str,
    y_label: str,
    x_axis_type: Literal["linear", "datetime"],
    sources: Iterable[ColumnDataSource],
) -> figure:
    longest: ColumnDataSource = functools.reduce(lambda i, j: max(i, j, key=lambda d: len(d.data["index"])), sources)
    # TODO: get width from `fig`
    select = figure(
        title="Select time range",
        y_axis_type=None,
        height=100,
        width=PLOT_WIDTH,
        tools="",
        toolbar_location=None,
        y_range=(0, 100),
        x_axis_type=x_axis_type,
    )
    range_tool = RangeTool(x_range=fig.x_range, start_gesture="pan")
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2
    select.line(x_label, y_label, source=longest)
    select.ygrid.grid_line_color = None
    select.add_tools(range_tool)
    return select


def get_resource(name: str) -> str:
    _resources = resources.files("spinetoolbox.plotting_resources")
    path, *_ = (f for f in _resources.iterdir() if f.name == name)
    return path.read_text()


class NamedCustomAction(CustomAction):
    """A CustomAction tool with a configurable label for the context
    menu.

    The `tool_label` property allows you to customize the text that appears
    in the right-click context menu, instead of the default "Custom Action".

    """

    __implementation__ = TypeScript(get_resource("named_custom_action.ts"))

    tool_label = String(
        default="Custom Action",
        help="Label shown in the right-click context menu for this tool",
    )


def add_download_buttons(fig, legend=None):
    save_tool: SaveTool = fig.select_one(SaveTool)
    save_tool.filename = "plot.jpg"
    save_tool.description = "Save as image"
    # Opacity is currently hard-coded to match the other icons.  TODO:
    # Find a way to match icon colors automatically; same for below
    save_tool.icon = "data:image/svg+xml;utf8," + get_resource("icon-image.svg")

    # Download data as file via QWebChannel bridge (CSV is generated on demand in Python).
    # The callback inspects legend item visibility so that only data series currently
    # shown in the plot (not toggled off via legend click) are included in the export.
    # If no legend is provided (e.g. bar chart), we assume all data is to be downloaded.
    download_action: CustomAction = NamedCustomAction(
        icon="data:image/svg+xml;utf8," + get_resource("icon-csv.svg"),
        tool_label="Export data",
        description="Export data as CSV",  # tooltip on hover
        callback=CustomJS(args={"legend": legend} if legend else {}, code=get_resource("download_action_cb.js")),
    )

    # Add the data download button _under_ the graph save button.
    tools = fig.toolbar.tools
    tools.insert(tools.index(save_tool) + 1, download_action)


def _get_default_selections(sdf: pd.DataFrame) -> dict:
    # NOTE: ignore type hints b/c of 2 upstream bugs: 1) itertuples
    # type hints Iterable, but that doesn't seem to match with
    # SupportsNext (protocol for __next__), and 2) the items are typed
    # as tuple, not NamedTuple
    row: NamedTuple = next(sdf.itertuples(index=False))  # type: ignore
    ncols = len(row)
    return {col: val for i, (col, val) in enumerate(row._asdict().items()) if i < (ncols - 3)}


def plot_overlayed(sdf: pd.DataFrame, nplots: pd.DataFrame, title: str, *, max_points: int = 1_000, **selections):
    match sdf.shape:
        case _, 2:
            # FIXME: support single column data
            sources = {"value": ColumnDataSource(data=sdf)}
        case _, 3:
            col = sdf.columns[0]
            grouped = sdf.groupby(col)
            sources = {
                f"{col}=={v!r}": ColumnDataSource(data=sdf.loc[idx, sdf.columns[1:]])
                for v, idx in grouped.groups.items()
            }
        case _, ncols if ncols > 3:
            selections = selections if len(selections) else _get_default_selections(sdf)
            _cols = list(selections)
            if (factors := set(sdf.columns[:-3])) != (query_cols := set(_cols)):
                # FIXME: warn & fallback, instead of raising an error
                raise PlottingError(f"{query_cols=} != {factors=}: query doesn't match data")

            grouped = sdf.groupby(_cols)
            if ncols == 4 and not isinstance(next(iter(grouped.groups)), tuple):
                # FIXME: Pandas groupby creates scalar group keys when grouping over a single column
                ks = list(grouped.groups)
                for k in ks:
                    v = grouped.groups.pop(k)
                    grouped.groups.update([((k,), v)])

            selector = get_dim_selector(nplots)

            title = "|".join(
                [
                    title,
                    *(f"{k}={v}" for k, v in selections.items()),
                ]
            )
            idx = tuple(selections.values())
            sdf = sdf.loc[grouped.groups[idx]].drop(_cols, axis=1)
            nplots = nplots.drop(_cols, axis=1).drop_duplicates()
            plot = plot_overlayed(sdf, nplots, title, max_points=max_points)
            return row(plot, selector, sizing_mode="scale_width")
        case _, ncols:
            raise PlottingError(f"{ncols=}: too few columns to plot")

    x_label, y_label = sdf.columns[-2:]
    x_axis_type = "datetime" if sdf[x_label].dtype.kind == "M" else "linear"
    x_range, y_range = get_ranges(sdf, nplots.columns.to_list(), max_points)
    fig = figure(
        title=title,
        width=PLOT_WIDTH,
        height=PLOT_HEIGHT,
        x_axis_label=x_label,
        y_axis_label=y_label,
        x_range=x_range,
        y_range=y_range,
        x_axis_type=x_axis_type,
        tools="pan,box_zoom,wheel_zoom,save,reset",
    )

    palette = Palette(len(nplots))

    def _draw(cds: ColumnDataSource, idx: int):
        line = fig.line(x_label, y_label, source=cds, color=palette[idx])
        point = fig.scatter(x_label, y_label, source=cds, color=palette[idx], size=3)
        return [line, point]

    legend_items = [(key, _draw(cds, idx)) for idx, (key, cds) in enumerate(sources.items())]
    legend = Legend(items=legend_items)
    fig.add_layout(legend, place="right")
    fig.legend.click_policy = "hide"

    add_download_buttons(fig, legend=legend)

    select = get_window_selector(fig, x_label, y_label, x_axis_type, sources.values())
    return column(fig, select, sizing_mode="stretch_both")


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
        case shape:
            raise RuntimeError(f"plot_barchart: unsupported {shape=}")

    fig.vbar(x=str(x_label), top=str(y_label), source=source)
    fig.y_range.start = -10
    add_download_buttons(fig)
    return fig


def plot_parameter_table_selection(model, model_indexes, value_section_label, plot_widget=None):
    """
    Returns a plot widget with plots of the selected indexes.

    Args:
        model (QAbstractTableModel): a model
        model_indexes (Iterable of QModelIndex): a list of QModelIndex objects for plotting
        value_section_label (str): value column's header label
        plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget

    Returns:
        PlotWidget: a PlotWidget object
    """
    header_columns = {model.headerData(column): column for column in range(model.columnCount())}
    data_column = header_columns[value_section_label]
    model_indexes = [i for i in model_indexes if i.column() == data_column]
    if not model_indexes:
        raise PlottingError("Nothing to plot.")
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
    model_indexes = [i for i in model_indexes if model.is_leaf_value(i)]
    if not model_indexes:
        raise PlottingError("Nothing to plot.")
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
    if not model_indexes:
        raise PlottingError("Nothing to plot.")
    dfs = [
        to_dataframe(model.index(i.row(), i.column()).data(PARAMETER_VALUE_ROLE))
        for i in sorted(model_indexes, key=methodcaller("row"))
    ]
    return plot_data(dfs, plot_widget)


def plot_db_mngr_items(items, _db_maps, _db_name_registry, plot_widget=None):
    """Returns a plot widget with plots of database manager parameter value items.

    Args:
        items (list of dict): parameter value items
        plot_widget (PlotWidget, optional): widget to add plots to
    """
    if not items:
        raise PlottingError("Nothing to plot.")
    dfs = [to_dataframe(item) for item in items if item["value"] is not None]
    if not dfs:
        raise PlottingError("Nothing to plot.")
    return plot_data(dfs, plot_widget)
