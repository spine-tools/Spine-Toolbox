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
General helper functions and classes.

:authors: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   10.1.2018
"""

import logging
import datetime
import os
import time
import shutil
import glob
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QCursor
from config import DEFAULT_PROJECT_DIR
from sqlalchemy import text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.mysql import TINYINT, DOUBLE
from sqlalchemy.engine import Engine
from sqlalchemy import event

# TODO: check if this is the right place for this
@compiles(TINYINT, 'sqlite')
def compile_TINYINT_mysql_sqlite(element, compiler, **kw):
    """ Handles mysql TINYINT datatype as INTEGER in sqlite """
    return compiler.visit_INTEGER(element, **kw)


@compiles(DOUBLE, 'sqlite')
def compile_DOUBLE_mysql_sqlite(element, compiler, **kw):
    """ Handles mysql DOUBLE datatype as REAL in sqlite """
    return compiler.visit_REAL(element, **kw)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def busy_effect(func):
    """ Decorator to change the mouse cursor to 'busy' while a function is processed.

    Args:
        func: Decorated function.
    """
    def new_function(*args, **kwargs):
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception("Error {}".format(e.args[0]))
            raise e
        finally:
            # noinspection PyArgumentList
            QApplication.restoreOverrideCursor()
    return new_function


def project_dir(configs=None):
    """Returns current project directory.

    Args:
        configs (ConfigurationParser): Configuration parser object. Default value is for unit tests.
    """
    if not configs:
        return DEFAULT_PROJECT_DIR
    proj_dir = configs.get('settings', 'project_directory')
    if not proj_dir:
        return DEFAULT_PROJECT_DIR
    else:
        return proj_dir


def short_name_reserved(short_name, project_model):
    """Check if folder name derived from the name of the given item is in use.

    Args:
        short_name (str): Item short name
        project_model (QStandardItemModel): Project model containing items

    Returns:
        True if short name is taken, False if it is available.
    """
    # short_name = name.lower().replace(' ', '_')
    # Traverse all items in project model
    top_level_items = project_model.findItems('*', Qt.MatchWildcard, column=0)
    for top_level_item in top_level_items:
        if top_level_item.hasChildren():
            n_children = top_level_item.rowCount()
            for i in range(n_children):
                child = top_level_item.child(i, 0)
                child_name = child.data(Qt.UserRole).name
                child_short_name = child.data(Qt.UserRole).short_name
                if short_name == child_short_name:
                    logging.error(
                        "Item {0} short name matches new short name {1}".format(child_name, short_name))
                    return True
    return False


def get_datetime(configs):
    """Returns date and time string for appending into Event Log messages."""
    show_date = configs.getboolean("settings", "datetime")
    if show_date:
        t = datetime.datetime.now()
        return "[{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}] ".format(t.day, t.month, t.year, t.hour, t.minute, t.second)
    else:
        return ""


def create_dir(base_path, folder='', verbosity=False):
    """Create (input/output) directories recursively.

    Args:
        base_path (str): Absolute path to wanted dir
        folder (str): (Optional) Folder name. Usually short name of item.
        verbosity (bool): True prints a message that tells if the directory already existed or if it was created.

    Returns:
        True if directory already exists or if it was created successfully.

    Raises:
        OSError if operation failed.
    """
    directory = os.path.join(base_path, folder)
    if os.path.exists(directory):
        if verbosity:
            logging.debug("Directory found: {0}".format(directory))
        return True
    else:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            raise
        if verbosity:
            logging.debug("Directory created: {0}".format(directory))
        return True


def create_output_dir_timestamp():
    """ Creates a new timestamp string that is used as Tool output
    directory.

    Returns:
        Timestamp string or empty string if failed.
    """
    try:
        # Create timestamp
        stamp = datetime.datetime.fromtimestamp(time.time())
    except OverflowError:
        logging.error('Timestamp out of range.')
        return ''
    extension = stamp.strftime('%Y-%m-%dT%H.%M.%S')
    return extension


@busy_effect
def copy_files(src_dir, dst_dir, includes=None, excludes=None):
    """Method for copying files. Does not copy folders.

    Args:
        src_dir (str): Source directory
        dst_dir (str): Destination directory
        includes (list): Included files (wildcards accepted)
        excludes (list): Excluded files (wildcards accepted)

    Returns:
        count (int): Number of files copied
    """
    if not includes:
        includes = ['*']
    if not excludes:
        excludes = []
    src_files = []
    for pattern in includes:
        src_files += glob.glob(os.path.join(src_dir, pattern))
    exclude_files = []
    for pattern in excludes:
        exclude_files += glob.glob(os.path.join(src_dir, pattern))
    count = 0
    for filename in src_files:
        if os.path.isdir(filename):
            continue
        if filename not in exclude_files:
            shutil.copy(filename, dst_dir)
            count += 1
    return count


@busy_effect
def erase_dir(path, verbosity=False):
    """Delete directory and all its contents without prompt.

    Args:
        path (str): Path to directory
        verbosity (bool): Print logging messages or not
    """
    if not os.path.exists(path):
        if verbosity:
            logging.debug("Path does not exist: {}".format(path))
        return False
    if verbosity:
        logging.debug("Deleting directory {0}".format(path))
    try:
        shutil.rmtree(path)
    except OSError:
        raise
    return True

def create_fresh_Spine_database(engine):
    """Create a fresh Spine database in the given engine."""
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
            FOREIGN KEY(child_object_class_id) REFERENCES object_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(parent_object_class_id) REFERENCES object_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(parent_relationship_class_id) REFERENCES relationship_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
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
            FOREIGN KEY(class_id) REFERENCES relationship_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(child_object_id) REFERENCES object (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(parent_object_id) REFERENCES object (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(parent_relationship_id) REFERENCES relationship (id) ON DELETE CASCADE ON UPDATE CASCADE,
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
            FOREIGN KEY(object_class_id) REFERENCES object_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(relationship_class_id) REFERENCES relationship_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
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
            FOREIGN KEY(object_id) REFERENCES object (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(relationship_id) REFERENCES relationship (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(parameter_id) REFERENCES parameter (id) ON DELETE CASCADE ON UPDATE CASCADE,
            CHECK (`relationship_id` IS NOT NULL OR `object_id` IS NOT NULL)
        );
    """
    engine.execute(text(sql))
    sql = """
        INSERT OR IGNORE INTO `object_class` (`name`, `description`, `category_id`, `display_order`, `display_icon`, `hidden`, `commit_id`) VALUES
        ('unittemplate', 'Template for a generic unit', NULL, 1, NULL, 0, NULL),
        ('unit', 'Unit class', NULL, 2, NULL, 0, NULL),
        ('commodity', 'Commodity class', NULL, 3, NULL, 0, NULL),
        ('archetype', 'Archetype class', NULL, 4, NULL, 0, NULL),
        ('node', 'Node class', NULL, 5, NULL, 0, NULL),
        ('grid', 'Grid class', NULL, 6, NULL, 0, NULL),
        ('normalized', 'Normalized class', NULL, 7, NULL, 0, NULL),
        ('absolute', 'Absolute class', NULL, 8, NULL, 0, NULL),
        ('flow', 'Flow class', NULL, 9, NULL, 0, NULL),
        ('influx', 'Influx class', NULL, 10, NULL, 0, NULL),
        ('time', 'Time class', NULL, 11, NULL, 0, NULL),
        ('arc', 'Arc class', NULL, 12, NULL, 0, NULL),
        ('simulation_settings', 'Simulation settings class', NULL, 13, NULL, 0, NULL),
        ('hidden_settings', 'Hidden settings class', NULL, 14, NULL, 1, NULL),
        ('constraint', 'Constraint class', NULL, 15, NULL, 0, NULL),
        ('variable', 'Variable class', NULL, 16, NULL, 0, NULL),
        ('objective_term', 'Objective term class', NULL, 17, NULL, 0, NULL),
        ('group', 'Group class', NULL, 18, NULL, 0, NULL),
        ('alternative', 'Alternative class', NULL, 19, NULL, 0, NULL);
    """
    engine.execute(text(sql))

# NOTE: no longer needed. The cause for dialogs to freeze was calling setLine()
# within paint() in QLineItems back in the days. All this is fixed now.
# def blocking_updates(view, func):
#     """Wrapper to block updates to a view while calling a function.
#     Fix bug on Linux which causes QFileDialogs to become unresponsive
#     when there is visible items on QGraphicsView.
#     """
#     def new_function(*args, **kwargs):
#         view.setUpdatesEnabled(False)
#         try:
#             return func(*args, **kwargs)
#         except Exception as e:
#             logging.exception("Error {}".format(e.args[0]))
#             raise e
#         finally:
#             view.setUpdatesEnabled(True)
#     return new_function
