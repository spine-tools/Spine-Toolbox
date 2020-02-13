:mod:`spinetoolbox.widgets.open_project_widget`
===============================================

.. py:module:: spinetoolbox.widgets.open_project_widget

.. autoapi-nested-parse::

   Contains a class for a widget that represents a 'Open Project Directory' dialog.

   :author: P. Savolainen (VTT)
   :date: 1.11.2019



Module Contents
---------------

.. py:class:: OpenProjectDialog(toolbox)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   A dialog that let's user select a project to open either by choosing
   an old .proj file or by choosing a project directory.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI

   .. method:: set_keyboard_shortcuts(self)


      Creates keyboard shortcuts for the 'Root', 'Home', etc. buttons.


   .. method:: connect_signals(self)


      Connects signals to slots.


   .. method:: expand_and_resize(self, p)


      Expands, resizes, and scrolls the tree view to the current directory
      when the file model has finished loading the path. Slot for the file
      model's directoryLoaded signal. The directoryLoaded signal is emitted only
      if the directory has not been cached already.

      :param p: Directory that has been loaded
      :type p: str


   .. method:: combobox_key_press_event(self, e)


      Interrupts Enter and Return key presses when QComboBox is in focus.
      This is needed to prevent showing the 'Not a valid Spine Toolbox project'
      Notifier every time Enter is pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: validator_state_changed(self)


      Changes the combobox border color according to the current state of the validator.


   .. method:: current_index_changed(self, i)


      Combobox selection changed. This slot is processed when a new item
      is selected from the drop-down list. This is not processed when new
      item txt is QValidotor.Intermediate.

      :param i: Selected row in combobox
      :type i: int


   .. method:: current_changed(self, current, previous)


      Processed when the current item in file system tree view has been
      changed with keyboard or mouse. Updates the text in combobox.

      :param current: Currently selected index
      :type current: QModelIndex
      :param previous: Previously selected index
      :type previous: QModelIndex


   .. method:: set_selected_path(self, index)


      Sets the text in the combobox as the selected path in the file system tree view.

      :param index: The index which was mouse clicked.
      :type index: QModelIndex


   .. method:: combobox_text_edited(self, text)


      Updates selected path when combobox text is edited.
      Note: pressing enter in combobox does not trigger this.


   .. method:: selection(self)


      Returns the selected path from dialog.


   .. method:: go_root(self, checked=False)


      Slot for the 'Root' button. Scrolls the treeview to show and select the user's root directory.

      Note: We need to expand and scroll the tree view here after setCurrentIndex
      just in case the directory has been loaded already.


   .. method:: go_home(self, checked=False)


      Slot for the 'Home' button. Scrolls the treeview to show and select the user's home directory.


   .. method:: go_documents(self, checked=False)


      Slot for the 'Documents' button. Scrolls the treeview to show and select the user's documents directory.


   .. method:: go_desktop(self, checked=False)


      Slot for the 'Desktop' button. Scrolls the treeview to show and select the user's desktop directory.


   .. method:: done(self, r)


      Checks that selected path exists and is a valid
      Spine Toolbox directory when ok button is clicked or
      when enter is pressed without the combobox being in focus.

      :param r:
      :type r: int


   .. method:: update_recents(entry, qsettings)
      :staticmethod:


      Adds a new entry to QSettings variable that remembers the five most recent project storages.

      :param entry: Abs. path to a directory that most likely contains other Spine Toolbox Projects as well.
                    First entry is also used as the initial path for File->New Project dialog.
      :type entry: str
      :param qsettings: Toolbox qsettings object
      :type qsettings: QSettings


   .. method:: remove_directory_from_recents(p, qsettings)
      :staticmethod:


      Removes directory from the recent project storages.

      :param p: Full path to a project directory
      :type p: str
      :param qsettings: Toolbox qsettings object
      :type qsettings: QSettings


   .. method:: show_context_menu(self, pos)


      Shows the context menu for the QCombobox with a 'Clear history' entry.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: closeEvent(self, event=None)


      Handles dialog closing.

      :param event: Close event
      :type event: QCloseEvent



.. py:class:: CustomQFileSystemModel

   Bases: :class:`PySide2.QtWidgets.QFileSystemModel`

   Custom file system model.

   .. method:: columnCount(self, parent=QModelIndex())


      Returns one.



.. py:class:: DirValidator(parent=None)

   Bases: :class:`PySide2.QtGui.QValidator`

   .. method:: validate(self, txt, pos)


      Returns Invalid if input is invalid according to this
      validator's rules, Intermediate if it is likely that a
      little more editing will make the input acceptable and
      Acceptable if the input is valid.

      :param txt: Text to validate
      :type txt: str
      :param pos: Cursor position
      :type pos: int

      :returns: Invalid, Intermediate, or Acceptable
      :rtype: QValidator.State



