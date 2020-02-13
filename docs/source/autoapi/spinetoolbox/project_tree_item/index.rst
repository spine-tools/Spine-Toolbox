:mod:`spinetoolbox.project_tree_item`
=====================================

.. py:module:: spinetoolbox.project_tree_item

.. autoapi-nested-parse::

   Project Tree items.

   :authors: A. Soininen (VTT)
   :date:   17.1.2020



Module Contents
---------------

.. py:class:: BaseProjectTreeItem(name, description)

   Bases: :class:`spinetoolbox.metaobject.MetaObject`

   Base class for all project tree items.

   :param name: Object name
   :type name: str
   :param description: Object description
   :type description: str

   .. method:: flags(self)


      Returns the item flags.


   .. method:: parent(self)


      Returns parent project tree item.


   .. method:: child_count(self)


      Returns the number of child project tree items.


   .. method:: children(self)


      Returns the children of this project tree item.


   .. method:: child(self, row)


      Returns child BaseProjectTreeItem on given row.

      :param row: Row of child to return
      :type row: int

      :returns: item on given row or None if it does not exist
      :rtype: BaseProjectTreeItem


   .. method:: row(self)


      Returns the row on which this item is located.


   .. method:: add_child(self, child_item)
      :abstractmethod:


      Base method that shall be overridden in subclasses.


   .. method:: remove_child(self, row)


      Remove the child of this BaseProjectTreeItem from given row. Do not call this method directly.
      This method is called by LeafProjectItemTreeModel when items are removed.

      :param row: Row of child to remove
      :type row: int

      :returns: True if operation succeeded, False otherwise
      :rtype: bool


   .. method:: custom_context_menu(self, parent, pos)
      :abstractmethod:


      Returns the context menu for this item. Implement in subclasses as needed.
      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param pos: Position on screen
      :type pos: QPoint


   .. method:: apply_context_menu_action(self, parent, action)
      :abstractmethod:


      Applies given action from context menu. Implement in subclasses as needed.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param action: The selected action
      :type action: str



.. py:class:: RootProjectTreeItem

   Bases: :class:`spinetoolbox.project_tree_item.BaseProjectTreeItem`

   Class for the root project tree item.

   .. method:: add_child(self, child_item)


      Adds given category item as the child of this root project tree item. New item is added as the last item.

      :param child_item: Item to add
      :type child_item: CategoryProjectTreeItem

      :returns: True for success, False otherwise


   .. method:: custom_context_menu(self, parent, pos)
      :abstractmethod:


      See base class.


   .. method:: apply_context_menu_action(self, parent, action)
      :abstractmethod:


      See base class.



.. py:class:: CategoryProjectTreeItem(name, description, item_maker, icon_maker, add_form_maker, properties_ui)

   Bases: :class:`spinetoolbox.project_tree_item.BaseProjectTreeItem`

   Class for category project tree items.

   :param name: Category name
   :type name: str
   :param description: Category description
   :type description: str
   :param item_maker: A function for creating project items in this category
   :type item_maker: function
   :param icon_maker: A function for creating icons (QGraphicsItems) for project items in this category
   :type icon_maker: function
   :param add_form_maker: A function for creating the form to add project items to this category
   :type add_form_maker: function
   :param properties_ui: An object holding the Item Properties UI
   :type properties_ui: object

   .. method:: flags(self)


      Returns the item flags.


   .. method:: item_maker(self)


      Returns the item maker method.


   .. method:: add_child(self, child_item)


      Adds given project tree item as the child of this category item. New item is added as the last item.

      :param child_item: Item to add
      :type child_item: LeafProjectTreeTreeItem
      :param toolbox: A toolbox instance
      :type toolbox: ToolboxUI

      :returns: True for success, False otherwise


   .. method:: custom_context_menu(self, parent, pos)


      Returns the context menu for this item.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param pos: Position on screen
      :type pos: QPoint


   .. method:: apply_context_menu_action(self, parent, action)


      Applies given action from context menu.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param action: The selected action
      :type action: str



.. py:class:: LeafProjectTreeItem(project_item, toolbox)

   Bases: :class:`spinetoolbox.project_tree_item.BaseProjectTreeItem`

   Class for leaf items in the project item tree.

   :param project_item: the real project item this item represents
   :type project_item: ProjectItem
   :param toolbox: a toolbox instance
   :type toolbox: ToobloxUI

   .. method:: project_item(self)
      :property:


      the project item linked to this leaf


   .. method:: toolbox(self)
      :property:


      the toolbox instance


   .. method:: add_child(self, child_item)
      :abstractmethod:


      See base class.


   .. method:: flags(self)


      Returns the item flags.


   .. method:: custom_context_menu(self, parent, pos)


      Returns the context menu for this item.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param pos: Position on screen
      :type pos: QPoint


   .. method:: apply_context_menu_action(self, parent, action)


      Applies given action from context menu.

      :param parent: The widget that is controlling the menu
      :type parent: QWidget
      :param action: The selected action
      :type action: str


   .. method:: rename(self, new_name)


      Renames this item.

      :param new_name: New name
      :type new_name: str

      :returns: True if renaming was successful, False if renaming failed
      :rtype: bool



