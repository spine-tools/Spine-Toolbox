:mod:`spinetoolbox.mvcmodels.minimal_tree_model`
================================================

.. py:module:: spinetoolbox.mvcmodels.minimal_tree_model

.. autoapi-nested-parse::

   Models to represent items in a tree.

   :authors: P. Vennström (VTT), M. Marin (KTH)
   :date:   11.3.2019



Module Contents
---------------

.. py:class:: TreeItem(model=None)

   A tree item that can fetch its children.

   Initializes item.

   :param model: The model where the item belongs.
   :type model: MinimalTreeModel, NoneType

   .. method:: model(self)
      :property:



   .. method:: child_item_type(self)
      :property:


      Returns the type of child items. Reimplement in subclasses to return something more meaningfull.


   .. method:: children(self)
      :property:



   .. method:: parent_item(self)
      :property:



   .. method:: child(self, row)


      Returns the child at given row or None if out of bounds.


   .. method:: last_child(self)


      Returns the last child.


   .. method:: child_count(self)


      Returns the number of children.


   .. method:: child_number(self)


      Returns the rank of this item within its parent or 0 if it's an orphan.


   .. method:: find_children(self, cond=lambda child: True)


      Returns children that meet condition expressed as a lambda function.


   .. method:: find_child(self, cond=lambda child: True)


      Returns first child that meet condition expressed as a lambda function or None.


   .. method:: next_sibling(self)


      Returns the next sibling or None if it's the last.


   .. method:: previous_sibling(self)


      Returns the previous sibling or None if it's the first.


   .. method:: index(self)



   .. method:: insert_children(self, position, *children)


      Insert new children at given position. Returns a boolean depending on how it went.

      :param position: insert new items here
      :type position: int
      :param children: insert items from this iterable
      :type children: iter


   .. method:: append_children(self, *children)


      Append children at the end.


   .. method:: remove_children(self, position, count)


      Removes count children starting from the given position.


   .. method:: clear_children(self)


      Clear children list.


   .. method:: flags(self, column)


      Enables the item and makes it selectable.


   .. method:: data(self, column, role=Qt.DisplayRole)


      Returns data for given column and role.


   .. method:: has_children(self)


      Returns whether or not this item has or could have children.


   .. method:: can_fetch_more(self)


      Returns whether or not this item can fetch more.


   .. method:: fetch_more(self)


      Fetches more children.


   .. method:: display_name(self)
      :property:




.. py:class:: MinimalTreeModel(parent=None)

   Bases: :class:`PySide2.QtCore.QAbstractItemModel`

   Base class for all tree models.

   Init class.

   :param parent:
   :type parent: DataStoreForm

   .. method:: visit_all(self, index=QModelIndex())


      Iterates all items in the model including and below the given index.
      Iterative implementation so we don't need to worry about Python recursion limits.


   .. method:: item_from_index(self, index)


      Return the item corresponding to the given index.


   .. method:: index_from_item(self, item)


      Return a model index corresponding to the given item.


   .. method:: index(self, row, column, parent=QModelIndex())


      Returns the index of the item in the model specified by the given row, column and parent index.


   .. method:: parent(self, index)


      Returns the parent of the model item with the given index.


   .. method:: columnCount(self, parent=QModelIndex())



   .. method:: rowCount(self, parent=QModelIndex())



   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the data stored under the given role for the index.


   .. method:: setData(self, index, value, role=Qt.EditRole)


      Sets data for given index and role.
      Returns True if successful; otherwise returns False.


   .. method:: flags(self, index)


      Returns the item flags for the given index.


   .. method:: hasChildren(self, parent)



   .. method:: canFetchMore(self, parent)



   .. method:: fetchMore(self, parent)




