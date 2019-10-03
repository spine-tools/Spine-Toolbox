######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes to hold parameters.

:authors: M. Marin (KTH)
:date:   2.10.2019
"""


class ParameterItem:
    """Class to hold parameter definitions or values within an EmptyParameterModel or SubParameterModel.
    It provides __getitem__ and __setitem__ methods so the item behaves more or less like a list.
    """

    def __init__(self, header, database=None, id_=None):
        """Init class.

        Args:
            header (list): header from the model where this item belong
            database (str): the database where this item comes from
            id_ (int): the id of the item in the database table
        """
        self._header = header
        self.database = database
        self.id = id_

    def __getitem__(self, index):
        """Returns the item corresponding to the given index."""
        return getattr(self, self._header[index])

    def __setitem__(self, index, value):
        """Sets the value for the item corresponding to the given index."""
        fieldname = self._header[index]
        setattr(self, fieldname, value)

    def __len__(self):
        return len(self._header)

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        raise NotImplementedError


class ParameterDefinitionItem(ParameterItem):
    """Class to hold parameter definitions within an EmptyParameterModel or SubParameterModel.
    It provides attributes for fields that are common to all parameter definitions
    regardless of the entity class.
    """

    def __init__(
        self,
        header,
        database=None,
        id_=None,
        parameter_name=None,
        value_list_id=None,
        value_list_name=None,
        parameter_tag_id_list=None,
        parameter_tag_list=None,
        default_value=None,
    ):
        """Init class.
        """
        super().__init__(header, database, id_)
        self.parameter_name = parameter_name
        self.value_list_id = value_list_id
        self.value_list_name = value_list_name
        self.parameter_tag_list = parameter_tag_list
        self.parameter_tag_id_list = parameter_tag_id_list
        self.default_value = default_value

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        if not self.parameter_name:
            return None
        item = {"name": self.parameter_name, "default_value": self.default_value}
        if self.value_list_id is not None:
            item["parameter_value_list_id"] = self.value_list_id
        return item


class ObjectParameterDefinitionItem(ParameterDefinitionItem):
    """Class to hold object parameter definitions within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter definition attributes,
    it adds attributes that are unique to the *object* entity class.
    """

    def __init__(
        self,
        header,
        database=None,
        id_=None,
        parameter_name=None,
        value_list_id=None,
        value_list_name=None,
        parameter_tag_id_list=None,
        parameter_tag_list=None,
        default_value=None,
        object_class_id=None,
        object_class_name=None,
    ):
        """Init class."""
        super().__init__(
            header,
            database,
            id_,
            parameter_name,
            value_list_id,
            value_list_name,
            parameter_tag_id_list,
            parameter_tag_list,
            default_value,
        )
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        if not self.object_class_id:
            return None
        item = super().for_insert()
        if item:
            item["object_class_id"] = self.object_class_id
        return item


class RelationshipParameterDefinitionItem(ParameterDefinitionItem):
    """Class to hold relationship parameter definitions within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter definition attributes,
    it adds attributes that are unique to the *relationship* entity class.
    """

    def __init__(
        self,
        header,
        database=None,
        id_=None,
        parameter_name=None,
        value_list_id=None,
        value_list_name=None,
        parameter_tag_id_list=None,
        parameter_tag_list=None,
        default_value=None,
        relationship_class_id=None,
        relationship_class_name=None,
        object_class_id_list=None,
        object_class_name_list=None,
    ):
        """Init class."""
        super().__init__(
            header,
            database,
            id_,
            parameter_name,
            value_list_id,
            value_list_name,
            parameter_tag_id_list,
            parameter_tag_list,
            default_value,
        )
        self.relationship_class_id = relationship_class_id
        self.relationship_class_name = relationship_class_name
        self.object_class_id_list = object_class_id_list
        self.object_class_name_list = object_class_name_list

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        if not self.relationship_class_id:
            return None
        item = super().for_insert()
        if item:
            item["relationship_class_id"] = self.relationship_class_id
        return item


class ParameterValueItem(ParameterItem):
    """Class to hold parameter values within an EmptyParameterModel or SubParameterModel.
    It provides attributes for fields that are common to all parameter values
    regardless of the entity.
    """

    def __init__(self, header, database=None, id_=None, parameter_id=None, parameter_name=None, value=None):
        """Init class.
        """
        super().__init__(header, database, id_)
        self.parameter_id = parameter_id
        self.parameter_name = parameter_name
        self.value = value
        self._definition_dict = dict()

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        if not self.parameter_id:
            return None
        return {"value": self.value, "parameter_definition_id": self.parameter_id}


class ObjectParameterValueItem(ParameterValueItem):
    """Class to hold object parameter values within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter value attributes,
    it adds attributes that are unique to the *object* entity.
    """

    def __init__(
        self,
        header,
        database=None,
        id_=None,
        parameter_id=None,
        parameter_name=None,
        value=None,
        object_id=None,
        object_name=None,
        object_class_id=None,
        object_class_name=None,
    ):
        """Init class."""
        super().__init__(header, database, id_, parameter_id, parameter_name, value)
        self.object_id = object_id
        self.object_name = object_name
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._object_dict = dict()

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        if not self.object_id:
            return None
        item = super().for_insert()
        if item:
            item["object_id"] = self.object_id
        return item


class RelationshipParameterValueItem(ParameterValueItem):
    """Class to hold relationship parameter values within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter value attributes,
    it adds attributes that are unique to the *relationship* entity.
    """

    def __init__(
        self,
        header,
        database=None,
        id_=None,
        parameter_id=None,
        parameter_name=None,
        value=None,
        relationship_id=None,
        object_id_list=None,
        object_name_list=None,
        object_class_id_list=None,
        object_class_name_list=None,
        relationship_class_id=None,
        relationship_class_name=None,
    ):
        """Init class."""
        super().__init__(header, database, id_, parameter_id, parameter_name, value)
        self.relationship_id = relationship_id
        self.object_id_list = object_id_list
        self.object_name_list = object_name_list
        self.object_class_id_list = object_class_id_list
        self.object_class_name_list = object_class_name_list
        self.relationship_class_id = relationship_class_id
        self.relationship_class_name = relationship_class_name
        self._relationship_dict = dict()
        self._object_name_class_id_tups = list()

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        if not self.relationship_id:
            return None
        item = super().for_insert()
        if item:
            item["relationship_id"] = self.relationship_id
        return item

    def relationship_for_insert(self):
        """Returns a dictionary corresponding to
        this item's relationship for adding to the db."""
        if self.relationship_id:
            # The relationship must already exist if it has an id, so...
            return None
        if (
            not self.relationship_class_id
            or not self.object_id_list
            or not self.relationship_class_name
            or not self.object_name_list
        ):
            return None
        return {
            "name": self.relationship_class_name + "_" + self.object_name_list.replace(",", "__"),
            "object_id_list": [int(x) for x in self.object_id_list.split(",")],
            "class_id": self.relationship_class_id,
        }
