:mod:`spinetoolbox.mvcmodels.minimal_table_model`
=================================================

.. py:module:: spinetoolbox.mvcmodels.minimal_table_model

.. autoapi-nested-parse::

   Contains a minimal table model.

   :authors: M. Marin (KTH)
   :date:   20.5.2018



Module Contents
---------------

.. py:class:: MinimalTableModel(parent=None, header=None, lazy=True)

   Bases: :class:`PySide2.QtCore.QAbstractTableModel`

   Table model for outlining simple tabular data.

   :param parent: the parent object
   :type parent: QObject

   .. method:: clear(self)


      Clear all data in model.


   .. method:: flags(self, index)


      Return index flags.


   .. method:: canFetchMore(self, parent=None)


      Return True if the model hasn't been fetched.


   .. method:: fetchMore(self, parent=None)


      Fetch data and use it to reset the model.


   .. method:: rowCount(self, parent=QModelIndex())


      Number of rows in the model.


   .. method:: columnCount(self, parent=QModelIndex())


      Number of columns in the model.


   .. method:: headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole)


      Returns headers.


   .. method:: set_horizontal_header_labels(self, labels)


      Set horizontal header labels.


   .. method:: insert_horizontal_header_labels(self, section, labels)


      Insert horizontal header labels at the given section.


   .. method:: horizontal_header_labels(self)



   .. method:: setHeaderData(self, section, orientation, value, role=Qt.EditRole)


      Sets the data for the given role and section in the header
      with the specified orientation to the value supplied.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the data stored under the given role for the item referred to by the index.

      :param index: Index of item
      :type index: QModelIndex
      :param role: Data role
      :type role: int

      :returns: Item data for given role.


   .. method:: row_data(self, row, role=Qt.DisplayRole)


      Returns the data stored under the given role for the given row.

      :param row: Item row
      :type row: int
      :param role: Data role
      :type role: int

      :returns: Row data for given role.


   .. method:: setData(self, index, value, role=Qt.EditRole)


      Set data in model.


   .. method:: batch_set_data(self, indexes, data)


      Batch set data for indexes.


   .. method:: insertRows(self, row, count, parent=QModelIndex())


      Inserts count rows into the model before the given row.
      Items in the new row will be children of the item represented
      by the parent model index.

      :param row: Row number where new rows are inserted
      :type row: int
      :param count: Number of inserted rows
      :type count: int
      :param parent: Parent index
      :type parent: QModelIndex

      :returns: True if rows were inserted successfully, False otherwise


   .. method:: insertColumns(self, column, count, parent=QModelIndex())


      Inserts count columns into the model before the given column.
      Items in the new column will be children of the item represented
      by the parent model index.

      :param column: Column number where new columns are inserted
      :type column: int
      :param count: Number of inserted columns
      :type count: int
      :param parent: Parent index
      :type parent: QModelIndex

      :returns: True if columns were inserted successfully, False otherwise


   .. method:: removeRows(self, row, count, parent=QModelIndex())


      Removes count rows starting with the given row under parent.

      :param row: Row number where to start removing rows
      :type row: int
      :param count: Number of removed rows
      :type count: int
      :param parent: Parent index
      :type parent: QModelIndex

      :returns: True if rows were removed successfully, False otherwise


   .. method:: removeColumns(self, column, count, parent=QModelIndex())


      Removes count columns starting with the given column under parent.

      :param column: Column number where to start removing columns
      :type column: int
      :param count: Number of removed columns
      :type count: int
      :param parent: Parent index
      :type parent: QModelIndex

      :returns: True if columns were removed successfully, False otherwise


   .. method:: reset_model(self, main_data=None)


      Reset model.



