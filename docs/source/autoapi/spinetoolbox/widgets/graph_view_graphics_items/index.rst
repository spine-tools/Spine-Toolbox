:mod:`spinetoolbox.widgets.graph_view_graphics_items`
=====================================================

.. py:module:: spinetoolbox.widgets.graph_view_graphics_items

.. autoapi-nested-parse::

   Classes for drawing graphics items on graph view's QGraphicsScene.

   :authors: M. Marin (KTH), P. Savolainen (VTT)
   :date:   4.4.2018



Module Contents
---------------

.. py:class:: EntityItem(graph_view_form, x, y, extent, entity_id=None, entity_class_id=None)

   Bases: :class:`PySide2.QtWidgets.QGraphicsPixmapItem`

   Initializes item

   :param graph_view_form: 'owner'
   :type graph_view_form: GraphViewForm
   :param x: x-coordinate of central point
   :type x: float
   :param y: y-coordinate of central point
   :type y: float
   :param extent: Preferred extent
   :type extent: int
   :param entity_id: The entity id in case of a non-wip item
   :type entity_id: int, optional
   :param entity_class_id: The entity class id in case of a wip item
   :type entity_class_id: int, optional

   .. method:: entity_type(self)
      :property:



   .. method:: entity_name(self)
      :property:



   .. method:: entity_class_type(self)
      :property:



   .. method:: entity_class_id(self)
      :property:



   .. method:: entity_class_name(self)
      :property:



   .. method:: boundingRect(self)



   .. method:: _init_bg(self)



   .. method:: refresh_icon(self)


      Refreshes the icon.


   .. method:: shape(self)


      Returns a shape containing the entire bounding rect, to work better with icon transparency.


   .. method:: paint(self, painter, option, widget=None)


      Shows or hides the selection halo.


   .. method:: _paint_as_selected(self)



   .. method:: _paint_as_deselected(self)



   .. method:: add_arc_item(self, arc_item)


      Adds an item to the list of arcs.

      :param arc_item:
      :type arc_item: ArcItem


   .. method:: become_wip(self)


      Turns this item into a work-in-progress.


   .. method:: _make_wip_tool_tip(self)
      :abstractmethod:



   .. method:: become_whole(self)


      Removes the wip status from this item.


   .. method:: adjust_to_zoom(self, transform)


      Saves the view's transform to determine collisions later on.

      :param transform: The view's transformation matrix after the zoom.
      :type transform: QTransform


   .. method:: device_rect(self)


      Returns the item's rect in devices's coordinates.
      Used to accurately determine collisions.


   .. method:: _find_merge_target(self)


      Returns a suitable merge target if any.

      :returns: spinetoolbox.widgets.graph_view_graphics_items.EntityItem, NoneType


   .. method:: _is_target_valid(self)


      Whether or not the registered merge target is valid.

      :returns: bool


   .. method:: merge_into_target(self, force=False)


      Merges this item into the registered target if valid.

      :returns: True if merged, False if not.
      :rtype: bool


   .. method:: mousePressEvent(self, event)


      Saves original position for bouncing purposes.

      :param event:
      :type event: QGraphicsSceneMouseEvent


   .. method:: mouseMoveEvent(self, event)


      Moves the item and all connected arcs. Also checks for a merge target
      and sets an appropriate mouse cursor.

      :param event:
      :type event: QGraphicsSceneMouseEvent


   .. method:: move_arc_items(self, pos_diff)
      :abstractmethod:


      Moves arc items.

      :param pos_diff:
      :type pos_diff: QPoint


   .. method:: mouseReleaseEvent(self, event)


      Merges the item into the registered target if any. Bounces it if not possible.
      Shrinks the scene if needed.

      :param event:
      :type event: QGraphicsSceneMouseEvent


   .. method:: _bounce_back(self, current_pos)


      Bounces the item back from given position to its original position.

      :param current_pos:
      :type current_pos: QPoint


   .. method:: itemChange(self, change, value)


      Keeps track of item's movements on the scene.

      :param change: a flag signalling the type of the change
      :type change: GraphicsItemChange
      :param value: a value related to the change

      :returns: the same value given as input


   .. method:: set_all_visible(self, on)


      Sets visibility status for this item and all arc items.

      :param on:
      :type on: bool


   .. method:: wipe_out(self)


      Removes this item and all its arc items from the scene.


   .. method:: contextMenuEvent(self, e)


      Shows context menu.

      :param e: Mouse event
      :type e: QGraphicsSceneMouseEvent


   .. method:: _show_item_context_menu_in_parent(self, pos)
      :abstractmethod:




.. py:class:: RelationshipItem

   Bases: :class:`spinetoolbox.widgets.graph_view_graphics_items.EntityItem`

   Relationship item to use with GraphViewForm.

   .. method:: entity_type(self)
      :property:



   .. method:: object_class_id_list(self)
      :property:



   .. method:: object_name_list(self)
      :property:



   .. method:: object_id_list(self)
      :property:



   .. method:: db_representation(self)
      :property:



   .. method:: _init_bg(self)



   .. method:: validate_member_objects(self)


      Goes through connected object items and tries to complete the relationship.


   .. method:: move_arc_items(self, pos_diff)


      Moves arc items.

      :param pos_diff:
      :type pos_diff: QPoint


   .. method:: _make_wip_tool_tip(self)



   .. method:: become_whole(self)



   .. method:: _show_item_context_menu_in_parent(self, pos)




.. py:class:: ObjectItem(graph_view_form, x, y, extent, entity_id=None, entity_class_id=None)

   Bases: :class:`spinetoolbox.widgets.graph_view_graphics_items.EntityItem`

   Initializes the item.

   :param graph_view_form: 'owner'
   :type graph_view_form: GraphViewForm
   :param x: x-coordinate of central point
   :type x: float
   :param y: y-coordinate of central point
   :type y: float
   :param extent: preferred extent
   :type extent: int
   :param entity_id: object id, if not given the item becomes a template
   :type entity_id: int, optional
   :param entity_class_id: object class id, for template items
   :type entity_class_id: int, optional

   :raises ValueError: in case object_id and object_class_id are both not provided

   .. method:: entity_type(self)
      :property:



   .. method:: db_representation(self)
      :property:



   .. method:: refresh_name(self)


      Refreshes the name.


   .. method:: _paint_as_selected(self)



   .. method:: _make_wip_tool_tip(self)



   .. method:: edit_name(self)


      Starts editing the object name.


   .. method:: finish_name_editing(self, text)


      Runs when the user finishes editing the name.
      Adds or updates the object in the database.

      :param text: The new name.
      :type text: str


   .. method:: move_arc_items(self, pos_diff)


      Moves arc items.

      :param pos_diff:
      :type pos_diff: QPoint


   .. method:: keyPressEvent(self, event)


      Starts editing the name if F2 is pressed.

      :param event:
      :type event: QKeyEvent


   .. method:: mouseDoubleClickEvent(self, event)


      Starts editing the name.

      :param event:
      :type event: QGraphicsSceneMouseEvent


   .. method:: _is_in_wip_relationship(self)



   .. method:: _is_target_valid(self)


      Whether or not the registered merge target is valid.

      :returns: bool


   .. method:: merge_into_target(self, force=False)


      Merges this item into the registered target if valid.

      :param force:
      :type force: bool

      :returns: True if merged, False if not.
      :rtype: bool


   .. method:: _show_item_context_menu_in_parent(self, pos)




.. py:class:: EntityLabelItem(entity_item)

   Bases: :class:`PySide2.QtWidgets.QGraphicsTextItem`

   Label item for items in GraphViewForm.

   Initializes item.

   :param entity_item: The parent item.
   :type entity_item: spinetoolbox.widgets.graph_view_graphics_items.EntityItem

   .. attribute:: entity_name_edited
      

      

   .. method:: setPlainText(self, text)


      Set texts and resets position.

      :param text:
      :type text: str


   .. method:: reset_position(self)


      Adapts item geometry so text is always centered.


   .. method:: set_bg_color(self, bg_color)


      Sets background color.

      :param bg_color:
      :type bg_color: QColor


   .. method:: start_editing(self)


      Starts editing.


   .. method:: keyPressEvent(self, event)


      Keeps text centered as the user types.
      Gives up focus when the user presses Enter or Return.

      :param event:
      :type event: QKeyEvent


   .. method:: focusOutEvent(self, event)


      Ends editing and sends entity_name_edited signal.


   .. method:: mouseDoubleClickEvent(self, event)


      Starts editing the name.

      :param event:
      :type event: QGraphicsSceneMouseEvent



.. py:class:: ArcItem(rel_item, obj_item, width, is_wip=False)

   Bases: :class:`PySide2.QtWidgets.QGraphicsLineItem`

   Arc item to use with GraphViewForm. Connects a RelationshipItem to an ObjectItem.

   Initializes item.

   :param rel_item: relationship item
   :type rel_item: spinetoolbox.widgets.graph_view_graphics_items.RelationshipItem
   :param obj_item: object item
   :type obj_item: spinetoolbox.widgets.graph_view_graphics_items.ObjectItem
   :param width: Preferred line width
   :type width: float

   .. method:: mousePressEvent(self, event)


      Accepts the event so it's not propagated.


   .. method:: other_item(self, item)



   .. method:: become_wip(self)


      Turns this arc into a work-in-progress.


   .. method:: become_whole(self)


      Removes the wip status from this arc.


   .. method:: move_rel_item_by(self, pos_diff)


      Moves source point.

      :param pos_diff:
      :type pos_diff: QPoint


   .. method:: move_obj_item_by(self, pos_diff)


      Moves destination point.

      :param pos_diff:
      :type pos_diff: QPoint


   .. method:: adjust_to_zoom(self, transform)


      Adjusts the item's geometry so it stays the same size after performing a zoom.

      :param transform: The view's transformation matrix after the zoom.
      :type transform: QTransform


   .. method:: wipe_out(self)




.. py:class:: OutlinedTextItem(text, parent, font=QFont(), brush=QBrush(Qt.white), outline_pen=QPen(Qt.black, 3, Qt.SolidLine))

   Bases: :class:`PySide2.QtWidgets.QGraphicsSimpleTextItem`

   Outlined text item.

   Initializes item.

   :param text: text to show
   :type text: str
   :param font: font to display the text
   :type font: QFont, optional
   :param brush:
   :type brush: QBrush, optional
   :param outline_pen:
   :type outline_pen: QPen, optional


