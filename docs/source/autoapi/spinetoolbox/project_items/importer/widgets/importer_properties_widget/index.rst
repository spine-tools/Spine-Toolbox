:mod:`spinetoolbox.project_items.importer.widgets.importer_properties_widget`
=============================================================================

.. py:module:: spinetoolbox.project_items.importer.widgets.importer_properties_widget

.. autoapi-nested-parse::

   Importer properties widget.

   :author: M. Marin (KTH)
   :date:   12.9.2019



Module Contents
---------------

.. py:class:: ImporterPropertiesWidget(toolbox)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Widget for the Importer Item Properties.

   :param toolbox: The toolbox instance where this widget should be embedded
   :type toolbox: ToolboxUI

   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: show_files_context_menu(self, pos)


      Create and show a context-menu in Importer properties source files view.

      :param pos: Mouse position
      :type pos: QPoint



