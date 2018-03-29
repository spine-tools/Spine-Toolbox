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
Tool template classes.

:authors: Pekka Savolainen <pekka.t.savolainen@vtt.fi>, Erkka Rinne <erkka.rinne@vtt.fi>
:date:   24.1.2018
"""

import os
import logging
from collections import OrderedDict
from metaobject import MetaObject
from config import REQUIRED_KEYS, OPTIONAL_KEYS, LIST_REQUIRED_KEYS


class ToolTemplate(MetaObject):
    """Super class for various tool templates.

    Attributes:
        parent (ToolBoxUI): QMainWindow instance
        name (str): Name of the tool
        description (str): Short description of the tool
        path (str): Path to tool
        includes (str): List of files belonging to the tool template (relative to 'path')
        inputfiles (list): List of required data files
        inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
        outputfiles (list, optional): List of output files (wildcards may be used)
        cmdline_args (str, optional): Tool command line arguments (read from tool definition file)
    """
    def __init__(self, parent, name, description, tooltype, path, includes,
                 inputfiles=None, inputfiles_opt=None,
                 outputfiles=None, cmdline_args=None):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = parent
        self.tooltype = tooltype
        if not os.path.exists(path):
            pass
        else:
            self.path = path
        self.includes = includes
        self.cmdline_args = cmdline_args
        self.inputfiles = set(inputfiles) if inputfiles else set()
        self.inputfiles_opt = set(inputfiles_opt) if inputfiles_opt else set()
        self.outputfiles = set(outputfiles) if outputfiles else set()
        self.return_codes = {}
        self.def_file_path = ''  # JSON tool definition file path

    def set_return_code(self, code, description):
        """Set a return code and associated text description for the tool.

        Args:
            code (int): Return code
            description (str): Description
        """
        self.return_codes[code] = description

    def set_def_path(self, path):
        """Set definition file path for tool.

        Args:
            path (str): Absolute path to the definition file.
        """
        self.def_file_path = path

    def get_def_path(self):
        """Returns tool definition file path."""
        return self.def_file_path

    def append_cmdline_args(self, command, extra_cmdline_args):
        """Append command line arguments to a command.

        Args:
            command (str): Tool command
            extra_cmdline_args (str): Extra command line arguments
        """
        if (extra_cmdline_args is not None) and (not extra_cmdline_args == ''):
            if (self.cmdline_args is not None) and (not self.cmdline_args == ''):
                command += ' ' + self.cmdline_args + ' ' + extra_cmdline_args
            else:
                command += ' ' + extra_cmdline_args
        else:
            if (self.cmdline_args is not None) and (not self.cmdline_args == ''):
                command += ' ' + self.cmdline_args
        return command

    @staticmethod
    def check_definition(ui, data):
        """Check that a tool template definition contains
        the required keys and that it is in correct format.

        Args:
            ui (ToolboxUI): Spine Toolbox QMainWindow instance
            data (dict): Tool template definition

        Returns:
            Dictionary or None if there was a problem in the tool definition.
        """
        kwargs = dict()
        for p in REQUIRED_KEYS + OPTIONAL_KEYS:
            try:
                kwargs[p] = data[p]
            except KeyError:
                if p in REQUIRED_KEYS:
                    ui.msg_error.emit("Required keyword '{0}' missing".format(p))
                    return None
                else:
                    # logging.info("Optional keyword '{0}' missing".format(p))
                    pass
            # Check that some values are lists
            if p in LIST_REQUIRED_KEYS:
                try:
                    if not isinstance(data[p], list):
                        ui.msg_error.emit("Keyword '{0}' value must be a list".format(p), 2)
                        return None
                except KeyError:
                    pass
        return kwargs


class GAMSTool(ToolTemplate):
    """Class for GAMS tool templates.

    Attributes:
        name (str): GAMS Tool name
        description (str): GAMS Tool description
        path (str): Path to model main file
        includes (str): List of files belonging to the tool (relative to 'path')
                     First file in the list is the main GAMS program.
        inputfiles (list): List of required data files
        inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
        outputfiles (list, optional): List of output files (wildcards may be used)
        cmdline_args (str, optional): GAMS tool command line arguments (read from tool definition file)
    """

    def __init__(self, parent, name, description, tooltype, path, includes,
                 inputfiles=None, inputfiles_opt=None,
                 outputfiles=None, cmdline_args=None):
        """Class constructor."""
        super().__init__(parent, name, description, tooltype, path, includes,
                         inputfiles, inputfiles_opt, outputfiles,
                         cmdline_args)
        main_file = includes[0]
        # Add .lst file to list of output files
        self.lst_file = os.path.splitext(main_file)[0] + '.lst'
        self.outputfiles.add(self.lst_file)
        # Split main_prgm to main_dir and main_prgm
        # because GAMS needs to run in the directory of the main program
        # TODO: This does not work because main_file is always just file name
        self.main_dir, self.main_prgm = os.path.split(main_file)
        self.gams_options = OrderedDict()
        self.return_codes = {
            0: "Normal return",
            1: "Solver is to be called the system should never return this number",  # ??
            2: "There was a compilation error",
            3: "There was an execution error",
            4: "System limits were reached",
            5: "There was a file error",
            6: "There was a parameter error",
            7: "There was a licensing error",
            8: "There was a GAMS system error",
            9: "GAMS could not be started",
            10: "Out of memory",
            11: "Out of disk",
            62097: "Simulation interrupted by user"  # Not official
        }

    def __repr__(self):
        """Remove this if not necessary."""
        return "GAMSTool('{}')".format(self.name)

    def update_gams_options(self, key, value):
        """Update GAMS command line options. Only 'cerr and 'logoption' keywords supported.

        Args:
            key: Option name
            value: Option value
        """
        # Supported GAMS logoption values
        # 3 writes LOG output to standard output
        # 4 writes LOG output to a file and standard output  [Not supported in GAMS v24.0]
        if key == 'logoption' or key == 'cerr':
            self.gams_options[key] = "{0}={1}".format(key, value)
        else:
            logging.error("Updating GAMS options failed. Unknown key: {}".format(key))

    @staticmethod
    def load(parent, path, data):
        """Create a GAMSTool according to a tool definition.

        Args:
            parent (ToolboxUI): QMainWindow instance
            path (str): Base path to tool files
            data (dict): Dictionary of tool definitions

        Returns:
            GAMSTool instance or None if there was a problem in the tool definition file.
        """
        kwargs = GAMSTool.check_definition(parent, data)
        if kwargs is not None:
            # Return an executable model instance
            return GAMSTool(parent=parent, path=path, **kwargs)
        else:
            return None


class JuliaTool(ToolTemplate):
    """Class for Julia tool templates.

    Attributes:
        name (str): Julia Tool name
        description (str): Julia Tool description
        path (str): Path to model main file
        includes (str): List of files belonging to the tool (relative to 'path')
                     First file in the list is the main Julia program.
        inputfiles (list): List of required data files
        inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
        outputfiles (list, optional): List of output files (wildcards may be used)
        cmdline_args (str, optional): Julia tool command line arguments (read from tool definition file)
    """

    def __init__(self, parent, name, description, tooltype, path, includes,
                 inputfiles=None, inputfiles_opt=None,
                 outputfiles=None, cmdline_args=None):
        """Class constructor."""
        super().__init__(parent, name, description, tooltype, path, includes,
                         inputfiles, inputfiles_opt, outputfiles,
                         cmdline_args)
        main_file = includes[0]
        self.main_dir, self.main_prgm = os.path.split(main_file)
        self.julia_options = OrderedDict()
        self.return_codes = {
            0: "Normal return"  # Not official
        }

    def __repr__(self):
        """Remove this if not necessary."""
        return "JuliaTool('{}')".format(self.name)

    def update_julia_options(self, key, value):
        """Update Julia command line options.

        Args:
            key: Option name
            value: Option value
        """
        return True

    @staticmethod
    def load(parent, path, data):
        """Create a JuliaTool according to a tool definition.

        Args:
            parent (ToolboxUI): QMainWindow instance
            path (str): Base path to tool files
            data (dict): Dictionary of tool definitions

        Returns:
            JuliaTool instance or None if there was a problem in the tool definition file.
        """
        kwargs = JuliaTool.check_definition(parent, data)
        if kwargs is not None:
            # Return an executable model instance
            return JuliaTool(parent=parent, path=path, **kwargs)
        else:
            return None
