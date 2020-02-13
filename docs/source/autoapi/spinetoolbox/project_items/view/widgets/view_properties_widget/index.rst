:mod:`spinetoolbox.project_items.view.widgets.view_properties_widget`
=====================================================================

.. py:module:: spinetoolbox.project_items.view.widgets.view_properties_widget

.. autoapi-nested-parse::

   View properties widget.

   :author: M. Marin (KTH)
   :date:   12.9.2019



Module Contents
---------------

.. py:class:: ViewPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the View Item Properties.

   :param toolbox: The toolbox instance where this widget should be embeded
   :type toolbox: ToolboxUI

   Init class.

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_view_properties_context_menu(self, pos)


      Create and show a context-menu in View properties.

      :param pos: Mouse position
      :type pos: QPoint



