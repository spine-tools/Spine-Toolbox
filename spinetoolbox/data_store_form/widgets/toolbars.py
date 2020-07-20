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
Functions to make and handle QToolBars.

:author: P. Savolainen (VTT)
:date:   19.1.2018
"""

from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QToolBar, QLabel, QAction, QButtonGroup, QPushButton, QWidget, QSizePolicy
from ...config import PARAMETER_TAG_TOOLBAR_SS


class ParameterTagToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions."""

    tag_button_toggled = Signal("QVariant", "bool")
    manage_tags_action_triggered = Signal("bool")
    tag_actions_added = Signal("QVariant", "QVariant")

    def __init__(self, parent, db_mngr, *db_maps):
        """

        Args:
            parent (DataStoreForm): tree or graph view form
            db_mngr (SpineDBManager): the DB manager for interacting with the db
            db_maps (iter): DiffDatabaseMapping instances
        """
        super().__init__("Parameter Tag Toolbar", parent=parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        label = QLabel("Parameter tag")
        self.addWidget(label)
        self.tag_button_group = QButtonGroup(self)
        self.tag_button_group.setExclusive(False)
        self.actions = []
        self.db_map_ids = []
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.empty_action = self.addWidget(empty)
        button = QPushButton("Manage tags...")
        self.addWidget(button)
        # noinspection PyUnresolvedReferences
        # pylint: disable=unnecessary-lambda
        button.clicked.connect(lambda checked: self.manage_tags_action_triggered.emit(checked))
        self.setStyleSheet(PARAMETER_TAG_TOOLBAR_SS)
        self.setObjectName("ParameterTagToolbar")
        self.tag_actions_added.connect(self._add_db_map_tag_actions)

    def init_toolbar(self):
        for button in self.tag_button_group.buttons():
            self.tag_button_group.removeButton(button)
        for action in self.actions:
            self.removeAction(action)
        action = QAction("untagged")
        self.insertAction(self.empty_action, action)
        action.setCheckable(True)
        button = self.widgetForAction(action)
        self.tag_button_group.addButton(button, id=0)
        self.actions = [action]
        self.db_map_ids = [[(db_map, 0) for db_map in self.db_maps]]
        tag_data = {}
        for db_map in self.db_maps:
            for parameter_tag in self.db_mngr.get_items(db_map, "parameter_tag"):
                tag_data.setdefault(parameter_tag["tag"], {})[db_map] = parameter_tag["id"]
        for tag, db_map_data in tag_data.items():
            action = QAction(tag)
            self.insertAction(self.empty_action, action)
            action.setCheckable(True)
            button = self.widgetForAction(action)
            self.tag_button_group.addButton(button, id=len(self.db_map_ids))
            self.actions.append(action)
            self.db_map_ids.append(list(db_map_data.items()))
        self.tag_button_group.buttonToggled["int", "bool"].connect(
            lambda i, checked: self.tag_button_toggled.emit(self.db_map_ids[i], checked)
        )

    def receive_parameter_tags_added(self, db_map_data):
        for db_map, parameter_tags in db_map_data.items():
            self.tag_actions_added.emit(db_map, parameter_tags)

    @Slot("QVariant", "QVariant")
    def _add_db_map_tag_actions(self, db_map, parameter_tags):
        action_texts = [a.text() for a in self.actions]
        for parameter_tag in parameter_tags:
            if parameter_tag["tag"] in action_texts:
                # Already a tag named after that, add db_map id information
                i = action_texts.index(parameter_tag["tag"])
                self.db_map_ids[i].append((db_map, parameter_tag["id"]))
            else:
                action = QAction(parameter_tag["tag"])
                self.insertAction(self.empty_action, action)
                action.setCheckable(True)
                button = self.widgetForAction(action)
                self.tag_button_group.addButton(button, id=len(self.db_map_ids))
                self.actions.append(action)
                self.db_map_ids.append([(db_map, parameter_tag["id"])])
                action_texts.append(action.text())

    def receive_parameter_tags_removed(self, db_map_data):
        for db_map, parameter_tags in db_map_data.items():
            parameter_tag_ids = {x["id"] for x in parameter_tags}
            self._remove_db_map_tag_actions(db_map, parameter_tag_ids)

    def _remove_db_map_tag_actions(self, db_map, parameter_tag_ids):
        for tag_id in parameter_tag_ids:
            i = next(k for k, x in enumerate(self.db_map_ids) if (db_map, tag_id) in x)
            self.db_map_ids[i].remove((db_map, tag_id))
            if not self.db_map_ids[i]:
                self.db_map_ids.pop(i)
                self.removeAction(self.actions.pop(i))

    def receive_parameter_tags_updated(self, db_map_data):
        for db_map, parameter_tags in db_map_data.items():
            self._update_db_map_tag_actions(db_map, parameter_tags)

    def _update_db_map_tag_actions(self, db_map, parameter_tags):
        for parameter_tag in parameter_tags:
            i = next(k for k, x in enumerate(self.db_map_ids) if (db_map, parameter_tag["id"]) in x)
            action = self.actions[i]
            action.setText(parameter_tag["tag"])
