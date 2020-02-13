:mod:`spinetoolbox.widgets.add_project_item_widget`
===================================================

.. py:module:: spinetoolbox.widgets.add_project_item_widget

.. autoapi-nested-parse::

   Widget shown to user when a new Project Item is created.

   :author: P. Savolainen (VTT)
   :date:   19.1.2017



Module Contents
---------------

.. py:class:: AddProjectItemWidget(toolbox, x, y, initial_name='')

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget to query user's preferences for a new item.

   .. attribute:: toolbox

      Parent widget

      :type: ToolboxUI

   .. attribute:: x

      X coordinate of new item

      :type: int

   .. attribute:: y

      Y coordinate of new item

      :type: int

   Initialize class.

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: name_changed(self)


      Update label to show upcoming folder name.


   .. method:: ok_clicked(self)


      Check that given item name is valid and add it to project.


   .. method:: call_add_item(self)
      :abstractmethod:


      Creates new Item according to user's selections.

      Must be reimplemented by subclasses.


   .. method:: keyPressEvent(self, e)


      Close Setup form when escape key is pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent



