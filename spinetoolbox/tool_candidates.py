#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
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
Tool candidate classes.

:authors: Pekka Savolainen <pekka.t.savolainen@vtt.fi>, Erkka Rinne <erkka.rinne@vtt.fi>
:date:   24.1.2018
"""

import os.path
import logging
from collections import OrderedDict
from metaobject import MetaObject
from config import GAMS_EXECUTABLE, REQUIRED_KEYS, OPTIONAL_KEYS, LIST_REQUIRED_KEYS


class ToolCandidate(MetaObject):
    """Super class for various tool candidates.

    Attributes:
        name (str): Name of the tool
        description (str): Short description of the tool
        path (str): Path to tool
        includes (str): List of files belonging to the tool (relative to 'path')
        inputfiles (list): List of required data files
        opt_inputfiles (list, optional): List of optional data files (wildcards may be used)
        outputfiles (list, optional): List of output files (wildcards may be used)
        logfile (str, optional): Log file name (relative to 'path')
        cmdline_args (str, optional): Tool command line arguments (read from tool definition file)
    """
    def __init__(self, name, description, path, includes,
                 inputfiles=None, opt_inputfiles=None,
                 outputfiles=None, logfile=None, cmdline_args=None):
        """Class constructor."""
        super().__init__(name, description)
        if not os.path.exists(path):
            pass  # TODO: Do something here
        else:
            self.path = path
        self.includes = includes
        self.cmdline_args = cmdline_args
        self.inputfiles = set(inputfiles) if inputfiles else set()
        self.opt_inputfiles = set(opt_inputfiles) if opt_inputfiles else set()
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

    def create_instance(self, ui, setup_cmdline_args, tool_output_dir, setup_name):
        """Create an instance of the tool.

        Args:
            ui (TitanUI): Titan GUI instance
            setup_cmdline_args (str): Extra command line arguments
            tool_output_dir (str): Output directory for tool
            setup_name (str): Short name of Setup that calls this method
        """
        return ToolInstance(self, ui, tool_output_dir, setup_name)

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
    def check_definition(data, ui):
        """Check that a tool condidate definition contains
        the required keys and that it is in correct format.

        Args:
            data (dict): Tool candidate definition
            ui (ToolboxUI): Spine Toolbox QMainWindow instance

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


class GAMSTool(ToolCandidate):
    """Class for GAMS tool candidates.

    Attributes:
        name (str): GAMS Tool name
        description (str): GAMS Tool description
        path (str): Path (#TODO: to model main program? Check this)
        includes (str): List of files belonging to the tool (relative to 'path')
                     First file in the list is the main GAMS program.
        inputfiles (list): List of required data files
        opt_inputfiles (list, optional): List of optional data files (wildcards may be used)
        outputfiles (list, optional): List of output files (wildcards may be used)
        cmdline_args (str, optional): GAMS tool command line arguments (read from tool definition file)
    """

    def __init__(self, name, description, path, includes,
                 inputfiles=None, opt_inputfiles=None,
                 outputfiles=None, cmdline_args=None):
        """Class constructor."""
        super().__init__(name, description, path, includes,
                         inputfiles, opt_inputfiles, outputfiles,
                         cmdline_args)
        self.main_prgm = includes[0]
        # Add .lst file to list of output files
        self.lst_file = os.path.splitext(self.main_prgm)[0] + '.lst'
        self.outputfiles.add(self.lst_file)
        # Split main_prgm to main_dir and main_prgm
        # because GAMS needs to run in the directory of the main program
        self.main_dir, self.main_prgm = os.path.split(self.main_prgm)
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

    def create_instance(self, ui, extra_cmdline_args, tool_output_dir, tool_name, configs):
        """Create an instance of the GAMS Tool.

        TODO: This should probably be done by Tool class of Spine Toolbox.

        Args:
            ui (TitanUI): Titan GUI window
            extra_cmdline_args (str): Extra command line arguments.
                In addition to the ones defined in tool definition file.
            tool_output_dir (str): Tool output directory
            tool_name (str): Short name of Tool that owns this Tool candidate!!!
            configs: (ConfigurationParser): Application configurations
        """
        # Let ToolCandidate class create the ToolInstance. TODO: Do this in Tool class?
        instance = super().create_instance(ui, extra_cmdline_args, tool_output_dir, tool_name)
        # Use gams.exe according to the selected GAMS directory in settings
        # Read needed settings from config file
        gams_path = configs.get('settings', 'gams_path')
        logoption_value = configs.get('settings', 'logoption')
        cerr_value = configs.get('settings', 'cerr')
        gams_exe_path = GAMS_EXECUTABLE
        if not gams_path == '':
            gams_exe_path = os.path.join(gams_path, GAMS_EXECUTABLE)
        # General GAMS options
        if logoption_value == '':  # If logoption is missing from .conf file
            logoption_value = 3
        if cerr_value == '':  # If cerr is missing from .conf file
            cerr_value = 1
        self.update_gams_options('logoption', logoption_value)
        self.update_gams_options('cerr', cerr_value)
        gams_option_list = list(self.gams_options.values())
        # Update logfile to instance outfiles
        logfile = os.path.splitext(self.files[0])[0] + '.log'
        logfile_path = os.path.join(instance.basedir, logfile)
        if logoption_value == '3':
            # Remove path for <TOOLNAME>.log from outfiles if present
            for out in instance.outfiles:
                if os.path.basename(out) == logfile:
                    try:
                        instance.outfiles.remove(out)
                        logging.debug("Removed path '{}' from outfiles".format(out))
                    except ValueError:
                        logging.exception("Tried to remove path '{}' but failed".format(out))
        elif logoption_value == '4':
            # Add <TOOLNAME>.log file to outfiles
            instance.outfiles.append(logfile_path)  # TODO: Instance outfiles is a list, tool outfiles is a set
        else:
            logging.error("Unknown value for logoption: {}".format(logoption_value))
        # Create run command for GAMS
        # command = '{} "{}" {}'.format(gams_exe_path,
        #                                           self.main_prgm,
        #                                           ' '.join(gams_option_list))
        self.main_dir = instance.basedir  # TODO: Get rid of self.main_dir
        command = '{} "{}" Curdir="{}" {}'.format(gams_exe_path,
                                                  self.main_prgm,
                                                  self.main_dir,
                                                  ' '.join(gams_option_list))
        # Update instance command
        instance.command = self.append_cmdline_args(command, setup_cmdline_args)
        return instance

    @staticmethod
    def load(path, data, ui):
        """Create a GAMSTool according to a tool definition.

        Args:
            path (str): Base path to tool files
            data (dict): Dictionary of tool definitions
            ui (TitanUI): Titan GUI instance

        Returns:
            GAMSTool instance or None if there was a problem in the tool definition file.
        """
        kwargs = GAMSTool.check_definition(data, ui)
        if kwargs is not None:
            # Return a Executable model instance
            return GAMSTool(path=path, **kwargs)
        else:
            return None
