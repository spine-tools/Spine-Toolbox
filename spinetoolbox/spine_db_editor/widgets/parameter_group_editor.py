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
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QAction
from spinedb_api import DatabaseMapping
from spinetoolbox.spine_db_editor.empty_table_size_hint_provider import EmptyTableSizeHintProvider
from spinetoolbox.spine_db_editor.mvcmodels.empty_models import EmptyParameterGroupModel
from spinetoolbox.spine_db_editor.mvcmodels.parameter_group_model import ParameterGroupModel
from spinetoolbox.spine_db_editor.stacked_table_seam import StackedTableSeam
from spinetoolbox.spine_db_editor.widgets.custom_qtableview import EmptyParameterGroupTableView, ParameterGroupTableView
from spinetoolbox.spine_db_editor.widgets.custom_qwidgets import ResizeSignallingWidget
from spinetoolbox.spine_db_manager import SpineDBManager


class ParameterGroupEditor:
    def __init__(
        self,
        parameter_group_table_view: ParameterGroupTableView,
        empty_parameter_group_table_view: EmptyParameterGroupTableView,
        contents_widget: ResizeSignallingWidget,
        copy_action: QAction,
        paste_action: QAction,
        db_mngr: SpineDBManager,
        row_height: int,
        parent: QObject | None,
    ):
        self._db_mngr = db_mngr
        self._table_view = parameter_group_table_view
        self._table_view.verticalHeader().setDefaultSectionSize(row_height)
        self._table_view.set_external_copy_and_paste_actions(copy_action, paste_action)
        self._model = ParameterGroupModel(db_mngr, parent)
        self._table_view.setModel(self._model)
        self._empty_model = EmptyParameterGroupModel(db_mngr, parent)
        self._empty_table_view = empty_parameter_group_table_view
        self._empty_table_view.setModel(self._empty_model)
        self._empty_table_view.verticalHeader().setDefaultSectionSize(row_height)
        self._seam = StackedTableSeam(self._table_view, self._empty_table_view)
        self._size_hint_provider = EmptyTableSizeHintProvider(self._table_view, self._empty_table_view)
        self._empty_table_view.set_size_hint_provider(self._size_hint_provider)
        contents_widget.height_changed.connect(self._update_empty_view_geometry)

    def init_models(self, db_maps: list[DatabaseMapping]) -> None:
        self._model.reset_db_maps(db_maps)
        if db_maps:
            self._empty_model.set_default_row(database=self._db_mngr.name_registry.display_name(db_maps[0].sa_url))
        else:
            self._empty_model.set_default_row()
        self._empty_model.reset_model()

    @Slot()
    def _update_empty_view_geometry(self) -> None:
        self._empty_table_view.updateGeometry()

    def tear_down(self) -> None:
        self._model.tear_down()
        self._empty_model.tear_down()
