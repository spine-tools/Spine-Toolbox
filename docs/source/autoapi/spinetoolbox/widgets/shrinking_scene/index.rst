:mod:`spinetoolbox.widgets.shrinking_scene`
===========================================

.. py:module:: spinetoolbox.widgets.shrinking_scene

.. autoapi-nested-parse::

   A QGraphicsScene that can shrink sometimes.

   :author: A. Soininen (VTT)
   :date:   18.10.2019



Module Contents
---------------

.. py:class:: ShrinkingScene(horizontal_shrinking_threshold, vertical_shrinking_threshold, parent)

   Bases: :class:`PySide2.QtWidgets.QGraphicsScene`

   A QGraphicsScene class that can shrinks its scene rectangle.

   Shrinking can be triggered by shrink_if_needed(). It is controlled by two threshold values
   which control how far the items need to be from the scene rectangle's edges
   to trigger the shrinking.

   :param horizontal_shrinking_threshold: horizontal threshold before the scene is shrank
   :type horizontal_shrinking_threshold: float
   :param vertical_shrinking_threshold: vertical threshold before the scene is shrank
   :type vertical_shrinking_threshold: float
   :param parent: a parent
   :type parent: QObject

   .. attribute:: item_move_finished
      

      Emitted when an item has finished moving.


   .. method:: shrink_if_needed(self)


      Shrinks the scene rectangle if it is considerably larger than the area occupied by items.



