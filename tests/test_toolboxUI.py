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

"""
Unit tests for ToolboxUI class.
"""

from collections import namedtuple
from contextlib import contextmanager
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import logging
import os
import sys
import spinetoolbox.ui_main
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings, Qt, QPoint, QItemSelectionModel, QPointF, QMimeData
from PySide6.QtTest import QTest
from PySide6.QtGui import QDropEvent
from spinetoolbox.project_item_icon import ProjectItemIcon
from spinetoolbox.project import SpineToolboxProject
from spinetoolbox.widgets.project_item_drag import ProjectItemDragMixin
from spinetoolbox.widgets.persistent_console_widget import PersistentConsoleWidget
from spinetoolbox.link import Link
from spinetoolbox.mvcmodels.project_tree_item import RootProjectTreeItem
from spinetoolbox.resources_icons_rc import qInitResources
from .mock_helpers import (
    clean_up_toolbox,
    create_toolboxui,
    create_project,
    add_ds,
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
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
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

    def test_init_project_item_model_without_project(self):
        """Test that a new project item model contains 6 category items.
        Note: This test is done WITHOUT a project open.
        """
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_project_item_model()
        self.check_init_project_item_model()

    def test_init_project_item_model_with_project(self):
        """Test that project item model is initialized successfully.
        Note: This test is done WITH a project.
        Mock save_project() and create_dir() so that .proj file and project directory (and work directory) are
        not actually created.
        """
        with TemporaryDirectory() as project_dir:
            create_project(self.toolbox, project_dir)
            self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)  # Check that a project is open
            self.toolbox.init_project_item_model()
            self.check_init_project_item_model()

    def check_init_project_item_model(self):
        """Checks that category items are created as expected."""
        n = self.toolbox.project_item_model.rowCount()
        # Data Stores, Data Connections, Tools, Views, Importers, Exporters, Manipulators
        self.assertEqual(n, 7)
        # Check that there's only one column
        self.assertEqual(self.toolbox.project_item_model.columnCount(), 1)
        # Check that the items DisplayRoles are (In this particular order)
        item1 = self.toolbox.project_item_model.root().child(0)
        self.assertEqual(item1.name, "Data Stores", "Item on row 0 is not 'Data Stores'")
        self.assertIsInstance(
            item1.parent(), RootProjectTreeItem, "Parent item of category item on row 0 should be root"
        )
        item2 = self.toolbox.project_item_model.root().child(1)
        self.assertEqual(item2.name, "Data Connections", "Item on row 1 is not 'Data Connections'")
        self.assertIsInstance(
            item2.parent(), RootProjectTreeItem, "Parent item of category item on row 1 should be root"
        )
        item3 = self.toolbox.project_item_model.root().child(2)
        self.assertEqual(item3.name, "Tools", "Item on row 2 is not 'Tools'")
        self.assertIsInstance(
            item3.parent(), RootProjectTreeItem, "Parent item of category item on row 2 should be root"
        )
        item4 = self.toolbox.project_item_model.root().child(3)
        self.assertEqual(item4.name, "Views", "Item on row 3 is not 'Views'")
        self.assertIsInstance(
            item4.parent(), RootProjectTreeItem, "Parent item of category item on row 3 should be root"
        )
        item5 = self.toolbox.project_item_model.root().child(4)
        self.assertEqual(item5.name, "Importers", "Item on row 4 is not 'Importers'")
        self.assertIsInstance(
            item5.parent(), RootProjectTreeItem, "Parent item of category item on row 4 should be root"
        )
        item6 = self.toolbox.project_item_model.root().child(5)
        self.assertEqual(item6.name, "Exporters", "Item on row 5 is not 'Exporters'")
        self.assertIsInstance(
            item6.parent(), RootProjectTreeItem, "Parent item of category item on row 5 should be root"
        )
        item7 = self.toolbox.project_item_model.root().child(6)
        self.assertEqual(item7.name, "Manipulators", "Item on row 6 is not 'Manipulators'")
        self.assertIsInstance(
            item7.parent(), RootProjectTreeItem, "Parent item of category item on row 6 should be root"
        )

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
        project_dir = os.path.abspath(os.path.join(os.curdir, "tests", "test_resources", "Project Directory"))
        if not os.path.exists(project_dir):
            self.skipTest("Test project directory '{0}' does not exist".format(project_dir))
            return
        self.assertIsNone(self.toolbox.project())
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
            "spinetoolbox.project.create_dir"
        ), mock.patch("spinetoolbox.project_item.project_item.create_dir"), mock.patch(
            "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
        ):
            self.toolbox.open_project(project_dir)
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)
        # Check that project contains four items
        self.assertEqual(self.toolbox.project_item_model.n_items(), 4)
        # Check that design view has three links
        links = [item for item in self.toolbox.ui.graphicsView.scene().items() if isinstance(item, Link)]
        self.assertEqual(len(links), 3)
        # Check project items have the right links
        index_a = self.toolbox.project_item_model.find_item("a")
        item_a = self.toolbox.project_item_model.item(index_a).project_item
        icon_a = item_a.get_icon()
        links_a = [link for conn in icon_a.connectors.values() for link in conn.links]
        index_b = self.toolbox.project_item_model.find_item("b")
        item_b = self.toolbox.project_item_model.item(index_b).project_item
        icon_b = item_b.get_icon()
        links_b = [link for conn in icon_b.connectors.values() for link in conn.links]
        index_c = self.toolbox.project_item_model.find_item("c")
        item_c = self.toolbox.project_item_model.item(index_c).project_item
        icon_c = item_c.get_icon()
        links_c = [link for conn in icon_c.connectors.values() for link in conn.links]
        index_d = self.toolbox.project_item_model.find_item("d")
        item_d = self.toolbox.project_item_model.item(index_d).project_item
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
        project_dir = os.path.abspath(os.path.join(os.curdir, "tests", "test_resources", "Project Directory"))
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

    def test_selection_in_project_item_list_1(self):
        """Test item selection in treeView_project. Simulates a mouse click on a Data Store item
        in the project Tree View widget (i.e. the project item list).
        """
        with TemporaryDirectory() as project_dir:
            create_project(self.toolbox, project_dir)
            ds1 = "DS1"
            add_ds(self.toolbox.project(), self.toolbox.item_factories, ds1)
            n_items = self.toolbox.project_item_model.n_items()
            self.assertEqual(n_items, 1)  # Check that the project contains one item
            ds_ind = self.toolbox.project_item_model.find_item(ds1)
            tv = self.toolbox.ui.treeView_project
            tv.expandAll()  # NOTE: mouseClick does not work without this
            tv_sm = tv.selectionModel()
            # Scroll to item -> get rectangle -> click
            tv.scrollTo(ds_ind)  # Make sure the item is 'visible'
            ds1_rect = tv.visualRect(ds_ind)
            # logging.debug("viewport geometry:{0}".format(tv.viewport().geometry()))  # this is pos() and size() combined
            # logging.debug("item rect:{0}".format(ds1_rect))
            # Simulate mouse click on selected item
            QTest.mouseClick(tv.viewport(), Qt.LeftButton, Qt.NoModifier, ds1_rect.center())
            self.assertTrue(tv_sm.isSelected(ds_ind))
            self.assertEqual(tv_sm.currentIndex(), ds_ind)
            self.assertEqual(1, len(tv_sm.selectedIndexes()))
            # Active project item should be DS1
            self.assertEqual(
                self.toolbox.project_item_model.item(ds_ind).project_item, self.toolbox.active_project_item
            )

    def test_selection_in_project_item_list_2(self):
        """Test item selection in treeView_project. Simulates mouse clicks on a Data Store items.
        Click on a project item and then on another project item.
        """
        with TemporaryDirectory() as project_dir:
            create_project(self.toolbox, project_dir)
            ds1 = "DS1"
            ds2 = "DS2"
            add_ds(self.toolbox.project(), self.toolbox.item_factories, ds1)
            add_ds(self.toolbox.project(), self.toolbox.item_factories, ds2)
            n_items = self.toolbox.project_item_model.n_items()
            self.assertEqual(n_items, 2)
            ds1_ind = self.toolbox.project_item_model.find_item(ds1)
            ds2_ind = self.toolbox.project_item_model.find_item(ds2)
            tv = self.toolbox.ui.treeView_project
            tv.expandAll()
            tv_sm = tv.selectionModel()
            # Scroll to item -> get rectangle -> click
            tv.scrollTo(ds1_ind)
            ds1_rect = tv.visualRect(ds1_ind)
            QTest.mouseClick(tv.viewport(), Qt.LeftButton, Qt.NoModifier, ds1_rect.center())
            # Scroll to item -> get rectangle -> click
            tv.scrollTo(ds2_ind)
            ds2_rect = tv.visualRect(ds2_ind)
            QTest.mouseClick(tv.viewport(), Qt.LeftButton, Qt.NoModifier, ds2_rect.center())
            self.assertTrue(tv_sm.isSelected(ds2_ind))
            self.assertEqual(tv_sm.currentIndex(), ds2_ind)
            self.assertEqual(1, len(tv_sm.selectedIndexes()))
            # Active project item should be DS2
            self.assertEqual(
                self.toolbox.project_item_model.item(ds2_ind).project_item, self.toolbox.active_project_item
            )

    def test_selection_in_project_item_list_3(self):
        """Test item selection in treeView_project. Simulates mouse clicks on a Data Store items.
        Test multiple selection (Ctrl-pressed) with two Data Store items.
        """
        with TemporaryDirectory() as project_dir:
            create_project(self.toolbox, project_dir)
            ds1 = "DS1"
            ds2 = "DS2"
            add_ds(self.toolbox.project(), self.toolbox.item_factories, ds1)
            add_ds(self.toolbox.project(), self.toolbox.item_factories, ds2)
            n_items = self.toolbox.project_item_model.n_items()
            self.assertEqual(n_items, 2)
            ds1_ind = self.toolbox.project_item_model.find_item(ds1)
            ds2_ind = self.toolbox.project_item_model.find_item(ds2)
            tv = self.toolbox.ui.treeView_project
            tv.expandAll()
            tv_sm = tv.selectionModel()
            # Scroll to item -> get rectangle -> click
            tv.scrollTo(ds1_ind)
            ds1_rect = tv.visualRect(ds1_ind)
            QTest.mouseClick(tv.viewport(), Qt.LeftButton, Qt.ControlModifier, ds1_rect.center())
            # Scroll to item -> get rectangle -> click
            tv.scrollTo(ds2_ind)
            ds2_rect = tv.visualRect(ds2_ind)
            QTest.mouseClick(tv.viewport(), Qt.LeftButton, Qt.ControlModifier, ds2_rect.center())
            # Both items should be selected, but we don't know which one is current as QGraphicsScene.selecteItems() is not sorted
            self.assertTrue(tv_sm.isSelected(ds1_ind))
            self.assertTrue(tv_sm.isSelected(ds2_ind))
            self.assertEqual(2, len(tv_sm.selectedIndexes()))
            # There should also be 2 items selected in the Design View
            n_selected_items_in_design_view = len(self.toolbox.ui.graphicsView.scene().selectedItems())
            self.assertEqual(2, n_selected_items_in_design_view)
            # Active project item should be None
            self.assertIsNone(self.toolbox.active_project_item)

    def test_selection_in_design_view_1(self):
        """Test item selection in Design View. Simulates mouse click on a Data Connection item.
        Test a single item selection.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        n_items = self.toolbox.project_item_model.n_items()
        self.assertEqual(n_items, 1)  # Check that the project contains one item
        dc1_index = self.toolbox.project_item_model.find_item(dc1)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project_item_model.item(dc1_index).project_item
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)  # Center point in graphics view viewport coords.
        # Simulate mouse click on Data Connection in Design View
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        tv_sm = self.toolbox.ui.treeView_project.selectionModel()
        self.assertTrue(tv_sm.isSelected(dc1_index))
        self.assertEqual(dc1_index, tv_sm.currentIndex())
        self.assertEqual(1, len(tv_sm.selectedIndexes()))
        self.assertEqual(1, len(gv.scene().selectedItems()))
        # Active project item should be DC1
        self.assertEqual(self.toolbox.project_item_model.item(dc1_index).project_item, self.toolbox.active_project_item)

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
        n_items = self.toolbox.project_item_model.n_items()
        self.assertEqual(n_items, 2)  # Check the number of project items
        dc1_index = self.toolbox.project_item_model.find_item(dc1)
        dc2_index = self.toolbox.project_item_model.find_item(dc2)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project_item_model.item(dc1_index).project_item
        dc2_item = self.toolbox.project_item_model.item(dc2_index).project_item
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        dc2_center_point = self.find_click_point_of_pi(dc2_item, gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        # Then mouse click on dc2
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc2_center_point)
        tv_sm = self.toolbox.ui.treeView_project.selectionModel()
        self.assertTrue(tv_sm.isSelected(dc2_index))
        self.assertEqual(dc2_index, tv_sm.currentIndex())
        self.assertEqual(1, len(tv_sm.selectedIndexes()))
        self.assertEqual(1, len(gv.scene().selectedItems()))
        # Active project item should be DC2
        self.assertEqual(self.toolbox.project_item_model.item(dc2_index).project_item, self.toolbox.active_project_item)

    def test_selection_in_design_view_3(self):
        """Test item selection in Design View.
        First mouse click on project item. Second mouse click on design view.
        """
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        dc1 = "DC1"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, dc1, x=0, y=0)
        dc1_index = self.toolbox.project_item_model.find_item(dc1)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project_item_model.item(dc1_index).project_item
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, dc1_center_point)
        # Then mouse click somewhere else in Design View (not on project item)
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(1, 1))
        # Treeview current index should be dc1_index
        tv_sm = self.toolbox.ui.treeView_project.selectionModel()
        self.assertEqual(dc1_index, tv_sm.currentIndex())
        self.assertEqual(0, len(tv_sm.selectedIndexes()))  # No items in pi list should be selected
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
        n_items = self.toolbox.project_item_model.n_items()
        self.assertEqual(n_items, 2)  # Check the number of project items
        dc1_index = self.toolbox.project_item_model.find_item(dc1)
        dc2_index = self.toolbox.project_item_model.find_item(dc2)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project_item_model.item(dc1_index).project_item
        dc2_item = self.toolbox.project_item_model.item(dc2_index).project_item
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
        tv_sm = self.toolbox.ui.treeView_project.selectionModel()
        # Check that dc1 is NOT selected
        self.assertFalse(tv_sm.isSelected(dc1_index))
        # Check that dc2 is NOT selected
        self.assertFalse(tv_sm.isSelected(dc2_index))
        # No items should be selected in the tree view
        self.assertEqual(0, len(tv_sm.selectedIndexes()))
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
        n_items = self.toolbox.project_item_model.n_items()
        self.assertEqual(n_items, 2)  # Check the number of project items
        dc1_index = self.toolbox.project_item_model.find_item(dc1)
        dc2_index = self.toolbox.project_item_model.find_item(dc2)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project_item_model.item(dc1_index).project_item
        dc2_item = self.toolbox.project_item_model.item(dc2_index).project_item
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
        tv_sm = self.toolbox.ui.treeView_project.selectionModel()
        # Check that dc1 is NOT selected
        self.assertFalse(tv_sm.isSelected(dc1_index))
        # Check that dc2 is NOT selected
        self.assertFalse(tv_sm.isSelected(dc2_index))
        # No items should be selected in the tree view
        self.assertEqual(0, len(tv_sm.selectedIndexes()))
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
        n_items = self.toolbox.project_item_model.n_items()
        self.assertEqual(n_items, 2)  # Check the number of project items
        dc1_index = self.toolbox.project_item_model.find_item(dc1)
        dc2_index = self.toolbox.project_item_model.find_item(dc2)
        gv = self.toolbox.ui.graphicsView
        dc1_item = self.toolbox.project_item_model.item(dc1_index).project_item
        dc2_item = self.toolbox.project_item_model.item(dc2_index).project_item
        dc1_center_point = self.find_click_point_of_pi(dc1_item, gv)
        dc2_center_point = self.find_click_point_of_pi(dc2_item, gv)
        # Mouse click on dc1
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.ControlModifier, dc1_center_point)
        # Then mouse click on dc2
        QTest.mouseClick(gv.viewport(), Qt.LeftButton, Qt.ControlModifier, dc2_center_point)
        tv_sm = self.toolbox.ui.treeView_project.selectionModel()
        self.assertEqual(2, len(tv_sm.selectedIndexes()))
        self.assertTrue(tv_sm.isSelected(dc1_index))
        self.assertTrue(tv_sm.isSelected(dc2_index))
        # NOTE: No test for tv_sm current index here!
        self.assertEqual(2, len(gv.scene().selectedItems()))
        # Active project item should be None
        self.assertIsNone(self.toolbox.active_project_item)

    def test_drop_invalid_drag_on_design_view(self):
        mime_data = QMimeData()
        gv = self.toolbox.ui.graphicsView
        pos = QPoint(0, 0)
        event = QDropEvent(pos, Qt.CopyAction, mime_data, Qt.NoButton, Qt.NoModifier)
        with mock.patch(
            'PySide6.QtWidgets.QGraphicsSceneDragDropEvent.source'
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
            'PySide6.QtWidgets.QGraphicsSceneDragDropEvent.source'
        ) as mock_drop_event_source, mock.patch.object(self.toolbox, "project"), mock.patch.object(
            self.toolbox, "show_add_project_item_form"
        ) as mock_show_add_project_item_form:
            mock_drop_event_source.return_value = ProjectItemDragMixin()
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
        n_items = self.toolbox.project_item_model.n_items()
        self.assertEqual(n_items, 1)
        # Check DAG handler
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertEqual(1, len(dags))  # Number of DAGs (DiGraph objects) in project
        self.assertEqual(1, len(dags[0].nodes()))  # Number of nodes in the DiGraph
        # Check number of items in Design View
        items_in_design_view = self.toolbox.ui.graphicsView.scene().items()
        n_items_in_design_view = len([item for item in items_in_design_view if isinstance(item, ProjectItemIcon)])
        self.assertEqual(n_items_in_design_view, 1)
        # NOW REMOVE DC1
        dc1_ind = self.toolbox.project_item_model.find_item(dc1)
        self.toolbox.ui.treeView_project.selectionModel().select(dc1_ind, QItemSelectionModel.ClearAndSelect)
        with mock.patch.object(spinetoolbox.ui_main.QMessageBox, "exec") as mock_message_box_exec:
            mock_message_box_exec.return_value = QMessageBox.StandardButton.Ok
            self.toolbox.ui.actionRemove.trigger()
        self.assertEqual(self.toolbox.project_item_model.n_items(), 0)  # Check the number of project items
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertEqual(0, len(dags))  # Number of DAGs (DiGraph) objects in project
        items_in_design_view = self.toolbox.ui.graphicsView.scene().items()
        n_items_in_design_view = len([item for item in items_in_design_view if isinstance(item, ProjectItemIcon)])
        self.assertEqual(n_items_in_design_view, 0)

    def test_add_and_remove_specification(self):
        """Tests that adding and removing a specification
        to project works from a valid tool specification file.
        Uses an actual Spine Toolbox Project in order to actually
        test something.

        Note: Test 'project.json' file should not have any
        specifications when this test starts and ends."""
        project_dir = os.path.abspath(os.path.join(os.curdir, "tests", "test_resources", "Project Directory"))
        if not os.path.exists(project_dir):
            self.skipTest("Test project directory '{0}' does not exist".format(project_dir))
            return
        self.assertIsNone(self.toolbox.project())
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.save_project"), mock.patch(
            "spinetoolbox.ui_main.ToolboxUI.update_recent_projects"
        ):
            self.toolbox.open_project(project_dir)
        # Tool spec model must be empty at this point
        self.assertEqual(0, self.toolbox.specification_model.rowCount())
        tool_spec_path = os.path.abspath(os.path.join(os.curdir, "tests", "test_resources", "test_tool_spec.json"))
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
        item_index = self.toolbox.project_item_model.find_item("data_connection")
        self.toolbox.ui.treeView_project.selectionModel().select(item_index, QItemSelectionModel.Select)
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
        self.assertEqual(self.toolbox.project_item_model.n_items(), 1)
        item_index = self.toolbox.project_item_model.find_item("data_connection")
        self.toolbox.ui.treeView_project.selectionModel().select(item_index, QItemSelectionModel.Select)
        self.toolbox.ui.actionCopy.triggered.emit()
        self.toolbox.ui.actionPaste.triggered.emit()
        self.assertEqual(self.toolbox.project_item_model.n_items(), 2)
        new_item_index = self.toolbox.project_item_model.find_item("data_connection (1)")
        self.assertIsNotNone(new_item_index)

    def test_duplicate_project_item(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_dc(self.toolbox.project(), self.toolbox.item_factories, "data_connection")
        self.assertEqual(self.toolbox.project_item_model.n_items(), 1)
        item_index = self.toolbox.project_item_model.find_item("data_connection")
        self.toolbox.ui.treeView_project.selectionModel().select(item_index, QItemSelectionModel.Select)
        with mock.patch("spinetoolbox.project_item.project_item.create_dir"):
            self.toolbox.ui.actionDuplicate.triggered.emit()
        self.assertEqual(self.toolbox.project_item_model.n_items(), 2)
        new_item_index = self.toolbox.project_item_model.find_item("data_connection (1)")
        self.assertIsNotNone(new_item_index)

    def test_persistent_console_requested(self):
        self._temp_dir = TemporaryDirectory()
        create_project(self.toolbox, self._temp_dir.name)
        add_tool(self.toolbox.project(), self.toolbox.item_factories, "tool")
        index = self.toolbox.project_item_model.find_item("tool")
        item = self.toolbox.project_item_model.item(index).project_item
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
        index = self.toolbox.project_item_model.find_item("tool")
        item = self.toolbox.project_item_model.item(index).project_item
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


if __name__ == '__main__':
    unittest.main()
