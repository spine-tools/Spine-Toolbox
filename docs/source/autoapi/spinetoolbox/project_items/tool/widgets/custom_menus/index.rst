:mod:`spinetoolbox.project_items.tool.widgets.custom_menus`
===========================================================

.. py:module:: spinetoolbox.project_items.tool.widgets.custom_menus

.. autoapi-nested-parse::

   Classes for custom context menus and pop-up menus.

   :author: P. Savolainen (VTT)
   :date:   9.1.2018



Module Contents
---------------

.. py:class:: ToolPropertiesContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Common context menu class for all Tool QTreeViews in Tool properties.

   .. attribute:: parent

      Parent for menu widget (ToolboxUI)

      :type: QWidget

   .. attribute:: position

      Position on screen

      :type: QPoint

   .. attribute:: index

      Index of item that requested the context-menu

      :type: QModelIndex

   Class constructor.


.. py:class:: ToolContextMenu(parent, tool, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.ProjectItemContextMenu`

   Context menu for Tools in the QTreeView and in the QGraphicsView.

   .. attribute:: parent

      Parent for menu widget (ToolboxUI)

      :type: QWidget

   .. attribute:: position

      Position on screen

      :type: QPoint

   Class constructor.


