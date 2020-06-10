######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Provides the ManageGroupObjectDialog.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from PySide2.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QComboBox,
    QToolButton,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
)
from PySide2.QtCore import Slot, Qt, QSize
from PySide2.QtGui import QIcon


class ManageGroupObjectDialog(QDialog):
    def __init__(self, parent, object_item, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            object_item (ObjectItem)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping)
        """
        super().__init__(parent)
        self.setWindowTitle("Manage group object")
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self.db_map = db_maps[0]
        self.db_maps_by_codename = {db_map.codename: db_map for db_map in db_maps}
        self.object_item = object_item
        self.added = set()
        self.removed = set()
        self.db_combo_box = QComboBox(self)
        self.header_widget = QWidget(self)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.addWidget(QLabel(f"Object: {self.object_item.display_data}"))
        header_layout.addSpacing(32)
        header_layout.addWidget(QLabel("Database"))
        header_layout.addWidget(self.db_combo_box)
        self.non_members_tree = QTreeWidget(self)
        self.non_members_tree.setHeaderLabel("Non members")
        self.non_members_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.non_members_tree.setColumnCount(1)
        self.non_members_tree.setIndentation(0)
        self.members_tree = QTreeWidget(self)
        self.members_tree.setHeaderLabel("Members")
        self.members_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.members_tree.setColumnCount(1)
        self.members_tree.setIndentation(0)
        self.add_button = QToolButton()
        self.add_button.setToolTip("<p>Add selected non-members.</p>")
        self.add_button.setIcon(QIcon(":/icons/menu_icons/cube_plus.svg"))
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.add_button.setText(">>")
        self.remove_button = QToolButton()
        self.remove_button.setToolTip("<p>Remove selected members.</p>")
        self.remove_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.remove_button.setIconSize(QSize(24, 24))
        self.remove_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.remove_button.setText("<<")
        self.vertical_button_widget = QWidget()
        vertical_button_layout = QVBoxLayout(self.vertical_button_widget)
        vertical_button_layout.addStretch()
        vertical_button_layout.addWidget(self.add_button)
        vertical_button_layout.addWidget(self.remove_button)
        vertical_button_layout.addStretch()
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QGridLayout(self)
        layout.addWidget(self.header_widget, 0, 0, 1, 3, Qt.AlignHCenter)
        layout.addWidget(self.non_members_tree, 1, 0)
        layout.addWidget(self.vertical_button_widget, 1, 1)
        layout.addWidget(self.members_tree, 1, 2)
        layout.addWidget(self.button_box, 2, 0, 1, 3)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.db_combo_box.addItems(list(self.db_maps_by_codename))
        self.db_map_object_ids = {
            db_map: {
                x["name"]: x["id"]
                for x in self.db_mngr.get_items_by_field(
                    self.db_map, "object", "class_id", self.object_item.db_map_data(db_map)["class_id"]
                )
            }
            for db_map in db_maps
        }
        self.reset_list_widgets(db_maps[0].codename)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.db_combo_box.currentTextChanged.connect(self.reset_list_widgets)
        self.add_button.clicked.connect(self.add_members)
        self.remove_button.clicked.connect(self.remove_members)

    def reset_list_widgets(self, database):
        self.db_map = self.db_maps_by_codename[database]
        object_ids = self.db_map_object_ids[self.db_map]
        self.added.clear()
        self.removed.clear()
        members = []
        non_members = []
        for obj_name, obj_id in object_ids.items():
            if obj_id in self.object_item.db_map_member_ids(self.db_map):
                members.append(obj_name)
            elif obj_id != self.object_item.db_map_id(self.db_map):
                non_members.append(obj_name)
        member_items = [QTreeWidgetItem([obj_name]) for obj_name in members]
        non_member_items = [QTreeWidgetItem([obj_name]) for obj_name in non_members]
        self.members_tree.addTopLevelItems(member_items)
        self.non_members_tree.addTopLevelItems(non_member_items)

    @Slot(bool)
    def add_members(self, checked=False):
        indexes = sorted(
            [self.non_members_tree.indexOfTopLevelItem(x) for x in self.non_members_tree.selectedItems()], reverse=True
        )
        items = [self.non_members_tree.takeTopLevelItem(ind) for ind in indexes]
        self.members_tree.addTopLevelItems(items)
        self.added.update({x.text(0) for x in items})

    @Slot(bool)
    def remove_members(self, checked=False):
        indexes = sorted(
            [self.members_tree.indexOfTopLevelItem(x) for x in self.members_tree.selectedItems()], reverse=True
        )
        items = [self.members_tree.takeTopLevelItem(ind) for ind in indexes]
        self.non_members_tree.addTopLevelItems(items)
        removed = set(x.text(0) for x in items)
        self.removed.update(removed - self.added)
        self.added.difference_update(removed)

    @Slot()
    def accept(self):
        obj = self.object_item.db_map_data(self.db_map)
        added_member_id_list = [self.db_map_object_ids[self.db_map][name] for name in self.added]
        db_map_data_to_add = {
            self.db_map: [
                {"entity_id": obj["id"], "entity_class_id": obj["class_id"], "member_id": member_id}
                for member_id in added_member_id_list
            ]
        }
        removed_member_id_list = [self.db_map_object_ids[self.db_map][name] for name in self.removed]
        db_map_typed_data_to_remove = {
            self.db_map: {
                "group entity": [
                    x
                    for x in self.object_item.db_map_group_entities(self.db_map)
                    if x["member_id"] in removed_member_id_list
                ]
            }
        }
        self.db_mngr.add_group_entities(db_map_data_to_add)
        self.db_mngr.remove_items(db_map_typed_data_to_remove)
        super().accept()
