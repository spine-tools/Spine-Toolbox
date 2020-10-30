######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
For exporting a database to GAMS .gdx file.

Currently, this module supports databases that are "GAMS-like", that is, they follow the EAV model
but the object classes, objects, relationship classes etc. directly reflect the GAMS data
structures. Conversions e.g. from Spine model to TIMES are not supported at the moment.

This module contains low level functions for reading a database into an intermediate format and
for writing that intermediate format into a .gdx file. A higher lever function
:func:`to_gdx_file` that does basically everything needed for exporting is provided for convenience.

:author: A. Soininen (VTT)
:date:   30.8.2019
"""

import enum
import functools
import math
import os
import os.path
import sys
from gdx2py import GAMSSet, GAMSScalar, GAMSParameter, GdxFile
from spinedb_api import from_database, IndexedValue, Map, ParameterValueFormatError

if sys.platform == "win32":
    import winreg


@enum.unique
class NoneExport(enum.Enum):
    """Options to export None values."""

    DO_NOT_EXPORT = 0
    """Does not export Nones."""
    EXPORT_AS_NAN = 1
    """Replace Nones with NaNs while exporting."""


@enum.unique
class NoneFallback(enum.Enum):
    """Options load None values from the database."""

    USE_IT = 0
    """Keep using the value."""
    USE_DEFAULT_VALUE = 1
    """Replace None by the default value."""


class GdxExportException(Exception):
    """An exception raised when something goes wrong within the gdx module."""

    def __init__(self, message):
        """
        Args:
            message (str): a message detailing the cause of the exception
        """
        super().__init__()
        self._message = message

    @property
    def message(self):
        """A message detailing the cause of the exception."""
        return self._message

    def __str__(self):
        """Returns the message detailing the cause of the exception."""
        return self._message


class GdxUnsupportedValueTypeException(GdxExportException):
    """An exception raised when an unsupported parameter type is read from the database."""


class Set:
    """
    Represents a GAMS domain, set or a subset.

    Attributes:
        description (str): set's explanatory text
        domain_names (tuple of str): a list of superset (domain) names, None if the Set is a domain
        name (str): set's name
        records (list of Record): set's elements as a list of Record objects
    """

    def __init__(self, name, description="", domain_names=None):
        """
        Args:
            name (str): set's name
            description (str): set's explanatory text
            domain_names (tuple of str, optional): a list of indexing domain names
        """
        self.description = description if description is not None else ""
        self.domain_names = domain_names if domain_names is not None else (None,)
        self.name = name
        self.records = list()

    @property
    def dimensions(self):
        """Number of dimensions of this Set."""
        return len(self.domain_names)

    def is_domain(self):
        """Returns True if this set is a domain set."""
        return self.domain_names[0] is None


def _drop_sets_not_in_settings(sets, set_names, logger):
    """
    Removes sets for ``sets`` that are not mentioned in ``set_names``.

    Args:
        sets (Iterable of Set): sets
        set_names (Iterable of str): names to check against
        logger (LoggerInterface, optional): a logger

    Returns:
        list of Set: remaining sets
    """
    keep = list()
    missing_names = list()
    for set_ in sets:
        if set_.name in set_names:
            keep.append(set_)
        else:
            missing_names.append(set_.name)
    if missing_names:
        if logger is not None:
            logger.msg_warning.emit(
                "Skipping the following domains/sets which are missing from export settings: "
                f"{', '.join(missing_names)}"
            )
        else:
            raise GdxExportException(f"Missing domains/sets in export settings: {', '.join(missing_names)}")
    return keep


class Record:
    """
    Represents a GAMS set element in a :class:`Set`.

    Attributes:
        keys (tuple): a tuple of record's keys
    """

    def __init__(self, keys):
        """
        Args:
            keys (tuple): a tuple of record's keys
        """
        self.keys = keys

    def __eq__(self, other):
        """
        Returns True if other is equal to self.

        Args:
            other (Record):  a record to compare to
        """
        if not isinstance(other, Record):
            return NotImplemented
        return other.keys == self.keys

    @property
    def name(self):
        """Record's 'name' as a comma separated list of its keys."""
        return ",".join(self.keys)


class Parameter:
    """
    Represents a GAMS parameter.

    Attributes:
        domain_names (tuple of str): indexing domain names (currently Parameters can be indexed by domains only)
        data (dict): a map from index tuples to parsed values
    """

    def __init__(self, domain_names, indexes, values):
        """
        Args:
            domain_names (tuple of str): indexing domain names (currently Parameters can be indexed by domains only)
            indexes (list): parameter's indexes
            values (list): parameter's values
        """
        self.domain_names = domain_names
        if len(indexes) != len(values):
            raise GdxExportException("Parameter index and value length mismatch.")
        if values and not all([isinstance(value, type(values[0])) or value is None for value in values[1:]]):
            raise GdxExportException("Not all values are of the same type.")
        self.data = dict(zip(indexes, values))

    def __eq__(self, other):
        """
        Compares two :class:`Parameter` objects for equality.

        Args:
            other (Parameter): a parameter

        Returns:
            bool: True if the parameters are equal, False otherwise
        """
        if not isinstance(other, Parameter):
            return NotImplemented
        return other.domain_names == self.domain_names and other.data == self.data

    @property
    def indexes(self):
        """list: indexing key tuples"""
        return self.data.keys()

    @property
    def values(self):
        """list: parsed values"""
        return self.data.values()

    def is_consistent(self):
        """Checks that all values are :class:`IndexedValue` objects or scalars."""
        if not self.data:
            return True
        if all(value is None or isinstance(value, IndexedValue) for value in self.data.values()):
            return True
        return all(value is None or isinstance(value, float) for value in self.data.values())

    def slurp(self, parameter):
        """
        Appends the indexes and values from another parameter.

        Args:
            parameter (Parameter): a parameter to append from
        """
        if len(parameter.domain_names) != len(self.domain_names):
            raise GdxExportException(f"Cannot combine domains {self.domain_names} into {parameter.domain_names}.")
        domain_names = list()
        for name, other_name in zip(self.domain_names, parameter.domain_names):
            if name == other_name:
                domain_names.append(name)
            else:
                domain_names.append(None)
        self.domain_names = tuple(domain_names)
        self.data.update(parameter.data)

    def is_scalar(self):
        """Returns True if this parameter seems to contain scalars."""
        return all(not isinstance(value, IndexedValue) for value in self.data.values())

    def is_indexed(self):
        """Returns True if this parameter seems to contain indexed values."""
        return all(isinstance(value, IndexedValue) for value in self.data.values())

    def expand_indexes(self, indexing_setting, sets):
        """
        Expands indexed values to scalars in place by adding a new dimension (index).

        The indexes and values attributes are resized to accommodate all scalars in the indexed values.
        A new indexing domain is inserted to domain_names and the corresponding keys into indexes.
        Effectively, this increases parameter's dimensions by one.

        Args:
            indexing_setting (IndexingSetting): description of how the expansion should be done
            sets (dict): mapping from set name to :class:`Set`
        """
        index_position = indexing_setting.index_position
        indexing_domain_name = indexing_setting.indexing_domain_name
        self.domain_names = (
            self.domain_names[:index_position] + (indexing_domain_name,) + self.domain_names[index_position:]
        )
        set_ = sets[indexing_domain_name]
        picked_records = [record.keys for i, record in enumerate(set_.records) if indexing_setting.picking.pick(i)]
        new_data = dict()
        for parameter_index, parameter_value in self.data.items():
            if parameter_value is None:
                continue
            if isinstance(parameter_value, IndexedValue):
                values = parameter_value.values
            else:
                raise GdxExportException("Cannot expand indexes of a scalar value.")
            for new_index, new_value in zip(picked_records, values):
                expanded_index = tuple(parameter_index[:index_position] + new_index + parameter_index[index_position:])
                new_data[expanded_index] = new_value
        self.data = new_data


def _drop_parameters_conflicting_with_sets(parameters, set_settings, logger):
    """
    Filters out parameters whose names clash with existing domain or set names.

    Args:
        parameters (dict): a mapping from parameter name to a dict of domain names and :class:`Parameter`
        set_settings (SetSettings): export settings
        logger (LoggerInterface, optional): a logger

    Return:
        dict: filtered parameters
    """
    keep = dict()
    reserved_names = {name for name in set_settings.domain_names if set_settings.is_exportable(name)} | {
        name for name in set_settings.set_names if set_settings.is_exportable(name)
    }
    for parameter_name, by_dimensions in parameters.items():
        if parameter_name in reserved_names:
            if logger is not None:
                logger.msg_warning.emit(
                    f"Skipping parameter '{parameter_name}' as it conflicts with a domain/set with the same name."
                )
                continue
            else:
                raise GdxExportException(
                    f"Parameter '{parameter_name}' conflicts with a domain/set with the same name."
                )
        keep[parameter_name] = by_dimensions
    return keep


class Picking:
    """
    An interface for picking objects.

    Picking object are used to select indexes from an indexing domain when performing parameter index expansion.
    """

    def pick(self, i):
        """
        Returns pick for given indexing domain record.

        Args:
            i (int): record index

        Returns:
            bool: True if the record is picked, False otherwise
        """
        raise NotImplementedError()

    def to_dict(self):
        """
        Serializes the picking to a dict.

        Returns:
            dict: serialized picking
        """

    @staticmethod
    def from_dict(picking_dict):
        """
        Deseriealizes the picking from a dict.

        Args:
            picking_dict (dict): serialized picking

        Returns:
            Picking: deserialized picking
        """


class FixedPicking(Picking):
    """Picking from a fixed boolean array."""

    def __init__(self, picked):
        """
        Args:
            picked (list of bool): a list of booleans, where True picks and False drops a record
        """
        self._picked = picked

    def __eq__(self, other):
        """
        Compared pickings for equality.

        Args:
            other (FixedPicking): another picking

        Returns:
            bool: True if the pickings are equal, False otherwise
        """
        if not isinstance(other, FixedPicking):
            return False
        return other._picked == self._picked

    def pick(self, i):
        """See base class."""
        return self._picked[i]

    def to_dict(self):
        """See base class."""
        if all(self._picked):
            return {"picking": f"all {len(self._picked)}"}
        return {"picking_type": "fixed", "picking": self._picked}

    @staticmethod
    def from_dict(picking_dict):
        """See base class."""
        entry = picking_dict["picking"]
        if isinstance(entry, str):
            _, _, length = entry.partition(" ")
            picking = int(length) * [True]
        else:
            picking = entry
        return FixedPicking(picking)


class GeneratedPicking(Picking):
    """
    Picking using a Python expression.

    The expression should return a value that can be cast to bool. It has a single parameter, ``i``, at its disposal.
    This is a one-based index to the pick list.
    """

    def __init__(self, expression):
        """
        Args:
            expression (str): the expression used for picking
        """
        self._expression = expression
        self._pick = None

    def pick(self, i):
        """See base class."""
        if self._pick is None:
            try:
                compiled = compile(self._expression, "<string>", "eval")
            except (SyntaxError, ValueError):
                raise GdxExportException("Failed to compile pick expression.")
            self._pick = functools.partial(eval, compiled, {})
        try:
            return bool(self._pick({"i": (i + 1)}))
        except (AttributeError, NameError, ValueError):
            raise GdxExportException("Failed to evaluate pick expression.")

    def to_dict(self):
        """See base class."""
        return {"picking_type": "expression", "picking": self._expression}

    @staticmethod
    def from_dict(picking_dict):
        """See base class."""
        expression = picking_dict["picking"]
        return GeneratedPicking(expression)

    @property
    def expression(self):
        """the picking expression"""
        return self._expression


def _picking_from_dict(picking_dict):
    """
    Deserializes pickings from dictionary.

    Args:
        picking_dict (dict): a serialized picking

    Returns:
        Picking: a :class:`FixedPicking` or :class:`GeneratedPicking`
    """
    picking_type = picking_dict.get("picking_type")
    if picking_type is None:
        picking_type = "fixed"
    if picking_type == "fixed":
        return FixedPicking.from_dict(picking_dict)
    return GeneratedPicking.from_dict(picking_dict)


class Records:
    """An interface for records used in :class:`SetSettings`."""

    def __eq__(self, other):
        """
        Tests for equality.

        Returns:
             bool: True if the records are equal, False otherwise.
        """
        raise NotImplementedError()

    def __len__(self):
        """
        Gives the number of records

        Returns:
            int: number of records
        """
        raise NotImplementedError()

    @property
    def records(self):
        """stored records as a list of key tuples"""
        raise NotImplementedError()

    def shuffle(self, new_order):
        """
        Reorders the records if the order is not fixed, otherwise raises :class:`NotImplementedError`.

        Args:
            new_order (list of tuple): new records
        """
        raise NotImplementedError()

    def is_shufflable(self):
        """
        Tells if the records can be shuffled.

        Returns:
            bool: True if the records can be shuffled, False otherwise
        """
        raise NotImplementedError()

    @staticmethod
    def update(old, new):
        """
        Merges two records.

        Args:
            old (Records): the 'original' records
            new (Records): 'new' records

        Returns:
            Records: merged records
        """
        raise NotImplementedError()

    def to_dict(self):
        """
        Serializes the records to a dict.

        Returns:
            dict: serialized records.
        """
        raise NotImplementedError()

    @staticmethod
    def from_dict(record_dict):
        """
        Deserializes records from a dict.

        Args:
            record_dict: serialized records

        Return:
            Records: deserialized records
        """
        raise NotImplementedError()


class LiteralRecords(Records):
    """Shufflable records with fixed keys."""

    def __init__(self, records):
        """
        Args:
            records (list of tuple): list of key tuples
        """
        self._records = records

    def __eq__(self, other):
        """
        Compares two :class:`LiteralRecords` for equality.

        Args:
            other (LiteralRecords): records to compare to

        Returns:
            bool: True if the key lists are equal, False otherwise
        """
        if not isinstance(other, LiteralRecords):
            return False
        return self._records == other._records

    def __len__(self):
        """See base class."""
        return len(self._records)

    @property
    def records(self):
        """See base class."""
        return self._records

    def shuffle(self, new_order):
        """See base class."""
        self._records = new_order

    def is_shufflable(self):
        """Returns True; :class:`LiteralRecords` is shufflable."""
        return True

    @staticmethod
    def update(old, new):
        """
        Updates the keys from another :class:`LiteralRecords`.

        Common keys are kept in their old order while new keys are added last.
        Keys present only in old records are dropped.

        Args:
            old (LiteralRecords): original records
            new (LiteralRecords): new records

        Returns:
            LiteralRecords: updated records
        """
        old_keys = set(old.records)
        new_keys = set(new.records)
        common_records = old_keys & new_keys
        retained = [record for record in old.records if record in common_records]
        new_key_order = {key: i for i, key in enumerate(new.records)}
        new = sorted(new_keys - old_keys, key=lambda key: new_key_order[key])
        return LiteralRecords(retained + new)

    def to_dict(self):
        """See base class."""
        return {"indexing_type": "fixed", "indexes": self._records}

    @staticmethod
    def from_dict(record_dict):
        """See base class."""
        records = [tuple(keys) for keys in record_dict["indexes"]]
        return LiteralRecords(records)


class GeneratedRecords(Records):
    """
    Non-shuffleable records where keys are generated by a Python expression.

    The expression should return a string.The expression has a single parameter, ``i``, at it disposal.
    ``i`` is a one-based index to the pick list.
    """

    def __init__(self, expression, length):
        """
        Args:
            expression (str): key generator expression
            length (int): number of records to generate
        """
        self._expression = expression
        self._length = length
        self._records = None

    def __eq__(self, other):
        """
        Compares to another :class:`GeneratedRecords` for equality

        Args:
            other (GeneratedRecords): records

        Returns:
            bool: True if the record expressions and lengths are equal, False otherwise
        """
        if not isinstance(other, GeneratedRecords):
            return False
        return self._expression == other._expression and self._length == other._length

    def __len__(self):
        """See base class."""
        return self._length if self._expression else 0

    @property
    def expression(self):
        """the expression used to generate the records"""
        return self._expression

    @property
    def records(self):
        """See base class."""
        if self._records is None:
            self._records = self._record_list()
        return self._records

    def shuffle(self, new_order):
        """See base class."""
        raise NotImplementedError()

    def is_shufflable(self):
        """Returns False; :class:`GeneratedRecords` is not shuffleable."""
        return False

    @staticmethod
    def update(old, new):
        """Updating is not supported by :class:`GeneratedRecords`."""
        raise NotImplementedError()

    def to_dict(self):
        """See base class."""
        return {"indexing_type": "expression", "indexes": self._expression, "length": self._length}

    @staticmethod
    def from_dict(record_dict):
        """See base class."""
        return GeneratedRecords(record_dict["indexes"], record_dict["length"])

    def _record_list(self):
        """
        Generates records according to given Python expression.

        Returns:
            list: generated records
        """
        try:
            compiled = compile(self._expression, "<string>", "eval")
        except (SyntaxError, ValueError):
            raise GdxExportException("Failed to compile index expression.")
        generate_record = functools.partial(eval, compiled, {})
        try:
            records = [(generate_record({"i": i}),) for i in range(1, self._length + 1)]  # pylint: disable=eval-used
        except (AttributeError, NameError, ValueError):
            raise GdxExportException("Failed to evaluate index expression.")
        return records


class ExtractedRecords(Records):
    """Records that are extracted from an indexed parameter."""

    def __init__(self, parameter_name, domain_names, indexes):
        """
        Args:
            parameter_name (str): name of the parameter from which the records were extracted
            domain_names (tuple): parameter's indexing domains
            indexes (list of tuple): records
        """
        self._parameter_name = parameter_name
        self._domain_names = domain_names
        self._records = indexes

    def __eq__(self, other):
        """
        Compares two :class:`ExtractedRecords` for equality.

        Args:
            other (ExtractedRecords): records to compare to

        Returns:
            bool: True if the records and parameter name are equal, False otherwise
        """
        if not isinstance(other, ExtractedRecords):
            return False
        return (
            self._records == other._records
            and self._parameter_name == other._parameter_name
            and self._domain_names == other._domain_names
        )

    def __len__(self):
        """See base class."""
        return len(self._records)

    @property
    def parameter_name(self):
        """name of the parameter from which the records were extracted"""
        return self._parameter_name

    @property
    def domain_names(self):
        """parameter's indexing domains"""
        return self._domain_names

    @property
    def records(self):
        """See base class."""
        return self._records

    def shuffle(self, new_order):
        """See base class."""
        raise NotImplementedError()

    def is_shufflable(self):
        """Returns False; :class:`ExtractedRecords` is never shufflable."""
        return False

    @staticmethod
    def update(old, new):
        """
        Takes the parameter name from old and the records from new.

        Args:
            old (ExtractedRecords): original records
            new (ExtractedRecords): new records

        Returns:
            ExtractedRecords: merged records
        """
        return ExtractedRecords(old.parameter_name, new.domain_names, new.records)

    def to_dict(self):
        """See base class."""
        return {
            "indexing_type": "extracted",
            "parameter_name": self._parameter_name,
            "domain_names": self._domain_names,
            "indexes": self._records,
        }

    @staticmethod
    def from_dict(record_dict):
        """See base class."""
        indexes = [tuple(i) for i in record_dict["indexes"]]
        domain_names = record_dict.get("domain_names")
        if domain_names is not None:
            domain_names = tuple(domain_names)
        return ExtractedRecords(record_dict["parameter_name"], domain_names, indexes)


def _update_records(old, new):
    """
    Updates records where appropriate.

    Args:
        old (Records): original records
        new (Records): new records

    Returns:
        Records: updated records
    """
    if isinstance(old, LiteralRecords) and isinstance(new, LiteralRecords):
        return LiteralRecords.update(old, new)
    if isinstance(old, ExtractedRecords) and isinstance(new, ExtractedRecords):
        return ExtractedRecords.update(old, new)
    return old


def _records_from_dict(record_dict):
    """
    Deserializes records from a dict.

    Args:
        record_dict (dict): serialized records

    Returns:
        Records: deserialized records
    """
    type_ = record_dict["indexing_type"]
    if type_ == "fixed":
        return LiteralRecords.from_dict(record_dict)
    if type_ == "expression":
        return GeneratedRecords.from_dict(record_dict)
    return ExtractedRecords.from_dict(record_dict)


def _python_interpreter_bitness():
    """Returns 64 for 64bit Python interpreter or 32 for 32bit interpreter."""
    # As recommended in Python's docs:
    # https://docs.python.org/3/library/platform.html#cross-platform
    return 64 if sys.maxsize > 2 ** 32 else 32


def _read_value(value_in_database):
    """Converts a parameter from its database representation to a value object."""
    try:
        value = from_database(value_in_database)
    except ParameterValueFormatError:
        raise GdxExportException("Failed to read parameter_value.")
    if value is not None and not isinstance(value, (float, IndexedValue)):
        raise GdxUnsupportedValueTypeException(f"Unsupported parameter_value type '{type(value).__name__}'.")
    if isinstance(value, Map):
        if value.is_nested():
            raise GdxUnsupportedValueTypeException("Nested maps are not supported.")
        if not all(isinstance(x, float) for x in value.values):
            raise GdxUnsupportedValueTypeException("Exporting non-numerical values in map is not supported.")
    return value


def _windows_dlls_exist(gams_path):
    """Returns True if required DLL files exist in given GAMS installation path."""
    bitness = _python_interpreter_bitness()
    # This DLL must exist on Windows installation
    dll_name = "gdxdclib{}.dll".format(bitness)
    dll_path = os.path.join(gams_path, dll_name)
    return os.path.isfile(dll_path)


def find_gams_directory():
    """
    Returns GAMS installation directory or None if not found.

    On Windows systems, this function looks for `gams.location` in registry;
    on other systems the `PATH` environment variable is checked.

    Returns:
        a path to GAMS installation directory or None if not found.
    """
    if sys.platform == "win32":
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "gams.location") as gams_location_key:
                gams_path, _ = winreg.QueryValueEx(gams_location_key, "")
                if not _windows_dlls_exist(gams_path):
                    return None
                return gams_path
        except FileNotFoundError:
            return None
    executable_paths = os.get_exec_path()
    for path in executable_paths:
        if "gams" in path.casefold():
            return path
    return None


def expand_indexed_parameter_values(parameters, indexing_settings, sets):
    """
    Expands the dimensions of indexed parameter values.

    Args:
        parameters (dict): a map from parameter names to a dict of domain names and :class:`Parameters`
        indexing_settings (dict): mapping from parameter name to :class:`IndexingSetting`
        sets (dict): mapping from domain name to :class:`Set`

    Returns:
        dict: parameters that have had their indexes expanded and can thus be removed
    """
    erasable = dict()
    for parameter_name, by_dimensions in parameters.items():
        try:
            indexing_settings_by_dimension = indexing_settings[parameter_name]
        except KeyError:
            continue
        newly_expanded = dict()
        for domain_names, parameter in by_dimensions.items():
            try:
                indexing_setting = indexing_settings_by_dimension[domain_names]
            except KeyError:
                continue
            try:
                parameter.expand_indexes(indexing_setting, sets)
            except GdxExportException as error:
                raise GdxExportException(f"Problem with parameter '{parameter_name}': {error}")
            existing = by_dimensions.get(parameter.domain_names)
            if existing is None:
                newly_expanded[parameter.domain_names] = parameter
            else:
                existing.slurp(parameter)
            erasable.setdefault(parameter_name, list()).append(domain_names)
        by_dimensions.update(newly_expanded)
    return erasable


class MergingSetting:
    """
    Holds settings needed to merge a single parameter.

    Attributes:
        parameter_names (list of str): parameters to merge
        new_domain_name (str): name of the additional domain that contains the parameter names
        new_domain_description (str): explanatory text for the additional domain
        previous_set (str): name of the set containing the parameters before merging;
            not needed for the actual merging but included here to make the parameters' origin traceable
        previous_domain_names (tuple of str): parameter's original dimensions
        index_position (int): new dimension's position in the dimension list
    """

    def __init__(self, parameter_names, new_domain_name, new_domain_description, previous_set, previous_domain_names):
        """
        Args:
            parameter_names (list of str): parameters to merge
            new_domain_name (str): name of the additional domain that contains the parameter names
            new_domain_description (str): explanatory text for the additional domain
            previous_set (str): name of the set containing the parameters before merging
            previous_domain_names (tuple of str): list of parameters' original indexing domains
        """
        self.parameter_names = parameter_names
        self.new_domain_name = new_domain_name
        self.new_domain_description = new_domain_description
        self.previous_set = previous_set
        self.previous_domain_names = previous_domain_names
        self.index_position = len(previous_domain_names)

    def domain_names(self):
        """
        Composes a list of merged parameter's indexing domains.

        Returns:
            tuple: a list of indexing domains including the new domain containing the merged parameters' names
        """
        return (
            self.previous_domain_names[: self.index_position]
            + (self.new_domain_name,)
            + self.previous_domain_names[self.index_position :]
        )

    def to_dict(self):
        """Stores the settings to a dictionary."""
        return {
            "parameters": self.parameter_names,
            "new_domain": self.new_domain_name,
            "domain_description": self.new_domain_description,
            "previous_set": self.previous_set,
            "previous_domains": self.previous_domain_names,
            "index_position": self.index_position,
        }

    @staticmethod
    def from_dict(setting_dict):
        """Restores settings from a dictionary."""
        parameters = setting_dict["parameters"]
        new_domain = setting_dict["new_domain"]
        description = setting_dict["domain_description"]
        previous_set = setting_dict["previous_set"]
        previous_domains = tuple(setting_dict["previous_domains"])
        index_position = setting_dict["index_position"]
        setting = MergingSetting(parameters, new_domain, description, previous_set, previous_domains)
        setting.index_position = index_position
        return setting


def update_merging_settings(merging_settings, set_settings, db_map):
    """
    Returns parameter merging settings updated according to new export settings.

    Args:
        merging_settings (dict): old merging settings
        set_settings (SetSettings): new set settings
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database map
    Returns:
        dict: updated merging settings
    """
    updated = dict()
    for merged_parameter_name, setting_list in merging_settings.items():
        updated_list = list()
        for setting in setting_list:
            if setting.previous_set not in set_settings.domain_names | set_settings.set_names:
                continue
            entity_class_sq = db_map.entity_class_sq
            entity_class = db_map.query(entity_class_sq).filter(entity_class_sq.c.name == setting.previous_set).first()
            class_id = entity_class.id
            type_id = entity_class.type_id
            type_name = (
                db_map.query(db_map.entity_class_type_sq)
                .filter(db_map.entity_class_type_sq.c.id == type_id)
                .first()
                .name
            )
            if type_name == "object":
                parameters = db_map.parameter_definition_list(object_class_id=class_id)
            elif type_name == "relationship":
                parameters = db_map.parameter_definition_list(relationship_class_id=class_id)
            else:
                raise GdxExportException(f"Unknown entity_class type '{type_name}'")
            defined_parameter_names = [parameter.name for parameter in parameters]
            if not defined_parameter_names:
                continue
            setting.parameter_names = defined_parameter_names
            updated_list.append(setting)
        if setting_list:
            updated[merged_parameter_name] = setting_list
    return updated


def merging_records(merging_setting):
    """
    Constructs records which contain the merged parameters' names.

    Args:
        merging_setting (MergingSetting): settings
    Returns:
        Records: records needed to index merged parameters
    """
    keys = [(name,) for name in merging_setting.parameter_names]
    return LiteralRecords(keys)


def merge_parameters(parameters, merging_settings):
    """
    Merges multiple parameters into a single parameter.

    Args:
        parameters (dict): a mapping from existing parameter name to its Parameter object
        merging_settings (dict): a mapping from the merged parameter name to a list of merging settings

    Returns:
        dict: a dict of parameters that should be removed from the parameters dict
    """
    erasable = dict()
    for merged_name, setting_list in merging_settings.items():
        for setting in setting_list:
            indexes = list()
            values = list()
            index_position = setting.index_position
            merged_domain_names = setting.domain_names()
            for name in setting.parameter_names:
                try:
                    parameter = parameters[name][setting.previous_domain_names]
                except KeyError:
                    continue
                erasable.setdefault(name, list()).append(setting.previous_domain_names)
                if len(merged_domain_names) < len(parameter.domain_names) + 1:
                    raise GdxExportException(
                        f"Merged parameter '{merged_name}' contains indexed values and therefore cannot be merged."
                    )
                for value, base_index in zip(parameter.values, parameter.indexes):
                    expanded_index = base_index[:index_position] + (name,) + base_index[index_position:]
                    indexes.append(expanded_index)
                    values.append(value)
            try:
                merged_parameter = Parameter(merged_domain_names, indexes, values)
            except GdxExportException as error:
                raise GdxExportException(f"Error while merging parameter '{merged_name}': {error}")
            by_dimensions = parameters.setdefault(merged_name, dict())
            existing = by_dimensions.get(merged_domain_names)
            if existing is None:
                by_dimensions[merged_domain_names] = merged_parameter
            else:
                existing.slurp(merged_parameter)
    return erasable


def sets_to_gams(gdx_file, sets, set_settings):
    """
    Writes Set objects to .gdx file as GAMS sets.

    Records and Parameters contained within the Sets are written as well.

    Args:
        gdx_file (GdxFile): a target file
        sets (list of Set): a list of Set objects
        set_settings (SetSettings): export settings
    """
    for current_set in sets:
        if not set_settings.is_exportable(current_set.name):
            continue
        record_keys = list()
        for record in current_set.records:
            if record is None:
                raise RuntimeError()
            record_keys.append(record.keys)
        gams_set = GAMSSet(record_keys, current_set.domain_names, expl_text=current_set.description)
        try:
            gdx_file[current_set.name] = gams_set
        except NotImplementedError as error:
            raise GdxExportException(f"Failed to write to .gdx file: {error}.")


def parameters_to_gams(gdx_file, parameters, none_export):
    """
    Writes parameters to .gdx file as GAMS parameters.

    Args:
        gdx_file (GdxFile): a target file
        parameters (dict): a list of Parameter objects
        none_export (NoneExport): option how to handle None values
    """
    for parameter_name, by_dimension in parameters.items():
        namesakes = list(by_dimension.values())
        parameter = namesakes[0]
        for other in namesakes[1:]:
            parameter.slurp(other)
        indexed_values = dict()
        for index, value in zip(parameter.indexes, parameter.values):
            if index is None:
                continue
            if isinstance(value, IndexedValue):
                raise GdxExportException(
                    f"Cannot write parameter '{parameter_name}':"
                    + " parameter contains indexed values but indexing domain information is missing."
                )
            if value is None:
                if none_export == NoneExport.DO_NOT_EXPORT:
                    continue
                value = math.nan
            if not isinstance(value, float) and index is not None:
                raise GdxExportException(
                    f"Cannot write parameter '{parameter_name}':"
                    + f" parameter contains unsupported values of type '{type(value).__name__}'."
                )
            indexed_values[tuple(index)] = value
        try:
            gams_parameter = GAMSParameter(indexed_values, domain=parameter.domain_names)
        except ValueError as error:
            raise GdxExportException(f"Failed to create GAMS parameter '{parameter_name}': {error}")
        try:
            gdx_file[parameter_name] = gams_parameter
        except NotImplementedError as error:
            raise GdxExportException(f"Failed to write .gdx: {error}")


def domain_parameters_to_gams_scalars(gdx_file, parameters, domain_name):
    """
    Adds the parameter from given domain as a scalar to .gdx file.

    Args:
        gdx_file (GdxFile): a target file
        parameters (dict): a map from parameter name to a dict of dimensions and :class:`Parameter`
        domain_name (str): name of domain whose parameters to add
    Returns:
        dict: a dict of parameters that should be removed
    """
    erasable = dict()
    scalar_domain = (domain_name,)
    for parameter_name, by_dimensions in parameters.items():
        parameter = by_dimensions.get(scalar_domain)
        if parameter is not None:
            if len(parameter.data) != 1 or not parameter.is_scalar():
                raise GdxExportException(f"Parameter '{parameter_name}' is not suitable as GAMS scalar.")
            gams_scalar = GAMSScalar(next(iter(parameter.values)))
            try:
                gdx_file[parameter_name] = gams_scalar
            except NotImplementedError as error:
                raise GdxExportException(f"Failed to write to .gdx: {error}")
            erasable.setdefault(parameter_name, list()).append(scalar_domain)
    return erasable


def object_classes_to_domains(db_map):
    """
    Converts object classes and objects from a database to the intermediate format.

    Object classes get converted to :class:`Set` objects
    while objects are stored as :class:`Record` objects in the :class:`Set` objects.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
    Returns:
         list of Set: all domains
    """
    domains = list()
    for object_class_row in db_map.object_class_list():
        class_id = object_class_row.id
        domain = Set(object_class_row.name, object_class_row.description)
        domains.append(domain)
        for object_row in db_map.object_list(class_id=class_id):
            domain.records.append(Record((object_row.name,)))
    return domains


def relationship_classes_to_sets(db_map):
    """
    Converts relationship classes and relationships from a database to the intermediate format.

    Relationship classes get converted to :class:`Set` objects
    while relationships are stored as :class:`Record` objects in corresponding :class:`Set` objects.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
    Returns:
         list of Set: exportable sets
    """
    sets = dict()
    for relationship_class_row in db_map.query(db_map.wide_relationship_class_sq):
        object_class_names = tuple(relationship_class_row.object_class_name_list.split(","))
        set_ = Set(relationship_class_row.name, relationship_class_row.description, object_class_names)
        class_id = relationship_class_row.id
        sets[class_id] = set_
        for relationship_row in db_map.wide_relationship_list(class_id=class_id):
            keys = tuple(relationship_row.object_name_list.split(","))
            set_.records.append(Record(keys))
    return sets


def object_parameters(db_map, fallback_on_none, logger):
    """
    Converts object parameters from database to :class:`Parameter` objects.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
        fallback_on_none (NoneFallback): fallback when encountering Nones
        logger (LoggingInterface, optional): a logger; if not None, some errors are logged and ignored instead of
            raising an exception
    Returns:
        dict: a map from parameter name to dict which maps domain names to :class:`Parameter`
    """
    classes_with_ignored_parameters = set() if logger is not None else None
    parameters, default_values = _read_object_parameter_definitions(
        db_map, classes_with_ignored_parameters, fallback_on_none
    )
    for parameter_row in db_map.query(db_map.object_parameter_value_sq).all():
        domain = parameter_row.object_class_name
        name = parameter_row.parameter_name
        try:
            parsed_value = _read_value(parameter_row.value)
        except GdxUnsupportedValueTypeException:
            if classes_with_ignored_parameters is not None:
                classes_with_ignored_parameters.add(domain)
                continue
            raise
        if fallback_on_none == NoneFallback.USE_DEFAULT_VALUE and parsed_value is None:
            parsed_value = default_values[name][(domain,)]
        dimensions = (domain,)
        parameters[name][dimensions].data[(parameter_row.object_name,)] = parsed_value
    for name, by_dimensions in parameters.items():
        for parameter in by_dimensions.values():
            if not parameter.is_consistent():
                raise GdxExportException(f"Parameter '{name}' contains a mixture of different value types.")
    if classes_with_ignored_parameters:
        class_list = ", ".join(classes_with_ignored_parameters)
        logger.msg_warning.emit(
            "Some object parameter values were of unsupported types and were ignored."
            f" The values were from these object classes: {class_list}"
        )
    return parameters


def _read_object_parameter_definitions(db_map, classes_with_ignored_parameters, fallback_on_none):
    """
    Reads parameters names and their default values from the database.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
        classes_with_ignored_parameters (set, optional): a set of problematic relationship_class names; if not None,
            relationship_class names are added to this set in case of errors instead of raising an exception
        fallback_on_none (NoneFallback): fallback when encountering Nones
    Returns:
        tuple: a skeleton parameters dict and
            a map from parameter name to dict of domain name and the parsed default value
    """
    parameters = dict()
    default_values = dict()
    for definition_row in db_map.query(db_map.object_parameter_definition_sq).all():
        domain_name = definition_row.object_class_name
        name = definition_row.parameter_name
        by_dimensions = parameters.setdefault(name, dict())
        domain_names = (domain_name,)
        by_dimensions[domain_names] = Parameter(domain_names, [], [])
        if fallback_on_none != NoneFallback.USE_DEFAULT_VALUE:
            continue
        try:
            parsed_default_value = _read_value(definition_row.default_value)
        except GdxUnsupportedValueTypeException:
            if classes_with_ignored_parameters is not None:
                classes_with_ignored_parameters.add(domain_name)
                continue
            raise
        by_dimension = default_values.setdefault(name, dict())
        by_dimension[domain_names] = parsed_default_value
    return parameters, default_values


def relationship_parameters(db_map, fallback_on_none, logger):
    """
    Converts relationship parameters from database to :class:`Parameter` objects.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
        fallback_on_none (NoneFallback): fallback when encountering Nones
        logger (LoggingInterface, optional): a logger; if not None, some errors are logged and ignored instead of
            raising an exception
    Returns:
        dict: a map from parameter name to dict which maps domain names to :class:`Parameter`
    """
    classes_with_ignored_parameters = set() if logger is not None else None
    parameters, default_values = _read_relationship_parameter_definitions(
        db_map, classes_with_ignored_parameters, fallback_on_none
    )
    for parameter_row in db_map.query(db_map.relationship_parameter_value_sq).all():
        set_name = parameter_row.relationship_class_name
        name = parameter_row.parameter_name
        try:
            parsed_value = _read_value(parameter_row.value)
        except GdxUnsupportedValueTypeException:
            if classes_with_ignored_parameters is not None:
                classes_with_ignored_parameters.add(set_name)
                continue
            raise
        dimensions = tuple(parameter_row.object_class_name_list.split(","))
        if fallback_on_none == NoneFallback.USE_DEFAULT_VALUE and parsed_value is None:
            parsed_value = default_values[name][dimensions]
        keys = tuple(parameter_row.object_name_list.split(","))
        parameters[name][dimensions].data[keys] = parsed_value
    for name, by_dimensions in parameters.items():
        for parameter in by_dimensions.values():
            if not parameter.is_consistent():
                raise GdxExportException(f"Parameter '{name}' contains a mixture of different value types.")
    if classes_with_ignored_parameters:
        class_list = ", ".join(classes_with_ignored_parameters)
        logger.msg_warning.emit(
            "Some relationship parameter values were of unsupported types and were ignored."
            f" The values were from these relationship classes: {class_list}"
        )
    return parameters


def _read_relationship_parameter_definitions(db_map, classes_with_ignored_parameters, fallback_on_none):
    """
    Reads parameters names and their default values from the database.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
        classes_with_ignored_parameters (set, optional): a set of problematic relationship_class names; if not None,
            relationship_class names are added to this set in case of errors instead of raising an exception
        fallback_on_none (NoneFallback): fallback when encountering Nones
    Returns:
        tuple: a skeleton parameters dict and
            a map from parameter name to dict of domain name and the parsed default value
    """
    parameters = dict()
    default_values = dict()
    for definition_row in db_map.query(db_map.relationship_parameter_definition_sq).all():
        name = definition_row.parameter_name
        dimensions = tuple(definition_row.object_class_name_list.split(","))
        by_dimensions = parameters.setdefault(name, dict())
        by_dimensions[dimensions] = Parameter(dimensions, [], [])
        if fallback_on_none != NoneFallback.USE_DEFAULT_VALUE:
            continue
        try:
            parsed_default_value = _read_value(definition_row.default_value)
        except GdxUnsupportedValueTypeException:
            if classes_with_ignored_parameters is not None:
                classes_with_ignored_parameters.add(definition_row.relationship_class_name)
                continue
            raise
        dimensions = tuple(definition_row.object_class_name_list.split(","))
        by_dimensions = default_values.setdefault(name, dict())
        by_dimensions[dimensions] = parsed_default_value
    return parameters, default_values


def _update_using_existing_relationship_parameter_values(
    parameters, db_map, sets_with_ids, classes_with_ignored_parameters
):
    """
    Updates an existing relationship parameter dict using actual parameter values.

    Args:
        parameters (dict): a mapping from relationship parameter names to :class:`Parameter` objects to update
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map
        sets_with_ids (dict): mapping from relationship_class ids to corresponding :class:`Set` objects
        classes_with_ignored_parameters (set, optional): a set of problematic relationship_class names; if not None,
            class names are added to this set in case of errors instead of raising an exception
    """
    for parameter_row in db_map.relationship_parameter_value_list():
        name = parameter_row.parameter_name
        parameter = parameters.get(name)
        if parameter is None:
            continue
        try:
            parsed_value = _read_value(parameter_row.value)
        except GdxUnsupportedValueTypeException:
            if classes_with_ignored_parameters is not None:
                class_name = sets_with_ids[parameter_row.relationship_class_id].name
                classes_with_ignored_parameters.add(class_name)
                continue
            raise
        if parsed_value is not None:
            keys = tuple(parameter_row.object_name_list.split(","))
            parameter.data[keys] = parsed_value


def _combine_parameters(domain_parameters, set_parameters):
    """
    Combines domain and set parameter dicts.

    Args:
        domain_parameters (dict): a map from parameter name to a dict of domain names and :class:`Parameter`
        set_parameters (dict): a map from parameter name to a dict of domain names and :class:`Parameter`

    Returns:
        dict: combined parameter dicts
    """
    combined = dict(domain_parameters)
    for parameter_name, by_dimensions in set_parameters.items():
        existing = combined.get(parameter_name)
        if existing is None:
            combined[parameter_name] = by_dimensions
            continue
        for dimensions, parameter in by_dimensions.items():
            existing_parameter = existing.get(dimensions)
            if existing_parameter is None:
                existing[dimensions] = parameter
            else:
                existing_parameter.slurp(parameter)
    return combined


def erase_parameters(parameters, erasable):
    """
    Removes given parameters from parameters dict.

    Args:
        parameters (dict): a map from parameter name to dict of dimensions and :class:`Parameter`
        erasable (dict): a map from parameter name to dimensions
    """
    empty = list()
    for name, dimensions in erasable.items():
        by_dimensions = parameters[name]
        for domain_names in dimensions:
            del by_dimensions[domain_names]
        if not by_dimensions:
            empty.append(name)
    for name in empty:
        del parameters[name]


def domain_names_and_records(db_map):
    """
    Returns a list of domain names and a map from a name to list of record keys.

    Args:
        db_map (DatabaseMapping or DiffDatabaseMapping): a database map

    Returns:
         tuple: a tuple containing set of domain names and a dict from domain name to its records
    """
    domain_names = set()
    domain_records = dict()
    class_list = db_map.object_class_list().all()
    for object_class in class_list:
        domain_name = object_class.name
        domain_names.add(domain_name)
        records = list()
        for set_object in db_map.object_list(class_id=object_class.id):
            records.append((set_object.name,))
        domain_records[domain_name] = LiteralRecords(records)
    return domain_names, domain_records


def set_names_and_records(db_map):
    """
    Returns a list of set names and a map from a name to list of record keys.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database map

    Returns:
         tuple: a tuple containing a set of set names and a dict from set name to its records
    """
    names = set()
    set_records = dict()
    for relationship_class in db_map.wide_relationship_class_list():
        set_name = relationship_class.name
        names.add(set_name)
        records = list()
        for relationship in db_map.wide_relationship_list(class_id=relationship_class.id):
            records.append(tuple(relationship.object_name_list.split(",")))
        set_records[set_name] = LiteralRecords(records)
    return names, set_records


class IndexingSetting:
    """
    Settings for indexed value expansion for a single Parameter.

    Attributes:
        indexing_domain_name (str): indexing domain's name
        picking (FixedPicking or GeneratePicking): index picking
        index_position (int): where to insert the new index when expanding a parameter
    """

    def __init__(self, index_position):
        """
        Args:
            index_position (int): where to insert the new index when expanding a parameter
        """
        self.indexing_domain_name = None
        self.index_position = index_position
        self.picking = None

    def to_dict(self):
        """
        Serializes settings to dict.

        Returns:
            dict: serialized settings
        """
        return {
            "indexing_domain": self.indexing_domain_name,
            "index_position": self.index_position,
            "picking": self.picking.to_dict() if self.picking is not None else None,
        }

    @staticmethod
    def from_dict(setting_dict):
        """
        Restores serialized setting from dict.

        Args:
            setting_dict (dict): serialized settings

        Returns:
            IndexingSetting: restored setting
        """
        index_position = setting_dict["index_position"]
        setting = IndexingSetting(index_position)
        setting.indexing_domain_name = setting_dict["indexing_domain"]
        picking_dict = setting_dict.get("picking")
        setting.picking = _picking_from_dict(picking_dict) if picking_dict is not None else None
        return setting


def make_indexing_settings(db_map, none_fallback, logger):
    """
    Constructs skeleton indexing settings for parameter indexed value expansion.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database mapping
        none_fallback (NoneFallback): how to handle None values
        logger (LoggerInterface, optional): a logger
    Returns:
        dict: a mapping from parameter name to a dict of parameter dimensions and :class:`IndexingSetting`
    """
    settings = _aggregate_object_indexed_parameters(db_map, _add_to_indexing_settings, none_fallback, logger)
    relationship_settings = _aggregate_relationship_indexed_parameters(
        db_map, _add_to_indexing_settings, none_fallback, logger
    )
    for parameter_name, by_dimensions in relationship_settings.items():
        settings.setdefault(parameter_name, dict()).update(by_dimensions)
    return settings


def _aggregate_object_indexed_parameters(db_map, aggregator, none_fallback, logger):
    """
    Aggregates indexed parameters from object classes to a dict using an aggregator function.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database mapping
        aggregator (Callable): an aggregator function
        none_fallback: how to handle Nones
        logger (LoggingInterface, optional): a logger
    Returns:
        dict: an aggregate
    """
    settings = dict()
    classes_with_unsupported_value_types = set() if logger is not None else None
    parameter_names_to_skip_on_second_pass = set()
    for parameter_row in db_map.object_parameter_value_list():
        value = _read_value(parameter_row.value)
        if isinstance(value, IndexedValue):
            object_class_name = parameter_row.object_class_name
            dimensions = (object_class_name,)
            index_keys = (parameter_row.object_name,)
            aggregator(
                settings,
                parameter_row.parameter_name,
                object_class_name,
                dimensions,
                value,
                index_keys,
                classes_with_unsupported_value_types,
            )
            parameter_names_to_skip_on_second_pass.add(parameter_row.parameter_name)
        if none_fallback != NoneFallback.USE_DEFAULT_VALUE:
            continue
        name = parameter_row.parameter_name
        for definition_row in db_map.object_parameter_definition_list(parameter_row.object_class_id):
            if definition_row.parameter_name != name:
                continue
            parameter_names_to_skip_on_second_pass.add(name)
            value = _read_value(definition_row.default_value)
            if not isinstance(value, IndexedValue):
                break
            object_class_name = parameter_row.object_class_name
            dimensions = (object_class_name,)
            index_keys = (parameter_row.object_name,)
            aggregator(
                settings, name, object_class_name, dimensions, value, index_keys, classes_with_unsupported_value_types
            )
            break
    if classes_with_unsupported_value_types:
        class_list = ", ".join(classes_with_unsupported_value_types)
        logger.msg_warning.emit(
            f"The following object classes have parameter values of unsupported types: {class_list}"
        )
    return settings


def _aggregate_relationship_indexed_parameters(db_map, aggregator, none_fallback, logger):
    """
    Aggregates indexed parameters from relationship classes to a dict using an aggregator function.

    Args:
        db_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database mapping
        aggregator (Callable): an aggregator function
        none_fallback (NoneFallback): how to handle Nones
        logger (LoggingInterface, optional): a logger
    Returns:
        dict: an aggregate
    """
    aggregate = dict()
    classes_with_unsupported_value_types = set() if logger is not None else None
    parameter_names_to_skip_on_second_pass = set()
    for parameter_row in db_map.relationship_parameter_value_list():
        value = _read_value(parameter_row.value)
        if isinstance(value, IndexedValue):
            dimensions = tuple(parameter_row.object_class_name_list.split(","))
            index_keys = tuple(parameter_row.object_name_list.split(","))
            aggregator(
                aggregate,
                parameter_row.parameter_name,
                parameter_row.relationship_class_name,
                dimensions,
                value,
                index_keys,
                classes_with_unsupported_value_types,
            )
            parameter_names_to_skip_on_second_pass.add(parameter_row.parameter_name)
        if none_fallback != NoneFallback.USE_DEFAULT_VALUE:
            continue
        name = parameter_row.parameter_name
        for definition_row in db_map.relationship_parameter_definition_list(parameter_row.relationship_class_id):
            if definition_row.parameter_name != name:
                continue
            parameter_names_to_skip_on_second_pass.add(name)
            value = _read_value(definition_row.default_value)
            if not isinstance(value, IndexedValue):
                break
            dimensions = tuple(parameter_row.object_class_name_list.split(","))
            index_keys = tuple(parameter_row.object_name_list.split(","))
            aggregator(
                aggregate,
                name,
                parameter_row.relationship_class_name,
                dimensions,
                value,
                index_keys,
                classes_with_unsupported_value_types,
            )
            break
    if classes_with_unsupported_value_types:
        class_list = ", ".join(classes_with_unsupported_value_types)
        logger.msg_warning.emit(
            f"The following relationship classes have parameter values of unsupported types: {class_list}"
        )
    return aggregate


def _add_to_indexing_settings(
    settings,
    parameter_name,
    entity_class_name,
    dimensions,
    parsed_value,
    index_keys,
    classes_with_unsupported_value_types,
):
    """
    Adds parameter to indexing settings.

    Parameters:
        settings (dict): indexing settings
        parameter_name (str): parameter's name
        entity_class_name (str): name of the object or relationship_class the parameter belongs to
        dimensions (tuple of str): a list of parameter's domain names
        parsed_value (IndexedValue): parsed parameter_value
        index_keys (tuple): parameter's keys
        classes_with_unsupported_value_types (set, optional): entity_class names with unsupported value types
    """
    try:
        parameter = Parameter(dimensions, [index_keys], [parsed_value])
    except GdxUnsupportedValueTypeException:
        if classes_with_unsupported_value_types is not None:
            classes_with_unsupported_value_types.add(entity_class_name)
            return
        raise
    by_dimension = settings.setdefault(parameter_name, dict())
    setting = by_dimension.get(parameter.domain_names)
    if setting is None:
        by_dimension[parameter.domain_names] = IndexingSetting(len(parameter.domain_names))


def _add_to_indexed_parameter(
    parameters,
    parameter_name,
    entity_class_name,
    dimensions,
    parsed_value,
    index_keys,
    classes_with_unsupported_value_types,
):
    """
    Adds parameters to parameters dict.

    Parameters:
        parameters (dict): parameter dict where to add the parameter
        parameter_name (str): parameter's name
        entity_class_name (str): name of the object or relationship_class the parameter belongs to
        dimensions (tuple of str): a list of parameter's domain names
        parsed_value (IndexedValue): parsed parameter_value
        index_keys (tuple): parameter's keys
        classes_with_unsupported_value_types (set, optional): entity_class names with unsupported value types
    """
    try:
        parameter = Parameter(dimensions, [index_keys], [parsed_value])
    except GdxUnsupportedValueTypeException:
        if classes_with_unsupported_value_types is not None:
            classes_with_unsupported_value_types.add(entity_class_name)
            return
        raise
    by_dimension = parameters.setdefault(parameter_name, dict())
    existing = by_dimension.get(parameter.domain_names)
    if existing is None:
        by_dimension[parameter.domain_names] = parameter
    else:
        existing.slurp(parameter)


def update_indexing_settings(old_indexing_settings, new_indexing_settings):
    """
    Returns new indexing settings merged from old and new ones.

    Entries that do not exist in old settings will be removed.
    If entries exist in both settings the old one will be chosen if both entries are 'equal',
    otherwise the new entry will override the old one.
    Entries existing in new settings only will be added.

    Args:
        old_indexing_settings (dict): settings to be updated
        new_indexing_settings (dict): settings used for updating
    Returns:
        dict: merged old and new indexing settings
    """
    updated = dict()
    for parameter_name, new_by_dimensions in new_indexing_settings.items():
        old_by_dimension = old_indexing_settings.get(parameter_name)
        if old_by_dimension is None:
            updated[parameter_name] = new_by_dimensions
            continue
        updated_by_dimensions = updated.setdefault(parameter_name, dict())
        for domain_names, setting in new_by_dimensions.items():
            old_setting = old_by_dimension.get(domain_names)
            if old_setting is None:
                updated_by_dimensions[domain_names] = setting
            else:
                updated_by_dimensions[domain_names] = old_setting
    return updated


def indexing_settings_to_dict(settings):
    """
    Stores indexing settings to a JSON compatible dictionary.

    Args:
        settings (dict): a mapping from parameter name to a dict of domain names and :class:`IndexingSetting`.
    Returns:
        dict: a JSON serializable dictionary
    """
    settings_dict = dict()
    for parameter_name, by_dimensions in settings.items():
        if not by_dimensions:
            continue
        setting_list = settings_dict.setdefault(parameter_name, list())
        for domain_names, setting in by_dimensions.items():
            setting_dict = setting.to_dict()
            setting_dict["domain_names"] = domain_names
            setting_list.append(setting_dict)
    return settings_dict


def indexing_settings_from_dict(settings_dict):
    """
    Restores indexing settings from a json compatible dictionary.

    Args:
        settings_dict (dict): a JSON compatible dictionary representing parameter indexing settings.
    Returns:
        dict: a dictionary mapping parameter name to IndexingSetting.
    """
    settings = dict()
    if not settings_dict:
        return settings
    for parameter_name, setting_list in settings_dict.items():
        by_dimensions = settings.setdefault(parameter_name, dict())
        if not isinstance(setting_list, list):
            # For 0.5 compatibility.
            setting_dict = setting_list
            setting_dict["domain_names"] = [None]
            setting_list = [setting_dict]
        for setting_dict in setting_list:
            domain_names = tuple(setting_dict["domain_names"])
            by_dimensions[domain_names] = IndexingSetting.from_dict(setting_dict)
    return settings


def _find_indexed_parameter(parameter_name, db_map, none_fallback, logger=None):
    """Searches for parameter_name in db_map and returns Parameter and its entity_class name."""
    object_classes_with_unsupported_parameter_types = set() if logger is not None else None
    relationship_classes_with_unsupported_parameter_types = set()
    definition_row = (
        db_map.parameter_definition_list().filter(db_map.parameter_definition_sq.c.name == parameter_name).first()
    )
    if definition_row is None:
        raise GdxExportException(f"Cannot find parameter '{parameter_name}' in the database.")
    class_name = (
        db_map.query(db_map.entity_class_sq)
        .filter(db_map.entity_class_sq.c.id == definition_row.entity_class_id)
        .first()
        .name
    )
    value_rows = db_map.query(db_map.parameter_value_sq).filter(
        db_map.parameter_value_sq.c.parameter_definition_id == definition_row.id
    )
    default_value = None
    parameter = None
    for value_row in value_rows:
        try:
            parsed_value = _read_value(value_row.value)
        except GdxUnsupportedValueTypeException:
            if object_classes_with_unsupported_parameter_types is not None:
                object_classes_with_unsupported_parameter_types.add(class_name)
                return None, class_name
            raise
        if parsed_value is None and none_fallback == NoneFallback.USE_DEFAULT_VALUE:
            if default_value is None:
                try:
                    default_value = _read_value(definition_row.default_value)
                except GdxUnsupportedValueTypeException:
                    if object_classes_with_unsupported_parameter_types is not None:
                        object_classes_with_unsupported_parameter_types.add(class_name)
                        return None, class_name
                    raise
            parsed_value = default_value
        if not isinstance(parsed_value, IndexedValue):
            continue
        if value_row.object_id is not None:
            object_row = db_map.query(db_map.object_sq).filter(db_map.object_sq.c.id == value_row.object_id).first()
            keys = (object_row.name,)
        else:
            relationship_row = (
                db_map.query(db_map.wide_relationship_sq)
                .filter(db_map.wide_relationship_sq.c.id == value_row.relationship_id)
                .first()
            )
            keys = tuple(relationship_row.object_name_list.split(","))
        if parameter is None:
            if value_row.object_class_id is not None:
                domain_list = (class_name,)
            else:
                relationship_class_row = (
                    db_map.query(db_map.wide_relationship_class_sq)
                    .filter(db_map.wide_relationship_class_sq.c.id == value_row.relationship_class_id)
                    .first()
                )
                domain_list = tuple(relationship_class_row.object_class_name_list.split(","))
            parameter = Parameter(domain_list, [keys], [parsed_value])
        else:
            parameter.data[keys] = parsed_value
    if parameter is None:
        raise GdxExportException(f"Cannot find values for parameter '{parameter_name}' in the database.")
    if logger is not None:
        if object_classes_with_unsupported_parameter_types:
            class_list = ", ".join(object_classes_with_unsupported_parameter_types)
            logger.msg_warning.emit(
                f"The following object classes contain parameter values of unsupported types: {class_list}"
            )
        if relationship_classes_with_unsupported_parameter_types:
            class_list = ", ".join(relationship_classes_with_unsupported_parameter_types)
            logger.msg_warning.emit(
                f"The following relationship classes contain parameter values of unsupported types: {class_list}"
            )
    return parameter, class_name


def indexed_parameters(db_map, none_fallback, logger):
    """
    Loads indexed parameters from the database.

    Args:
        db_map (spinedb_api.DatabaseMappingBase): a database mapping
        none_fallback (NoneFallback): how to handle None values
        logger (LoggerInterface, optional): a logger
    Returns:
        dict: a mapping from parameter name to a dict of parameter dimensions and :class:`Parameter`
    """
    settings = _aggregate_object_indexed_parameters(db_map, _add_to_indexed_parameter, none_fallback, logger)
    relationship_settings = _aggregate_relationship_indexed_parameters(
        db_map, _add_to_indexed_parameter, none_fallback, logger
    )
    for parameter_name, by_dimensions in relationship_settings.items():
        settings.setdefault(parameter_name, dict()).update(by_dimensions)
    return settings


def _create_additional_domains(set_settings):
    """
    Generates additional domains found in the settings.

    Args:
        set_settings (SetSettings): settings

    Returns:
        list: a list of additional :class:`Set` objects
    """
    domains = list()
    for name in set_settings.domain_names:
        metadata = set_settings.metadata(name)
        if not metadata.is_additional():
            continue
        domain = Set(name, metadata.description)
        domain.records = [Record(keys) for keys in set_settings.records(name).records]
        domains.append(domain)
    return domains


def _exported_set_names(names, set_settings):
    """
    Returns a set of names of the domains that are marked for exporting.

    Args:
        names (set): list of all domain or set names
        set_settings (SetSettings): settings

    Returns:
        set of str: names that should be exported
    """
    return {name for name in names if set_settings.is_exportable(name)}


def sort_sets(sets, order):
    """
    Sorts a list of sets according to ``sorted_names``

    Args:
        sets (list): :class:`Set` objects to be sorted
        order (dict): a mapping from set name to index

    Returns:
        list: sorted :class:`Set` objects
    """
    sorted_sets = sorted(sets, key=lambda set_: order[set_.name])
    return sorted_sets


def sort_records_inplace(sets, set_settings, logger):
    """
    Sorts the record lists of given domains according to the order given in settings.

    Args:
        sets (list of Set): a list of :class:`Set` objects whose records are to be sorted
        set_settings (SetSettings): settings that define the sorting order
        logger (LoggerInterface, optional): a logger
    """
    for current_set in sets:
        sorted_keys = set_settings.records(current_set.name).records
        sort_indexes = {key: index for index, key in enumerate(sorted_keys)}
        # pylint: disable=cell-var-from-loop
        try:
            sorted_records = sorted(current_set.records, key=lambda record: sort_indexes[record.keys])
        except KeyError as missing:
            missing = ", ".join(missing.args[0])
            message = f"Could not sort records in {current_set.name} as it contains an unknown key '{missing}'."
            if logger is not None:
                logger.msg_warning.emit(message)
                continue
            else:
                raise GdxExportException(message)
        current_set.records = sorted_records


def extract_domain(domains, name_to_extract):
    """
    Extracts the domain with given name from a list of domains.

    Args:
        domains (list): a list of Set objects
        name_to_extract (str): name of the domain to be extracted

    Returns:
        a tuple (list, Set) of the modified domains list and the extracted Set object
    """
    for index, domain in enumerate(domains):
        if domain.name == name_to_extract:
            del domains[index]
            return domains, domain
    return domains, None


def to_gdx_file(
    database_map,
    file_name,
    set_settings,
    indexing_settings,
    merging_settings,
    none_fallback,
    none_export,
    gams_system_directory=None,
    logger=None,
):
    """
    Exports given database map into .gdx file.

    Args:
        database_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database to export
        file_name (str): output file name
        set_settings (SetSettings): export settings
        indexing_settings (dict): a dictionary containing settings for indexed parameter expansion
        merging_settings (dict): a list of merging settings for parameter merging
        none_fallback (NoneFallback): options how to handle none parameter values on database read
        none_export (NoneExport): option how to handle none parameter values on export
        gams_system_directory (str, optional): path to GAMS system directory or None to let GAMS choose one for you
        logger (LoggingInterface, optional): a logger; if None given all error conditions raise GdxExportException
            otherwise some errors are logged and ignored
    """
    domains = object_classes_to_domains(database_map)
    domains = _drop_sets_not_in_settings(domains, set_settings.domain_names, logger)
    domain_parameters = object_parameters(database_map, none_fallback, logger)
    domains, global_parameters_domain = extract_domain(domains, set_settings.global_parameters_domain_name)
    domains += _create_additional_domains(set_settings)
    domains = sort_sets(domains, set_settings.domain_tiers)
    sort_records_inplace(domains, set_settings, logger)
    domains_with_names = {domain.name: domain for domain in domains}
    sets_with_ids = relationship_classes_to_sets(database_map)
    sets = list(sets_with_ids.values())
    sets = _drop_sets_not_in_settings(sets, set_settings.set_names, logger)
    sets = sort_sets(sets, set_settings.set_tiers)
    sort_records_inplace(sets, set_settings, logger)
    set_parameters = relationship_parameters(database_map, none_fallback, logger)
    parameters = _combine_parameters(domain_parameters, set_parameters)
    erasable = expand_indexed_parameter_values(parameters, indexing_settings, domains_with_names)
    erase_parameters(parameters, erasable)
    erasable = merge_parameters(parameters, merging_settings)
    erase_parameters(parameters, erasable)
    with GdxFile(file_name, mode="w", gams_dir=gams_system_directory) as output_file:
        sets_to_gams(output_file, domains, set_settings)
        sets_to_gams(output_file, sets, set_settings)
        if global_parameters_domain is not None:
            erasable = domain_parameters_to_gams_scalars(output_file, domain_parameters, global_parameters_domain.name)
            erase_parameters(parameters, erasable)
        parameters = _drop_parameters_conflicting_with_sets(parameters, set_settings, logger)
        parameters_to_gams(output_file, parameters, none_export)


def make_set_settings(database_map):
    """
    Builds a :class:`SetSettings` object from given database.

    Args:
        database_map (spinedb_api.DatabaseMapping or spinedb_api.DiffDatabaseMapping): a database from which
            domains, sets, records etc are extracted

    Returns:
        SetSettings: settings needed for exporting the entities and class from the given ``database_map``
    """
    domain_names, domain_records = domain_names_and_records(database_map)
    set_names, set_records = set_names_and_records(database_map)
    records = domain_records
    records.update(set_records)
    return SetSettings(domain_names, set_names, records)


class SetSettings:
    """
    This class holds the settings for domains, sets and records needed by `to_gdx_file()` for .gdx export.

    :class:`SetSettings` keeps track which domains, sets and records are exported into the .gdx file
    and in which order they are written to the file.
    This order is paramount for some models, like TIMES.
    """

    def __init__(
        self,
        domain_names,
        set_names,
        records,
        domain_tiers=None,
        set_tiers=None,
        metadatas=None,
        global_parameters_domain_name="",
    ):
        """
        Args:
            domain_names (set of str): domain names
            set_names (set of str): set names
            records (dict): a mapping from domain or set name to :class:`Records`
            domain_tiers (dict, optional): a mapping from domain name to tier
            set_tiers (dict, optional): a mapping from set name to tier
            metadatas (dict, optional): a mapping from domain or set name to :class:`SetMetadata`
            global_parameters_domain_name (str, optional): name of the domain
                whose parameters should be exported as scalars
        """
        name_clashes = domain_names & set_names
        if name_clashes:
            raise GdxExportException(f"Duplicate domain and set names: {name_clashes}.")
        self._domain_names = domain_names
        self._domain_tiers = (
            domain_tiers if domain_tiers is not None else {name: i for i, name in enumerate(sorted(domain_names))}
        )
        self._set_names = set_names
        self._set_tiers = set_tiers if set_tiers is not None else {name: i for i, name in enumerate(sorted(set_names))}
        self._records = records
        if metadatas is None:
            metadatas = {set_name: SetMetadata() for set_name in domain_names | set_names}
        self._metadatas = metadatas
        self._global_parameters_domain_name = global_parameters_domain_name

    @property
    def domain_names(self):
        """domain names"""
        return self._domain_names

    @property
    def domain_tiers(self):
        """a mapping from domain name to tier"""
        return self._domain_tiers

    @property
    def set_names(self):
        """set names"""
        return self._set_names

    @property
    def set_tiers(self):
        """a mapping from set name to tier"""
        return self._set_tiers

    def metadata(self, name):
        """
        Returns the metadata for given domain/set.

        Args:
            name (str): set/domain name

        Returns:
            Metadata: metadata
        """
        return self._metadatas[name]

    @property
    def global_parameters_domain_name(self):
        """the name of the domain, parameters of which should be exported as GAMS scalars"""
        return self._global_parameters_domain_name

    @global_parameters_domain_name.setter
    def global_parameters_domain_name(self, name):
        """
        Sets the global_parameters_domain_name and declares that domain NON_EXPORTABLE.

        Args:
            name (str): new global parameters domain name
        """
        if self._global_parameters_domain_name:
            self._metadatas[self._global_parameters_domain_name].exportable = ExportFlag.EXPORTABLE
        if name:
            self._metadatas[name].exportable = ExportFlag.NON_EXPORTABLE
        self._global_parameters_domain_name = name

    def is_exportable(self, set_name):
        """
        Returns True if the domain or set with the given name is exportable, False otherwise.

        Args:
            set_name (str): domain/set name

        Returns:
            bool: True if the set is exportable False otherwise
        """
        return self._metadatas[set_name].is_exportable()

    def is_additional(self, domain_name):
        """
        Returns True if the domain is an additional domain.

        Args:
            domain_name (str): domain name

        Returns:
            bool: True if the domain is additional, False otherwise
        """
        return self._metadatas[domain_name].is_additional()

    def add_or_replace_domain(self, domain_name, records, metadata):
        """
        Adds a new domain or replaces an existing domain's records and metadata.

        Args:
            domain_name (str): a domain to add/replace
            records (Records): domain's records
            metadata (SetMetadata): domain's metadata
        Returns:
            bool: True if a new domain was added, False if an existing domain was replaced
        """
        if domain_name in self._set_names:
            raise GdxExportException(f"A set named '{domain_name}' already exists.")
        existed = domain_name in self._domain_names
        self._domain_names.add(domain_name)
        if domain_name not in self._domain_tiers:
            self._domain_tiers[domain_name] = len(self._domain_tiers)
        self._records[domain_name] = records
        self._metadatas[domain_name] = metadata
        return existed

    def remove_domain(self, domain_name):
        """
        Erases domain.

        Args:
            domain_name (str): name of the domain to remove
        """
        self._domain_names.remove(domain_name)
        del self._domain_tiers[domain_name]
        del self._metadatas[domain_name]
        del self._records[domain_name]
        if domain_name == self._global_parameters_domain_name:
            self._global_parameters_domain_name = ""

    def records(self, name):
        """
        Returns the records of a given domain or set.

        Args:
            name (str): domain or set name

        Returns:
            Records: domain's or set's records
        """
        return self._records[name]

    def update_records(self, set_name, records):
        """
        Updates the records of given domain or set.

        Args:
            set_name (str): domain or set name
            records (Records): updated records
        """
        old = self._records[set_name]
        self._records[set_name] = _update_records(old, records)

    def update(self, updating_settings):
        """
        Updates the settings by merging with another one.

        All domains, sets and records that are in both settings (common)
        or in `updating_settings` (new) are retained.
        Common elements are ordered the same way they were ordered in the original settings.
        New elements are appended to the common ones in the order they were in `updating_settings`

        Args:
            updating_settings (SetSettings): settings to merge with
        """
        updated_records = dict()
        updated_metadatas = dict()
        updated_domain_names = set()
        for name in self._domain_names:
            metadata = self._metadatas[name]
            if metadata.is_additional():
                if name in updating_settings.set_names:
                    raise GdxExportException(
                        f"Additional domain '{name}' conflicts with a new set under the same name."
                    )
                updated_domain_names.add(name)
                updated_records[name] = self._records[name]
                updated_metadatas[name] = metadata
        old_names = self._domain_names | self._set_names
        updating_names = updating_settings._domain_names | updating_settings._set_names
        common_names = old_names & updating_names
        common_domain_names = self._domain_names & updating_settings._domain_names
        updating_domain_names = list(updating_settings._domain_names - self._domain_names)
        sorted_common_domain_names = list(
            sorted(common_domain_names | updated_domain_names, key=lambda n: self._domain_tiers[n])
        )
        updated_domain_tiers = {n: i for i, n in enumerate(sorted_common_domain_names + updating_domain_names)}
        for name in common_names:
            updated_records[name] = _update_records(self._records[name], updating_settings._records[name])
            updated_metadatas[name] = self._metadatas[name]
        new_names = updating_names - common_names
        common_set_names = self._set_names & updating_settings._set_names
        updating_set_names = list(updating_settings._set_names - self._set_names)
        sorted_common_set_names = list(sorted(common_set_names, key=lambda n: self._set_tiers[n]))
        updating_set_tiers = {n: i for i, n in enumerate(sorted_common_set_names + updating_set_names)}
        for name in new_names:
            updated_records[name] = updating_settings._records[name]
            updated_metadatas[name] = updating_settings._metadatas[name]
        updated_domain_names |= updating_settings._domain_names
        updated_set_names = set(updating_settings._set_names)
        if self._global_parameters_domain_name not in updated_domain_names:
            self._global_parameters_domain_name = ""
        self._domain_names = updated_domain_names
        self._domain_tiers = updated_domain_tiers
        self._set_names = updated_set_names
        self._set_tiers = updating_set_tiers
        self._records = updated_records
        self._metadatas = updated_metadatas

    def to_dict(self):
        """
        Serializes the this object to a dict.

        Returns:
            dict: serialized settings
        """
        as_dictionary = {
            "domains": {
                name: {
                    "tier": self._domain_tiers[name],
                    "records": self._records[name].to_dict(),
                    "metadata": self._metadatas[name].to_dict(),
                }
                for name in self._domain_names
            },
            "sets": {
                name: {
                    "tier": self._set_tiers[name],
                    "records": self._records[name].to_dict(),
                    "metadata": self._metadatas[name].to_dict(),
                }
                for name in self._set_names
            },
            "global_parameters_domain_name": self._global_parameters_domain_name,
        }
        return as_dictionary

    @staticmethod
    def from_dict(dictionary):
        """
        Deserializes :class:`SetSettings` from a dict.

        Args:
            dictionary (dict): serialized settings

        Returns:
            SetSettings: restored settings
        """
        try:
            domain_dicts = dictionary["domains"]
            domain_names = set()
            domain_tiers = dict()
            records = dict()
            metadatas = dict()
            for name, domain_dict in domain_dicts.items():
                domain_names.add(name)
                domain_tiers[name] = domain_dict["tier"]
                records[name] = _records_from_dict(domain_dict["records"])
                metadatas[name] = SetMetadata.from_dict(domain_dict["metadata"])
            set_dicts = dictionary["sets"]
            set_names = set()
            set_tiers = dict()
            for name, set_dict in set_dicts.items():
                set_names.add(name)
                set_tiers[name] = set_dict["tier"]
                records[name] = _records_from_dict(set_dict["records"])
                metadatas[name] = SetMetadata.from_dict(set_dict["metadata"])
            global_parameters_domain_name = dictionary["global_parameters_domain_name"]
            settings = SetSettings(
                domain_names, set_names, records, domain_tiers, set_tiers, metadatas, global_parameters_domain_name
            )
        except KeyError as missing_key:
            raise GdxExportException(f"'{missing_key}' field missing from settings dict.")
        return settings


@enum.unique
class ExportFlag(enum.Enum):
    """Options for exporting Set objects."""

    EXPORTABLE = 1
    """User has declared that the set should be exported."""
    NON_EXPORTABLE = 2
    """User has declared that the set should not be exported."""


@enum.unique
class Origin(enum.Enum):
    """Domain or set origin."""

    DATABASE = 1
    """Set exists in the database."""
    INDEXING = 2
    """Set has been generated for indexed parameter indexing."""
    MERGING = 3
    """Set has been generated for parameter merging."""


class SetMetadata:
    """
    This class holds some additional configuration for Sets.

    Attributes:
        exportable (ExportFlag): set's export flag
        origin (bool): True if the domain does not exist in the database but is supplied separately.
        description (str): set's description or None if its origin is from database
    """

    def __init__(self, exportable=ExportFlag.EXPORTABLE, origin=Origin.DATABASE):
        """
        Args:
            exportable (ExportFlag): set's export flag
            origin (Origin): where the set comes from
        """
        self.exportable = exportable
        self.origin = origin
        self.description = None if origin == Origin.DATABASE else ""

    def __eq__(self, other):
        """Returns True if other is equal to this metadata."""
        if not isinstance(other, SetMetadata):
            return NotImplemented
        return (
            self.exportable == other.exportable
            and self.origin == other.origin
            and self.description == other.description
        )

    def is_additional(self):
        """Returns True if Set does not originate from the database."""
        return self.origin != Origin.DATABASE

    def is_exportable(self):
        """Returns True if Set should be exported."""
        return self.exportable == ExportFlag.EXPORTABLE

    def to_dict(self):
        """Serializes metadata to a dictionary."""
        metadata_dict = dict()
        metadata_dict["exportable"] = self.exportable.value
        metadata_dict["origin"] = self.origin.value
        if self.description is not None:
            metadata_dict["description"] = self.description
        return metadata_dict

    @staticmethod
    def from_dict(metadata_dict):
        """Deserializes metadata from a dictionary."""
        metadata = SetMetadata()
        exportable = metadata_dict["exportable"]
        metadata.exportable = (
            ExportFlag.EXPORTABLE if exportable == ExportFlag.EXPORTABLE.value else ExportFlag.NON_EXPORTABLE
        )
        metadata.origin = Origin(metadata_dict["origin"])
        metadata.description = metadata_dict.get("description")
        return metadata
