:mod:`spinetoolbox.widgets.custom_qlineedit`
============================================

.. py:module:: spinetoolbox.widgets.custom_qlineedit

.. autoapi-nested-parse::

   Classes for custom line edits.

   :author: M. Marin (KTH)
   :date:   11.10.2018



Module Contents
---------------

.. py:class:: CustomQLineEdit

   Bases: :class:`PySide2.QtWidgets.QLineEdit`

   A custom QLineEdit that accepts file drops and displays the path.

   .. attribute:: parent

      Parent for line edit widget (DataStoreWidget)

      :type: QMainWindow

   .. attribute:: file_dropped
      

      

   .. method:: dragEnterEvent(self, event)


      Accept a single file drop from the filesystem.


   .. method:: dragMoveEvent(self, event)


      Accept event.


   .. method:: dropEvent(self, event)


      Emit file_dropped signal with the file for the dropped url.



