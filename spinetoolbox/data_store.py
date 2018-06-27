#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Module for data store class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   18.12.2017
"""

import os
import getpass
import logging
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Slot, QUrl, QFileSystemWatcher
from PySide2.QtWidgets import QInputDialog
from metaobject import MetaObject
from widgets.data_store_subwindow_widget import DataStoreWidget
from widgets.data_store_widget import DataStoreForm
from widgets.custom_menus import AddDbReferencePopupMenu
from widgets.add_db_reference_widget import AddDbReferenceWidget
from graphics_items import DataStoreImage
from helpers import create_dir, busy_effect
from config import APPLICATION_PATH
from sqlalchemy import create_engine, Table, MetaData, select, text
from sqlalchemy.exc import DatabaseError


class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        references (list): List of references (for now it's only database references)
    """
    def __init__(self, parent, name, description, project, references, x, y):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Store"
        self.item_category = "Data Stores"
        self._project = project
        self._widget = DataStoreWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self.data_dir_watcher = QFileSystemWatcher(self)
        # Make directory for Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.references = references
        try:
            create_dir(self.data_dir)
            self.data_dir_watcher.addPath(self.data_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        self.databases = list()  # name of imported databases NOTE: Not in use at the moment
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)
        self.add_db_reference_form = None
        self.data_store_form = None
        self._graphics_item = DataStoreImage(self._parent, x - 35, y - 35, 70, 70, self.name)
        self.connect_signals()
        self.add_db_reference_popup_menu = AddDbReferencePopupMenu(self)
        self._widget.ui.toolButton_plus.setMenu(self.add_db_reference_popup_menu)
        self._widget.ui.toolButton_plus.setStyleSheet('QToolButton::menu-indicator { image: none; }')

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.listView_data.doubleClicked.connect(self.open_data_file)
        self._widget.ui.listView_references.doubleClicked.connect(self.open_reference)
        self._widget.ui.toolButton_add.clicked.connect(self.import_references)
        self.data_dir_watcher.directoryChanged.connect(self.refresh)

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this Data Store on the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    @Slot(name="open_directory")
    def open_directory(self):
        """Open file explorer in this Data Store's data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._parent.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(name="show_add_db_reference_form")
    def show_add_db_reference_form(self):
        """Show the form for querying database connection options."""
        self.add_db_reference_form = AddDbReferenceWidget(self._parent, self)
        self.add_db_reference_form.show()

    def add_reference(self, reference):
        """Add reference to reference list and populate widget's reference list."""
        self.references.append(reference)
        self._widget.populate_reference_list(self.references)

    @Slot(name="remove_references")
    def remove_references(self):
        """Remove selected references from reference list.
        Removes all references if nothing is selected.
        """
        indexes = self._widget.ui.listView_references.selectedIndexes()
        if not indexes:  # Nothing selected
            self.references.clear()
            self._parent.msg.emit("All references removed")
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.references.pop(row)
            self._parent.msg.emit("Selected references removed")
        self._widget.populate_reference_list(self.references)

    @Slot(name="import_references")
    def import_references(self):
        """Import data from selected items in reference list into local SQLite file.
        If no item is selected then import all of them.
        """
        if not self.references:
            self._parent.msg_warning.emit("No data to import")
            return
        indexes = self._widget.ui.listView_references.selectedIndexes()
        if not indexes:  # Nothing selected, import all
            references_to_import = self.references
        else:
            references_to_import = [self.references[ind.row()] for ind in indexes]
        for reference in references_to_import:
            try:
                self.import_reference(reference)
            except Exception as e:
                self._parent.msg_error.emit("Import failed: {}".format(e))
                continue
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)

    @busy_effect
    def import_reference(self, reference):
        """Import reference database into local SQLite file"""
        database = reference['database']
        self._parent.msg.emit("Importing database <b>{0}</b>".format(database))
        # Source
        source_url = reference['url']
        source_engine = create_engine(source_url)
        # Destination
        dest_filename = os.path.join(self.data_dir, database + ".sqlite")
        try:
            os.remove(dest_filename)
        except OSError:
            pass
        dest_url = "sqlite:///" + dest_filename
        dest_engine = create_engine(dest_url)  # , echo=True)
        # Meta reflection
        meta = MetaData()
        meta.reflect(source_engine)
        meta.create_all(dest_engine)
        # Copy tables
        source_meta = MetaData(bind=source_engine)
        dest_meta = MetaData(bind=dest_engine)
        for t in meta.sorted_tables:
            source_table = Table(t, source_meta, autoload=True)
            dest_table = Table(t, dest_meta, autoload=True)
            sel = select([source_table])
            result = source_engine.execute(sel)
            values = [row for row in result]
            if values:
                ins = dest_table.insert()
                dest_engine.execute(ins, values)
        self.databases.append(database)

    @busy_effect
    @Slot("QModelIndex", name="open_data_file")
    def open_data_file(self, index):
        """Open file in spine data explorer."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            data_file = self.data_files()[index.row()]
            data_file_path = os.path.join(self.data_dir, data_file)
            engine = create_engine("sqlite:///" + data_file_path)
            # check if SQLite database
            try:
                engine.execute('pragma quick_check;')
            except DatabaseError as e:
                self._parent.msg_error.emit("Could not open <b>{}</b> as SQLite database: {}"
                                            .format(data_file, e.orig.args))
                return
            # check if locked
            try:
                engine.execute('BEGIN IMMEDIATE')
            except DatabaseError as e:
                self._parent.msg_error.emit("Could not open <b>{}</b>: {}".format(data_file, e.orig.args))
                return
            database = data_file
            username = getpass.getuser()
            self.data_store_form = DataStoreForm(self._parent, self, engine, database, username)
            self.data_store_form.show()

    @busy_effect
    @Slot("QModelIndex", name="open_reference")
    def open_reference(self, index):
        """Open reference in spine data explorer."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            reference = self.references[index.row()]
            db_url = reference['url']
            database = reference['database']
            username = reference['username']
            engine = create_engine(db_url)
            try:
                engine.connect()
            except DatabaseError as e:
                self._parent.msg_error.emit("Could not connect to <b>{}</b>: {}".format(db_url, e.orig.args))
                return
            self.data_store_form = DataStoreForm(self._parent, self, engine, database, username)
            self.data_store_form.show()

    def data_references(self):
        """Returns a list of connection strings that are in this item as references (self.references)."""
        return self.references

    def data_files(self):
        """Return a list of files in the data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    @Slot(name="refresh")
    def refresh(self):
        """Refresh data files QTreeView.
        NOTE: Might lead to performance issues."""
        d = self.data_files()
        self._widget.populate_data_list(d)

    def find_file(self, fname, visited_items):
        """Search for filename in data and return the path if found."""
        logging.debug("Looking for file {0} in DS {1}.".format(fname, self.name))
        if self in visited_items:
            logging.debug("Infinite loop detected while visiting {0}.".format(self.name))
            return None
        if fname in self.data_files():
            logging.debug("{0} found in DS {1}".format(fname, self.name))
            self._parent.msg.emit("\t<b>{0}</b> found in DS <b>{1}</b>".format(fname, self.name))
            path = os.path.join(self.data_dir, fname)
            return path
        visited_items.append(self)
        for input_item in self._parent.connection_model.input_items(self.name):
            # Find item from project model
            found_item = self._parent.project_item_model.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._parent.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item_data = found_item.data(Qt.UserRole)
            if item_data.item_type in ["Data Store", "Data Connection"]:
                path = item_data.find_file(fname, visited_items)
                if path is not None:
                    return path
        return None

    @Slot(name="add_new_spine_reference")
    def add_new_spine_reference(self):
        """Add reference to a new Spine empty database."""
        answer = QInputDialog.getText(self._parent, "Add new Spine SQLite database", "Database name:")
        database = answer[0]
        if not database:
            return
        filename = os.path.join(APPLICATION_PATH, "Spine.sqlite")
        # Wipe out file. This is better for debug phase, but later we can reuse the same one
        try:
            os.remove(filename)
        except OSError:
            pass
        url = "sqlite:///" + filename
        engine = create_engine(url)
        sql = """
            CREATE TABLE IF NOT EXISTS "commit" (
            	id INTEGER NOT NULL,
            	comment VARCHAR(255) NOT NULL,
            	date DATETIME NOT NULL,
            	user VARCHAR(45),
            	PRIMARY KEY (id),
            	UNIQUE (id)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS object_class_category (
            	id INTEGER NOT NULL,
            	name VARCHAR(255) NOT NULL,
            	description VARCHAR(255) DEFAULT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS object_class (
            	id INTEGER NOT NULL,
            	name VARCHAR(255) NOT NULL,
            	description VARCHAR(255) DEFAULT NULL,
            	category_id INTEGER DEFAULT NULL,
            	display_order INTEGER DEFAULT '99',
            	display_icon INTEGER DEFAULT NULL,
            	hidden INTEGER DEFAULT '0',
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            	FOREIGN KEY(category_id) REFERENCES object_class_category (id),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS object_category (
            	id INTEGER NOT NULL,
            	object_class_id INTEGER NOT NULL,
            	name VARCHAR(255) NOT NULL,
            	description VARCHAR(255) DEFAULT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(object_class_id) REFERENCES object_class (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS object (
            	id INTEGER NOT NULL,
            	class_id INTEGER NOT NULL,
            	name VARCHAR(255) NOT NULL,
            	description VARCHAR(255) DEFAULT NULL,
            	category_id INTEGER DEFAULT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            	FOREIGN KEY(class_id) REFERENCES object_class (id),
            	FOREIGN KEY(category_id) REFERENCES object_category (id),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS relationship_class (
            	id INTEGER NOT NULL,
            	name VARCHAR(155) NOT NULL,
            	parent_relationship_class_id INTEGER DEFAULT NULL,
            	parent_object_class_id INTEGER DEFAULT NULL,
            	child_object_class_id INTEGER NOT NULL,
            	inheritance VARCHAR(155) DEFAULT NULL,
            	hidden INTEGER DEFAULT '0',
            	type INTEGER DEFAULT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            	FOREIGN KEY(child_object_class_id) REFERENCES object_class (id),
            	FOREIGN KEY(parent_object_class_id) REFERENCES object_class (id),
            	FOREIGN KEY(parent_relationship_class_id) REFERENCES relationship_class (id),
            	CHECK (`parent_relationship_class_id` IS NOT NULL OR `parent_object_class_id` IS NOT NULL),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS relationship (
            	id INTEGER NOT NULL,
            	class_id INTEGER NOT NULL,
            	name VARCHAR(155) NOT NULL,
            	parent_relationship_id INTEGER DEFAULT NULL,
            	parent_object_id INTEGER DEFAULT NULL,
            	child_object_id INTEGER NOT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            	FOREIGN KEY(class_id) REFERENCES relationship_class (id),
            	FOREIGN KEY(child_object_id) REFERENCES object (id),
            	FOREIGN KEY(parent_object_id) REFERENCES object (id),
            	FOREIGN KEY(parent_relationship_id) REFERENCES relationship (id),
            	CHECK (`parent_relationship_id` IS NOT NULL OR `parent_object_id` IS NOT NULL),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS parameter (
            	id INTEGER NOT NULL,
            	name VARCHAR(155) NOT NULL,
            	description VARCHAR(155) DEFAULT NULL,
            	data_type VARCHAR(155) DEFAULT 'NUMERIC',
            	relationship_class_id INTEGER DEFAULT NULL,
            	object_class_id INTEGER DEFAULT NULL,
            	can_have_time_series INTEGER DEFAULT '0',
            	can_have_time_pattern INTEGER DEFAULT '1',
            	can_be_stochastic INTEGER DEFAULT '0',
            	default_value VARCHAR(155) DEFAULT '0',
            	is_mandatory INTEGER DEFAULT '0',
            	precision INTEGER DEFAULT '2',
            	unit VARCHAR(155) DEFAULT NULL,
            	minimum_value FLOAT DEFAULT NULL,
            	maximum_value FLOAT DEFAULT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            	FOREIGN KEY(object_class_id) REFERENCES object_class (id),
            	FOREIGN KEY(relationship_class_id) REFERENCES relationship_class (id),
            	CHECK (`relationship_class_id` IS NOT NULL OR `object_class_id` IS NOT NULL),
                UNIQUE(name)
            );
        """
        engine.execute(text(sql))
        sql = """
            CREATE TABLE IF NOT EXISTS parameter_value (
            	id INTEGER NOT NULL,
            	parameter_id INTEGER NOT NULL,
            	relationship_id INTEGER DEFAULT NULL,
            	object_id INTEGER DEFAULT NULL,
            	"index" INTEGER DEFAULT '1',
            	value VARCHAR(155) DEFAULT NULL,
            	json VARCHAR(255) DEFAULT NULL,
            	expression VARCHAR(255) DEFAULT NULL,
            	time_pattern VARCHAR(155) DEFAULT NULL,
            	time_series_id VARCHAR(155) DEFAULT NULL,
            	stochastic_model_id VARCHAR(155) DEFAULT NULL,
            	commit_id INTEGER,
            	PRIMARY KEY (id),
            	FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            	FOREIGN KEY(object_id) REFERENCES object (id),
            	FOREIGN KEY(relationship_id) REFERENCES relationship (id),
            	FOREIGN KEY(parameter_id) REFERENCES parameter (id),
            	CHECK (`relationship_id` IS NOT NULL OR `object_id` IS NOT NULL)
            );
        """
        engine.execute(text(sql))
        sql = """
            INSERT OR IGNORE INTO `object_class` (`name`, `description`, `category_id`, `display_order`, `display_icon`, `hidden`, `commit_id`) VALUES
            ('unittemplate', 'Template for a generic unit', 1, 1, NULL, 0, NULL),
            ('unit', 'Unit class', 1, 2, NULL, 0, NULL),
            ('commodity', 'Commodity class', 1, 3, NULL, 0, NULL),
            ('archetype', 'Archetype class', 1, 4, NULL, 0, NULL),
            ('node', 'Node class', 1, 5, NULL, 0, NULL),
            ('grid', 'Grid class', 1, 6, NULL, 0, NULL),
            ('normalized', 'Normalized class', 1, 7, NULL, 0, NULL),
            ('absolute', 'Absolute class', 1, 8, NULL, 0, NULL),
            ('flow', 'Flow class', 1, 9, NULL, 0, NULL),
            ('influx', 'Influx class', 1, 10, NULL, 0, NULL),
            ('time', 'Time class', 1, 11, NULL, 0, NULL),
            ('arc', 'Arc class', 1, 12, NULL, 0, NULL),
            ('simulation_settings', 'Simulation settings class', 2, 13, NULL, 0, NULL),
            ('hidden_settings', 'Hidden settings class', 3, 14, NULL, 1, NULL),
            ('constraint', 'Constraint class', 1, 15, NULL, 0, NULL),
            ('variable', 'Variable class', 1, 16, NULL, 0, NULL),
            ('objective_term', 'Objective term class', 1, 17, NULL, 0, NULL),
            ('group', 'Group class', 1, 18, NULL, 0, NULL),
            ('alternative', 'Alternative class', 1, 19, NULL, 0, NULL);
        """
        engine.execute(text(sql))
        reference = {
            'database': database,
            'username': getpass.getuser(),
            'url': url
        }
        self.add_reference(reference)
