:mod:`spinetoolbox.project_items.tool.widgets.tool_properties_widget`
=====================================================================

.. py:module:: spinetoolbox.project_items.tool.widgets.tool_properties_widget

.. autoapi-nested-parse::

   Tool properties widget.

   :author: M. Marin (KTH)
   :date:   12.9.2019



Module Contents
---------------

.. py:class:: ToolPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the Tool Item Properties.

   :param toolbox: The toolbox instance where this widget should be embeded
   :type toolbox: ToolboxUI

   Init class.

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_tool_properties_context_menu(self, pos)


      Create and show a context-menu in Tool properties
      if selected Tool has a Tool specification.

      :param pos: Mouse position
      :type pos: QPoint



