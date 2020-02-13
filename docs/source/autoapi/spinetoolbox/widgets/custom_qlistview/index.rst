:mod:`spinetoolbox.widgets.custom_qlistview`
============================================

.. py:module:: spinetoolbox.widgets.custom_qlistview

.. autoapi-nested-parse::

   Classes for custom QListView.

   :author: M. Marin (KTH)
   :date:   14.11.2018



Module Contents
---------------

.. py:class:: AutoFilterMenuView(parent)

   Bases: :class:`PySide2.QtWidgets.QListView`

   Initialize class.

   .. method:: keyPressEvent(self, event)


      Toggle checked state of current index if the user presses the Space key.


   .. method:: leaveEvent(self, event)


      Clear selection.


   .. method:: _handle_entered(self, index)


      Highlight current row.


   .. method:: _handle_clicked(self, index)


      Toggle checked state of clicked index.



.. py:class:: DragListView(parent)

   Bases: :class:`PySide2.QtWidgets.QListView`

   Custom QListView class with dragging support.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the view.

   .. method:: mousePressEvent(self, event)


      Register drag start position


   .. method:: mouseMoveEvent(self, event)


      Start dragging action if needed


   .. method:: mouseReleaseEvent(self, event)


      Forget drag start position



