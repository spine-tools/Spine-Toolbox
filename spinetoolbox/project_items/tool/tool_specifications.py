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
Contains Tool specification classes.

:authors: P. Savolainen (VTT), E. Rinne (VTT), M. Marin (KTH)
:date:   24.1.2018
"""

from collections import OrderedDict
import logging
import os
import json
from spinetoolbox.project_item_specification import ProjectItemSpecification
from spinetoolbox.helpers import open_url
from spinetoolbox.project_items.shared.helpers import split_cmdline_args, expand_tags
from .item_info import ItemInfo
from .tool_instance import GAMSToolInstance, JuliaToolInstance, PythonToolInstance, ExecutableToolInstance

# Tool types
TOOL_TYPES = ["Julia", "Python", "GAMS", "Executable"]

# Required and optional keywords for Tool specification dictionaries
REQUIRED_KEYS = ["name", "tooltype", "includes"]
OPTIONAL_KEYS = [
    "description",
    "short_name",
    "inputfiles",
    "inputfiles_opt",
    "outputfiles",
    "cmdline_args",
    "execute_in_work",
]
LIST_REQUIRED_KEYS = ["includes", "inputfiles", "inputfiles_opt", "outputfiles"]  # These should be lists


class ToolSpecification(ProjectItemSpecification):
    """Super class for all tool specifications."""

    def __init__(
        self,
        name,
        tooltype,
        path,
        includes,
        settings,
        logger,
        description=None,
        inputfiles=None,
        inputfiles_opt=None,
        outputfiles=None,
        cmdline_args=None,
        execute_in_work=True,
    ):
        """

        Args:
            name (str): Name of the tool
            tooltype (str): Type of Tool (e.g. Python, Julia, ..)
            path (str): Path to tool
            includes (list): List of files belonging to the tool specification (relative to 'path')
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): a logger instance
            description (str): Description of the Tool specification
            inputfiles (list): List of required data files
            inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
            outputfiles (list, optional): List of output files (wildcards may be used)
            cmdline_args (str, optional): Tool command line arguments (read from tool definition file)
            execute_in_work (bool): Execute in work folder
        """
        super().__init__(name, description, item_type=ItemInfo.item_type(), item_category=ItemInfo.item_category())
        self._settings = settings
        self._logger = logger
        self.tooltype = tooltype
        if not os.path.exists(path):
            pass
        else:
            self.path = path
        self.includes = includes
        if cmdline_args is not None:
            if isinstance(cmdline_args, str):
                # Old tool spec files may have the command line arguments as plain strings.
                self.cmdline_args = split_cmdline_args(cmdline_args)
            else:
                self.cmdline_args = cmdline_args
        else:
            self.cmdline_args = []
        self.inputfiles = set(inputfiles) if inputfiles else set()
        self.inputfiles_opt = set(inputfiles_opt) if inputfiles_opt else set()
        self.outputfiles = set(outputfiles) if outputfiles else set()
        self.return_codes = {}
        self.execute_in_work = execute_in_work

    def save(self):
        """Saves this specification to a .json file in the definition path.

        Returns:
            bool: How it went
        """
        definition_path = self.definition_file_path
        definition = {
            "name": self.name,
            "tooltype": self.tooltype,
            "includes": self.includes,
            "description": self.description,
            "inputfiles": list(self.inputfiles),
            "inputfiles_opt": list(self.inputfiles_opt),
            "outputfiles": list(self.outputfiles),
            "cmdline_args": self.cmdline_args,
            "execute_in_work": self.execute_in_work,
            "includes_main_path": os.path.relpath(self.path, os.path.dirname(definition_path)),
        }
        with open(definition_path, "w") as fp:
            try:
                json.dump(definition, fp, indent=4)
                return True
            except ValueError:
                self.statusbar.showMessage("Error saving file", 3000)
                self._logger.msg_error.emit("Saving Tool specification file failed. Path:{0}".format(definition_path))
                return False

    def is_equivalent(self, definition):
        """Checks if this spec is equivalent to the given definition dictionary.
        Used by the tool spec widget when updating specs.

        Args:
            definition (dict)

        Returns:
            bool: True if equivalent
        """
        for p in definition:
            if p in LIST_REQUIRED_KEYS:
                if set(self.__dict__[p]) != set(definition[p]):
                    return False
            else:
                if self.__dict__[p] != definition[p]:
                    return False
        return True

    def set_return_code(self, code, description):
        """Sets a return code and an associated text description for the tool specification.

        Args:
            code (int): Return code
            description (str): Description
        """
        self.return_codes[code] = description

    @staticmethod
    def check_definition(data, logger):
        """Checks that a tool specification contains
        the required keys and that it is in correct format.

        Args:
            data (dict): Tool specification
            logger (LoggerInterface): A logger instance

        Returns:
            Dictionary or None if there was a problem in the tool definition.
        """
        kwargs = dict()
        for p in REQUIRED_KEYS + OPTIONAL_KEYS:
            try:
                kwargs[p] = data[p]
            except KeyError:
                if p in REQUIRED_KEYS:
                    logger.msg_error.emit("Required keyword '{0}' missing".format(p))
                    return None
            # Check that some values are lists
            if p in LIST_REQUIRED_KEYS:
                try:
                    if not isinstance(data[p], list):
                        logger.msg_error.emit("Keyword '{0}' value must be a list".format(p))
                        return None
                except KeyError:
                    pass
        return kwargs

    def get_cmdline_args(self, optional_input_files, input_urls, output_urls):
        """
        Returns tool specification's command line args as list.

        Replaces special tags in arguments:

        - @@optional_inputs@@ expands to a space-separated list of Tool's optional input files
        - @@url:<Data Store name>@@ expands to the URL provided by a named data store
        - @@url_inputs@@ expands to a space-separated list of Tool's input database URLs
        - @@url_outputs@@ expands to a space-separated list of Tool's output database URLs

        Args:
            optional_input_files (list): a list of Tool's optional input file names
            input_urls (dict): a mapping from URL provider (input Data Store name) to URL string
            output_urls (dict): a mapping from URL provider (output Data Store name) to URL string
        Returns:
            list: a list of expanded command line arguments
        """
        tags_expanded, args = expand_tags(self.cmdline_args, optional_input_files, input_urls, output_urls)
        while tags_expanded:
            # Keep expanding until there is no tag left to expand.
            tags_expanded, args = expand_tags(args, optional_input_files, input_urls, output_urls)
        return args

    def create_tool_instance(self, basedir):
        """Returns an instance of the tool specification configured to run in the given directory.
        Needs to be implemented in subclasses.

        Args:
            basedir (str): Path to directory where the instance will run
        """
        raise NotImplementedError

    @staticmethod
    def toolbox_load(
        definition, definition_path, app_settings, logger, embedded_julia_console, embedded_python_console
    ):
        """
        Deserializes and constructs a tool specification from definition.

        Args:
            definition (dict): a dictionary containing the serialized specification.
            definition_path (str): path to the definition file
            app_settings (QSettings): Toolbox settings
            logger (LoggerInterface): a logger
            embedded_julia_console (JuliaREPLWidget, optional): Julia console widget,
                required if a Julia tool is to be run in the console
            embedded_python_console (PythonReplWidget, optional): Python console widget,
                required if a Python tool is to be run in the console
        Returns:
            ToolSpecification: a tool specification constructed from the given definition,
                or None if there was an error
        """
        includes_main_path = definition.get("includes_main_path", ".")
        path = os.path.normpath(os.path.join(os.path.dirname(definition_path), includes_main_path))
        try:
            _tooltype = definition["tooltype"].lower()
        except KeyError:
            logger.msg_error.emit(
                "No tool type defined in tool definition file. Supported types "
                "are 'python', 'gams', 'julia' and 'executable'"
            )
            return None
        if _tooltype == "julia":
            spec = JuliaTool.load(path, definition, app_settings, embedded_julia_console, logger)
        elif _tooltype == "python":
            spec = PythonTool.load(path, definition, app_settings, embedded_python_console, logger)
        elif _tooltype == "gams":
            spec = GAMSTool.load(path, definition, app_settings, logger)
        elif _tooltype == "executable":
            spec = ExecutableTool.load(path, definition, app_settings, logger)
        else:
            logger.msg_warning.emit("Tool type <b>{}</b> not available".format(_tooltype))
            return None
        spec.definition_file_path = definition_path
        return spec

    def open_main_program_file(self):
        """Open this specification's main program file in the default editor."""
        file_path = os.path.join(self.path, self.includes[0])
        # Check if file exists first. openUrl may return True even if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            self._logger.msg_error.emit("Tool main program file <b>{0}</b> not found.".format(file_path))
            return
        ext = os.path.splitext(os.path.split(file_path)[1])[1]
        if ext in [".bat", ".exe"]:
            self._logger.msg_warning.emit(
                "Sorry, opening files with extension <b>{0}</b> not supported. "
                "Please open the file manually.".format(ext)
            )
            return
        main_program_url = "file:///" + file_path
        # Open Tool specification main program file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = open_url(main_program_url)
        if not res:
            filename, file_extension = os.path.splitext(file_path)
            self._logger.msg_error.emit(
                "Unable to open Tool specification main program file {0}. "
                "Make sure that <b>{1}</b> "
                "files are associated with an editor. E.g. on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(filename, file_extension)
            )


class GAMSTool(ToolSpecification):
    """Class for GAMS tool specifications."""

    def __init__(
        self,
        name,
        tooltype,
        path,
        includes,
        settings,
        logger,
        description=None,
        inputfiles=None,
        inputfiles_opt=None,
        outputfiles=None,
        cmdline_args=None,
        execute_in_work=True,
    ):
        """

        Args:
            name (str): GAMS Tool name
            tooltype (str): Tool specification type
            path (str): Path to model main file
            includes (list): List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): a logger instance
            First file in the list is the main GAMS program.
            description (str): GAMS Tool description
            inputfiles (list): List of required data files
            inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
            outputfiles (list, optional): List of output files (wildcards may be used)
            cmdline_args (str, optional): GAMS tool command line arguments (read from tool definition file)
        """
        super().__init__(
            name,
            tooltype,
            path,
            includes,
            settings,
            logger,
            description,
            inputfiles,
            inputfiles_opt,
            outputfiles,
            cmdline_args,
            execute_in_work,
        )
        main_file = includes[0]
        # Add .lst file to list of output files
        self.lst_file = os.path.splitext(main_file)[0] + ".lst"
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
            62097: "Simulation interrupted by user",  # Not official
        }

    def update_gams_options(self, key, value):
        """[OBSOLETE?] Updates GAMS command line options. Only 'cerr' and 'logoption' keywords supported.

        Args:
            key (str): Option name
            value (int, float): Option value
        """
        # Supported GAMS logoption values
        # 3 writes LOG output to standard output
        # 4 writes LOG output to a file and standard output  [Not supported in GAMS v24.0]
        if key in ["logoption", "cerr"]:
            self.gams_options[key] = "{0}={1}".format(key, value)
        else:
            logging.error("Updating GAMS options failed. Unknown key: %s", key)

    @staticmethod
    def load(path, data, settings, logger):
        """Creates a GAMSTool according to a tool specification file.

        Args:
            path (str): Base path to tool files
            data (dict): Dictionary of tool definitions
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): A logger instance

        Returns:
            GAMSTool instance or None if there was a problem in the tool specification file.
        """
        kwargs = GAMSTool.check_definition(data, logger)
        if kwargs is not None:
            # Return an executable model instance
            return GAMSTool(path=path, settings=settings, logger=logger, **kwargs)
        return None

    def create_tool_instance(self, basedir):
        """Returns an instance of this tool specification that is configured to run in the given directory.

        Args:
            basedir (str): the path to the directory where the instance will run
        """
        return GAMSToolInstance(self, basedir, self._settings, self._logger)


class JuliaTool(ToolSpecification):
    """Class for Julia tool specifications."""

    def __init__(
        self,
        name,
        tooltype,
        path,
        includes,
        settings,
        embedded_julia_console,
        logger,
        description=None,
        inputfiles=None,
        inputfiles_opt=None,
        outputfiles=None,
        cmdline_args=None,
        execute_in_work=True,
    ):
        """
        Args:
            name (str): Julia Tool name
            tooltype (str): Tool specification type
            path (str): Path to model main file
            includes (list): List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
            First file in the list is the main Julia program.
            settings (QSettings): Toolbox settings
            embedded_julia_console (JuliaREPLWidget): a Julia console widget for execution in the embedded console
            logger (LoggerInterface): A logger instance
            description (str): Julia Tool description
            inputfiles (list): List of required data files
            inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
            outputfiles (list, optional): List of output files (wildcards may be used)
            cmdline_args (str, optional): Julia tool command line arguments (read from tool definition file)
        """
        super().__init__(
            name,
            tooltype,
            path,
            includes,
            settings,
            logger,
            description,
            inputfiles,
            inputfiles_opt,
            outputfiles,
            cmdline_args,
            execute_in_work,
        )
        self._embedded_console = embedded_julia_console
        main_file = includes[0]
        self.main_dir, self.main_prgm = os.path.split(main_file)
        self.julia_options = OrderedDict()
        self.return_codes = {0: "Normal return"}  # Not official

    def update_julia_options(self, key, value):
        """[OBSOLETE?] Updates Julia command line options.

        Args:
            key (str): Option name
            value (int, float): Option value
        """

    @staticmethod
    def load(path, data, settings, embedded_julia_console, logger):
        """Creates a JuliaTool according to a tool specification file.

        Args:
            path (str): Base path to tool files
            data (dict): Dictionary of tool definitions
            settings (QSetting): Toolbox settings
            embedded_julia_console (JuliaREPLWidget): a Julia console for execution in the embedded console
            logger (LoggerInterface): A logger instance

        Returns:
            JuliaTool instance or None if there was a problem in the tool definition file.
        """
        kwargs = JuliaTool.check_definition(data, logger)
        if kwargs is not None:
            # Return an executable model instance
            return JuliaTool(
                path=path, settings=settings, embedded_julia_console=embedded_julia_console, logger=logger, **kwargs
            )
        return None

    def create_tool_instance(self, basedir):
        """Returns an instance of this tool specification that is configured to run in the given directory.

        Args:
            basedir (str): the path to the directory where the instance will run
        """
        return JuliaToolInstance(self, basedir, self._settings, self._embedded_console, self._logger)


class PythonTool(ToolSpecification):
    """Class for Python tool specifications."""

    def __init__(
        self,
        name,
        tooltype,
        path,
        includes,
        settings,
        embedded_python_console,
        logger,
        description=None,
        inputfiles=None,
        inputfiles_opt=None,
        outputfiles=None,
        cmdline_args=None,
        execute_in_work=True,
    ):
        """
        Args:

            name (str): Python Tool name
            tooltype (str): Tool specification type
            path (str): Path to model main file
            includes (list): List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
            settings (QSettings): Toolbox settings
            embedded_python_console (PythonReplWidget): a Python console widget for embedded console execution
            logger (LoggerInterface): A logger instance
            First file in the list is the main Python program.
            description (str): Python Tool description
            inputfiles (list): List of required data files
            inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
            outputfiles (list, optional): List of output files (wildcards may be used)
            cmdline_args (str, optional): Python tool command line arguments (read from tool definition file)
        """
        super().__init__(
            name,
            tooltype,
            path,
            includes,
            settings,
            logger,
            description,
            inputfiles,
            inputfiles_opt,
            outputfiles,
            cmdline_args,
            execute_in_work,
        )
        self._embedded_console = embedded_python_console
        main_file = includes[0]
        self.main_dir, self.main_prgm = os.path.split(main_file)
        self.python_options = OrderedDict()
        self.return_codes = {0: "Normal return"}  # Not official

    def update_python_options(self, key, value):
        """[OBSOLETE?] Updates Python command line options.

        Args:
            key (str): Option name
            value (int, float): Option value
        """

    @staticmethod
    def load(path, data, settings, embedded_python_console, logger):
        """Creates a PythonTool according to a tool specification file.

        Args:
            path (str): Base path to tool files
            data (dict): Dictionary of tool definitions
            settings (QSettings): Toolbox settings
            embedded_python_console (PythonReplWidget): Python console widget for execution in the embedded console
            logger (LoggerInterface): A logger instance

        Returns:
            PythonTool instance or None if there was a problem in the tool definition file.
        """
        kwargs = PythonTool.check_definition(data, logger)
        if kwargs is not None:
            # Return an executable model instance
            return PythonTool(
                path=path, settings=settings, embedded_python_console=embedded_python_console, logger=logger, **kwargs
            )
        return None

    def create_tool_instance(self, basedir):
        """Returns an instance of this tool specification that is configured to run in the given directory.

        Args:
            basedir (str): the path to the directory where the instance will run
        """
        return PythonToolInstance(self, basedir, self._settings, self._embedded_console, self._logger)


class ExecutableTool(ToolSpecification):
    """Class for Executable tool specifications."""

    def __init__(
        self,
        name,
        tooltype,
        path,
        includes,
        settings,
        logger,
        description=None,
        inputfiles=None,
        inputfiles_opt=None,
        outputfiles=None,
        cmdline_args=None,
        execute_in_work=True,
    ):
        """
        Args:

            name (str): Tool name
            tooltype (str): Tool specification type
            path (str): Path to main script file
            includes (list): List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
            First file in the list is the main script file.
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): A logger instance
            description (str): Tool description
            inputfiles (list): List of required data files
            inputfiles_opt (list, optional): List of optional data files (wildcards may be used)
            outputfiles (list, optional): List of output files (wildcards may be used)
            cmdline_args (str, optional): Tool command line arguments (read from tool definition file)
        """
        super().__init__(
            name,
            tooltype,
            path,
            includes,
            settings,
            logger,
            description,
            inputfiles,
            inputfiles_opt,
            outputfiles,
            cmdline_args,
            execute_in_work,
        )
        main_file = includes[0]
        # TODO: This does not do anything because main_file is always just file name
        self.main_dir, self.main_prgm = os.path.split(main_file)
        self.options = OrderedDict()
        self.return_codes = {0: "Normal exit", 1: "Error happened"}

    @staticmethod
    def load(path, data, settings, logger):
        """Creates an ExecutableTool according to a tool specification file.

        Args:
            path (str): Base path to tool files
            data (dict): Tool specification
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): A logger instance

        Returns:
            ExecutableTool instance or None if there was a problem in the tool specification.
        """
        kwargs = ExecutableTool.check_definition(data, logger)
        if kwargs is not None:
            # Return an executable model instance
            return ExecutableTool(path=path, settings=settings, logger=logger, **kwargs)
        return None

    def create_tool_instance(self, basedir):
        """Returns an instance of this tool specification that is configured to run in the given directory.

        Args:
            basedir (str): the path to the directory where the instance will run
        """
        return ExecutableToolInstance(self, basedir, self._settings, self._logger)
