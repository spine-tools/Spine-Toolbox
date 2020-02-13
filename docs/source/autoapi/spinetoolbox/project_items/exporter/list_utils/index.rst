:mod:`spinetoolbox.project_items.exporter.list_utils`
=====================================================

.. py:module:: spinetoolbox.project_items.exporter.list_utils

.. autoapi-nested-parse::

   Contains list helper functions for list manipulation.

   :author: A. Soininen (VTT)
   :date:   12.12.2019



Module Contents
---------------

.. function:: move_list_elements(originals, first, last, target)

   Moves elements in a list.

   :param originals: a list
   :type originals: list
   :param first: index of the first element to move
   :type first: int
   :param last: index of the last element to move
   :type last: int
   :param target: index where the elements `[first:last]` should be inserted
   :type target: int

   :returns: a new list with the elements moved


