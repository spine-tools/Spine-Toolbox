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
Tool class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import logging
import os
import json
import shutil
from metaobject import MetaObject
from widgets.sw_tool_widget import ToolSubWindowWidget
from PySide2.QtCore import Slot, Qt
from tool_instance import ToolInstance
from config import TOOL_OUTPUT_DIR, GAMS_EXECUTABLE, JULIA_EXECUTABLE


class Tool(MetaObject):
    """Tool class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        tool_template (ToolTemplate): Template for this Tool
    """
    def __init__(self, parent, name, description, project, tool_template):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Tool"
        self.item_category = "Tools"
        self._project = project
        self._widget = ToolSubWindowWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_input_files()
        self._widget.make_header_for_output_files()
        self._widget.ui.comboBox_tool.setModel(self._parent.tool_template_model)
        self._tool_template = None
        self.set_tool_template(tool_template)
        # Set correct row selected in the comboBox
        if not tool_template:
            r = 0
        else:
            r = self._parent.tool_template_model.tool_template_row(tool_template.name)
            if r == -1:
                logging.error("error in tool_template_row() method")
                r = 0
        self._widget.ui.comboBox_tool.setCurrentIndex(r)
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        # Directory where results are saved
        self.output_dir = os.path.join(self._project.project_dir, TOOL_OUTPUT_DIR, self.short_name)
        #setup connections buttons
        self._widget.ui.toolButton_connector.is_connector = True
        self.connect_signals()

    def connect_signals(self):
        """Connect this tool's signals to slots."""
        self._widget.ui.pushButton_details.clicked.connect(self.show_details)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)
        self._widget.ui.pushButton_execute.clicked.connect(self.execute)
        self._widget.ui.comboBox_tool.currentIndexChanged.connect(self.update_tool_template)
        self._widget.ui.toolButton_connector.clicked.connect(self.draw_links)

    @Slot(name="draw_links")
    def draw_links(self):
        self._parent.ui.mdiArea.draw_links(self.sender())

    @Slot(name='show_details')
    def show_details(self):
        """Details button clicked."""
        if not self.tool_template():
            self._parent.msg_warning.emit("No Tool Template")
            return
        definition = self.read_tool_def(self.tool_template().get_def_path())
        if not definition:
            return
        self._parent.msg.emit("Tool template file contents:\n{0}"
                              .format(json.dumps(definition, sort_keys=True, indent=4)))

    @Slot(name="show_connections")
    def show_connections(self):
        """Show connections of this Tool."""
        inputs = self._parent.connection_model.input_items(self.name)
        outputs = self._parent.connection_model.output_items(self.name)
        self._parent.msg.emit("<br/><b>{0}</b>".format(self.name))
        self._parent.msg.emit("Input items")
        if not inputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in inputs:
                self._parent.msg_warning.emit("{0}".format(item))
        self._parent.msg.emit("Output items")
        if not outputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in outputs:
                self._parent.msg_warning.emit("{0}".format(item))

    def tool_template(self):
        """Returns Tool template."""
        return self._tool_template

    def set_tool_template(self, tool_template):
        """Sets Tool Template for this Tool. Removes Tool Template if None given as argument.

        Args:
            tool_template (ToolTemplate): Template for this Tool. None removes the template.

        Returns:
            ToolTemplate or None if no Tool Template set for this Tool.
        """
        self._tool_template = tool_template
        self.update_tool_ui()

    def update_tool_ui(self):
        """Update Tool UI to show Tool template details."""
        if not self.tool_template():
            # self._widget.ui.comboBox_tool.setCurrentText("")
            self._widget.ui.lineEdit_tool_args.setText("")
            self._widget.populate_input_files_list(None)
            self._widget.populate_output_files_list(None)
        else:
            # self._widget.ui.comboBox_tool.setCurrentText(self.tool_template().name)
            self._widget.ui.lineEdit_tool_args.setText(self.tool_template().cmdline_args)
            self.update_input_files()
            self.update_output_files()

    def update_input_files(self):
        """Show input files in QListView."""
        if not self.tool_template():
            return
        def_path = self.tool_template().get_def_path()
        definition = self.read_tool_def(def_path)
        if not definition:
            return
        try:
            input_files = definition["inputfiles"]
        except KeyError:
            logging.error("Key 'inputfiles' not found in file {0}".format(def_path))
            return
        self._widget.populate_input_files_list(input_files)

    def update_output_files(self):
        """Show output files in QListView."""
        if not self.tool_template():
            return
        def_path = self.tool_template().get_def_path()
        definition = self.read_tool_def(def_path)
        if not definition:
            return
        try:
            output_files = definition["outputfiles"]
        except KeyError:
            logging.error("Key 'outputfiles' not found in file {0}".format(def_path))
            return
        self._widget.populate_output_files_list(output_files)

    def read_tool_def(self, tool_def_file):
        """Return tool template definition file contents or None if operation failed."""
        try:
            with open(tool_def_file, 'r') as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self._parent.msg_error.emit("Tool definition file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self._parent.msg_error.emit("Tool definition file <b>{0}</b> not found".format(tool_def_file))
            return None
        return definition

    @Slot(name="execute")
    def execute(self):
        """Execute button clicked."""
        if not self.tool_template():
            self._parent.msg_warning.emit("No Tool to execute")
            return
        self._parent.msg.emit("")
        self._parent.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        try:
            self.instance = ToolInstance(self.tool_template(), self._parent, self.output_dir, self._project)
        except OSError as e:
            self._parent.msg_error.emit("Tool instance creation failed. {0}".format(e))
            return
        # Find required input files for ToolInstance (if any)
        if self._widget.input_file_model.rowCount() > 0:
            self._parent.msg.emit("*** Searching for required input files ***")
            # Abort if there are no input items connected to this Tool
            inputs = self._parent.connection_model.input_items(self.name)
            if not inputs:
                self._parent.msg_error.emit("This Tool has no input connections. Required input files not found.")
                return
            file_copy_paths = self.find_input_files()
            if not file_copy_paths:
                self._parent.msg_error.emit("Tool execution aborted")
                return
            self._parent.msg.emit("*** Copying input files to work directory ***")
            # Copy input files to ToolInstance work directory
            if not self.copy_input_files(file_copy_paths):
                self._parent.msg_error.emit("Tool execution aborted")
                return
        self.update_instance()  # Make command and stuff
        self.instance.instance_finished_signal.connect(self.execution_finished)
        self.instance.execute()

    def find_input_files(self):
        """Iterate files in required input files model and find them from connected items.

        Returns:
            Dictionary of paths where required files are found or None if some file was not found.
        """
        file_paths = dict()
        for i in range(self._widget.input_file_model.rowCount()):
            req_file_path = self._widget.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            path, filename = os.path.split(req_file_path)
            found_file = self.find_file(filename)
            if not found_file:
                self._parent.msg_error.emit("\tRequired file <b>{0}</b> not found".format(filename))
                return None
            else:
                # file_paths.append(found_file)
                file_paths[req_file_path] = found_file
        return file_paths

    def find_file(self, fname):
        """Find required input file for this Tool Instance. Search file from Data
        Connection items that are input items for the Tool that instantiates this
        ToolInstance.

        Args:
            fname (str): File name (no path)

        Returns:
            Path to file or None if it was not found.
        """
        # TODO: Loop through all input items but beware of feedback loops and infinite loops
        path = None
        # Find file only from immediate parent items
        for input_item in self._parent.connection_model.input_items(self.name):
            # self._parent.msg.emit("Searching for file <b>{0}</b> from item <b>{1}</b>".format(fname, input_item))
            # Find item from project model
            found_item = self._parent.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._parent.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                return path
            item_data = found_item.data(Qt.UserRole)
            # Find file from parent Data Connections
            if item_data.item_type == "Data Connection":
                # Search in Data Connection data directory
                dc_files = item_data.data_files()  # List of file names (no path)
                if fname in dc_files:
                    self._parent.msg.emit("\t<b>{0}</b> found in DC <b>{1}</b>".format(fname, item_data.name))
                    path = os.path.join(item_data.data_dir, fname)
                    break
                # Search in Data Connection references
                else:
                    refs = item_data.file_references()  # List of paths including file name
                    for ref in refs:
                        p, fn = os.path.split(ref)
                        if fn == fname:
                            self._parent.msg.emit("\tReference for <b>{0}</b> found in DC <b>{1}</b>"
                                                  .format(fname, item_data.name))
                            path = ref
                            break
            elif item_data.item_type == "Tool":
                # TODO: Find file from output files of parent Tools
                pass
        return path

    def copy_input_files(self, paths):
        """Copy files from given paths to the directories in work directory, where the Tool requires them to be.

        Args:
            paths (dict): Key is path to required file, value is the path to where the file is located.

        Returns:
            Boolean variable depending on operation success
        """
        n_copied_files = 0
        for dst_folder, src_path in paths.items():
            # Join work directory path to dst folder
            dst_path = os.path.abspath(os.path.join(self.instance.basedir, dst_folder))
            fname = os.path.split(src_path)[1]
            self._parent.msg.emit("\tCopying <b>{0}</b>".format(fname))
            if not os.path.exists(src_path):
                self._parent.msg_error.emit("\tFile <b>{0}</b> does not exist".format(src_path))
                return False
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                logging.error(e)
                self._parent.msg_error.emit("\t[OSError] Copying file <b>{0}</b> to <b>{1}</b> failed"
                                            .format(src_path, dst_path))
                return False
        self._parent.msg.emit("\tCopied <b>{0}</b> file(s)".format(n_copied_files))
        return True

    @Slot(int, name="execution_finished")
    def execution_finished(self, return_code):
        """Tool execution finished."""
        if return_code == 0:
            self._parent.msg_success.emit("Tool <b>{0}</b> execution finished".format(self.tool_template().name))
        else:
            self._parent.msg_error.emit("Tool <b>{0}</b> execution failed".format(self.tool_template().name))

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. Maybe this is where Tool
        type specific initialization should happen (whether instance is GAMS or Julia Model)."""
        if self.tool_template().tooltype == "gams":
            gams_path = self._parent._config.get("settings", "gams_path")
            if not gams_path == '':
                gams_exe = os.path.join(gams_path, GAMS_EXECUTABLE)
            else:
                gams_exe = GAMS_EXECUTABLE
            main_dir = self.instance.basedir  # TODO: Is main_dir needed?
            command = '{} "{}" Curdir="{}" logoption=3'\
                .format(gams_exe, self.tool_template().main_prgm, main_dir)
            # Append Tool specific command line arguments to command (if present and implemented)
            self.instance.command = self.append_cmdline_args(command)
        elif self.tool_template().tooltype == "julia":
            use_repl = self._parent._config.getboolean("settings", "use_repl")
            if use_repl:
                # Run scripts in Julia REPL
                main_dir = self.instance.basedir  # TODO: Is main_dir needed?
                mod_main_dir = main_dir.__repr__().strip("'")
                self.instance.command = r'cd("{}");'\
                    r'try include("{}"); info("repl_succ")'\
                    r'catch e; info(e); info("repl_err") end{}'\
                    .format(mod_main_dir, self.tool_template().main_prgm, "\n")
            else:
                # Run scripts with command "julia script.jl"
                julia_dir = self._parent._config.get("settings", "julia_path")
                if not julia_dir == '':
                    julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
                else:
                    julia_exe = JULIA_EXECUTABLE
                work_dir = self.instance.basedir
                script_path = os.path.join(work_dir, self.tool_template().main_prgm)
                cmnd = '{0} {1}'.format(julia_exe, script_path)
                # Append Tool specific command line arguments to command
                self.instance.command = self.append_cmdline_args(cmnd)
                return

    def append_cmdline_args(self, command):
        """Append command line arguments to a command.

        Args:
            command (str): Command that starts processing the Tool in a subprocess
        """
        if (self.extra_cmdline_args is not None) and (not self.extra_cmdline_args == ''):
            if (self.tool_template().cmdline_args is not None) and (not self.tool_template().cmdline_args == ''):
                command += ' ' + self.tool_template().cmdline_args + ' ' + self.extra_cmdline_args
            else:
                command += ' ' + self.extra_cmdline_args
        else:
            if (self.tool_template().cmdline_args is not None) and (not self.tool_template().cmdline_args == ''):
                command += ' ' + self.tool_template().cmdline_args
        return command

    @Slot(int, name="update_tool_template")
    def update_tool_template(self, row):
        """Update Tool template according to selection.

        Args:
            row (int): Selected row in the comboBox
        """
        if row == 0:
            new_tool = None
        else:
            # Find ToolTemplate from model according to row
            new_tool = self._parent.tool_template_model.tool_template(row)
        self.set_tool_template(new_tool)
