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
Classes to handle the Spine database object relational mapping.

:author: Manuel Marin <manuelma@kth.se>
:date:   11.8.2018
"""

from sqlalchemy import false
from sqlalchemy.ext.automap import automap_base, generate_relationship
from sqlalchemy.orm import interfaces, Session, aliased
from sqlalchemy.exc import NoSuchTableError, DBAPIError
from datetime import datetime, timezone

# TODO: SELECT queries should also be checked for errors
class DatabaseMapping(object):
    """A class to manipulate the Spine database object relational mapping.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        engine (Engine): The sql alchemy engine to get the mapping from
        username (str): The user name
    """
    def __init__(self, parent, engine, username):
        """Initialize class."""
        self._parent = parent
        self.engine = engine
        self.username = username
        self.session = Session(engine)
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

    def set_parent(self, parent):
        self._parent = parent

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
            return True
        except NoSuchTableError as e:
            self._parent.msg_error.emit("Unable to parse database in the Spine format. "
                                        " Table <b>{}</b> is missing.".format(e))
            return False

    def new_commit(self):
        """Add row to commit table"""
        comment = 'In progress...'
        user = self.username
        date = datetime.now(timezone.utc)
        self.commit = self.Commit(comment=comment, date=date, user=user)
        try:
            self.session.add(self.commit)
            self.session.flush()
            return True
        except DBAPIError as e:
            msg = "Could not insert new commit item: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def commit_session(self, comment):
        """Commit changes to source database."""
        if not self.session:
            self._parent.msg_error.emit("No session!")
            return
        if not self.commit.id:
            self._parent.msg_error.emit("No commit id!")
            return
        try:
            self.commit.comment = comment
            self.commit.date = datetime.now(timezone.utc)
            for i in reversed(range(len(self.transactions))):
                self.session.commit()
                del self.transactions[i]
            self.session.commit()  # also commit main transaction
        except DBAPIError as e:
            msg = "Error while trying to commit changes: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.commit.comment = None
            self.commit.date = None
            return
        msg = "All changes commited successfully."
        self._parent.msg.emit(msg)
        self.new_commit()

    def rollback_session(self):
        if not self.session:
            self._parent.msg_error.emit("No session!")
            return
        try:
            for i in reversed(range(len(self.transactions))):
                self.session.rollback()
                del self.transactions[i]
            self.session.rollback()  # also rollback main transaction
        except DBAPIError:
            msg = "Error while trying to rollback changes."
            self._parent.msg_error.emit(msg, 3000)
            return
        msg = "All changes since last commit rolled back successfully."
        self._parent.msg.emit(msg)
        self.new_commit()

    def single_object_class(self, id):
        """Return a single object class given the id or None if not found."""
        return self.session.query(
            self.ObjectClass.id,
            self.ObjectClass.name,
            self.ObjectClass.display_order,
        ).filter_by(id=id).one_or_none()

    def single_object(self, id):
        """Return a single object given the id or None if not found."""
        return self.session.query(
            self.Object.id,
            self.Object.class_id,
            self.Object.name
        ).filter_by(id=id).one_or_none()

    def single_relationship_class(self, id):
        """Return a single relationship class given the id or None if not found."""
        return self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.parent_relationship_class_id,
            self.RelationshipClass.parent_object_class_id,
            self.RelationshipClass.child_object_class_id
        ).filter_by(id=id).one_or_none()

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
            return qry.filter_by(class_id=class_id)
        return qry

    def proto_relationship_class_list(
            self,
            parent_object_class_id=None,
            child_object_class_id=None
        ):
        """Return proto-relationship classes, i.e., those that do not involve other relationship classes."""
        # NOTE: in our current convention, relationship classes are never the 'child'
        # in other relationship classes --I hope this doesn't change
        qry = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.parent_object_class_id,
            self.RelationshipClass.child_object_class_id
        ).filter_by(parent_relationship_class_id=None)
        if parent_object_class_id:
            return qry.filter_by(parent_object_class_id=parent_object_class_id)
        if child_object_class_id:
            return qry.filter_by(child_object_class_id=child_object_class_id)
        return qry

    def meta_relationship_class_list(
            self,
            parent_relationship_class_id=None
        ):
        """Return meta-relationship classes, i.e., those having another relationship class as parent."""
        # NOTE: in our current convention, relationship classes are never the 'child'
        # in other relationship classes --but this may change
        qry = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.parent_relationship_class_id,
            self.RelationshipClass.child_object_class_id
        ).filter_by(parent_object_class_id=None)
        if parent_relationship_class_id:
            return qry.filter_by(parent_relationship_class_id=parent_relationship_class_id)
        return qry

    def relationship_class_list(
            self,
            parent_relationship_class_id=None,
            parent_object_class_id=None,
            child_object_class_id=None
        ):
        """Return all relationship classes regardless of whether or not they involve other relationship classes."""
        qry = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.parent_relationship_class_id,
            self.RelationshipClass.parent_object_class_id,
            self.RelationshipClass.child_object_class_id
        )
        if parent_relationship_class_id:
            return qry.filter_by(parent_relationship_class_id=parent_relationship_class_id)
        if parent_object_class_id:
            return qry.filter_by(parent_object_class_id=parent_object_class_id)
        if child_object_class_id:
            return qry.filter_by(child_object_class_id=child_object_class_id)
        return qry

    def relationship_list(self, class_id=None):
        """Return relationships, optionally filtered by class id."""
        qry = self.session.query(
            self.Relationship.id,
            self.Relationship.class_id,
            self.Relationship.parent_relationship_id,
            self.Relationship.parent_object_id,
            self.Relationship.child_object_id,
            self.Relationship.name
        )
        if class_id:
            return qry.filter_by(class_id=class_id)
        return qry

    def parent_related_object_list(self, relationship_class_id, child_object_id):
        """Return objects related to a given child object through a relationship class."""
        qry = self.session.query(
            self.Object.id,
            self.Object.class_id,
            self.Object.name,
            self.Relationship.id.label('relationship_id'),
            self.Relationship.name.label('relationship_name')
        ).filter(self.Relationship.class_id == relationship_class_id)
        return qry.filter(self.Object.id == self.Relationship.parent_object_id).\
            filter(self.Relationship.child_object_id == child_object_id)

    def child_related_object_list(self, relationship_class_id, parent_object_id):
        """Return objects related to a given parent object through a relationship class."""
        qry = self.session.query(
            self.Object.id,
            self.Object.class_id,
            self.Object.name,
            self.Relationship.id.label('relationship_id'),
            self.Relationship.name.label('relationship_name')
        ).filter(self.Relationship.class_id == relationship_class_id)
        return qry.filter(self.Object.id == self.Relationship.child_object_id).\
            filter(self.Relationship.parent_object_id == parent_object_id)

    def meta_related_object_list(self, relationship_class_id, parent_relationship_id):
        """Return objects related to a given parent relationship through a meta-relationship class."""
        qry = self.session.query(
            self.Object.id,
            self.Object.class_id,
            self.Object.name,
            self.Relationship.id.label('relationship_id'),
            self.Relationship.name.label('relationship_name')
        ).filter(self.Relationship.class_id == relationship_class_id)
        return qry.filter(self.Object.id == self.Relationship.child_object_id).\
            filter(self.Relationship.parent_relationship_id == parent_relationship_id)

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
        object_ = self.single_object(object_id)
        if not object_:
            return self.empty_list()
        valued_parameter_ids = self.session.query(self.ParameterValue.parameter_id).\
            filter_by(object_id=object_id)
        return self.parameter_list().filter_by(object_class_id=object_.class_id).\
            filter(~self.Parameter.id.in_(valued_parameter_ids))

    def unvalued_relationship_parameter_list(self, relationship_id):
        """Return parameters that do not have a value for given relationship."""
        relationship = self.single_relationship(relationship_id)
        if not relationship:
            return self.empty_list()
        valued_parameter_ids = self.session.query(self.ParameterValue.parameter_id).\
            filter_by(relationship_id=relationship_id)
        return self.parameter_list().filter_by(relationship_class_id=relationship.class_id).\
            filter(~self.Parameter.id.in_(valued_parameter_ids))

    def single_object_parameter(self, id):
        """Return object class and the parameter corresponding to id."""
        return self.object_parameter_list().filter(self.Parameter.id == id).one_or_none()

    def single_relationship_parameter(self, id):
        """Return relationship class and the parameter corresponding to id."""
        return self.relationship_parameter_list().filter(self.Parameter.id == id).one_or_none()

    def single_object_parameter_value(self, id):
        """Return object and the parameter value corresponding to id."""
        return self.object_parameter_value_list().filter(self.ParameterValue.id == id).one_or_none()

    def single_relationship_parameter_value(self, id):
        """Return relationship and the parameter value corresponding to id."""
        return self.relationship_parameter_value_list().filter(self.ParameterValue.id == id).one_or_none()

    def object_parameter_list(self):
        """Return object classes and their parameters."""
        return self.session.query(
            self.ObjectClass.id.label('object_class_id'),
            self.ObjectClass.name.label('object_class_name'),
            self.Parameter.id.label('parameter_id'),
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
        return self.session.query(
            self.RelationshipClass.id.label('relationship_class_id'),
            self.RelationshipClass.name.label('relationship_class_name'),
            self.Parameter.id.label('parameter_id'),
            self.Parameter.name.label('parameter_name'),
            self.Parameter.can_have_time_series,
            self.Parameter.can_have_time_pattern,
            self.Parameter.can_be_stochastic,
            self.Parameter.default_value,
            self.Parameter.is_mandatory,
            self.Parameter.precision,
            self.Parameter.minimum_value,
            self.Parameter.maximum_value
        ).filter(self.RelationshipClass.id == self.Parameter.relationship_class_id).\
        order_by(self.Parameter.id)

    def object_parameter_value_list(self):
        """Return objects and their parameter values."""
        return self.session.query(
            self.Object.class_id.label('object_class_id'),
            self.ObjectClass.name.label('object_class_name'),
            self.ParameterValue.object_id,
            self.Object.name.label('object_name'),
            self.ParameterValue.id.label('parameter_value_id'),
            self.Parameter.name.label('parameter_name'),
            self.ParameterValue.index,
            self.ParameterValue.value,
            self.ParameterValue.json,
            self.ParameterValue.expression,
            self.ParameterValue.time_pattern,
            self.ParameterValue.time_series_id,
            self.ParameterValue.stochastic_model_id
        ).filter(self.Parameter.id == self.ParameterValue.parameter_id).\
        filter(self.Object.id == self.ParameterValue.object_id).\
        filter(self.Object.class_id == self.ObjectClass.id)

    def relationship_parameter_value_list(self):
        """Return relationships and their parameter values."""
        parent_relationship = aliased(self.Relationship)
        parent_object = aliased(self.Object)
        child_object = aliased(self.Object)
        return self.session.query(
            self.Relationship.class_id.label('relationship_class_id'),
            self.RelationshipClass.name.label('relationship_class_name'),
            # self.RelationshipClass.parent_relationship_class_id,
            # self.RelationshipClass.parent_object_class_id,
            # self.RelationshipClass.child_object_class_id,
            self.ParameterValue.relationship_id,
            self.Relationship.parent_relationship_id,
            self.Relationship.parent_object_id,
            self.Relationship.child_object_id,
            parent_relationship.name.label('parent_relationship_name'),
            parent_object.name.label('parent_object_name'),
            child_object.name.label('child_object_name'),
            self.ParameterValue.id.label('parameter_value_id'),
            self.Parameter.name.label('parameter_name'),
            self.ParameterValue.index,
            self.ParameterValue.value,
            self.ParameterValue.json,
            self.ParameterValue.expression,
            self.ParameterValue.time_pattern,
            self.ParameterValue.time_series_id,
            self.ParameterValue.stochastic_model_id
        ).filter(self.Parameter.id == self.ParameterValue.parameter_id).\
        filter(self.Relationship.id == self.ParameterValue.relationship_id).\
        filter(self.Relationship.class_id == self.RelationshipClass.id).\
        outerjoin(parent_relationship, parent_relationship.id == self.Relationship.parent_relationship_id).\
        outerjoin(parent_object, parent_object.id == self.Relationship.parent_object_id).\
        filter(child_object.id == self.Relationship.child_object_id)

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
            msg = "Successfully added new object class '{}'.".format(object_class.name)
            self._parent.msg.emit(msg)
            return object_class
        except DBAPIError as e:
            msg = "Could not insert new object class '{}': {}".format(object_class.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

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
            msg = "Successfully added new object '{}'.".format(object_.name)
            self._parent.msg.emit(msg)
            return object_
        except DBAPIError as e:
            msg = "Could not insert new object '{}': {}".format(object_.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def add_relationship_class(self, **kwargs):
        """Add relationship class to database.

        Returns:
            An instance of self.RelationshipClass if successful, None otherwise
        """
        relationship_class = self.RelationshipClass(commit_id=self.commit.id, **kwargs)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(relationship_class)
            self.session.flush()
            msg = "Successfully added new relationship class '{}'.".format(relationship_class.name)
            self._parent.msg.emit(msg)
            return relationship_class
        except DBAPIError as e:
            msg = "Could not insert new relationship class '{}': {}".format(relationship_class.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def add_relationship(self, **kwargs):
        """Add relationship to database.

        Returns:
            An instance of self.Relationship if successful, None otherwise
        """
        relationship = self.Relationship(commit_id=self.commit.id, **kwargs)
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(relationship)
            self.session.flush()
            msg = "Successfully added new relationship '{}'.".format(relationship.name)
            self._parent.msg.emit(msg)
            return relationship
        except DBAPIError as e:
            msg = "Could not insert new relationship '{}': {}".format(relationship.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

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
            msg = "Successfully added new parameter '{}'.".format(parameter.name)
            self._parent.msg.emit(msg)
            return parameter
        except DBAPIError as e:
            msg = "Could not insert new parameter: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

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
            msg = "Successfully added new parameter value."
            self._parent.msg.emit(msg)
            return parameter_value
        except DBAPIError as e:
            msg = "Could not insert new parameter value: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def rename_object_class(self, id, new_name):
        """Rename object class."""
        object_class = self.session.query(self.ObjectClass).filter_by(id=id).one_or_none()
        if not object_class:
            msg = "Could not find object class."
            self._parent.msg_error.emit(msg)
            return None
        try:
            self.transactions.append(self.session.begin_nested())
            object_class.name = new_name
            object_class.commit_id = self.commit.id
            self.session.flush()
            msg = "Successfully renamed object class to '{}'.".format(object_class.name)
            self._parent.msg.emit(msg)
            return object_class
        except DBAPIError as e:
            msg = "Could not rename object class '{}': {}".format(object_class.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def rename_object(self, id, new_name):
        """Rename object."""
        object_ = self.session.query(self.Object).filter_by(id=id).one_or_none()
        if not object_:
            msg = "Could not find object."
            self._parent.msg_error.emit(msg)
            return None
        try:
            self.transactions.append(self.session.begin_nested())
            object_.name = new_name
            object_.commit_id = self.commit.id
            self.session.flush()
            msg = "Successfully renamed object to '{}'.".format(object_.name)
            self._parent.msg.emit(msg)
            return object_
        except DBAPIError as e:
            msg = "Could not rename object '{}': {}".format(object_.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def rename_relationship_class(self, id, new_name):
        """Rename relationship class."""
        relationship_class = self.session.query(self.RelationshipClass).filter_by(id=id).one_or_none()
        if not relationship_class:
            msg = "Could not find relationship class."
            self._parent.msg_error.emit(msg)
            return None
        try:
            self.transactions.append(self.session.begin_nested())
            relationship_class.name = new_name
            relationship_class.commit_id = self.commit.id
            self.session.flush()
            msg = "Successfully renamed relationship class to '{}'.".format(relationship_class.name)
            self._parent.msg.emit(msg)
            return relationship_class
        except DBAPIError as e:
            msg = "Could not rename relationship class '{}': {}".format(relationship_class.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def rename_relationship(self, id, new_name):
        """Rename relationship."""
        relationship = self.session.query(self.Relationship).filter_by(id=id).one_or_none()
        if not relationship:
            msg = "Could not find relationship."
            self._parent.msg_error.emit(msg)
            return None
        try:
            self.transactions.append(self.session.begin_nested())
            relationship.name = new_name
            relationship.commit_id = self.commit.id
            self.session.flush()
            msg = "Successfully renamed relationship to '{}'.".format(relationship.name)
            self._parent.msg.emit(msg)
            return relationship
        except DBAPIError as e:
            msg = "Could not rename relationship '{}': {}".format(relationship.name, e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def remove_object_class(self, id):
        """Remove object class."""
        object_class = self.session.query(self.ObjectClass).filter_by(id=id).one_or_none()
        if not object_class:
            msg = "Could not find object class."
            self._parent.msg_error.emit(msg)
            return False
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(object_class)
            self.session.flush()
            msg = "Successfully removed object class."
            self._parent.msg.emit(msg)
            return True
        except DBAPIError as e:
            msg = "Could not remove object class: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def remove_object(self, id):
        """Remove object."""
        object_ = self.session.query(self.Object).filter_by(id=id).one_or_none()
        if not object_:
            msg = "Could not find object."
            self._parent.msg_error.emit(msg)
            return False
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(object_)
            self.session.flush()
            msg = "Successfully removed object."
            self._parent.msg.emit(msg)
            return True
        except DBAPIError as e:
            msg = "Could not remove object: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def remove_relationship_class(self, id):
        """Remove relationship class."""
        relationship_class = self.session.query(self.RelationshipClass).filter_by(id=id).one_or_none()
        if not relationship_class:
            msg = "Could not find relationship class."
            self._parent.msg_error.emit(msg)
            return False
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(relationship_class)
            self.session.flush()
            msg = "Successfully removed relationship class."
            self._parent.msg.emit(msg)
            return True
        except DBAPIError as e:
            msg = "Could not remove relationship class: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def remove_relationship(self, id):
        """Remove relationship."""
        relationship = self.session.query(self.Relationship).filter_by(id=id).one_or_none()
        if not relationship:
            msg = "Could not find relationship."
            self._parent.msg_error.emit(msg)
            return False
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(relationship)
            self.session.flush()
            msg = "Successfully removed relationship."
            self._parent.msg.emit(msg)
            return True
        except DBAPIError as e:
            msg = "Could not remove relationship: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def update_parameter(self, id, field_name, new_value):
        """Update parameter."""
        parameter = self.session.query(self.Parameter).\
            filter_by(id=id).one_or_none()
        if not parameter:
            msg = "Could not find parameter."
            return None
        value = getattr(parameter, field_name)
        data_type = type(value)
        try:
            new_casted_value = data_type(new_value)
        except TypeError:
            new_casted_value = new_value
        except ValueError:
            msg = "The new value does not fit the datatype."
            self._parent.msg_error.emit(msg)
            return None
        if value == new_casted_value:
            msg = "Parameter not changed."
            self._parent.msg.emit(msg)
            return None
        try:
            self.transactions.append(self.session.begin_nested())
            setattr(parameter, field_name, new_value)
            parameter.commit_id = self.commit.id
            self.session.flush()
            msg = "Parameter succesfully updated."
            self._parent.msg.emit(msg)
            return parameter
        except DBAPIError as e:
            msg = "Could not update parameter value: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def update_parameter_value(self, id, field_name, new_value):
        """Update parameter value."""
        parameter_value = self.session.query(self.ParameterValue).\
            filter_by(id=id).one_or_none()
        if not parameter_value:
            msg = "Could not find parameter value."
            self._parent.msg_error.emit(msg)
            return None
        value = getattr(parameter_value, field_name)
        data_type = type(value)
        try:
            new_casted_value = data_type(new_value)
        except TypeError:
            new_casted_value = new_value
        except ValueError:
            msg = "The new value does not fit the datatype."
            self._parent.msg_error.emit(msg)
            return None
        if value == new_casted_value:
            msg = "Parameter value not changed."
            self._parent.msg.emit(msg)
            return None
        try:
            self.transactions.append(self.session.begin_nested())
            setattr(parameter_value, field_name, new_casted_value)
            parameter_value.commit_id = self.commit.id
            self.session.flush()
            msg = "Parameter value succesfully updated."
            self._parent.msg.emit(msg)
            return parameter_value
        except DBAPIError as e:
            msg = "Could not update parameter value: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return None

    def remove_parameter(self, id):
        """Remove parameter."""
        parameter = self.session.query(self.Parameter).\
            filter_by(id=id).one_or_none()
        if not parameter:
            msg = "Could not find parameter."
            self._parent.msg_error.emit(msg)
            return False
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(parameter)
            self.session.flush()
            msg = "Parameter succesfully removed."
            self._parent.msg.emit(msg)
            return True
        except DBAPIError as e:
            msg = "Could not remove parameter: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def remove_parameter_value(self, id):
        """Remove parameter value."""
        parameter_value = self.session.query(self.ParameterValue).\
            filter_by(id=id).one_or_none()
        if not parameter_value:
            msg = "Could not find parameter value."
            self._parent.msg_error.emit(msg)
            return False
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(parameter_value)
            self.session.flush()
            msg = "Parameter value succesfully removed."
            self._parent.msg.emit(msg)
            return True
        except DBAPIError as e:
            msg = "Could not remove parameter value: {}".format(e.orig.args)
            self._parent.msg_error.emit(msg)
            self.session.rollback()
            return False

    def empty_list(self):
        return self.session.query(false()).filter(false())

    def close(self):
        if self.session:
            self.session.rollback()
            self.session.close()
        if self.engine:
            self.engine.dispose()
