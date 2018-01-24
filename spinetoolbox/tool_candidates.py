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
from config import GAMS_EXECUTABLE, CONFIGURATION_FILE


class ToolCandidate(MetaObject):
    """Super class for different tool candidates."""

    def __init__(self, name, description, path, files,
                 datafiles=None, datafiles_opt=None,
                 outfiles=None, short_name=None,
                 logfile=None, cmdline_args=None):
        """Class constructor.

        Args:
            name (str): Name of the tool
            description (str): Short description of the tool
            path (str): Path to tool
            files (str): List of files belonging to the tool (relative to 'path')
            datafiles (list, optional): List of required data files
            datafiles_opt (list, optional): List of optional data files (wildcards may be used)
            outfiles (list, optional): List of output files (wildcards may be used)
            short_name (str, optional): Short name for the tool
            logfile (str, optional): Log file name (relative to 'path')
            cmdline_args (str, optional): Tool command line arguments (read from tool definition file)
        """
        super().__init__(name, description)
        if not os.path.exists(path):
            pass  # TODO: Do something here
        else:
            self.path = path
        self.files = files
        self.cmdline_args = cmdline_args
        self.datafiles = set(datafiles) if datafiles else set()
        self.datafiles_opt = set(datafiles_opt) if datafiles_opt else set()
        self.outfiles = set(outfiles) if outfiles else set()
        self.return_codes = {}
        self.def_file_path = ''  # Tool definition file path (JSON)

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
    def check_definition(data, ui, required=None, optional=None, list_required=None):
        """Check a dict containing tool definition.

        Args:
            data (dict): Dictionary of tool definitions
            ui (TitanUI): Titan GUI instance
            required (list): required keys
            optional  (list): optional keys
            list_required (list): keys that need to be lists

        Returns:
            dict or None if there was a problem in the tool definition file
        """
        # Required and optional keys in definition file
        if required is None:
            required = REQUIRED_KEYS
        if optional is None:
            optional = OPTIONAL_KEYS
        if list_required is None:
            list_required = LIST_REQUIRED_KEYS
        kwargs = {}
        for p in required + optional:
            try:
                kwargs[p] = data[p]
            except KeyError:
                if p in required:
                    ui.add_msg_signal.emit(
                        "Required keyword '{0}' missing".format(p), 2)
                    logging.error("Required keyword '{0}' missing".format(p))
                    return None
                else:
                    # logging.info("Optional keyword '{0}' missing".format(p))
                    pass
            # Check that some variables are lists
            if p in list_required:
                try:
                    if not isinstance(data[p], list):
                        ui.add_msg_signal.emit(
                            "Keyword '{0}' value must be a list".format(p), 2)
                        logging.error(
                            "Keyword '{0}' value must be a list".format(p))
                        return None
                except KeyError:
                    pass
        return kwargs


class GAMSTool(ToolCandidate):
    """Class for GAMS Tools."""

    def __init__(self, name, description, path, files,
                 datafiles=None, datafiles_opt=None, outfiles=None,
                 short_name=None, cmdline_args=None):
        """Class constructor.

        Args:
            name (str): GAMS Tool name
            description (str): GAMS Tool description
            path (str): Path
            files (str): List of files belonging to the tool (relative to 'path')
                         First file in the list is the main GAMS program.
            datafiles (list, optional): List of required data files
            datafiles_opt (list, optional): List of optional data files (wildcards may be used)
            outfiles (list, optional): List of output files (wildcards may be used)
            short_name (str, optional): Short name for the GAMS tool
            cmdline_args (str, optional): GAMS tool command line arguments (read from tool definition file)
        """
        super().__init__(name, description, path, files,
                         datafiles, datafiles_opt, outfiles, short_name,
                         cmdline_args=cmdline_args)
        self.main_prgm = files[0]
        # Add .lst file to list of output files
        self.lst_file = os.path.splitext(self.main_prgm)[0] + '.lst'
        self.outfiles.add(self.lst_file)
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
        return "GAMSTool('{}')".format(self.name)

    def update_gams_options(self, key, value):
        """Update GAMS command line options. 'cerr and 'logoption' keywords supported.

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

    def create_instance(self, ui, setup_cmdline_args, tool_output_dir, setup_name, configs):
        """Create an instance of the GAMS model

        Args:
            ui (TitanUI): Titan GUI window
            setup_cmdline_args (str): Extra Setup command line arguments
            tool_output_dir (str): Tool output directory
            setup_name (str): Short name of Setup that owns this Tool
            configs: (ConfigurationParser): Application configurations
        """
        # Let Tool class create the ToolInstance
        instance = super().create_instance(ui, setup_cmdline_args, tool_output_dir, setup_name)
        # Use gams.exe according to the selected GAMS directory in settings
        # Read needed settings from config file
        gams_path = configs.get('general', 'gams_path')
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
