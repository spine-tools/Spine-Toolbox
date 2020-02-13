:mod:`spinetoolbox.project_items.importer.widgets.add_importer_widget`
======================================================================

.. py:module:: spinetoolbox.project_items.importer.widgets.add_importer_widget

.. autoapi-nested-parse::

   Widget shown to user when a new Importer is created.

   :author: P. Savolainen (VTT)
   :date:   19.1.2017



Module Contents
---------------

.. py:class:: AddImporterWidget(toolbox, x, y)

   Bases: :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`

   A widget to query user's preferences for a new item.

   :param toolbox: Parent widget
   :type toolbox: ToolboxUI
   :param x: X coordinate of new item
   :type x: float
   :param y: Y coordinate of new item
   :type y: float

   .. method:: call_add_item(self)


      Creates new Item according to user's selections.



