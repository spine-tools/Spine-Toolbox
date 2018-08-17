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
Classes to handle the Spine database object relational mapping.

:author: Manuel Marin <manuelma@kth.se>
:date:   11.8.2018
"""

from sqlalchemy import create_engine, false, distinct, func
from sqlalchemy.ext.automap import automap_base, generate_relationship
from sqlalchemy.orm import interfaces, Session, aliased
from sqlalchemy.util import KeyedTuple
from sqlalchemy.exc import NoSuchTableError, DBAPIError, DatabaseError
from .exception import SpineDBAPIError, TableNotFoundError, RecordNotFoundError, ParameterValueError
from datetime import datetime, timezone

# TODO: Consider return lists of dict (with _asdict()) rather than queries,
# to better support platforms that cannot handle queries efficiently (such as Julia)
# TODO: At some point DatabaseMapping attributes such as session, engine, and all the tables should be made 'private'
# so as to prevent hacking into the database.
# TODO: SELECT queries should also be checked for errors


class DatabaseMapping(object):
    """A class to manipulate the Spine database object relational mapping.

    Attributes:
        db_url (str): The database url formatted according to sqlalchemy rules
        username (str): The user name
    """
    def __init__(self, db_url, username=None):
        """Initialize class."""
        self.db_url = db_url
        self.username = username
        self.engine = None
        self.session = None
        self.commit = None
        self.transactions = list()
        self.Base = None
        self.ObjectClass = None
        self.Object = None
        self.RelationshipClass = None
        self.Relationship = None
        self.Parameter = None
        self.ParameterValue = None
        self.Commit = None
        self.create_engine_and_session()
        self.init_base()

    def create_engine_and_session(self):
        try:
            self.engine = create_engine(self.db_url)
            self.engine.connect()
        except DatabaseError as e:
            raise SpineDBAPIError("Could not connect to '{}': {}".format(self.db_url, e.orig.args))
        if self.db_url.startswith('sqlite'):
            try:
                self.engine.execute('pragma quick_check;')
            except DatabaseError as e:
                msg = "Could not open '{}' as SQLite database: {}".format(self.db_url, e.orig.args)
                raise SpineDBAPIError(msg)
            try:
                self.engine.execute('BEGIN IMMEDIATE')
            except DatabaseError as e:
                msg = "Could not open '{}', seems to be locked: {}".format(self.db_url, e.orig.args)
                raise SpineDBAPIError(msg)
        self.session = Session(self.engine)

    def init_base(self):
        """Create base and reflect tables."""
        def _gen_relationship(base, direction, return_fn, attrname, local_cls, referred_cls, **kw):
            if direction is interfaces.ONETOMANY:
                kw['cascade'] = 'all, delete-orphan'
                kw['passive_deletes'] = True
            return generate_relationship(base, direction, return_fn, attrname, local_cls, referred_cls, **kw)

        try:
            self.Base = automap_base()
            self.Base.prepare(self.engine, reflect=True, generate_relationship=_gen_relationship)
            self.ObjectClass = self.Base.classes.object_class
            self.Object = self.Base.classes.object
            self.RelationshipClass = self.Base.classes.relationship_class
            self.Relationship = self.Base.classes.relationship
            self.Parameter = self.Base.classes.parameter
            self.ParameterValue = self.Base.classes.parameter_value
            self.Commit = self.Base.classes.commit
        except NoSuchTableError as table:
            raise TableNotFoundError(table)

    def new_commit(self):
        """Add row to commit table"""
        comment = 'In progress...'
        user = self.username
        date = datetime.now(timezone.utc)
        self.commit = self.Commit(comment=comment, date=date, user=user)
        try:
            self.session.add(self.commit)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting new commit: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def commit_session(self, comment):
        """Commit changes to source database."""
        if not self.session:
            raise SpineDBAPIError("No session!")
        if not self.commit.id:
            raise SpineDBAPIError("No commit id!")
        try:
            self.commit.comment = comment
            self.commit.date = datetime.now(timezone.utc)
            for i in reversed(range(len(self.transactions))):
                self.session.commit()
                del self.transactions[i]
            self.session.commit()  # also commit main transaction
        except DBAPIError as e:
            self.commit.comment = None
            self.commit.date = None
            msg = "DBAPIError while commiting changes: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)
        self.new_commit()

    def rollback_session(self):
        if not self.session:
            raise SpineDBAPIError("No session!")
        try:
            for i in reversed(range(len(self.transactions))):
                self.session.rollback()
                del self.transactions[i]
            self.session.rollback()  # also rollback main transaction
        except DBAPIError:
            msg = "DBAPIError while rolling back changes: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)
        self.new_commit()

    def single_object_class(self, id=None, name=None):
        """Return a single object class given the id or name or None if not found."""
        if not id and not name:
            return self.empty_list()
        qry = self.session.query(
            self.ObjectClass.id,
            self.ObjectClass.name,
            self.ObjectClass.display_order,
        )
        if id:
            return qry.filter_by(id=id)
        if name:
            return qry.filter_by(name=name)

    def single_object(self, id=None, name=None):
        """Return a single object given the id or None if not found."""
        if not id and not name:
            return self.empty_list()
        qry = self.session.query(
            self.Object.id,
            self.Object.class_id,
            self.Object.name
        )
        if id:
            return qry.filter_by(id=id)
        if name:
            return qry.filter_by(name=name)

    def single_wide_relationship_class(self, id=None, name=None):
        """Return a single relationship class in wide format given the id or None if not found."""
        if not id and not name:
            return self.empty_list()
        qry = self.session.query(
            self.RelationshipClass.id,
            func.group_concat(self.RelationshipClass.object_class_id).label('object_class_id_list'),
            func.group_concat(self.ObjectClass.name).label('object_class_name_list'),
            self.RelationshipClass.name
        ).filter(self.RelationshipClass.object_class_id == self.ObjectClass.id).\
        group_by(self.RelationshipClass.id)
        if id:
            return qry.filter_by(id=id)
        if name:
            return qry.filter_by(name=name)

    def single_wide_relationship(self, id=None, name=None):
        """Return a single relationship in wide format given the id or None if not found."""
        if not id and not name:
            return self.empty_list()
        qry = self.session.query(
            self.Relationship.id,
            func.group_concat(self.Relationship.object_id).label('object_id_list'),
            func.group_concat(self.Object.name).label('object_name_list'),
            self.Relationship.name,
            self.Relationship.class_id
        ).filter(self.Relationship.object_id == self.Object.id).\
        group_by(self.Relationship.id)
        if id:
            return qry.filter_by(id=id)
        if name:
            return qry.filter_by(name=name)

    def single_relationship(self, id):
        """Return a single relationship given the id or None if not found."""
        return self.session.query(
            self.Relationship.id,
            self.Relationship.name,
            self.Relationship.class_id,
            self.Relationship.parent_relationship_id,
            self.Relationship.parent_object_id,
            self.Relationship.child_object_id
        ).filter_by(id=id).one_or_none()

    def object_class_list(self):
        """Return object classes ordered by display order."""
        return self.session.query(
            self.ObjectClass.id,
            self.ObjectClass.name,
            self.ObjectClass.display_order,
        ).order_by(self.ObjectClass.display_order)

    def object_list(self, class_id=None):
        """Return objects, optionally filtered by class id."""
        qry = self.session.query(
            self.Object.id,
            self.Object.class_id,
            self.Object.name
        )
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        return qry

    def distinct_relationship_class_id_list(self, object_class_id=None):
        """Return distinct relationship class ids optionally filtered by object class id."""
        qry = self.session.query(self.RelationshipClass.id).distinct()
        if object_class_id:
            qry = qry.filter_by(object_class_id=object_class_id)
        return qry

    def relationship_class_list(self, id=None):
        """Return all relationship classes optionally filtered by id."""
        qry = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.dimension,
            self.RelationshipClass.object_class_id,
            self.RelationshipClass.name
        ).order_by(self.RelationshipClass.id, self.RelationshipClass.dimension)
        if id:
            qry = qry.filter_by(id=id)
        return qry

    def wide_relationship_class_list(self, object_class_id=None):
        """Return list of relationship classes in wide format involving a given object class."""
        distinct_relationship_class_id_list = self.distinct_relationship_class_id_list(
            object_class_id=object_class_id)
        return self.session.query(
            self.RelationshipClass.id,
            func.group_concat(self.RelationshipClass.object_class_id).label('object_class_id_list'),
            func.group_concat(self.ObjectClass.name).label('object_class_name_list'),
            self.RelationshipClass.name
        ).filter(self.RelationshipClass.object_class_id == self.ObjectClass.id).\
        filter(self.RelationshipClass.id.in_(distinct_relationship_class_id_list)).\
        group_by(self.RelationshipClass.id)

    def distinct_relationship_id_list(self, class_id=None, object_id=None):
        """Return distinct relationship ids optionally filtered by class id and object id."""
        qry = self.session.query(self.Relationship.id).distinct()
        if class_id:
            qry = qry.filter_by(class_id=class_id)
        if object_id:
            qry = qry.filter_by(object_id=object_id)
        return qry

    def relationship_list(self, id=None):
        """Return relationships, optionally filtered by id."""
        qry = self.session.query(
            self.Relationship.id,
            self.Relationship.dimension,
            self.Relationship.object_id,
            self.Relationship.class_id,
            self.Relationship.name
        ).order_by(self.Relationship.id, self.Relationship.dimension)
        if id:
            qry = qry.filter_by(id=id)
        return qry

    def wide_relationship_list(self, class_id=None, object_id=None):
        """Return list of relationships in wide format involving a given relationship class and object."""
        wide_relationship_list = list()
        distinct_relationship_id_list = self.distinct_relationship_id_list(
            class_id=class_id,
            object_id=object_id)
        return self.session.query(
            self.Relationship.id,
            func.group_concat(self.Relationship.object_id).label('object_id_list'),
            func.group_concat(self.Object.name).label('object_name_list'),
            self.Relationship.name,
            self.Relationship.class_id
        ).filter(self.Relationship.object_id == self.Object.id).\
        filter(self.Relationship.id.in_(distinct_relationship_id_list)).\
        group_by(self.Relationship.id)

    def parameter_list(self):
        """Return parameters."""
        return self.session.query(
            self.Parameter.id,
            self.Parameter.name,
            self.Parameter.relationship_class_id,
            self.Parameter.object_class_id,
            self.Parameter.can_have_time_series,
            self.Parameter.can_have_time_pattern,
            self.Parameter.can_be_stochastic,
            self.Parameter.default_value,
            self.Parameter.is_mandatory,
            self.Parameter.precision,
            self.Parameter.minimum_value,
            self.Parameter.maximum_value)

    def unvalued_object_parameter_list(self, object_id):
        """Return parameters that do not have a value for given object."""
        object_ = self.single_object(object_id).one_or_none()
        if not object_:
            return self.empty_list()
        valued_parameter_ids = self.session.query(self.ParameterValue.parameter_id).\
            filter_by(object_id=object_id)
        return self.parameter_list().filter_by(object_class_id=object_.class_id).\
            filter(~self.Parameter.id.in_(valued_parameter_ids))

    def unvalued_relationship_parameter_list(self, relationship_id):
        """Return parameters that do not have a value for given relationship."""
        relationship = self.single_wide_relationship(relationship_id).one_or_none()
        if not relationship:
            return self.empty_list()
        valued_parameter_ids = self.session.query(self.ParameterValue.parameter_id).\
            filter_by(relationship_id=relationship_id)
        return self.parameter_list().filter_by(relationship_class_id=relationship.class_id).\
            filter(~self.Parameter.id.in_(valued_parameter_ids))

    def single_parameter(self, id=None, name=None):
        """Return parameter corresponding to id."""
        if id is None and name is None:
            return self.empty_list()
        qry = self.parameter_list()
        if id:
            return qry.filter_by(id=id)
        if name:
            return qry.filter_by(name=name)

    def single_object_parameter(self, id):
        """Return object class and the parameter corresponding to id."""
        return self.object_parameter_list().filter(self.Parameter.id == id)

    def single_relationship_parameter(self, id):
        """Return relationship class and the parameter corresponding to id."""
        return self.relationship_parameter_list().filter(self.Parameter.id == id)

    def single_object_parameter_value(self, id):
        """Return object and the parameter value corresponding to id."""
        return self.object_parameter_value_list().filter(self.ParameterValue.id == id)

    def single_relationship_parameter_value(self, id):
        """Return relationship and the parameter value corresponding to id."""
        return self.relationship_parameter_value_list().filter(self.ParameterValue.id == id)

    def object_parameter_list(self):
        """Return object classes and their parameters."""
        return self.session.query(
            #self.Parameter.object_class_id,
            self.ObjectClass.name.label('object_class_name'),
            #self.Parameter.id.label('parameter_id'),
            self.Parameter.name.label('parameter_name'),
            self.Parameter.can_have_time_series,
            self.Parameter.can_have_time_pattern,
            self.Parameter.can_be_stochastic,
            self.Parameter.default_value,
            self.Parameter.is_mandatory,
            self.Parameter.precision,
            self.Parameter.minimum_value,
            self.Parameter.maximum_value
        ).filter(self.ObjectClass.id == self.Parameter.object_class_id).\
        order_by(self.Parameter.id)

    def relationship_parameter_list(self):
        """Return relationship classes and their parameters."""
        wide_relationship_class_subqry = self.wide_relationship_class_list().subquery()
        return self.session.query(
            #self.Parameter.relationship_class_id,
            wide_relationship_class_subqry.c.name.label('relationship_class_name'),
            #wide_relationship_class_subqry.c.object_class_id_list,
            wide_relationship_class_subqry.c.object_class_name_list,
            #self.Parameter.id.label('parameter_id'),
            self.Parameter.name.label('parameter_name'),
            self.Parameter.can_have_time_series,
            self.Parameter.can_have_time_pattern,
            self.Parameter.can_be_stochastic,
            self.Parameter.default_value,
            self.Parameter.is_mandatory,
            self.Parameter.precision,
            self.Parameter.minimum_value,
            self.Parameter.maximum_value
        ).filter(self.Parameter.relationship_class_id == wide_relationship_class_subqry.c.id).\
        order_by(self.Parameter.id)

    def object_parameter_value_list(self):
        """Return objects and their parameter values."""
        return self.session.query(
            #self.Parameter.object_class_id,
            self.ObjectClass.name.label('object_class_name'),
            #self.ParameterValue.object_id,
            self.Object.name.label('object_name'),
            #self.ParameterValue.id.label('parameter_value_id'),
            self.Parameter.name.label('parameter_name'),
            self.ParameterValue.index,
            self.ParameterValue.value,
            self.ParameterValue.json,
            self.ParameterValue.expression,
            self.ParameterValue.time_pattern,
            self.ParameterValue.time_series_id,
            self.ParameterValue.stochastic_model_id
        ).filter(self.Parameter.id == self.ParameterValue.parameter_id).\
        filter(self.ParameterValue.object_id == self.Object.id).\
        filter(self.Parameter.object_class_id == self.ObjectClass.id)

    def relationship_parameter_value_list(self):
        """Return relationships and their parameter values."""
        wide_relationship_class_subqry = self.wide_relationship_class_list().subquery()
        wide_relationship_subqry = self.wide_relationship_list().subquery()
        return self.session.query(
            #self.Parameter.relationship_class_id,
            wide_relationship_class_subqry.c.name.label('relationship_class_name'),
            #self.ParameterValue.relationship_id,
            wide_relationship_class_subqry.c.object_class_name_list,
            wide_relationship_subqry.c.name.label('relationship_name'),
            #wide_relationship_subqry.c.object_id_list,
            wide_relationship_subqry.c.object_name_list,
            #self.ParameterValue.id.label('parameter_value_id'),
            self.Parameter.name.label('parameter_name'),
            self.ParameterValue.index,
            self.ParameterValue.value,
            self.ParameterValue.json,
            self.ParameterValue.expression,
            self.ParameterValue.time_pattern,
            self.ParameterValue.time_series_id,
            self.ParameterValue.stochastic_model_id
        ).filter(self.Parameter.id == self.ParameterValue.parameter_id).\
        filter(self.ParameterValue.relationship_id == wide_relationship_subqry.c.id).\
        filter(self.Parameter.relationship_class_id == wide_relationship_class_subqry.c.id)

    def add_object_class(self, **kwargs):
        """Add object class to database.

        Returns:
            An instance of self.ObjectClass if successful, None otherwise
        """
        object_class = self.ObjectClass(commit_id=self.commit.id, **kwargs)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(object_class)
            self.session.flush()
            return object_class
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting object class '{}': {}".format(object_class.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def add_object(self, **kwargs):
        """Add object to database.

        Returns:
            An instance of self.Object if successful, None otherwise
        """
        object_ = self.Object(commit_id=self.commit.id, **kwargs)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(object_)
            self.session.flush()
            return object_
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting object '{}': {}".format(object_.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def add_wide_relationship_class(self, wide_relationship_class_args):
        """Add relationship class to database.

        Args:
            wide_relationship_class_args (dict): the relationship class in wide format

        Returns:
            wide_relationship_class (KeyedTuple): the relationship class now with the id
        """
        id = self.session.query(func.max(self.RelationshipClass.id)).scalar()
        if not id:
            id = 0
        id += 1
        relationship_class_list = list()
        for dimension, object_class_id in enumerate(wide_relationship_class_args['object_class_id_list']):
            kwargs = {
                'id': id,
                'dimension': dimension,
                'object_class_id': object_class_id,
                'name': wide_relationship_class_args['name'],
                'commit_id': self.commit.id
            }
            relationship_class = self.RelationshipClass(**kwargs)
            relationship_class_list.append(relationship_class)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add_all(relationship_class_list)
            self.session.flush()
            wide_relationship_class = self.single_wide_relationship_class(id=id).one_or_none()
            return wide_relationship_class
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting relationship class '{}': {}".\
                format(wide_relationship_class_args['name'], e.orig.args)
            raise SpineDBAPIError(msg)

    def add_wide_relationship(self, wide_relationship_args):
        """Add relationship to database.

        Args:
            wide_relationship (dict): the relationship in wide format

        Returns:
            wide_relationship (dict): the relationship now with the id
        """
        id = self.session.query(func.max(self.Relationship.id)).scalar()
        if not id:
            id = 0
        id += 1
        relationship_list = list()
        for dimension, object_id in enumerate(wide_relationship_args['object_id_list']):
            kwargs = {
                'id': id,
                'dimension': dimension,
                'object_id': object_id,
                'name': wide_relationship_args['name'],
                'class_id': wide_relationship_args['class_id'],
                'commit_id': self.commit.id
            }
            relationship = self.Relationship(**kwargs)
            relationship_list.append(relationship)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add_all(relationship_list)
            self.session.flush()
            wide_relationship = self.single_wide_relationship(id=id).one_or_none()
            return wide_relationship
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting relationship '{}': {}".format(wide_relationship_args['name'], e.orig.args)
            raise SpineDBAPIError(msg)

    def add_parameter(self, **kwargs):
        """Add parameter to database.

        Returns:
            An instance of self.Parameter if successful, None otherwise
        """
        parameter = self.Parameter(commit_id=self.commit.id, **kwargs)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(parameter)
            self.session.flush()
            return parameter
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter '{}': {}".format(parameter.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def add_parameter_value(self, **kwargs):
        """Add parameter value to database.

        Returns:
            An instance of self.ParameterValue if successful, None otherwise
        """
        parameter_value = self.ParameterValue(commit_id=self.commit.id, **kwargs)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(parameter_value)
            self.session.flush()
            return parameter_value
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while inserting parameter value: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def rename_object_class(self, id, new_name):
        """Rename object class."""
        object_class = self.session.query(self.ObjectClass).filter_by(id=id).one_or_none()
        if not object_class:
            raise RecordNotFoundError('object_class', name=new_name)
        try:
            self.transactions.append(self.session.begin_nested())
            object_class.name = new_name
            object_class.commit_id = self.commit.id
            self.session.flush()
            return object_class
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while renaming object class '{}': {}".format(object_class.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def rename_object(self, id, new_name):
        """Rename object."""
        object_ = self.session.query(self.Object).filter_by(id=id).one_or_none()
        if not object_:
            raise RecordNotFoundError('object', name=new_name)
        try:
            self.transactions.append(self.session.begin_nested())
            object_.name = new_name
            object_.commit_id = self.commit.id
            self.session.flush()
            return object_
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while renaming object '{}': {}".format(object_.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def rename_relationship_class(self, id, new_name):
        """Rename relationship class."""
        relationship_class_list = self.session.query(self.RelationshipClass).filter_by(id=id)
        if not relationship_class_list.count():
            raise RecordNotFoundError('relationship_class', name=new_name)
        try:
            self.transactions.append(self.session.begin_nested())
            for relationship_class in relationship_class_list:
                relationship_class.name = new_name
                relationship_class.commit_id = self.commit.id
            self.session.flush()
            return relationship_class_list.first()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while renaming relationship class '{}': {}".format(relationship_class.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def rename_relationship(self, id, new_name):
        """Rename relationship."""
        relationship_list = self.session.query(self.Relationship).filter_by(id=id)
        if not relationship_list.count():
            raise RecordNotFoundError('relationship', name=new_name)
        try:
            self.transactions.append(self.session.begin_nested())
            for relationship in relationship_list:
                relationship.name = new_name
                relationship.commit_id = self.commit.id
            self.session.flush()
            return relationship.first()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while renaming relationship '{}': {}".format(relationship.name, e.orig.args)
            raise SpineDBAPIError(msg)

    def remove_object_class(self, id):
        """Remove object class."""
        object_class = self.session.query(self.ObjectClass).filter_by(id=id).one_or_none()
        if not object_class:
            raise RecordNotFoundError('object_class', id=id)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(object_class)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while removing object class: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def remove_object(self, id):
        """Remove object."""
        object_ = self.session.query(self.Object).filter_by(id=id).one_or_none()
        if not object_:
            raise RecordNotFoundError('object', id=id)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(object_)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while removing object: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def remove_relationship_class(self, id):
        """Remove relationship class."""
        relationship_class_list = self.session.query(self.RelationshipClass).filter_by(id=id)
        if not relationship_class_list.count():
            raise RecordNotFoundError('relationship_class', id=id)
        try:
            self.transactions.append(self.session.begin_nested())
            for relationship_class in relationship_class_list:
                self.session.delete(relationship_class)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while removing relationship class: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def remove_relationship(self, id):
        """Remove relationship."""
        relationship_list = self.session.query(self.Relationship).filter_by(id=id)
        if not relationship_list.count():
            raise RecordNotFoundError('relationship', id=id)
        try:
            self.transactions.append(self.session.begin_nested())
            for relationship in relationship_list:
                self.session.delete(relationship)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while removing relationship: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def update_parameter(self, id, field_name, new_value):
        """Update parameter."""
        parameter = self.session.query(self.Parameter).\
            filter_by(id=id).one_or_none()
        if not parameter:
            raise RecordNotFoundError('parameter', id=id)
        value = getattr(parameter, field_name)
        data_type = type(value)
        try:
            new_casted_value = data_type(new_value)
        except TypeError:
            new_casted_value = new_value
        except ValueError:
            raise ParameterValueError(new_value)
        if value == new_casted_value:
            msg = "Parameter not changed."
            raise SpineDBAPIError(msg)
        try:
            self.transactions.append(self.session.begin_nested())
            setattr(parameter, field_name, new_value)
            parameter.commit_id = self.commit.id
            self.session.flush()
            return parameter
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while updating parameter: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def update_parameter_value(self, id, field_name, new_value):
        """Update parameter value."""
        parameter_value = self.session.query(self.ParameterValue).\
            filter_by(id=id).one_or_none()
        if not parameter_value:
            raise RecordNotFoundError('parameter_value', id=id)
        value = getattr(parameter_value, field_name)
        data_type = type(value)
        try:
            new_casted_value = data_type(new_value)
        except TypeError:
            new_casted_value = new_value
        except ValueError:
            raise ParameterValueError(new_value)
        if value == new_casted_value:
            msg = "Parameter value not changed."
            raise SpineDBAPIError(msg)
        try:
            self.transactions.append(self.session.begin_nested())
            setattr(parameter_value, field_name, new_casted_value)
            parameter_value.commit_id = self.commit.id
            self.session.flush()
            return parameter_value
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while updating parameter value: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def remove_parameter(self, id):
        """Remove parameter."""
        parameter = self.session.query(self.Parameter).\
            filter_by(id=id).one_or_none()
        if not parameter:
            raise RecordNotFoundError('parameter', id=id)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(parameter)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while removing parameter: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def remove_parameter_value(self, id):
        """Remove parameter value."""
        parameter_value = self.session.query(self.ParameterValue).\
            filter_by(id=id).one_or_none()
        if not parameter_value:
            raise RecordNotFoundError('parameter_value', id=id)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(parameter_value)
            self.session.flush()
        except DBAPIError as e:
            self.session.rollback()
            msg = "DBAPIError while removing parameter value: {}".format(e.orig.args)
            raise SpineDBAPIError(msg)

    def empty_list(self):
        return self.session.query(false()).filter(false())

    def close(self):
        if self.session:
            self.session.rollback()
            self.session.close()
        if self.engine:
            self.engine.dispose()
