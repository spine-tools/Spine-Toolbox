#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Database API.
#
# Spine Spine Database API is free software: you can redistribute it and/or modify
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

:author: Manuel Marin <manuelma@kth.se>
:date:   15.8.2018
"""

from sqlalchemy import create_engine, text, Table, MetaData, select, event
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.mysql import TINYINT, DOUBLE
from sqlalchemy.engine import Engine
from .exception import SpineDBAPIError

OBJECT_CLASS_NAMES = (
    'unittemplate',
    'unit',
    'commodity',
    'archetype',
    'node',
    'grid',
    'normalized',
    'absolute',
    'flow',
    'influx',
    'time',
    'arc',
    'simulation_settings',
    'hidden_settings',
    'constraint',
    'variable',
    'objective_term',
    'group',
    'alternative'
)

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

def copy_database(dest_url, source_url):
    """Copy the database from source_url into dest_url,
    by reflecting all tables.
    """
    source_engine = create_engine(source_url)
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


def create_new_spine_database(db_url):
    """Create a new Spine database in the given database url."""
    try:
        engine = create_engine(db_url)
    except DatabaseError as e:
        raise SpineDBAPIError("Could not connect to '{}': {}".format(self.db_url, e.orig.args))
    sql_list = list()
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
    sql_list.append(sql)
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
    sql_list.append(sql)
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
    sql_list.append(sql)
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
    sql_list.append(sql)
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
            FOREIGN KEY(class_id) REFERENCES object_class (id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(category_id) REFERENCES object_category (id),
            UNIQUE(name)
        );
    """
    sql_list.append(sql)
    sql = """
        CREATE TABLE IF NOT EXISTS relationship_class (
            id INTEGER NOT NULL,
            dimension INTEGER NOT NULL,
            object_class_id INTEGER NOT NULL,
            name VARCHAR(155) NOT NULL,
            hidden INTEGER DEFAULT '0',
            commit_id INTEGER,
            PRIMARY KEY (id, dimension),
            FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            FOREIGN KEY(object_class_id) REFERENCES object_class (id) ON UPDATE CASCADE
        );
    """
    sql_list.append(sql)
    sql = """
        CREATE TABLE IF NOT EXISTS relationship (
            id INTEGER NOT NULL,
            dimension INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            name VARCHAR(155) NOT NULL,
            commit_id INTEGER,
            PRIMARY KEY (id, dimension),
            FOREIGN KEY(commit_id) REFERENCES "commit" (id),
            FOREIGN KEY(class_id, dimension) REFERENCES relationship_class (id, dimension) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(object_id) REFERENCES object (id) ON UPDATE CASCADE
        );
    """
    sql_list.append(sql)
    sql = """
        CREATE TABLE IF NOT EXISTS parameter (
            id INTEGER NOT NULL,
            name VARCHAR(155) NOT NULL,
            description VARCHAR(155) DEFAULT NULL,
            data_type VARCHAR(155) DEFAULT 'NUMERIC',
            relationship_class_id INTEGER DEFAULT NULL,
            dummy_relationship_class_dimmension INTEGER DEFAULT '1',
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
            FOREIGN KEY(relationship_class_id, dummy_relationship_class_dimmension)
                REFERENCES relationship_class (id, dimension) ON DELETE CASCADE ON UPDATE CASCADE,
            CHECK (`relationship_class_id` IS NOT NULL OR `object_class_id` IS NOT NULL),
            UNIQUE(name)
        );
    """
    sql_list.append(sql)
    sql = """
        CREATE TABLE IF NOT EXISTS parameter_value (
            id INTEGER NOT NULL,
            parameter_id INTEGER NOT NULL,
            relationship_id INTEGER DEFAULT NULL,
            dummy_relationship_dimmension INTEGER DEFAULT '1',
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
            FOREIGN KEY(relationship_id, dummy_relationship_dimmension)
                REFERENCES relationship (id, dimension) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(parameter_id) REFERENCES parameter (id) ON DELETE CASCADE ON UPDATE CASCADE,
            CHECK (`relationship_id` IS NOT NULL OR `object_id` IS NOT NULL)
        );
    """
    sql_list.append(sql)
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
    sql_list.append(sql)
    sql = """
        CREATE TRIGGER after_object_class_delete
            AFTER DELETE ON object_class
            FOR EACH ROW
        BEGIN
            DELETE FROM relationship_class
            WHERE id IN (
                SELECT id FROM relationship_class
                WHERE object_class_id = OLD.id
            );
        END
    """
    sql_list.append(sql)
    sql = """
        CREATE TRIGGER after_object_delete
            AFTER DELETE ON object
            FOR EACH ROW
        BEGIN
            DELETE FROM relationship
            WHERE id IN (
                SELECT id FROM relationship
                WHERE object_id = OLD.id
            );
        END
    """
    sql_list.append(sql)
    try:
        for sql in sql_list:
            engine.execute(text(sql))
        return engine
    except DatabaseError as e:
        raise SpineDBAPIError("Engine failed to execute creation script {}".format(e.orig.args))
