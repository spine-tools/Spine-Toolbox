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

from collections import namedtuple


class ObjectParameterItemMixin:
    @property
    def entity_class(self):
        object_class = namedtuple("object_class", "id")
        return object_class(self.object_class_id)


class RelationshipParameterItemMixin:
    @property
    def entity_class(self):
        relationship_class = namedtuple("relationship_class", "id object_class_id_list")
        return relationship_class(self.relationship_class_id, self.object_class_id_list)


class ParameterItem:
    """Class to hold parameter definitions or values within an EmptyParameterModel or SubParameterModel.
    It provides __getitem__ and __setitem__ methods so the item behaves more or less like a list.
    """

    def __init__(self, header, database=None, id=None):
        """Init class.

        Args:
            header (list): header from the model where this item belong
            database (str): the database where this item comes from
            id (int): the id of the item in the database table
        """
        self._header = header
        self.database = database
        self.id = id
        self._cache = {}  # A dict for storing changes before an update
        self._attr_field_map = {}  # Map from attribute name to db field name in case they differ
        self._mandatory_attrs_for_insert = []
        self._optional_attrs_for_insert = []
        self._updatable_attrs = []

    def __getitem__(self, index):
        """Returns the item corresponding to the given index."""
        attr = self._header[index]
        return self.__getattribute__(attr)

    def __setitem__(self, index, value):
        """Sets the value for the item corresponding to the given index."""
        attr = self._header[index]
        self.__setattr__(attr, value)

    def __setattr__(self, attr, value):
        """Sets the value for the given attribute and caches the old one."""
        try:
            self._cache[attr] = self.__getattribute__(attr)
        except AttributeError:
            # This happends the first time we set an attribute
            pass
        super().__setattr__(attr, value)

    def __len__(self):
        return len(self._header)

    def for_insert(self):
        """Returns a dictionary corresponding to this item for adding to the db."""
        item = {
            self._attr_field_map.get(attr, attr): self.__getattribute__(attr)
            for attr in self._mandatory_attrs_for_insert
        }
        if not all(item.values()):
            return None
        item.update(
            {
                self._attr_field_map.get(attr, attr): self.__getattribute__(attr)
                for attr in self._optional_attrs_for_insert
                if self.__getattribute__(attr)
            }
        )
        return item

    def for_update(self):
        """Returns a dictionary with recorded changes in this item for updating in the db."""
        if not self.id or not self._cache:
            return None
        return {
            "id": self.id,
            **{
                self._attr_field_map.get(attr, attr): getattr(self, attr)
                for attr in self._updatable_attrs
                if attr in self._cache
            },
        }

    def revert(self):
        """Reverts the item to it's cached values.
        Call this after failing to update the item.
        """
        for attr, value in self._cache.items():
            self.__setattr__(attr, value)

    def clear_cache(self):
        """Clears the item's cache.
        Call this after successfully updating the item.
        """
        self._cache.clear()


class ParameterDefinitionItem(ParameterItem):
    """Class to hold parameter definitions within an EmptyParameterModel or SubParameterModel.
    It provides attributes for fields that are common to all parameter definitions
    regardless of the entity class.
    """

    def __init__(
        self,
        header,
        database=None,
        id=None,
        parameter_name=None,
        value_list_id=None,
        value_list_name=None,
        parameter_tag_id_list=None,
        parameter_tag_list=None,
        default_value=None,
    ):
        """Init class.
        """
        super().__init__(header, database, id)
        self.parameter_name = parameter_name
        self.value_list_id = value_list_id
        self.value_list_name = value_list_name
        self.parameter_tag_list = parameter_tag_list
        self.parameter_tag_id_list = parameter_tag_id_list
        self.default_value = default_value
        self._attr_field_map.update({"parameter_name": "name", "value_list_id": "parameter_value_list_id"})
        self._mandatory_attrs_for_insert.append("parameter_name")
        self._optional_attrs_for_insert.extend(["value_list_id", "default_value"])
        self._updatable_attrs.extend(["parameter_name", "value_list_id", "default_value"])

    def tag_spec(self):
        """Returns a mapping from id to tag_list for setting in the db."""
        if not self.id or not self.parameter_tag_id_list:
            return None
        return {self.id: self.parameter_tag_id_list}

    @property
    def parameter_definition_id(self):
        return self.id


class ObjectParameterDefinitionItem(ObjectParameterItemMixin, ParameterDefinitionItem):
    """Class to hold object parameter definitions within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter definition attributes,
    it adds attributes that are unique to the *object* entity class.
    """

    def __init__(
        self,
        header,
        database=None,
        id=None,
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
            id,
            parameter_name,
            value_list_id,
            value_list_name,
            parameter_tag_id_list,
            parameter_tag_list,
            default_value,
        )
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._mandatory_attrs_for_insert.append("object_class_id")


class RelationshipParameterDefinitionItem(RelationshipParameterItemMixin, ParameterDefinitionItem):
    """Class to hold relationship parameter definitions within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter definition attributes,
    it adds attributes that are unique to the *relationship* entity class.
    """

    def __init__(
        self,
        header,
        database=None,
        id=None,
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
            id,
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
        self._mandatory_attrs_for_insert.append("relationship_class_id")


class ParameterValueItem(ParameterItem):
    """Class to hold parameter values within an EmptyParameterModel or SubParameterModel.
    It provides attributes for fields that are common to all parameter values
    regardless of the entity.
    """

    def __init__(self, header, database=None, id=None, parameter_id=None, parameter_name=None, value=None):
        """Init class.
        """
        super().__init__(header, database, id)
        self.parameter_id = parameter_id
        self.parameter_name = parameter_name
        self.value = value
        self._attr_field_map.update({"parameter_id": "parameter_definition_id"})
        self._mandatory_attrs_for_insert.append("parameter_id")
        self._optional_attrs_for_insert.append("value")  # TODO: optional or mandatory?
        self._updatable_attrs.append("value")
        self._parameter_dict = dict()

    @property
    def parameter_definition_id(self):
        return self.parameter_id


class ObjectParameterValueItem(ObjectParameterItemMixin, ParameterValueItem):
    """Class to hold object parameter values within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter value attributes,
    it adds attributes that are unique to the *object* entity.
    """

    def __init__(
        self,
        header,
        database=None,
        id=None,
        parameter_id=None,
        parameter_name=None,
        value=None,
        object_id=None,
        object_name=None,
        object_class_id=None,
        object_class_name=None,
    ):
        """Init class."""
        super().__init__(header, database, id, parameter_id, parameter_name, value)
        self.object_id = object_id
        self.object_name = object_name
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._mandatory_attrs_for_insert.append("object_id")
        self._object_dict = dict()


class RelationshipParameterValueItem(RelationshipParameterItemMixin, ParameterValueItem):
    """Class to hold relationship parameter values within an EmptyParameterModel or SubParameterModel.
    On top of the common parameter value attributes,
    it adds attributes that are unique to the *relationship* entity.
    """

    def __init__(
        self,
        header,
        database=None,
        id=None,
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
        super().__init__(header, database, id, parameter_id, parameter_name, value)
        self.relationship_id = relationship_id
        self.object_id_list = object_id_list
        self.object_name_list = object_name_list
        self.object_class_id_list = object_class_id_list
        self.object_class_name_list = object_class_name_list
        self.relationship_class_id = relationship_class_id
        self.relationship_class_name = relationship_class_name
        self._mandatory_attrs_for_insert.append("relationship_id")
        self._relationship_dict = dict()
        self._object_name_class_id_tups = list()

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
