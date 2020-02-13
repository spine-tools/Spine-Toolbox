:mod:`spinetoolbox.widgets.project_form_widget`
===============================================

.. py:module:: spinetoolbox.widgets.project_form_widget

.. autoapi-nested-parse::

   Widget shown to user when a new project is created.

   :authors: P. Savolainen (VTT)
   :date:   10.1.2018



Module Contents
---------------

.. py:class:: NewProjectForm(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Class for a new project widget.

   :param toolbox: Parent widget.
   :type toolbox: ToolboxUI

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: select_project_dir(self, checked=False)


      Opens a file browser, where user can select a directory for the new project.


   .. method:: ok_clicked(self)


      Check that project name is valid and create project.


   .. method:: call_create_project(self)


      Call ToolboxUI method create_project().


   .. method:: keyPressEvent(self, e)


      Close project form when escape key is pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent



