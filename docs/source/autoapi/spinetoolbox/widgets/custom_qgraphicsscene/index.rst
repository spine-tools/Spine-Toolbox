:mod:`spinetoolbox.widgets.custom_qgraphicsscene`
=================================================

.. py:module:: spinetoolbox.widgets.custom_qgraphicsscene

.. autoapi-nested-parse::

   Custom QGraphicsScene used in the Design View.

   :author: P. Savolainen (VTT)
   :date:   13.2.2019



Module Contents
---------------

.. py:class:: CustomQGraphicsScene(parent, toolbox)

   Bases: :class:`spinetoolbox.widgets.shrinking_scene.ShrinkingScene`

   A scene that handles drag and drop events of DraggableWidget sources.

   :param parent: scene's parent object
   :type parent: QObject
   :param toolbox: reference to the main window
   :type toolbox: ToolboxUI

   .. method:: connect_signals(self)


      Connect scene signals.


   .. method:: resize_scene(self)


      Resize scene to be at least the size of items bounding rectangle.
      Does not let the scene shrink.


   .. method:: scene_changed(self, rects)


      Resize scene as it changes.


   .. method:: handle_selection_changed(self)


      Synchronize selection with the project tree.


   .. method:: set_bg_color(self, color)


      Change background color when this is changed in Settings.

      :param color: Background color
      :type color: QColor


   .. method:: set_bg_grid(self, bg)


      Enable or disable background grid.

      :param bg: True to draw grid, False to fill background with a solid color
      :type bg: boolean


   .. method:: dragLeaveEvent(self, event)


      Accept event.


   .. method:: dragEnterEvent(self, event)


      Accept event. Then call the super class method
      only if drag source is not a DraggableWidget (from Add Item toolbar).


   .. method:: dragMoveEvent(self, event)


      Accept event. Then call the super class method
      only if drag source is not a DraggableWidget (from Add Item toolbar).


   .. method:: dropEvent(self, event)


      Only accept drops when the source is an instance of
      DraggableWidget (from Add Item toolbar).
      Capture text from event's mimedata and show the appropriate 'Add Item form.'


   .. method:: drawBackground(self, painter, rect)


      Reimplemented method to make a custom background.

      :param painter: Painter that is used to paint background
      :type painter: QPainter
      :param rect: The exposed (viewport) rectangle in scene coordinates
      :type rect: QRectF



