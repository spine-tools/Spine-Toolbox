:mod:`spinetoolbox.widgets.custom_qtextbrowser`
===============================================

.. py:module:: spinetoolbox.widgets.custom_qtextbrowser

.. autoapi-nested-parse::

   Class for a custom QTextBrowser for showing the logs and tool output.

   :author: P. Savolainen (VTT)
   :date:   6.2.2018



Module Contents
---------------

.. py:class:: CustomQTextBrowser(parent)

   Bases: :class:`PySide2.QtWidgets.QTextBrowser`

   Custom QTextBrowser class.

   .. attribute:: parent

      Parent widget

      :type: QWidget

   .. method:: append(self, text)


      Appends new text block to the end of the current contents.

      If the widget contains more text blocks after the addition than a set limit,
      blocks will be deleted at the start of the contents.

      :param text: text to add
      :type text: str


   .. method:: contextMenuEvent(self, event)


      Reimplemented method to add a clear action into the default context menu.

      :param event: Received event
      :type event: QContextMenuEvent


   .. method:: max_blocks(self)
      :property:


      Returns the upper limit of text blocks that can be appended to the widget.



