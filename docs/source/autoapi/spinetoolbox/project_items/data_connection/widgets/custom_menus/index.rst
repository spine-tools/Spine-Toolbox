:mod:`spinetoolbox.project_items.data_connection.widgets.custom_menus`
======================================================================

.. py:module:: spinetoolbox.project_items.data_connection.widgets.custom_menus

.. autoapi-nested-parse::

   Classes for custom context menus and pop-up menus.

   :author: P. Savolainen (VTT)
   :date:   9.1.2018



Module Contents
---------------

.. py:class:: DcRefContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for references view in Data Connection properties.

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


.. py:class:: DcDataContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for data view in Data Connection properties.

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


