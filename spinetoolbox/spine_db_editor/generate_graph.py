######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################


import sys
import locale
import logging
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QItemSelectionModel
from spinetoolbox import resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import pyside6_version_check
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor


def generate_graph(
    url,
    entity_classes,
    name_parameter="",
    color_parameter="",
    arc_width_parameter="",
    bg_img_path=None,
    bg_img_entity_coordinates=None,
):
    """Launches Spine Db Editor and generates a graph."""
    if not pyside6_version_check():
        return 1
    app = QApplication(sys.argv)
    status = QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    if status < 0:
        logging.warning("Could not load fonts from resources file. Some icons may not render properly.")
    locale.setlocale(locale.LC_NUMERIC, 'C')
    settings = QSettings("SpineProject", "Spine Toolbox")
    db_mngr = SpineDBManager(settings, None, synchronous=False)
    multi_editor = MultiSpineDBEditor(db_mngr)
    multi_editor.add_new_tab({url: None})
    editor = multi_editor.tab_widget.widget(0)
    multi_editor.show()
    app.processEvents()
    graph_view = editor.ui.graphicsView
    editor.ui.dockWidget_entity_graph.show()
    graph_view.name_parameter = name_parameter
    graph_view.color_parameter = color_parameter
    graph_view.arc_width_parameter = arc_width_parameter
    if bg_img_path:
        graph_view.set_bg_image(bg_img_path)
    if bg_img_entity_coordinates:
        graph_view.set_bg_entity_coordinates(bg_img_entity_coordinates)
    for item_type, tree_view in (
        ("object_class", editor.ui.treeView_object),
        ("relationship_class", editor.ui.treeView_relationship),
    ):
        model = tree_view.model()
        selection_model = tree_view.selectionModel()
        for item in model.visit_all():
            if hasattr(item, "item_type") and item.item_type == item_type and item.display_data in entity_classes:
                index = model.index_from_item(item)
                selection_model.select(index, QItemSelectionModel.Select)
    return_code = app.exec()
    return return_code
