:mod:`spinetoolbox.widgets.custom_menus`
========================================

.. py:module:: spinetoolbox.widgets.custom_menus

.. autoapi-nested-parse::

   Classes for custom context menus and pop-up menus.

   :author: P. Savolainen (VTT)
   :date:   9.1.2018



Module Contents
---------------

.. py:class:: CustomContextMenu(parent, position)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   Context menu master class for several context menus.

   :param parent: Parent for menu widget (ToolboxUI)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint

   Constructor.

   .. method:: add_action(self, text, icon=QIcon(), enabled=True)


      Adds an action to the context menu.

      :param text: Text description of the action
      :type text: str
      :param icon: Icon for menu item
      :type icon: QIcon
      :param enabled: Is action enabled?
      :type enabled: bool


   .. method:: set_action(self, option)


      Sets the action which was clicked.

      :param option: string with the text description of the action
      :type option: str


   .. method:: get_action(self)


      Returns the clicked action, a string with a description.



.. py:class:: CategoryProjectItemContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu for category project items in the QTreeView.

   :param parent: Parent for menu widget (ToolboxUI)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint

   Class constructor.


.. py:class:: ProjectItemModelContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu for project item model in the QTreeView.

   :param parent: Parent for menu widget (ToolboxUI)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint

   Class constructor.


.. py:class:: ProjectItemContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu for project items in the Project tree widget and in the Design View.

   :param parent: Parent for menu widget (ToolboxUI)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint


.. py:class:: LinkContextMenu(parent, position, link)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for connection links.

   :param parent: Parent for menu widget (ToolboxUI)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param link: Link that requested the menu
   :type link: Link(QGraphicsPathItem)

   Class constructor.


.. py:class:: ToolSpecificationContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for Tool specifications.

   :param parent: Parent for menu widget (ToolboxUI)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex

   Class constructor.


.. py:class:: EntityTreeContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for object tree items in tree view form.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex

   Class constructor.


.. py:class:: ObjectTreeContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.EntityTreeContextMenu`

   Context menu class for object tree items in tree view form.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex

   Class constructor.


.. py:class:: RelationshipTreeContextMenu

   Bases: :class:`spinetoolbox.widgets.custom_menus.EntityTreeContextMenu`

   Context menu class for relationship tree items in tree view form.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex


.. py:class:: ParameterContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for object (relationship) parameter items in tree views.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex

   Class constructor.


.. py:class:: SimpleEditableParameterValueContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for object (relationship) parameter value items in graph views.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex

   Class constructor.


.. py:class:: EditableParameterValueContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for object (relationship) parameter value items in tree views.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex


.. py:class:: ParameterValueListContextMenu(parent, position, index)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for parameter enum view in tree view form.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param index: Index of item that requested the context-menu
   :type index: QModelIndex

   Class constructor.


.. py:class:: GraphViewContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for qgraphics view in graph view.

   :param parent: Parent for menu widget (GraphViewForm)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint

   Class constructor.


.. py:class:: EntityItemContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Context menu class for entity graphic items in graph view.

   Class constructor.

   :param parent: Parent for menu widget (GraphViewForm)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint


.. py:class:: ObjectItemContextMenu(parent, position, graphics_item)

   Bases: :class:`spinetoolbox.widgets.custom_menus.EntityItemContextMenu`

   Class constructor.

   :param parent: Parent for menu widget (GraphViewForm)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint
   :param graphics_item: item that requested the menu
   :type graphics_item: spinetoolbox.widgets.graph_view_graphics_items.ObjectItem


.. py:class:: RelationshipItemContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.EntityItemContextMenu`

   Class constructor.

   :param parent: Parent for menu widget (GraphViewForm)
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint


.. py:class:: OpenProjectDialogComboBoxContextMenu(parent, position)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomContextMenu`

   Class constructor.

   :param parent: Parent for menu widget
   :type parent: QWidget
   :param position: Position on screen
   :type position: QPoint


.. py:class:: CustomPopupMenu(parent)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   Popup menu master class for several popup menus.

   :param parent: Parent widget of this pop-up menu
   :type parent: QWidget

   Class constructor.

   .. method:: add_action(self, text, slot, enabled=True, tooltip=None)


      Adds an action to the popup menu.

      :param text: Text description of the action
      :type text: str
      :param slot: Method to connect to action's triggered signal
      :type slot: method
      :param enabled: Is action enabled?
      :type enabled: bool
      :param tooltip: Tool tip for the action
      :type tooltip: str



.. py:class:: AddToolSpecificationPopupMenu(parent)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomPopupMenu`

   Popup menu class for add Tool specification button.

   :param parent: parent widget (ToolboxUI)
   :type parent: QWidget

   Class constructor.


.. py:class:: ToolSpecificationOptionsPopupmenu(parent, tool)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomPopupMenu`

   Popup menu class for tool specification options button in Tool item.

   :param parent: Parent widget of this menu (ToolboxUI)
   :type parent: QWidget
   :param tool: Tool item that is associated with the pressed button
   :type tool: Tool


.. py:class:: AddIncludesPopupMenu(parent)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomPopupMenu`

   Popup menu class for add includes button in Tool specification editor widget.

   :param parent: Parent widget (ToolSpecificationWidget)
   :type parent: QWidget

   Class constructor.


.. py:class:: CreateMainProgramPopupMenu(parent)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomPopupMenu`

   Popup menu class for add main program QToolButton in Tool specification editor widget.

   :param parent: Parent widget (ToolSpecificationWidget)
   :type parent: QWidget

   Class constructor.


.. py:class:: RecentProjectsPopupMenu(parent)

   Bases: :class:`spinetoolbox.widgets.custom_menus.CustomPopupMenu`

   Recent projects menu embedded to 'File-Open recent' QAction.

   :param parent: Parent widget of this menu (ToolboxUI)
   :type parent: QWidget

   .. method:: add_recent_projects(self)


      Reads the previous project names and paths from QSettings. Adds them to the QMenu as QActions.


   .. method:: call_open_project(self, checked, p)


      Slot for catching the user selected action from the recent projects menu.

      :param checked: Argument sent by triggered signal
      :type checked: bool
      :param p: Full path to a project file
      :type p: str



.. py:class:: FilterMenuBase(parent)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   Filter menu.

   :param parent:
   :type parent: QWidget

   .. method:: connect_signals(self)



   .. method:: set_filter_list(self, data)



   .. method:: add_items_to_filter_list(self, items)



   .. method:: remove_items_from_filter_list(self, items)



   .. method:: _clear_filter(self)



   .. method:: _check_filter(self)



   .. method:: _cancel_filter(self)



   .. method:: _change_filter(self)



   .. method:: emit_filter_changed(self, valid_values)
      :abstractmethod:



   .. method:: wipe_out(self)




.. py:class:: SimpleFilterMenu(parent, show_empty=True)

   Bases: :class:`spinetoolbox.widgets.custom_menus.FilterMenuBase`

   :param parent:
   :type parent: TabularViewMixin

   .. attribute:: filterChanged
      

      

   .. method:: emit_filter_changed(self, valid_values)




.. py:class:: TabularViewFilterMenu(parent, identifier, item_type, show_empty=True)

   Bases: :class:`spinetoolbox.widgets.custom_menus.FilterMenuBase`

   Filter menu to use together with FilterWidget in TabularViewMixin.

   :param parent:
   :type parent: TabularViewMixin
   :param identifier: index identifier
   :type identifier: int
   :param item_type: either "object" or "parameter definition"
   :type item_type: str

   .. attribute:: filterChanged
      

      

   .. method:: emit_filter_changed(self, valid_values)



   .. method:: event(self, event)




.. py:class:: PivotTableModelMenu(parent)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   :param parent:
   :type parent: TabularViewMixin

   .. attribute:: _DELETE_OBJECT
      :annotation: = Remove selected objects

      

   .. attribute:: _DELETE_RELATIONSHIP
      :annotation: = Remove selected relationships

      

   .. attribute:: _DELETE_PARAMETER
      :annotation: = Remove selected parameter definitions

      

   .. method:: delete_values(self)



   .. method:: delete_objects(self)



   .. method:: delete_relationships(self)



   .. method:: delete_parameters(self)



   .. method:: open_value_editor(self)


      Opens the parameter value editor for the first selected cell.


   .. method:: plot(self)


      Plots the selected cells in the pivot table.


   .. method:: request_menu(self, QPos=None)


      Shows the context menu on the screen.


   .. method:: _find_selected_indexes(self)



   .. method:: _update_actions_enable(self)



   .. method:: _update_actions_text(self)




.. py:class:: PivotTableHorizontalHeaderMenu(proxy_model, parent=None)

   Bases: :class:`PySide2.QtWidgets.QMenu`

   A context menu for the horizontal header of a pivot table.

   :param proxy_model: a proxy model
   :type proxy_model: PivotTableSortFilterProxy
   :param parent: a parent widget
   :type parent: QWidget

   .. method:: _plot_column(self)


      Plots a single column not the selection.


   .. method:: request_menu(self, pos)


      Shows the context menu on the screen.


   .. method:: _set_x_flag(self)


      Sets the X flag for a column.



