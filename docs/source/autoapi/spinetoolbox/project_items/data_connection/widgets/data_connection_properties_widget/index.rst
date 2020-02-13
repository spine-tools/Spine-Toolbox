:mod:`spinetoolbox.project_items.data_connection.widgets.data_connection_properties_widget`
===========================================================================================

.. py:module:: spinetoolbox.project_items.data_connection.widgets.data_connection_properties_widget

.. autoapi-nested-parse::

   Data connection properties widget.

   :author: M. Marin (KTH)
   :date:   12.9.2019



Module Contents
---------------

.. py:class:: DataConnectionPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the Data Connection Item Properties.

   :param toolbox: The toolbox instance where this widget should be embedded
   :type toolbox: ToolboxUI

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_references_context_menu(self, pos)


      Create and show a context-menu in data connection properties
      references view.

      :param pos: Mouse position
      :type pos: QPoint


   .. method:: show_data_context_menu(self, pos)


      Create and show a context-menu in data connection properties
      data view.

      :param pos: Mouse position
      :type pos: QPoint



