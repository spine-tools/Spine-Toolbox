:mod:`spinetoolbox.mvcmodels.project_item_model`
================================================

.. py:module:: spinetoolbox.mvcmodels.project_item_model

.. autoapi-nested-parse::

   Contains a class for storing project items.

   :authors: P. Savolainen (VTT)
   :date:   23.1.2018



Module Contents
---------------

.. py:class:: ProjectItemModel(toolbox, root)

   Bases: :class:`PySide2.QtCore.QAbstractItemModel`

   Class to store project tree items and ultimately project items in a tree structure.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param root: Root item for the project item tree
   :type root: RootProjectTreeItem

   .. method:: root(self)


      Returns the root item.


   .. method:: rowCount(self, parent=QModelIndex())


      Reimplemented rowCount method.

      :param parent: Index of parent item whose children are counted.
      :type parent: QModelIndex

      :returns: Number of children of given parent
      :rtype: int


   .. method:: columnCount(self, parent=QModelIndex())


      Returns model column count which is always 1.


   .. method:: flags(self, index)


      Returns flags for the item at given index

      :param index: Flags of item at this index.
      :type index: QModelIndex


   .. method:: parent(self, index=QModelIndex())


      Returns index of the parent of given index.

      :param index: Index of item whose parent is returned
      :type index: QModelIndex

      :returns: Index of parent item
      :rtype: QModelIndex


   .. method:: index(self, row, column, parent=QModelIndex())


      Returns index of item with given row, column, and parent.

      :param row: Item row
      :type row: int
      :param column: Item column
      :type column: int
      :param parent: Parent item index
      :type parent: QModelIndex

      :returns: Item index
      :rtype: QModelIndex


   .. method:: data(self, index, role=None)


      Returns data in the given index according to requested role.

      :param index: Index to query
      :type index: QModelIndex
      :param role: Role to return
      :type role: int

      :returns: Data depending on role.
      :rtype: object


   .. method:: item(self, index)


      Returns item at given index.

      :param index: Index of item
      :type index: QModelIndex

      :returns:

                Item at given index or root project
                    item if index is not valid
      :rtype: RootProjectTreeItem, CategoryProjectTreeItem or LeafProjectTreeItem


   .. method:: find_category(self, category_name)


      Returns the index of the given category name.

      :param category_name: Name of category item to find
      :type category_name: str

      :returns: index of a category item or None if it was not found
      :rtype: QModelIndex


   .. method:: find_item(self, name)


      Returns the QModelIndex of the leaf item with the given name

      :param name: The searched project item (long) name
      :type name: str

      :returns: Index of a project item with the given name or None if not found
      :rtype: QModelIndex


   .. method:: get_item(self, name)


      Returns leaf item with given name or None if it doesn't exist.

      :param name: Project item name
      :type name: str

      :returns: LeafProjectTreeItem, NoneType


   .. method:: category_of_item(self, name)


      Returns the category item of the category that contains project item with given name

      :param name: Project item name
      :type name: str

      :returns: category item or None if the category was not found


   .. method:: insert_item(self, item, parent=QModelIndex())


      Adds a new item to model. Fails if given parent is not
      a category item nor a leaf item. New item is inserted as
      the last item of its branch.

      :param item: Project item to add to model
      :type item: CategoryProjectTreeItem or LeafProjectTreeItem
      :param parent: Parent project item
      :type parent: QModelIndex

      :returns: True if successful, False otherwise
      :rtype: bool


   .. method:: remove_item(self, item, parent=QModelIndex())


      Removes item from model.

      :param item: Project item to remove
      :type item: BaseProjectTreeItem
      :param parent: Parent of item that is to be removed
      :type parent: QModelIndex

      :returns: True if item removed successfully, False if item removing failed
      :rtype: bool


   .. method:: setData(self, index, value, role=Qt.EditRole)


      Changes the name of the leaf item at given index to given value.

      :param index: Tree item index
      :type index: QModelIndex
      :param value: New project item name
      :type value: str
      :param role: Item data role to set
      :type role: int

      :returns: True or False depending on whether the new name is acceptable and renaming succeeds
      :rtype: bool


   .. method:: items(self, category_name=None)


      Returns a list of leaf items in model according to category name. If no category name given,
      returns all leaf items in a list.

      :param category_name: Item category. Data Connections, Data Stores, Importers, Exporters, Tools or Views
                            permitted.
      :type category_name: str

      :returns: obj:'list' of :obj:'LeafProjectTreeItem': Depending on category_name argument, returns all items or only
                items according to category. An empty list is returned if there are no items in the given category
                or if an unknown category name was given.


   .. method:: n_items(self)


      Returns the number of all items in the model excluding category items and root.

      :returns: Number of items
      :rtype: int


   .. method:: item_names(self)


      Returns all leaf item names in a list.

      :returns: 'list' of obj:'str': Item names
      :rtype: obj


   .. method:: short_name_reserved(self, short_name)


      Checks if the directory name derived from the name of the given item is in use.

      :param short_name: Item short name
      :type short_name: str

      :returns: True if short name is taken, False if it is available.
      :rtype: bool



