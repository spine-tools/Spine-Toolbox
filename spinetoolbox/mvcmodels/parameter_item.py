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


class ParameterItem:
    """Class to hold parameter definitions or values within a subclass of MinimalTableModel.
    It provides __getitem__ and __setitem__ methods so the item behaves more or less like a list.
    """

    def __init__(self, header, database=None, db_map=None, id=None):
        """Init class.

        Args:
            header (list): header from the model where this item belong
            database (str): the name of the database where this item comes from
            db_map (DiffDatabaseMapping): the db mapping to the database
            id (int): the id of the item in the db_map table
        """
        self._header = header
        self.database = database
        self.db_map = db_map
        self.id = id
        self._cache = {}  # A dict for storing changes before an update
        self._attr_field_map = {}  # Map from attribute name to db field name in case they differ
        self._mandatory_attrs_for_insert = []
        self._optional_attrs_for_insert = []
        self._updatable_attrs = []

    @property
    def entity_class(self):
        """Returns a named tuple corresponding to the entity associated with this parameter.
        Must be reimplemented by subclasses.
        """
        raise NotImplementedError()

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


class ObjectParameterItemMixin:
    """Provides a common interface to object parameter definition and value items."""

    def __init__(
        self, header, database=None, db_map=None, id=None, object_class_id=None, object_class_name=None, **kwargs
    ):
        """Init class."""
        super().__init__(header, database, db_map, id, **kwargs)
        self.object_class_id = object_class_id
        self.object_class_name = object_class_name
        self._mandatory_attrs_for_insert.append("object_class_id")

    @property
    def entity_class(self):
        """Returns a named tuple corresponding to the entity associated with this parameter."""
        object_class = namedtuple("object_class", "id")
        return object_class(self.object_class_id)


class RelationshipParameterItemMixin:
    """Provides a common interface to relationship parameter definition and value items."""

    def __init__(
        self,
        header,
        database=None,
        db_map=None,
        id=None,
        relationship_class_id=None,
        relationship_class_name=None,
        object_class_id_list=None,
        object_class_name_list=None,
        **kwargs
    ):
        """Init class."""
        super().__init__(header, database, db_map, id, **kwargs)
        self.relationship_class_id = relationship_class_id
        self.relationship_class_name = relationship_class_name
        self.object_class_id_list = object_class_id_list
        self.object_class_name_list = object_class_name_list
        self._mandatory_attrs_for_insert.append("relationship_class_id")

    @property
    def entity_class(self):
        """Returns a named tuple corresponding to the entity associated with this parameter."""
        relationship_class = namedtuple("relationship_class", "id object_class_id_list")
        return relationship_class(self.relationship_class_id, self.object_class_id_list)

    def rename_object_classes(self, object_classes):
        """Rename object class.

        Args:
            object_classes (dict): maps id to new name
        """
        if not self.object_class_id_list:
            return False
        split_object_class_id_list = [int(id_) for id_ in self.object_class_id_list.split(",")]
        matches = [(k, id_) for k, id_ in enumerate(split_object_class_id_list) if id_ in object_classes]
        if not matches:
            return False
        split_object_class_name_list = self.object_class_name_list.split(",")
        for k, id_ in matches:
            new_name = object_classes[id_]
            split_object_class_name_list[k] = new_name
        self.object_class_name_list = ",".join(split_object_class_name_list)
        return True


class ParameterDefinitionItemMixin:
    """Provides a common interface to all parameter definitions regardless of the entity class."""

    def __init__(
        self,
        header,
        database=None,
        db_map=None,
        id=None,
        parameter_name=None,
        value_list_id=None,
        value_list_name=None,
        parameter_tag_id_list=None,
        parameter_tag_list=None,
        default_value=None,
        **kwargs
    ):
        """Init class.
        """
        super().__init__(header, database, db_map, id, **kwargs)
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

    def rename_parameter_tags(self, parameter_tags):
        """Rename parameter tags.

        Args:
            parameter_tags (dict): maps id to new tag
        """
        if not self.parameter_tag_id_list:
            return False
        split_parameter_tag_id_list = [int(id_) for id_ in self.parameter_tag_id_list.split(",")]
        matches = [(k, id_) for k, id_ in enumerate(split_parameter_tag_id_list) if id_ in parameter_tags]
        if not matches:
            return False
        split_parameter_tag_list = self.parameter_tag_list.split(",")
        for k, id_ in matches:
            new_tag = parameter_tags[id_]
            split_parameter_tag_list[k] = new_tag
        self.parameter_tag_list = ",".join(split_parameter_tag_list)
        return True

    def remove_parameter_tags(self, parameter_tag_ids):
        """Remove parameter tags.

        Args:
            parameter_tag_ids (set): set of ids to remove
        """
        if not self.parameter_tag_id_list:
            return False
        split_parameter_tag_id_list = [int(id_) for id_ in self.parameter_tag_id_list.split(",")]
        matches = [k for k, id_ in enumerate(split_parameter_tag_id_list) if id_ in parameter_tag_ids]
        if not matches:
            return False
        split_parameter_tag_list = self.parameter_tag_list.split(",")
        for k in sorted(matches, reverse=True):
            del split_parameter_tag_list[k]
        self.parameter_tag_list = ",".join(split_parameter_tag_list)
        return True


class ParameterValueItemMixin:
    """Provides a common interface to all parameter definitions regardless of the entity class."""

    def __init__(
        self, header, database=None, db_map=None, id=None, parameter_id=None, parameter_name=None, value=None, **kwargs
    ):
        """Init class.
        """
        super().__init__(header, database, db_map, id, **kwargs)
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


class ObjectParameterDefinitionItem(ObjectParameterItemMixin, ParameterDefinitionItemMixin, ParameterItem):
    """Class to hold object parameter definitions within a subclass of MinimalTableModel."""


class RelationshipParameterDefinitionItem(RelationshipParameterItemMixin, ParameterDefinitionItemMixin, ParameterItem):
    """Class to hold relationship parameter definitions within a subclass of MinimalTableModel."""


class ObjectParameterValueItem(ObjectParameterItemMixin, ParameterValueItemMixin, ParameterItem):
    """Class to hold object parameter values within a subclass of MinimalTableModel."""

    def __init__(self, header, database=None, db_map=None, id=None, object_id=None, object_name=None, **kwargs):
        """Init class."""
        super().__init__(header, database, db_map, id, **kwargs)
        self.object_id = object_id
        self.object_name = object_name
        self._mandatory_attrs_for_insert.append("object_id")
        self._object_dict = dict()


class RelationshipParameterValueItem(RelationshipParameterItemMixin, ParameterValueItemMixin, ParameterItem):
    """Class to hold relationship parameter values within a subclass of MinimalTableModel."""

    def __init__(
        self,
        header,
        database=None,
        db_map=None,
        id=None,
        relationship_id=None,
        object_id_list=None,
        object_name_list=None,
        **kwargs
    ):
        """Init class."""
        super().__init__(header, database, db_map, id, **kwargs)
        self.relationship_id = relationship_id
        self.object_id_list = object_id_list
        self.object_name_list = object_name_list
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

    def rename_objects(self, objects):
        """Rename objects.

        Args:
            objects (dict): maps id to new name
        """
        if not self.object_id_list:
            return False
        split_object_id_list = [int(id_) for id_ in self.object_id_list.split(",")]
        matches = [(k, id_) for k, id_ in enumerate(split_object_id_list) if id_ in objects]
        if not matches:
            return False
        split_object_name_list = self.object_name_list.split(",")
        for k, id_ in matches:
            new_name = objects[id_]
            split_object_name_list[k] = new_name
        self.object_name_list = ",".join(split_object_name_list)
        return True
