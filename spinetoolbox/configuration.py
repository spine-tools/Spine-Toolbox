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
Module for handling Spine Toolbox configuration files.

:author: P. Savolainen (VTT)
:date:   10.1.2018
"""

import configparser
import logging
import codecs
from config import SETTINGS


class ConfigurationParser(object):
    """ConfigurationParser class takes care of handling configurations files
    in persistent storage."""
    def __init__(self, file_path, defaults=None):
        """Initialize configuration parser.

        Args:
            file_path (str): Absolute path to the configuration file.
            defaults (dict): A dictionary containing configuration default options.
        """
        self.parser = configparser.ConfigParser()
        self.file_path = file_path
        if defaults:
            self.parser['settings'] = defaults
        else:
            self.parser['settings'] = SETTINGS

    def __str__(self):
        """Print the current configuration."""
        output = ''
        for section_name in self.parser.sections():
            output += ('[%s]\n' % section_name)
            for name, value in self.parser.items(section_name):
                output += ('    %s = %s\n' % (name, value))
        return output.strip()

    def get(self, section, option):
        """Get configuration option value.

        Args:
            section (str): Selected configuration section.
            option (str): Configuration option to get.

        Returns:
            Value of the option as a string or default if the option was
            not found.
        """
        if not self.parser.has_section(section):
            self.parser[section] = {}
        try:
            value = self.parser.get(section, option)
        except configparser.NoOptionError:
            logging.debug("Option '{}' not found in conf file".format(option))
            value = ''
        return value

    def getboolean(self, section, option):
        """Get configuration option boolean value.
        Supported values: true, false, yes, no, 1, 0, etc.

        Args:
            section (str): Selected configuration section.
            option (str): Configuration option to get.

        Returns:
            Value of the option as a boolean or default if the option was
            not found.
        """
        if not self.parser.has_section(section):
            self.parser[section] = {}
        try:
            value = self.parser.getboolean(section, option)
        except ValueError:
            # value not a boolean
            return False
        return value

    def set(self, section, option, value):
        """Set configuration option value.

        Args:
            section (str): The configuration section to edit.
            option (str): The configuration option to set.
            value (str): The option values to be set.
        """
        if not self.parser.has_section(section):
            self.parser[section] = {}
        self.parser.set(section, option, value)

    def setboolean(self, section, option, value):
        """Set boolean configuration option value from a given integer value.
        Note: Writes true if a string is given.

        Args:
            section (str): The configuration section to edit.
            option (str): The configuration option to set.
            value (int, bool): Writes false if 0 (or False), true if any other value given.
        """
        if value == 0:
            self.set(section, option, 'false')
        else:
            self.set(section, option, 'true')

    def load(self, insert_missing=True):
        """Load configuration file. By default if 'default'
        section is missing, it is inserted into the configuration.

        Args:
            insert_missing (bool): Add missing sections.

        Returns:
            A boolean value depending on the operation success.
        """
        try:
            self.parser.read(self.file_path, 'utf-8')
        except configparser.MissingSectionHeaderError:
            self.parser.add_section("settings")
        except configparser.ParsingError:
            logging.exception("Failed to parse configuration file.")
            return False
        return True

    def save(self):
        """Save configuration into persistent storage, overwriting old file."""
        with codecs.open(self.file_path, 'w', 'utf-8') as output_file:
            self.parser.write(output_file)

    def copy_section(self, source, destination):
        """Copy all option parameters from source section to destination section.

        Args:
            source (str): Source configuration section to copy options from.
            destination (str): Destination configuration section.
        """
        for option in self.parser.options(source):
            logging.debug("Copy option: %s" % self.get(source, option))
            self.set(destination, option, self.get(source, option))
