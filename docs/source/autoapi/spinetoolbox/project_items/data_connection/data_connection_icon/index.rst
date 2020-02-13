:mod:`spinetoolbox.project_items.data_connection.data_connection_icon`
======================================================================

.. py:module:: spinetoolbox.project_items.data_connection.data_connection_icon

.. autoapi-nested-parse::

   Module for data connection icon class.

   :authors: M. Marin (KTH), P. Savolainen (VTT)
   :date:   4.4.2018



Module Contents
---------------

.. py:class:: DataConnectionIcon(toolbox, x, y, w, h, name)

   Bases: :class:`spinetoolbox.graphics_items.ProjectItemIcon`

   Data Connection icon for the Design View.

   :param toolbox: main window instance
   :type toolbox: ToolboxUI
   :param x: Icon x coordinate
   :type x: float
   :param y: Icon y coordinate
   :type y: float
   :param w: Width of master icon
   :type w: float
   :param h: Height of master icon
   :type h: float
   :param name: Item name
   :type name: str

   .. py:class:: _SignalHolder

      Bases: :class:`PySide2.QtCore.QObject`

      .. attribute:: files_dropped_on_icon
         

         A signal that it triggered when files are dragged and dropped on the item.



   .. method:: dragEnterEvent(self, event)


      Drag and drop action enters.
      Accept file drops from the filesystem.

      :param event: Event
      :type event: QGraphicsSceneDragDropEvent


   .. method:: dragLeaveEvent(self, event)


      Drag and drop action leaves.

      :param event: Event
      :type event: QGraphicsSceneDragDropEvent


   .. method:: dragMoveEvent(self, event)


      Accept event.


   .. method:: dropEvent(self, event)


      Emit files_dropped_on_dc signal from scene,
      with this instance, and a list of files for each dropped url.


   .. method:: select_on_drag_over(self)


      Called when the timer started in drag_enter_event is elapsed.
      Select this item if the drag action is still over it.



