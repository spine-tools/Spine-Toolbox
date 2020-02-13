:mod:`spinetoolbox.widgets.settings_widget`
===========================================

.. py:module:: spinetoolbox.widgets.settings_widget

.. autoapi-nested-parse::

   Widget for controlling user settings.

   :author: P. Savolainen (VTT)
   :date:   17.1.2018



Module Contents
---------------

.. py:class:: SettingsWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget to change user's preferred settings.

   .. attribute:: toolbox

      Parent widget.

      :type: ToolboxUI

   Initialize class.

   .. method:: connect_signals(self)


      Connect signals.


   .. method:: browse_gams_path(self, checked=False)


      Open file browser where user can select a GAMS program.


   .. method:: browse_julia_path(self, checked=False)


      Open file browser where user can select a Julia executable (i.e. julia.exe on Windows).


   .. method:: browse_julia_project_path(self, checked=False)


      Open file browser where user can select a Julia project path.


   .. method:: browse_python_path(self, checked=False)


      Open file browser where user can select a python interpreter (i.e. python.exe on Windows).


   .. method:: browse_work_path(self, checked=False)


      Open file browser where user can select the path to wanted work directory.


   .. method:: show_color_dialog(self, checked=False)


      Let user pick the bg color.

      :param checked: Value emitted with clicked signal
      :type checked: boolean


   .. method:: update_bg_color(self)


      Set tool button icon as the selected color and update
      Design View scene background color.


   .. method:: update_scene_bg(self, checked=False)


      Draw background on scene depending on radiobutton states.

      :param checked: Toggle state
      :type checked: boolean


   .. method:: update_links_geometry(self, checked=False)



   .. method:: read_settings(self)


      Read saved settings from app QSettings instance and update UI to display them.


   .. method:: read_project_settings(self)


      Get project name and description and update widgets accordingly.


   .. method:: handle_ok_clicked(self)


      Get selections and save them to persistent memory.
      Note: On Linux, True and False are saved as boolean values into QSettings.
      On Windows, booleans and integers are saved as strings. To make it consistent,
      we should use strings.


   .. method:: update_project_settings(self)


      Update project name and description if these have been changed.


   .. method:: check_if_python_env_changed(self, new_path)


      Checks if Python environment was changed.
      This indicates that the Python Console may need a restart.


   .. method:: check_if_work_dir_changed(self, new_work_dir)


      Checks if work directory was changed.

      :param new_work_dir: Possibly a new work directory
      :type new_work_dir: str


   .. method:: file_is_valid(self, file_path, msgbox_title)


      Checks that given path is not a directory and it's a file that actually exists.
      Needed because the QLineEdits are editable.


   .. method:: dir_is_valid(self, dir_path, msgbox_title)


      Checks that given path is a directory.
      Needed because the QLineEdits are editable.


   .. method:: keyPressEvent(self, e)


      Close settings form when escape key is pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent


   .. method:: mousePressEvent(self, e)


      Save mouse position at the start of dragging.

      :param e: Mouse event
      :type e: QMouseEvent


   .. method:: mouseReleaseEvent(self, e)


      Save mouse position at the end of dragging.

      :param e: Mouse event
      :type e: QMouseEvent


   .. method:: mouseMoveEvent(self, e)


      Moves the window when mouse button is pressed and mouse cursor is moved.

      :param e: Mouse event
      :type e: QMouseEvent



