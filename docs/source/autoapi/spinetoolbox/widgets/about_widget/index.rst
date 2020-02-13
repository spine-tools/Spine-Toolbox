:mod:`spinetoolbox.widgets.about_widget`
========================================

.. py:module:: spinetoolbox.widgets.about_widget

.. autoapi-nested-parse::

   A widget for presenting basic information about the application.

   :author: P. Savolainen (VTT)
   :date: 14.12.2017



Module Contents
---------------

.. py:class:: AboutWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   About widget class.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI

   .. method:: calc_pos(self)


      Calculate the top-left corner position of this widget in relation to main window
      position and size in order to show about window in the middle of the main window.


   .. method:: setup_license_text(self)


      Add license to QTextBrowser.


   .. method:: keyPressEvent(self, e)


      Close form when Escape, Enter, Return, or Space bar keys are pressed.

      :param e: Received key press event.
      :type e: QKeyEvent


   .. method:: closeEvent(self, event=None)


      Handle close window.

      :param event: Closing event if 'X' is clicked.
      :type event: QEvent


   .. method:: mousePressEvent(self, e)


      Save mouse position at the start of dragging.

      :param e: Mouse event
      :type e: QMouseEvent


   .. method:: mouseReleaseEvent(self, e)


      Save mouse position at the end of dragging.

      :param e: Mouse event
      :type e: QMouseEvent


   .. method:: mouseMoveEvent(self, e)


      Moves the window when mouse button is pressed and mouse cursor is moved.

      :param e: Mouse event
      :type e: QMouseEvent



