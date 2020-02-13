:mod:`spinetoolbox.project_items.view.widgets.add_view_widget`
==============================================================

.. py:module:: spinetoolbox.project_items.view.widgets.add_view_widget

.. autoapi-nested-parse::

   Widget shown to user when a new View is created.

   :author: P. Savolainen (VTT)
   :date:   19.1.2017



Module Contents
---------------

.. py:class:: AddViewWidget(toolbox, x, y)

   Bases: :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`

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

   .. method:: call_add_item(self)


      Creates new Item according to user's selections.



