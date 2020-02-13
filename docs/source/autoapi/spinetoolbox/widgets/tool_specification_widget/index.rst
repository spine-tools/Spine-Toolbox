:mod:`spinetoolbox.widgets.tool_specification_widget`
=====================================================

.. py:module:: spinetoolbox.widgets.tool_specification_widget

.. autoapi-nested-parse::

   QWidget that is used to create or edit Tool specifications.
   In the former case it is presented empty, but in the latter it
   is filled with all the information from the specification being edited.

   :author: M. Marin (KTH), P. Savolainen (VTT)
   :date:   12.4.2018



Module Contents
---------------

.. py:class:: ToolSpecificationWidget(toolbox, tool_specification=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget to query user's preferences for a new tool specification.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param tool_specification: If given, the form is pre-filled with this specification
   :type tool_specification: ToolSpecification

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: populate_sourcefile_list(self, items)


      List source files in QTreeView.
      If items is None or empty list, model is cleared.


   .. method:: populate_inputfiles_list(self, items)


      List input files in QTreeView.
      If items is None or empty list, model is cleared.


   .. method:: populate_inputfiles_opt_list(self, items)


      List optional input files in QTreeView.
      If items is None or empty list, model is cleared.


   .. method:: populate_outputfiles_list(self, items)


      List output files in QTreeView.
      If items is None or empty list, model is cleared.


   .. method:: browse_main_program(self, checked=False)


      Open file browser where user can select the path of the main program file.


   .. method:: set_main_program_path(self, file_path)


      Set main program file and folder path.


   .. method:: new_main_program_file(self)


      Creates a new blank main program file. Let's user decide the file name and path.
      Alternative version using only one getSaveFileName dialog.


   .. method:: new_source_file(self)


      Let user create a new source file for this tool specification.


   .. method:: show_add_source_files_dialog(self, checked=False)


      Let user select source files for this tool specification.


   .. method:: show_add_source_dirs_dialog(self, checked=False)


      Let user select a source directory for this tool specification.
      All files and sub-directories will be added to the source files.


   .. method:: add_dropped_includes(self, file_paths)


      Adds dropped file paths to Source files list.


   .. method:: add_single_include(self, path)


      Add file path to Source files list.


   .. method:: open_includes_file(self, index)


      Open source file in default program.


   .. method:: remove_source_files_with_del(self)


      Support for deleting items with the Delete key.


   .. method:: remove_source_files(self, checked=False)


      Remove selected source files from include list.
      Do not remove anything if there are no items selected.


   .. method:: add_inputfiles(self, checked=False)


      Let user select input files for this tool specification.


   .. method:: remove_inputfiles_with_del(self)


      Support for deleting items with the Delete key.


   .. method:: remove_inputfiles(self, checked=False)


      Remove selected input files from list.
      Do not remove anything if there are no items selected.


   .. method:: add_inputfiles_opt(self, checked=False)


      Let user select optional input files for this tool specification.


   .. method:: remove_inputfiles_opt_with_del(self)


      Support for deleting items with the Delete key.


   .. method:: remove_inputfiles_opt(self, checked=False)


      Remove selected optional input files from list.
      Do not remove anything if there are no items selected.


   .. method:: add_outputfiles(self, checked=False)


      Let user select output files for this tool specification.


   .. method:: remove_outputfiles_with_del(self)


      Support for deleting items with the Delete key.


   .. method:: remove_outputfiles(self, checked=False)


      Remove selected output files from list.
      Do not remove anything if there are no items selected.


   .. method:: handle_ok_clicked(self)


      Checks that everything is valid, creates Tool spec definition dictionary and adds Tool spec to project.


   .. method:: call_add_tool_specification(self)


      Adds or updates Tool specification according to user's selections.
      If the name is the same as an existing tool specification, it is updated and
      auto-saved to the definition file. (User is editing an existing
      tool specification.) If the name is not in the tool specification model, creates
      a new tool specification and offer to save the definition file. (User is
      creating a new tool specification from scratch or spawning from an existing one).


   .. method:: keyPressEvent(self, e)


      Close Setup form when escape key is pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent


   .. method:: _make_add_cmdline_tag_menu(self)


      Constructs a popup menu for the '@@' button.


   .. method:: _insert_spaces_around_tag_in_args_edit(self, tag_length, restore_cursor_to_tag_end=False)


      Inserts spaces before/after @@ around cursor position/selection

      Expects cursor to be at the end of the tag.


   .. method:: _add_cmdline_tag_url_inputs(self, _)


      Inserts @@url_inputs@@ tag to command line arguments.


   .. method:: _add_cmdline_tag_url_outputs(self, _)


      Inserts @@url_outputs@@ tag to command line arguments.


   .. method:: _add_cmdline_tag_data_store_url(self, _)


      Inserts @@url:<data-store-name>@@ tag to command line arguments and selects '<data-store-name>'.


   .. method:: _add_cmdline_tag_optional_inputs(self, _)


      Inserts @@optional_inputs@@ tag to command line arguments.



