:mod:`spinetoolbox.widgets.custom_qgraphicsviews`
=================================================

.. py:module:: spinetoolbox.widgets.custom_qgraphicsviews

.. autoapi-nested-parse::

   Classes for custom QGraphicsViews for the Design and Graph views.

   :authors: P. Savolainen (VTT), M. Marin (KTH)
   :date:   6.2.2018



Module Contents
---------------

.. py:class:: CustomQGraphicsView(parent)

   Bases: :class:`PySide2.QtWidgets.QGraphicsView`

   Super class for Design and Graph QGraphicsViews.

   .. attribute:: parent

      Parent widget

      :type: QWidget

   Init CustomQGraphicsView.

   .. method:: keyPressEvent(self, event)


      Overridden method. Enable zooming with plus and minus keys (comma resets zoom).
      Send event downstream to QGraphicsItems if pressed key is not handled here.

      :param event: Pressed key
      :type event: QKeyEvent


   .. method:: enterEvent(self, event)


      Overridden method. Do not show the stupid open hand mouse cursor.

      :param event: event
      :type event: QEvent


   .. method:: mousePressEvent(self, event)


      Set rubber band selection mode if Control pressed.
      Enable resetting the zoom factor from the middle mouse button.


   .. method:: mouseReleaseEvent(self, event)


      Reestablish scroll hand drag mode.


   .. method:: wheelEvent(self, event)


      Zoom in/out.

      :param event: Mouse wheel event
      :type event: QWheelEvent


   .. method:: resizeEvent(self, event)


      Updates zoom if needed when the view is resized.

      :param event: a resize event
      :type event: QResizeEvent


   .. method:: setScene(self, scene)


      Sets a new scene to this view.

      :param scene: a new scene
      :type scene: ShrinkingScene


   .. method:: _update_zoom_limits(self, rect)


      Updates the minimum zoom limit and the zoom level with which the entire scene fits the view.

      :param rect: the scene's rect
      :type rect: QRectF


   .. method:: scaling_time(self, pos)


      Called when animation value for smooth zoom changes. Perform zoom.


   .. method:: anim_finished(self)


      Called when animation for smooth zoom finishes. Clean up.


   .. method:: zoom_in(self)


      Perform a zoom in with a fixed scaling.


   .. method:: zoom_out(self)


      Perform a zoom out with a fixed scaling.


   .. method:: reset_zoom(self)


      Reset zoom to the default factor.


   .. method:: gentle_zoom(self, factor, zoom_focus)


      Perform a zoom by a given factor.

      :param factor: a scaling factor relative to the current scene scaling
      :type factor: float
      :param zoom_focus: focus of the zoom, e.g. mouse pointer position
      :type zoom_focus: QPoint


   .. method:: _ensure_item_visible(self, item)


      Resets zoom if item is not visible.



.. py:class:: DesignQGraphicsView(parent)

   Bases: :class:`spinetoolbox.widgets.custom_qgraphicsviews.CustomQGraphicsView`

   QGraphicsView for the Design View.

   :param parent: Graph View Form's (QMainWindow) central widget (self.centralwidget)
   :type parent: QWidget

   .. method:: mousePressEvent(self, event)


      Manage drawing of links. Handle the case where a link is being
      drawn and the user doesn't hit a connector button.

      :param event: Mouse event
      :type event: QGraphicsSceneMouseEvent


   .. method:: mouseMoveEvent(self, event)


      Update line end position.

      :param event: Mouse event
      :type event: QGraphicsSceneMouseEvent


   .. method:: set_ui(self, toolbox)


      Set a new scene into the Design View when app is started.


   .. method:: init_scene(self, empty=False)


      Resize scene and add a link drawer on scene.
      The scene must be cleared before calling this.

      :param empty: True when creating a new project
      :type empty: boolean


   .. method:: set_project_item_model(self, model)


      Set project item model.


   .. method:: remove_icon(self, icon)


      Removes icon and all connected links from scene.


   .. method:: links(self)


      Returns all Links in the scene.
      Used for saving the project.


   .. method:: add_link(self, src_connector, dst_connector)


      Draws link between source and destination connectors on scene.

      :param src_connector: Source connector button
      :type src_connector: ConnectorButton
      :param dst_connector: Destination connector button
      :type dst_connector: ConnectorButton


   .. method:: remove_link(self, link)


      Removes link from scene.


   .. method:: take_link(self, link)


      Remove link, then start drawing another one from the same source connector.


   .. method:: restore_links(self, connections)


      Creates Links from the given connections list.

      - List of dicts is accepted, e.g.

      .. code-block::

          [
              {"from": ["DC1", "right"], "to": ["Tool1", "left"]},
              ...
          ]

      :param connections: List of connections.
      :type connections: list


   .. method:: draw_links(self, connector)


      Draw links when slot button is clicked.

      :param connector: Connector button that triggered the drawing
      :type connector: ConnectorButton


   .. method:: notify_destination_items(self)


      Notify destination items that they have been connected to a source item.


   .. method:: connect_engine_signals(self, engine)


      Connects signals needed for icon animations from given engine.


   .. method:: _start_animation(self, item_name, direction)


      Starts item icon animation when executing forward.


   .. method:: _stop_animation(self, item_name, direction)


      Stops item icon animation when executing forward.



.. py:class:: GraphQGraphicsView

   Bases: :class:`spinetoolbox.widgets.custom_qgraphicsviews.CustomQGraphicsView`

   QGraphicsView for the Graph View.

   .. attribute:: item_dropped
      

      

   .. attribute:: context_menu_requested
      

      

   .. method:: dragLeaveEvent(self, event)


      Accept event. Then call the super class method
      only if drag source is not DragListView.


   .. method:: dragEnterEvent(self, event)


      Accept event. Then call the super class method
      only if drag source is not DragListView.


   .. method:: dragMoveEvent(self, event)


      Accept event. Then call the super class method
      only if drag source is not DragListView.


   .. method:: dropEvent(self, event)


      Only accept drops when the source is an instance of DragListView.
      Capture text from event's mimedata and emit signal.


   .. method:: contextMenuEvent(self, e)


      Show context menu.

      :param e: Context menu event
      :type e: QContextMenuEvent


   .. method:: gentle_zoom(self, factor, zoom_focus)


      Perform a zoom by a given factor.

      :param factor: a scaling factor relative to the current scene scaling
      :type factor: float
      :param zoom_focus: focus of the zoom, e.g. mouse pointer position
      :type zoom_focus: QPoint


   .. method:: reset_zoom(self)


      Reset zoom to the default factor.


   .. method:: init_zoom(self)


      Init zoom.


   .. method:: adjust_items_to_zoom(self)


      Update items geometry after performing a zoom.

      Some items (e.g. ArcItem) need this to stay the same size after a zoom.



