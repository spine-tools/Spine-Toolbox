:mod:`spinetoolbox.widgets.tabular_view_header_widget`
======================================================

.. py:module:: spinetoolbox.widgets.tabular_view_header_widget

.. autoapi-nested-parse::

   Contains TabularViewHeaderWidget class.

   :authors: P. Vennström (VTT), M. Marin (KTH)
   :date:   2.12.2019



Module Contents
---------------

.. py:class:: TabularViewHeaderWidget(identifier, name, area, menu=None, parent=None)

   Bases: :class:`PySide2.QtWidgets.QFrame`

   A draggable QWidget.

   :param identifier:
   :type identifier: int
   :param name:
   :type name: str
   :param area: either "rows", "columns", or "frozen"
   :type area: str
   :param menu:
   :type menu: FilterMenu, optional
   :param parent: Parent widget
   :type parent: QWidget, optional

   .. attribute:: header_dropped
      

      

   .. attribute:: _H_MARGIN
      :annotation: = 3

      

   .. attribute:: _SPACING
      :annotation: = 16

      

   .. method:: identifier(self)
      :property:



   .. method:: area(self)
      :property:



   .. method:: mousePressEvent(self, event)


      Register drag start position


   .. method:: mouseMoveEvent(self, event)


      Start dragging action if needed


   .. method:: mouseReleaseEvent(self, event)


      Forget drag start position


   .. method:: dragEnterEvent(self, event)



   .. method:: dropEvent(self, event)




