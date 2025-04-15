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
from PySide6.QtCore import QSortFilterProxyModel
from spinetoolbox.spine_db_editor.mvcmodels.grouped_parameter_value_model import GroupedParameterValueModel


class GroupedParameterValueProxyModel(QSortFilterProxyModel):
    def mapFromSource(self, sourceIndex):
        if not sourceIndex.isValid():
            return sourceIndex
        proxy_index = super().mapFromSource(sourceIndex)
        if sourceIndex.internalPointer() is not None:
            return proxy_index
        source_model: GroupedParameterValueModel = self.sourceModel()
        ungrouped_row = source_model.ungrouped_row()
        if ungrouped_row is None:
            return proxy_index
        # return proxy_index
        ungrouped_index = source_model.index(ungrouped_row, sourceIndex.column())
        proxy_ungrouped_index = super().mapFromSource(ungrouped_index)
        proxy_ungrouped_row = proxy_ungrouped_index.row()
        proxy_row = proxy_index.row()
        if proxy_row < proxy_ungrouped_row:
            return proxy_index
        if proxy_row > proxy_ungrouped_row:
            return self.index(proxy_row - 1, proxy_index.column())
        last_proxy_row = self.rowCount() - 1
        return self.index(last_proxy_row, proxy_index.column())

    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid():
            return proxyIndex
        source_index = super().mapToSource(proxyIndex)
        if source_index.internalPointer() is not None:
            return source_index
        source_model: GroupedParameterValueModel = self.sourceModel()
        ungrouped_row = source_model.ungrouped_row()
        if ungrouped_row is None:
            return source_index
        last_proxy_row = self.rowCount() - 1
        proxy_row = proxyIndex.row()
        if proxy_row == last_proxy_row:
            return source_model.index(ungrouped_row, source_index.column())
        ungrouped_index = source_model.index(ungrouped_row, 0)
        ungrouped_proxy_index = super().mapFromSource(ungrouped_index)
        ungrouped_proxy_row = ungrouped_proxy_index.row()
        if proxy_row < ungrouped_proxy_row:
            return source_index
        return source_model.index(source_index.row() + 1, source_index.column())
