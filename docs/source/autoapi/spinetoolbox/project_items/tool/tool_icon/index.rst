:mod:`spinetoolbox.project_items.tool.tool_icon`
================================================

.. py:module:: spinetoolbox.project_items.tool.tool_icon

.. autoapi-nested-parse::

   Module for tool icon class.

   :authors: M. Marin (KTH), P. Savolainen (VTT)
   :date:   4.4.2018



Module Contents
---------------

.. py:class:: ToolIcon(toolbox, x, y, w, h, name)

   Bases: :class:`spinetoolbox.graphics_items.ProjectItemIcon`

   Tool icon for the Design View.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolBoxUI
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

   .. method:: _value_for_time(msecs)
      :staticmethod:



   .. method:: start_animation(self)


      Start the animation that plays when the Tool associated to this GraphicsItem is running.


   .. method:: stop_animation(self)


      Stop animation



