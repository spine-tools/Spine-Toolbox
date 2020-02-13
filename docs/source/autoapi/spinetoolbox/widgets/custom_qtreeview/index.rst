:mod:`spinetoolbox.widgets.custom_qtreeview`
============================================

.. py:module:: spinetoolbox.widgets.custom_qtreeview

.. autoapi-nested-parse::

   Classes for custom QTreeView.

   :author: M. Marin (KTH)
   :date:   25.4.2018



Module Contents
---------------

.. py:class:: CopyTreeView(parent)

   Bases: :class:`PySide2.QtWidgets.QTreeView`

   Custom QTreeView class with copy support.


   Initialize the view.

   .. method:: copy(self)


      Copy current selection to clipboard in excel format.



.. py:class:: EntityTreeView(parent)

   Bases: :class:`spinetoolbox.widgets.custom_qtreeview.CopyTreeView`

   Custom QTreeView class for object tree in DataStoreForm.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the view.

   .. attribute:: edit_key_pressed
      

      

   .. method:: edit(self, index, trigger, event)


      Send signal instead of editing item, so
      DataStoreForm can catch this signal and open a custom QDialog
      for edition.



.. py:class:: StickySelectionEntityTreeView

   Bases: :class:`spinetoolbox.widgets.custom_qtreeview.EntityTreeView`

   Custom QTreeView class for object tree in DataStoreForm.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   .. method:: mousePressEvent(self, event)


      Overrides selection behaviour if the user has selected sticky
      selection in Settings. If sticky selection is enabled, multi-selection is
      enabled when selecting items in the Object tree. Pressing the Ctrl-button down,
      enables single selection. If sticky selection is disabled, single selection is
      enabled and pressing the Ctrl-button down enables multi-selection.

      :param event:
      :type event: QMouseEvent



.. py:class:: ReferencesTreeView(parent)

   Bases: :class:`PySide2.QtWidgets.QTreeView`

   Custom QTreeView class for 'References' in Data Connection properties.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the view.

   .. attribute:: files_dropped
      

      

   .. attribute:: del_key_pressed
      

      

   .. method:: dragEnterEvent(self, event)


      Accept file drops from the filesystem.


   .. method:: dragMoveEvent(self, event)


      Accept event.


   .. method:: dropEvent(self, event)


      Emit files_dropped signal with a list of files for each dropped url.


   .. method:: keyPressEvent(self, event)


      Overridden method to make the view support deleting items with a delete key.



.. py:class:: DataTreeView(parent)

   Bases: :class:`PySide2.QtWidgets.QTreeView`

   Custom QTreeView class for 'Data' in Data Connection properties.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the view.

   .. attribute:: files_dropped
      

      

   .. attribute:: del_key_pressed
      

      

   .. method:: dragEnterEvent(self, event)


      Accept file drops from the filesystem.


   .. method:: dragMoveEvent(self, event)


      Accept event.


   .. method:: dropEvent(self, event)


      Emit files_dropped signal with a list of files for each dropped url.


   .. method:: mousePressEvent(self, event)


      Register drag start position.


   .. method:: mouseMoveEvent(self, event)


      Start dragging action if needed.


   .. method:: mouseReleaseEvent(self, event)


      Forget drag start position


   .. method:: keyPressEvent(self, event)


      Overridden method to make the view support deleting items with a delete key.



.. py:class:: SourcesTreeView(parent)

   Bases: :class:`PySide2.QtWidgets.QTreeView`

   Custom QTreeView class for 'Sources' in Tool specification editor widget.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the view.

   .. attribute:: files_dropped
      

      

   .. attribute:: del_key_pressed
      

      

   .. method:: dragEnterEvent(self, event)


      Accept file and folder drops from the filesystem.


   .. method:: dragMoveEvent(self, event)


      Accept event.


   .. method:: dropEvent(self, event)


      Emit files_dropped signal with a list of files for each dropped url.


   .. method:: keyPressEvent(self, event)


      Overridden method to make the view support deleting items with a delete key.



.. py:class:: CustomTreeView(parent)

   Bases: :class:`PySide2.QtWidgets.QTreeView`

   Custom QTreeView class for Tool specification editor form to enable keyPressEvent.

   .. attribute:: parent

      The parent of this view

      :type: QWidget

   Initialize the view.

   .. attribute:: del_key_pressed
      

      

   .. method:: keyPressEvent(self, event)


      Overridden method to make the view support deleting items with a delete key.



