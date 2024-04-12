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

"""Unit tests for ToolboxUI class."""
from pathlib import Path
from contextlib import contextmanager
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import logging
import os
import sys
import spinetoolbox.ui_main
from PySide6.QtWidgets import QApplication, QMessageBox, QMenu
from PySide6.QtCore import QSettings, Qt, QPoint, QPointF, QMimeData
from PySide6.QtTest import QTest
from PySide6.QtGui import QDropEvent
from spinetoolbox.project import SpineToolboxProject
from spinetoolbox.project_item.project_item import ProjectItem
from spinetoolbox.widgets.project_item_drag import ProjectItemDragMixin, NiceButton
from spinetoolbox.widgets.persistent_console_widget import PersistentConsoleWidget
from spinetoolbox.link import Link
from spinetoolbox.resources_icons_rc import qInitResources
from .mock_helpers import (
    clean_up_toolbox,
    create_toolboxui,
    create_project,
    add_dc,
    add_tool,
    qsettings_value_side_effect,
)


# noinspection PyUnusedLocal,DuplicatedCode
class TestToolboxUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        qInitResources()
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes an instance of ToolboxUI class
        without opening previous project."""
        self.toolbox = create_toolboxui()
        self._temp_dir = None

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        clean_up_toolbox(self.toolbox)
        if self._temp_dir is not None:
            self._temp_dir.cleanup()

    def test_init_specification_model(self):
        """Check that specification model has no items after init and that
        signals are connected just once.
        """
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_specification_model()
        self.assertEqual(self.toolbox.specification_model.rowCount(), 0)

    def test_create_project(self):
        """Test that create_project method makes a SpineToolboxProject instance.
        Does not actually create a project directory nor project.json file.
        """
        with TemporaryDirectory() as project_dir:
            create_project(self.toolbox, project_dir)
            self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)  # Check that a project is open

    def test_open_project(self):
        """Test that opening a project directory works.
        This test uses an actual Spine Toolbox project.
        The project should contain four items. Data Store 'a',
        Data Connection 'b', Tool 'c', and View 'd'. The items are connected
        a->b->c->d.
        """
        project_dir = os.path.abspath(os.path.join(str(Path(__file__).parent), "test_resources", "Project Directory"))
        self.assertTrue(os.path.exists(project_dir))
        self.assertIsNone(self.toolbox.project())
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
            "spinetoolbox.project.create_dir"
        ), mock.patch("spinetoolbox.project_item.project_item.create_dir"), mock.patch(
            "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
        ):
            self.toolbox.open_project(project_dir)
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)
        # Check that project contains four items
        self.assertEqual(self.toolbox.project().n_items, 4)
        # Check that design view has three links
        links = [item for item in self.toolbox.ui.graphicsView.scene().items() if isinstance(item, Link)]
        self.assertEqual(len(links), 3)
        # Check project items have the right links
        item_a = self.toolbox.project().get_item("a")
        icon_a = item_a.get_icon()
        links_a = [link for conn in icon_a.connectors.values() for link in conn.links]
        item_b = self.toolbox.project().get_item("b")
        icon_b = item_b.get_icon()
        links_b = [link for conn in icon_b.connectors.values() for link in conn.links]
        item_c = self.toolbox.project().get_item("c")
        icon_c = item_c.get_icon()
        links_c = [link for conn in icon_c.connectors.values() for link in conn.links]
        item_d = self.toolbox.project().get_item("d")
        icon_d = item_d.get_icon()
        links_d = [link for conn in icon_d.connectors.values() for link in conn.links]
        self.assertEqual(len(links_a), 1)
        self.assertEqual(links_a[0].src_connector._parent, icon_a)
        self.assertEqual(links_a[0].dst_connector._parent, icon_b)
        self.assertEqual(len(links_b), 2)
        self.assertTrue(links_a[0] in links_b)
        links_b.remove(links_a[0])
        self.assertEqual(links_b[0].src_connector._parent, icon_b)
        self.assertEqual(links_b[0].dst_connector._parent, icon_c)
        self.assertEqual(len(links_c), 2)
        self.assertTrue(links_b[0] in links_c)
        links_c.remove(links_b[0])
        self.assertEqual(links_c[0].src_connector._parent, icon_c)
        self.assertEqual(links_c[0].dst_connector._parent, icon_d)
        self.assertEqual(len(links_d), 1)
        self.assertEqual(links_c[0], links_d[0])
        # Check that DAG graph is correct
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertTrue(len(dags) == 1)  # Only one graph
        g = dags[0]
        self.assertTrue(len(g.nodes()) == 4)  # graph has four nodes
        self.assertTrue(len(g.edges()) == 3)  # graph has three edges
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_node("d"))
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("b", "c"))
        self.assertTrue(g.has_edge("c", "d"))

    def test_init_project(self):
        project_dir = os.path.abspath(os.path.join(str(Path(__file__).parent), "test_resources", "Project Directory"))
        self.assertTrue(os.path.exists(project_dir))
        self.assertIsNone(self.toolbox.project())
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
            "spinetoolbox.project.create_dir"
        ), mock.patch("spinetoolbox.project_item.project_item.create_dir"), mock.patch(
            "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
        ):
            self.toolbox.init_project(project_dir)
        self.assertIsNotNone(self.toolbox.project())
        self.assertEqual(self.toolbox.project().name, "Project Directory")

    def test_new_project(self):
        self._temp_dir = TemporaryDirectory()
        with mock.patch("spinetoolbox.ui_main.QSettings.setValue"), mock.patch(
            "spinetoolbox.ui_main.QSettings.sync"
        ), mock.patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory") as mock_dir_getter:
            mock_dir_getter.return_value = self._temp_dir.name
            self.toolbox.new_project()
        self.assertIsNotNone(self.toolbox.project())
        self.assertEqual(self.toolbox.project().name, os.path.basename(self._temp_dir.name))

    def test_save_project(self):
        self._temp_dir = TemporaryDirectory()
        with mock.patch("spinetoolbox.ui_main.QSettings.setValue"), mock.patch(
            "spinetoolbox.ui_main.QSettings.sync"
        ), mock.patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory") as mock_dir_getter:
            mock_dir_getter.return_value = self._temp_dir.name
            self.toolbox.new_project()
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        self.toolbox.save_project()
        self.assertTrue(self.toolbox.undo_stack.isClean())
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            # Make sure that the test uses LocalSpineEngineManager
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            self.assertTrue(self.toolbox.close_project())
            mock_qsettings_value.assert_called()
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
            "spinetoolbox.project.create_dir"
        ), mock.patch("spinetoolbox.project_item.project_item.create_dir"), mock.patch(
            "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
        ):
            self.toolbox.open_project(self._temp_dir.name)
        self.assertIsNotNone(self.toolbox.project())
        self.assertEqual(self.toolbox.project().get_item("DC").name, "DC")

    def test_close_project(self):
        self.assertIsNone(self.toolbox.project())
        self.assertTrue(self.toolbox.close_project())
        self.assertIsNone(self.toolbox.project())
        with TemporaryDirectory() as project_dir:
            create_project(self.toolbox, project_dir)
            self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)
            with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
                # Make sure that the test uses LocalSpineEngineManager
                mock_qsettings_value.side_effect = qsettings_value_side_effect
                self.assertTrue(self.toolbox.close_project())
                mock_qsettings_value.assert_called()
        self.assertIsNone(self.toolbox.project())

    def test_show_project_or_item_context_menu(self):
        self._temp_dir = TemporaryDirectory()
        with mock.patch("spinetoolbox.ui_main.QSettings.setValue") as mock_set_value, mock.patch(
            "spinetoolbox.ui_main.QSettings.sync"
        ) as mock_sync, mock.patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory") as mock_dir_getter:
            mock_dir_getter.return_value = self._temp_dir.name
            self.toolbox.new_project()
            mock_set_value.assert_called()
            mock_sync.assert_called()
            mock_dir_getter.assert_called()
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        # mocking "PySide6.QtWidgets.QMenu.exec directly doesn't work because QMenu.exec is overloaded!
        with mock.patch("spinetoolbox.ui_main.QMenu") as mock_qmenu:
            mock_qmenu.side_effect = MockQMenu
            self.toolbox.show_project_or_item_context_menu(QPoint(0, 0), None)
        with mock.patch("spinetoolbox.ui_main.QMenu") as mock_qmenu:
            mock_qmenu.side_effect = MockQMenu
            dc = self.toolbox.project().get_item("DC")
            self.toolbox.show_project_or_item_context_menu(QPoint(0, 0), dc)

    def test_refresh_edit_action_states(self):
        self.toolbox.refresh_edit_action_states()
        # No project
        self.assertFalse(self.toolbox.ui.actionCopy.isEnabled())
        self.assertFalse(self.toolbox.ui.actionPaste.isEnabled())
        self.assertFalse(self.toolbox.ui.actionPasteAndDuplicateFiles.isEnabled())
        self.assertFalse(self.toolbox.ui.actionDuplicate.isEnabled())
        self.assertFalse(self.toolbox.ui.actionDuplicateAndDuplicateFiles.isEnabled())
        self.assertFalse(self.toolbox.ui.actionRemove.isEnabled())
        self.assertFalse(self.toolbox.ui.actionRemove_all.isEnabled())
        # Make project
        self._temp_dir = TemporaryDirectory()
        with mock.patch("spinetoolbox.ui_main.QSettings.setValue") as mock_set_value, mock.patch(
            "spinetoolbox.ui_main.QSettings.sync"
        ) as mock_sync, mock.patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory") as mock_dir_getter:
            mock_dir_getter.return_value = self._temp_dir.name
            self.toolbox.new_project()
            mock_set_value.assert_called()
            mock_sync.assert_called()
            mock_dir_getter.assert_called()
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        dc = self.toolbox.project().get_item("DC")
        icon = dc.get_icon()
        icon.setSelected(True)
        with mock.patch("spinetoolbox.ui_main.QApplication.clipboard") as mock_clipboard:
            self.toolbox.refresh_edit_action_states()
            mock_clipboard.assert_called()
        self.assertTrue(self.toolbox.ui.actionCopy.isEnabled())
        self.assertFalse(self.toolbox.ui.actionPaste.isEnabled())
        self.assertFalse(self.toolbox.ui.actionPasteAndDuplicateFiles.isEnabled())
        self.assertTrue(self.toolbox.ui.actionDuplicate.isEnabled())
        self.assertTrue(self.toolbox.ui.actionDuplicateAndDuplicateFiles.isEnabled())
        self.assertTrue(self.toolbox.ui.actionRemove.isEnabled())
        self.assertTrue(self.toolbox.ui.actionRemove_all.isEnabled())
        # Cover enable_edit_actions()
        self.toolbox.enable_edit_actions()
        self.assertTrue(self.toolbox.ui.actionCopy.isEnabled())
        self.assertTrue(self.toolbox.ui.actionPaste.isEnabled())
        self.assertTrue(self.toolbox.ui.actionPasteAndDuplicateFiles.isEnabled())
        self.assertTrue(self.toolbox.ui.actionDuplicate.isEnabled())
        self.assertTrue(self.toolbox.ui.actionDuplicateAndDuplicateFiles.isEnabled())
        self.assertTrue(self.toolbox.ui.actionRemove.isEnabled())
        self.assertTrue(self.toolbox.ui.actionRemove_all.isEnabled())

    def test_selection_in_design_view_1(self):
        """Test item selection in Design View. Simulates mouse click on a Data Connection item.
        Test a single item selection.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        n_items = self.toolbox.project().n_items
        self.assertEqual(n_items, 1)  # Check that the project contains one item
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project().get_item(dc1)
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)  # Center point in graphics view viewport coords.
        # Simulate mouse click on Data Connection in Design View
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        self.assertEqual(1, len(gv.scene().selectedItems()))
        # Active project item should be DC1
        self.assertEqual(self.toolbox.project().get_item(dc1), self.toolbox.active_project_item)

    def test_selection_in_design_view_2(self):
        """Test item selection in Design View.
        First mouse click on project item. Second mouse click on a project item.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        dc2 = "DC2"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc2, x=100, y=100)
        n_items = self.toolbox.project().n_items
        self.assertEqual(n_items, 2)  # Check the number of project items
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project().get_item(dc1)
        dc2_item = self.toolbox.project().get_item(dc2)
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        dc2_center_point = self.find_click_point_of_pi(dc2_item, gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        # Then mouse click on dc2
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc2_center_point)
        self.assertEqual(1, len(gv.scene().selectedItems()))
        # Active project item should be DC2
        self.assertEqual(self.toolbox.project().get_item(dc2), self.toolbox.active_project_item)

    def test_selection_in_design_view_3(self):
        """Test item selection in Design View.
        First mouse click on project item. Second mouse click on design view.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project().get_item(dc1)
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        # Then mouse click somewhere else in Design View (not on project item)
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(1, 1))
        self.assertEqual(0, len(gv.scene().selectedItems()))  # No items in design view should be selected
        # Active project item should be None
        self.assertIsNone(self.toolbox.active_project_item)

    def test_selection_in_design_view_4(self):
        """Test item selection in Design View.
        Mouse click on a link. Check that Link is selected.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        dc2 = "DC2"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc2, x=100, y=100)
        n_items = self.toolbox.project().n_items
        self.assertEqual(n_items, 2)  # Check the number of project items
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project().get_item(dc1)
        dc2_item = self.toolbox.project().get_item(dc2)
        # Add link between dc1 and dc2
        gv.add_link(dc1_item.get_icon().conn_button("bottom"), dc2_item.get_icon().conn_button("bottom"))
        # Find link
        dc1_links = dc1_item.get_icon().conn_button("bottom").links
        dc2_links = dc2_item.get_icon().conn_button("bottom").links
        self.assertEqual(dc1_links, dc2_links)
        links = dc2_links
        self.assertEqual(1, len(links))
        link_center_point = self.find_click_point_of_link(links[0], gv)
        # Mouse click on link
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, link_center_point)
        # One item should be selected in Design View (the Link)
        selected_items = gv.scene().selectedItems()
        self.assertEqual(1, len(selected_items))
        # The Link item should be selected in Design View
        self.assertIsInstance(selected_items[0], Link)
        # Active project item should be None
        self.assertIsNone(self.toolbox.active_project_item)

    def test_selection_in_design_view_5(self):
        """Test item selection in Design View.
        First mouse click on project item, then mouse click on a Link.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        dc2 = "DC2"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc2, x=100, y=100)
        n_items = self.toolbox.project().n_items
        self.assertEqual(n_items, 2)  # Check the number of project items
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project().get_item(dc1)
        dc2_item = self.toolbox.project().get_item(dc2)
        # Add link between dc1 and dc2
        gv.add_link(dc1_item.get_icon().conn_button("bottom"), dc2_item.get_icon().conn_button("bottom"))
        # Find link
        dc1_links = dc1_item.get_icon().conn_button("bottom").links
        dc2_links = dc2_item.get_icon().conn_button("bottom").links
        self.assertEqual(dc1_links, dc2_links)
        links = dc2_links
        self.assertEqual(1, len(links))
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        link_center_point = self.find_click_point_of_link(links[0], gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        # Mouse click on link
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, link_center_point)
        # One item should be selected in Design View (the Link)
        selected_items = gv.scene().selectedItems()
        self.assertEqual(1, len(selected_items))
        # The Link item should be selected in Design View
        self.assertIsInstance(selected_items[0], Link)
        # Active project item should be None
        self.assertIsNone(self.toolbox.active_project_item)

    def test_selection_in_design_view_6(self):
        """Test multiple item selection in Design View.
        First mouse click on project item (Ctrl-key pressed).
        Second mouse click on a project item (Ctrl-key pressed).
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        dc2 = "DC2"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc2, x=100, y=100)
        n_items = self.toolbox.project().n_items
        self.assertEqual(n_items, 2)  # Check the number of project items
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project().get_item(dc1)
        dc2_item = self.toolbox.project().get_item(dc2)
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        dc2_center_point = self.find_click_point_of_pi(dc2_item, gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.ControlModifier, dc1_center_point)
        # Then mouse click on dc2
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.ControlModifier, dc2_center_point)
        self.assertEqual(2, len(gv.scene().selectedItems()))
        # Active project item should be None
        self.assertIsNone(self.toolbox.active_project_item)

    def test_drop_invalid_drag_on_design_view(self):
        mime_data = QMimeData()
        gv = self.toolbox.ui.graphicsView
        pos = QPoint(0, 0)
        event = QDropEvent(pos, Qt.CopyAction, mime_data, Qt.NoButton, Qt.NoModifier)
        with mock.patch(
            "PySide6.QtWidgets.QGraphicsSceneDragDropEvent.source"
        ) as mock_drop_event_source, mock.patch.object(self.toolbox, "project"), mock.patch.object(
            self.toolbox, "show_add_project_item_form"
        ) as mock_show_add_project_item_form:
            mock_drop_event_source.return_value = "Invalid source"
            gv.dropEvent(event)
            mock_show_add_project_item_form.assert_not_called()
        item_shadow = gv.scene().item_shadow
        self.assertIsNone(item_shadow)

    def test_drop_project_item_on_design_view(self):
        mime_data = QMimeData()
        item_type = next(iter(self.toolbox.item_factories))
        mime_data.setText(f"{item_type},spec")
        gv = self.toolbox.ui.graphicsView
        scene_pos = QPointF(44, 20)
        pos = gv.mapFromScene(scene_pos)
        event = QDropEvent(pos, Qt.CopyAction, mime_data, Qt.NoButton, Qt.NoModifier)
        with mock.patch(
            "PySide6.QtWidgets.QGraphicsSceneDragDropEvent.source"
        ) as mock_drop_event_source, mock.patch.object(self.toolbox, "project"), mock.patch.object(
            self.toolbox, "show_add_project_item_form"
        ) as mock_show_add_project_item_form:
            mock_drop_event_source.return_value = MockDraggableButton()
            gv.dropEvent(event)
            mock_show_add_project_item_form.assert_called_once()
            mock_show_add_project_item_form.assert_called_with(item_type, scene_pos.x(), scene_pos.y(), spec="spec")
        item_shadow = gv.scene().item_shadow
        self.assertTrue(item_shadow.isVisible())
        self.assertEqual(item_shadow.pos(), scene_pos)

    def test_remove_item(self):
        """Test removing a single project item."""
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1)
        # Check the size of project item model
        n_items = self.toolbox.project().n_items
        self.assertEqual(n_items, 1)
        # Check DAG handler
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertEqual(1, len(dags))  # Number of DAGs (DiGraph objects) in project
        self.assertEqual(1, len(dags[0].nodes()))  # Number of nodes in the DiGraph
        # Check number of items in Design View
        item_icons = self.toolbox.ui.graphicsView.scene().project_item_icons()
        self.assertEqual(len(item_icons), 1)
        item_icons[0].setSelected(True)  # Select item on Design View
        # NOW REMOVE DC1
        with mock.patch.object(spinetoolbox.ui_main.QMessageBox, "exec") as mock_message_box_exec:
            mock_message_box_exec.return_value = QMessageBox.StandardButton.Ok
            self.toolbox.ui.actionRemove.trigger()
        self.assertEqual(self.toolbox.project().n_items, 0)  # Check the number of project items
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertEqual(0, len(dags))  # Number of DAGs (DiGraph) objects in project
        item_icons = self.toolbox.ui.graphicsView.scene().project_item_icons()
        self.assertEqual(len(item_icons), 0)

    def test_add_and_remove_specification(self):
        """Tests that adding and removing a specification
        to project works from a valid tool specification file.
        Uses an actual Spine Toolbox Project in order to actually
        test something.

        Note: Test 'project.json' file should not have any
        specifications when this test starts and ends."""
        project_dir = os.path.abspath(os.path.join(str(Path(__file__).parent), "test_resources", "Project Directory"))
        self.assertTrue(os.path.exists(project_dir))
        self.assertIsNone(self.toolbox.project())
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
            "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
        ):
            self.toolbox.open_project(project_dir)
        # Tool spec model must be empty at this point
        self.assertEqual(0, self.toolbox.specification_model.rowCount())
        tool_spec_path = os.path.abspath(
            os.path.join(str(Path(__file__).parent), "test_resources", "test_tool_spec.json")
        )
        self.assertTrue(os.path.exists(tool_spec_path))
        # Add a Tool spec to 'project.json' file
        with mock.patch("spinetoolbox.ui_main.QFileDialog.getOpenFileName") as mock_filename, mock.patch(
            "spine_items.tool.tool_specifications.ToolSpecification.save"
        ) as mock_save_specification:
            mock_filename.return_value = [tool_spec_path]
            mock_save_specification.return_value = True
            self.toolbox.import_specification()
        self.assertEqual(1, self.toolbox.specification_model.rowCount())  # Tool spec model has one entry now
        # Find tool spec on row 0 from model and check that the name matches
        tool_spec = self.toolbox.specification_model.specification(0)
        self.assertEqual("Python Tool Specification", tool_spec.name)
        # Now, remove the Tool Spec from the model
        index = self.toolbox.specification_model.specification_index("Python Tool Specification")
        self.assertTrue(index.isValid())
        with mock.patch.object(spinetoolbox.ui_main.QMessageBox, "exec") as mock_message_box_exec:
            mock_message_box_exec.return_value = QMessageBox.StandardButton.Ok
            self.toolbox.remove_specification(index)
        # Tool spec model must be empty again
        self.assertEqual(0, self.toolbox.specification_model.rowCount())

    def test_tasks_before_exit_without_open_project(self):
        """_tasks_before_exit is called with every possible combination of the two QSettings values that it uses.
        This test is done without a project so MUT only calls QSettings.value() once.
        This can probably be simplified but at least it does not edit user's Settings, while doing the test."""
        self.assertIsNone(self.toolbox.project())
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_1
            tasks = self.toolbox._tasks_before_exit()
            mock_qsettings_value.assert_called_once()
            mock_qsettings_value.assert_called_with("appSettings/showExitPrompt", defaultValue="2")
        self.assertEqual(tasks, [])
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_2
            tasks = self.toolbox._tasks_before_exit()
            mock_qsettings_value.assert_called_once()
            mock_qsettings_value.assert_called_with("appSettings/showExitPrompt", defaultValue="2")
        self.assertEqual(tasks, ["prompt exit"])
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_5
            tasks = self.toolbox._tasks_before_exit()
            mock_qsettings_value.assert_called_once()
            mock_qsettings_value.assert_called_with("appSettings/showExitPrompt", defaultValue="2")
        self.assertEqual(tasks, [])
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_6
            tasks = self.toolbox._tasks_before_exit()
            mock_qsettings_value.assert_called_once()
            mock_qsettings_value.assert_called_with("appSettings/showExitPrompt", defaultValue="2")
        self.assertEqual(tasks, ["prompt exit"])

    def test_tasks_before_exit_with_open_dirty_project(self):
        """_tasks_before_exit is called with every possible combination of the two QSettings values that it uses.
        This test is done with a 'mock' project so MUST call QSettings.value() twice."""
        self.toolbox._project = 1  # Just make sure project is not None
        self.toolbox.undo_stack = mock.Mock()
        self.toolbox.undo_stack.isClean.return_value = False
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_1
            tasks = self.toolbox._tasks_before_exit()
            self.assertEqual(1, mock_qsettings_value.call_count)
        self.assertEqual(tasks, ["prompt save"])
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_2
            tasks = self.toolbox._tasks_before_exit()
            self.assertEqual(1, mock_qsettings_value.call_count)
        self.assertEqual(tasks, ["prompt save"])
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_5
            tasks = self.toolbox._tasks_before_exit()
            self.assertEqual(2, mock_qsettings_value.call_count)
        self.assertEqual(tasks, ["save"])
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = self._tasks_before_exit_scenario_6
            tasks = self.toolbox._tasks_before_exit()
            self.assertEqual(2, mock_qsettings_value.call_count)
        self.assertEqual(tasks, ["prompt exit", "save"])
        self.toolbox._project = None

    def test_copy_project_item_to_clipboard(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "data_connection")
        items_on_design_view = self.toolbox.ui.graphicsView.scene().project_item_icons()
        self.assertEqual(len(items_on_design_view), 1)
        items_on_design_view[0].setSelected(True)
        self.toolbox.ui.actionCopy.triggered.emit()
        # noinspection PyArgumentList
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        mime_formats = mime_data.formats()
        self.assertEqual(len(mime_formats), 1)
        self.assertEqual(mime_formats[0], "application/vnd.spinetoolbox.ProjectItem")
        item_dump = str(mime_data.data("application/vnd.spinetoolbox.ProjectItem").data(), "utf-8")
        self.assertTrue(item_dump)

    def test_paste_project_item_from_clipboard(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "data_connection")
        self.assertEqual(self.toolbox.project().n_items, 1)
        items_on_design_view = self.toolbox.ui.graphicsView.scene().project_item_icons()
        self.assertEqual(len(items_on_design_view), 1)
        items_on_design_view[0].setSelected(True)
        self.toolbox.ui.actionCopy.triggered.emit()
        self.toolbox.ui.actionPaste.triggered.emit()
        self.assertEqual(self.toolbox.project().n_items, 2)
        new_item = self.toolbox.project().get_item("data_connection (1)")
        self.assertIsInstance(new_item, ProjectItem)

    def test_duplicate_project_item(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "data_connection")
        self.assertEqual(self.toolbox.project().n_items, 1)
        items_on_design_view = self.toolbox.ui.graphicsView.scene().project_item_icons()
        self.assertEqual(len(items_on_design_view), 1)
        items_on_design_view[0].setSelected(True)
        with mock.patch("spinetoolbox.project_item.project_item.create_dir"):
            self.toolbox.ui.actionDuplicate.triggered.emit()
        self.assertEqual(self.toolbox.project().n_items, 2)
        new_item = self.toolbox.project().get_item("data_connection (1)")
        self.assertIsInstance(new_item, ProjectItem)

    def test_persistent_console_requested(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_tool(self.toolbox.project(), self.toolbox.item_factories, "tool")
        item = self.toolbox.project().get_item("tool")
        filter_id = ""
        key = ("too", "")
        language = "julia"
        self.toolbox.refresh_active_elements(item, None, {"tool"})
        self.toolbox._setup_persistent_console(item, filter_id, key, language)
        console = self.toolbox.ui.splitter_console.widget(1)
        self.assertTrue(isinstance(console, PersistentConsoleWidget))
        self.assertEqual(console.owners, {item})
        self.assertFalse(self.toolbox.ui.listView_console_executions.isVisible())
        self.assertEqual(self.toolbox.ui.listView_console_executions.model().rowCount(), 0)

    def test_filtered_persistent_consoles_requested(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_tool(self.toolbox.project(), self.toolbox.item_factories, "tool")
        item = self.toolbox.project().get_item("tool")
        language = "julia"
        self.toolbox.refresh_active_elements(item, None, {"tool"})
        self.toolbox._setup_persistent_console(item, "filter1", ("tool", "filter1"), language)
        self.toolbox._setup_persistent_console(item, "filter2", ("tool", "filter2"), language)
        self.toolbox._setup_persistent_console(item, "filter3", ("tool", "filter3"), language)
        view = self.toolbox.ui.listView_console_executions
        self.assertEqual(view.model().rowCount(), 3)
        # Scroll to item -> get rectangle -> click
        for row in range(view.model().rowCount()):
            ind = view.model().index(row, 0)
            view.scrollTo(ind)
            rect = view.visualRect(ind)
            QTest.mouseClick(view.viewport(), Qt.LeftButton, Qt.ControlModifier, rect.center())
            console = self.toolbox.ui.splitter_console.widget(1)
            self.assertTrue(isinstance(console, PersistentConsoleWidget))
            self.assertEqual(console.owners, {item})

    def test_closeEvent_saves_window_state(self):
        self.toolbox._qsettings = mock.NonCallableMagicMock()
        self.toolbox._perform_pre_exit_tasks = mock.MagicMock(return_value=True)
        self.toolbox.julia_repl = mock.NonCallableMagicMock()
        self.toolbox.python_console = mock.NonCallableMagicMock()
        self.toolbox.closeEvent(mock.MagicMock())
        qsettings_save_calls = self.toolbox._qsettings.setValue.call_args_list
        self.assertEqual(len(qsettings_save_calls), 7)
        saved_dict = {saved[0][0]: saved[0][1] for saved in qsettings_save_calls}
        self.assertIn("appSettings/previousProject", saved_dict)
        self.assertIn("mainWindow/windowSize", saved_dict)
        self.assertIn("mainWindow/windowPosition", saved_dict)
        self.assertIn("mainWindow/windowState", saved_dict)
        self.assertIn("mainWindow/windowMaximized", saved_dict)
        self.assertIn("mainWindow/n_screens", saved_dict)
        self.assertIn("appSettings/toolbarIconOrdering", saved_dict)

    @staticmethod
    def find_click_point_of_pi(pi, gv):
        """Maps given project item icons center coordinates to given Graphics View viewport coordinates.

        Args:
            pi (ProjectItem): Project item to process
            gv (QGraphicsView): View that contains the scene where the project item icon is shown

        Returns:
            (QPoint): Center point of the project item icon in graphics view viewport coordinates.
        """
        # We need to map item coordinates to scene coordinates to graphics view viewport coordinates
        # Get project item icon rectangle
        qrectf = pi.get_icon().rect()  # Returns a rectangle in item coordinate system
        # Map project item icon rectangle center point to scene coordinates
        qpointf = pi.get_icon().mapToScene(qrectf.center())  # Returns a point in scene coordinate system
        # Map scene coordinates to graphics view viewport coordinates
        qpoint = gv.mapFromScene(qpointf)  # Returns a point in Graphics view viewport coordinate system
        return qpoint

    @staticmethod
    def find_click_point_of_link(link, gv):
        """Maps given Link icons center coordinates to given Graphics View viewport coordinates.

        Args:
            link (QGraphicsPathItem): Link to process
            gv (QGraphicsView): Graphics View containing the scene that displays the link

        Returns:
            (QPoint): Center point of the Link in graphics view viewport coordinates.
        """
        # Make sure the boundingRect's center point is *on* the link
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            mock_qsettings_value.side_effect = "false"
            link.update_geometry()
        path = link.guide_path()
        # We need to map item coordinates to scene coordinates to graphics view viewport coordinates
        # Get link center
        center = path.pointAtPercent(0.5)
        # Map link center point to scene coordinates
        qpointf = link.mapToScene(center)  # Returns a point in scene coordinate system
        # Map scene coordinates to graphics view viewport coordinates
        qpoint = gv.mapFromScene(qpointf)  # Returns a point in Graphics view viewport coordinate system
        return qpoint

    @staticmethod
    def _tasks_before_exit_scenario_1(key, defaultValue="2"):
        if key == "appSettings/showExitPrompt":
            return "0"
        if key == "appSettings/saveAtExit":
            return "prompt"

    @staticmethod
    def _tasks_before_exit_scenario_2(key, defaultValue="2"):
        if key == "appSettings/showExitPrompt":
            return "2"
        if key == "appSettings/saveAtExit":
            return "prompt"

    @staticmethod
    def _tasks_before_exit_scenario_5(key, defaultValue="2"):
        if key == "appSettings/showExitPrompt":
            return "0"
        if key == "appSettings/saveAtExit":
            return "automatic"

    @staticmethod
    def _tasks_before_exit_scenario_6(key, defaultValue="2"):
        if key == "appSettings/showExitPrompt":
            return "2"
        if key == "appSettings/saveAtExit":
            return "automatic"


class MockDraggableButton(ProjectItemDragMixin, NiceButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestToolboxUIWithTestSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_legacy_settings_keys_get_renamed(self):
        settings_dict = {"appSettings/useEmbeddedJulia": "julia value", "appSettings/useEmbeddedPython": "python value"}
        with toolbox_with_settings(settings_dict) as toolbox:
            settings = toolbox.qsettings()
            self.assertTrue(settings.contains("appSettings/useJuliaKernel"))
            self.assertTrue(settings.contains("appSettings/usePythonKernel"))
            self.assertEqual(settings.value("appSettings/useJuliaKernel"), "julia value")
            self.assertEqual(settings.value("appSettings/usePythonKernel"), "python value")

    def test_legacy_saveAtExit_value_0_is_updated_to_prompt(self):
        settings_dict = {"appSettings/saveAtExit": "0"}
        with toolbox_with_settings(settings_dict) as toolbox:
            settings = toolbox.qsettings()
            self.assertEqual(settings.value("appSettings/saveAtExit"), "prompt")

    def test_legacy_saveAtExit_value_1_is_updated_to_prompt(self):
        settings_dict = {"appSettings/saveAtExit": "1"}
        with toolbox_with_settings(settings_dict) as toolbox:
            settings = toolbox.qsettings()
            self.assertEqual(settings.value("appSettings/saveAtExit"), "prompt")

    def test_legacy_saveAtExit_value_2_is_updated_to_automatic(self):
        settings_dict = {"appSettings/saveAtExit": "2"}
        with toolbox_with_settings(settings_dict) as toolbox:
            settings = toolbox.qsettings()
            self.assertEqual(settings.value("appSettings/saveAtExit"), "automatic")


@contextmanager
def toolbox_with_settings(settings_dict):
    settings = QSettings("SpineProject", "Spine Toolbox tests")
    for key, value in settings_dict.items():
        settings.setValue(key, value)
    with mock.patch("spinetoolbox.ui_main.QSettings") as settings_constructor:
        settings_constructor.return_value = settings
        toolbox = create_toolboxui()
    try:
        yield toolbox
    finally:
        settings.clear()
        settings.deleteLater()
        clean_up_toolbox(toolbox)


class MockQMenu(QMenu):
    def exec(self, pos):
        return True


if __name__ == "__main__":
    unittest.main()
