:mod:`spinetoolbox.graphics_items`
==================================

.. py:module:: spinetoolbox.graphics_items

.. autoapi-nested-parse::

   Classes for drawing graphics items on QGraphicsScene.

   :authors: M. Marin (KTH), P. Savolainen (VTT)
   :date:   4.4.2018



Module Contents
---------------

.. py:class:: ConnectorButton(parent, toolbox, position='left')

   Bases: :class:`PySide2.QtWidgets.QGraphicsRectItem`

   Connector button graphics item. Used for Link drawing between project items.

   :param parent: Project item bg rectangle
   :type parent: QGraphicsItem
   :param toolbox: QMainWindow instance
   :type toolbox: ToolBoxUI
   :param position: Either "top", "left", "bottom", or "right"
   :type position: str

   .. attribute:: brush
      

      

   .. attribute:: hover_brush
      

      

   .. method:: outgoing_links(self)



   .. method:: incoming_links(self)



   .. method:: parent_name(self)


      Returns project item name owning this connector button.


   .. method:: mousePressEvent(self, event)


      Connector button mouse press event. Starts drawing a link.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: mouseDoubleClickEvent(self, event)


      Connector button mouse double click event. Makes sure the LinkDrawer is hidden.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: hoverEnterEvent(self, event)


      Sets a darker shade to connector button when mouse enters its boundaries.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: hoverLeaveEvent(self, event)


      Restore original brush when mouse leaves connector button boundaries.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent



.. py:class:: ExclamationIcon(parent)

   Bases: :class:`PySide2.QtSvg.QGraphicsSvgItem`

   Exclamation icon graphics item.
   Used to notify that a ProjectItem is missing some configuration.

   :param parent: the parent item
   :type parent: ProjectItemIcon

   .. method:: clear_notifications(self)


      Clear all notifications.


   .. method:: add_notification(self, text)


      Add a notification.


   .. method:: hoverEnterEvent(self, event)


      Shows notifications as tool tip.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: hoverLeaveEvent(self, event)


      Hides tool tip.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent



.. py:class:: NotificationListItem

   Bases: :class:`PySide2.QtWidgets.QGraphicsTextItem`

   Notification list graphics item.
   Used to show notifications for a ProjectItem

   .. method:: setHtml(self, html)




.. py:class:: RankIcon(parent)

   Bases: :class:`PySide2.QtWidgets.QGraphicsTextItem`

   Rank icon graphics item.
   Used to show the rank of a ProjectItem within its DAG

   :param parent: the parent item
   :type parent: ProjectItemIcon

   .. method:: set_rank(self, rank)




.. py:class:: ProjectItemIcon(toolbox, x, y, w, h, project_item, icon_file, icon_color, background_color)

   Bases: :class:`PySide2.QtWidgets.QGraphicsRectItem`

   Base class for project item icons drawn in Design View.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolBoxUI
   :param x: Icon x coordinate
   :type x: float
   :param y: Icon y coordinate
   :type y: float
   :param w: Icon width
   :type w: float
   :param h: Icon height
   :type h: float
   :param project_item: Item
   :type project_item: ProjectItem
   :param icon_file: Path to icon resource
   :type icon_file: str
   :param icon_color: Icon's color
   :type icon_color: QColor
   :param background_color: Background color
   :type background_color: QColor

   .. method:: _setup(self, brush, svg, svg_color)


      Setup item's attributes.

      :param brush: Used in filling the background rectangle
      :type brush: QBrush
      :param svg: Path to SVG icon file
      :type svg: str
      :param svg_color: Color of SVG icon
      :type svg_color: QColor


   .. method:: name(self)


      Returns name of the item that is represented by this icon.


   .. method:: update_name_item(self, new_name)


      Set a new text to name item. Used when a project item is renamed.


   .. method:: set_name_attributes(self)


      Set name QGraphicsSimpleTextItem attributes (font, size, position, etc.)


   .. method:: conn_button(self, position='left')


      Returns items connector button (QWidget).


   .. method:: outgoing_links(self)



   .. method:: incoming_links(self)



   .. method:: hoverEnterEvent(self, event)


      Sets a drop shadow effect to icon when mouse enters its boundaries.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: hoverLeaveEvent(self, event)


      Disables the drop shadow when mouse leaves icon boundaries.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: mouseMoveEvent(self, event)


      Moves icon(s) while the mouse button is pressed.
      Update links that are connected to selected icons.

      :param event: Event
      :type event: QGraphicsSceneMouseEvent


   .. method:: mouseReleaseEvent(self, event)



   .. method:: contextMenuEvent(self, event)


      Show item context menu.

      :param event: Mouse event
      :type event: QGraphicsSceneMouseEvent


   .. method:: keyPressEvent(self, event)


      Handles deleting and rotating the selected
      item when dedicated keys are pressed.

      :param event: Key event
      :type event: QKeyEvent


   .. method:: itemChange(self, change, value)


      Reacts to item removal and position changes.

      In particular, destroys the drop shadow effect when the items is removed from a scene
      and keeps track of item's movements on the scene.

      :param change: a flag signalling the type of the change
      :type change: GraphicsItemChange
      :param value: a value related to the change

      :returns: Whatever super() does with the value parameter


   .. method:: show_item_info(self)


      Update GUI to show the details of the selected item.



.. py:class:: LinkBase(toolbox)

   Bases: :class:`PySide2.QtWidgets.QGraphicsPathItem`

   Base class for Link and LinkDrawer.

   Mainly provides the `update_geometry` method for 'drawing' the link on the scene.

   Initializes the instance.

   :param toolbox: main UI class instance
   :type toolbox: ToolboxUI

   .. method:: src_rect(self)
      :property:


      Returns the scene rectangle of the source connector.


   .. method:: src_center(self)
      :property:


      Returns the center point of the source rectangle.


   .. method:: dst_rect(self)
      :property:


      Returns the scene rectangle of the destination connector.


   .. method:: dst_center(self)
      :property:


      Returns the center point of the destination rectangle.


   .. method:: update_geometry(self)


      Updates geometry.


   .. method:: do_update_geometry(self, curved_links)


      Sets the path for this item.

      :param curved_links: Whether the path should follow a curvy line or a straight line
      :type curved_links: bool


   .. method:: _make_ellipse_path(self)


      Returns an ellipse path for the link's base.

      :returns: QPainterPath


   .. method:: _get_src_offset(self)



   .. method:: _get_dst_offset(self, c1)



   .. method:: _make_guide_path(self, curved_links)


      Returns a 'narrow' path connecting this item's source and destination.

      :param curved_links: Whether the path should follow a curved line or just a straight line
      :type curved_links: bool

      :returns: QPainterPath


   .. method:: _points_and_angles_from_path(self, path)


      Returns a list of representative points and angles from given path.

      :param path:
      :type path: QPainterPath

      :returns: points
                list(float): angles
      :rtype: list(QPointF)


   .. method:: _make_connecting_path(self, guide_path)


      Returns a 'thick' path connecting source and destination, by following the given 'guide' path.

      :param guide_path:
      :type guide_path: QPainterPath

      :returns: QPainterPath


   .. method:: _follow_points(curve_path, points)
      :staticmethod:



   .. method:: _radius_from_point_and_angle(self, point, angle)



   .. method:: _make_arrow_path(self, guide_path)


      Returns an arrow path for the link's tip.

      :param guide_path: A narrow path connecting source and destination,
                         used to determine the arrow orientation.
      :type guide_path: QPainterPath

      :returns: QPainterPath


   .. method:: _get_joint_line(self, guide_path)



   .. method:: _get_joint_angle(self, guide_path)




.. py:class:: Link(toolbox, src_connector, dst_connector)

   Bases: :class:`spinetoolbox.graphics_items.LinkBase`

   A graphics item to represent the connection between two project items.

   :param toolbox: main UI class instance
   :type toolbox: ToolboxUI
   :param src_connector: Source connector button
   :type src_connector: ConnectorButton
   :param dst_connector: Destination connector button
   :type dst_connector: ConnectorButton

   .. method:: make_execution_animation(self)


      Returns an animation to play when execution 'passes' through this link.

      :returns: QVariantAnimation


   .. method:: _handle_execution_animation_value_changed(self, step)



   .. method:: has_parallel_link(self)


      Returns whether or not this link entirely overlaps another.


   .. method:: send_to_bottom(self)


      Stacks this link before the parallel one if any.


   .. method:: mousePressEvent(self, e)


      Ignores event if there's a connector button underneath,
      to allow creation of new links.

      :param e: Mouse event
      :type e: QGraphicsSceneMouseEvent


   .. method:: mouseDoubleClickEvent(self, e)


      Accepts event if there's a connector button underneath,
      to prevent unwanted creation of feedback links.


   .. method:: contextMenuEvent(self, e)


      Selects the link and shows context menu.

      :param e: Mouse event
      :type e: QGraphicsSceneMouseEvent


   .. method:: keyPressEvent(self, event)


      Removes this link if delete is pressed.


   .. method:: paint(self, painter, option, widget)


      Sets a dashed pen if selected.


   .. method:: itemChange(self, change, value)


      Brings selected link to top.


   .. method:: wipe_out(self)


      Removes any trace of this item from the system.



.. py:class:: LinkDrawer(toolbox)

   Bases: :class:`spinetoolbox.graphics_items.LinkBase`

   An item for drawing links between project items.

   :param toolbox: main UI class instance
   :type toolbox: ToolboxUI

   .. method:: start_drawing_at(self, src_connector)


      Starts drawing a link from the given connector.

      :param src_connector:
      :type src_connector: ConnectorButton


   .. method:: dst_connector(self)
      :property:



   .. method:: dst_rect(self)
      :property:



   .. method:: dst_center(self)
      :property:




