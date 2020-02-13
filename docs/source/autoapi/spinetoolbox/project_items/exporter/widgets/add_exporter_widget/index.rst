:mod:`spinetoolbox.project_items.exporter.widgets.add_exporter_widget`
======================================================================

.. py:module:: spinetoolbox.project_items.exporter.widgets.add_exporter_widget

.. autoapi-nested-parse::

   Widget shown to user when a new Exporter item is created.

   :author: A. Soininen (VTT)
   :date:   6.9.2019



Module Contents
---------------

.. py:class:: AddExporterWidget(toolbox, x, y)

   Bases: :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`

   A widget to query user's preferences for a new item.

   :param toolbox: Parent widget
   :type toolbox: ToolboxUI
   :param x: X coordinate of new item
   :type x: int
   :param y: Y coordinate of new item
   :type y: int

   .. method:: call_add_item(self)


      Creates new Item according to user's selections.



