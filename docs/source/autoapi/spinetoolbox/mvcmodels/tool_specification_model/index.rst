:mod:`spinetoolbox.mvcmodels.tool_specification_model`
======================================================

.. py:module:: spinetoolbox.mvcmodels.tool_specification_model

.. autoapi-nested-parse::

   Contains a class for storing Tool specifications.

   :authors: P. Savolainen (VTT)
   :date:   23.1.2018



Module Contents
---------------

.. py:class:: ToolSpecificationModel

   Bases: :class:`PySide2.QtCore.QAbstractListModel`

   Class to store tools that are available in a project e.g. GAMS or Julia models.

   .. method:: rowCount(self, parent=None)


      Must be reimplemented when subclassing. Returns
      the number of Tools in the model.

      :param parent: Not used (because this is a list)
      :type parent: QModelIndex

      :returns: Number of rows (available tools) in the model


   .. method:: data(self, index, role=None)


      Must be reimplemented when subclassing.

      :param index: Requested index
      :type index: QModelIndex
      :param role: Data role
      :type role: int

      :returns: Data according to requested role


   .. method:: flags(self, index)


      Returns enabled flags for the given index.

      :param index: Index of Tool
      :type index: QModelIndex


   .. method:: insertRow(self, tool, row=None, parent=QModelIndex())


      Insert row (tool specification) into model.

      :param tool: Tool added to the model
      :type tool: Tool
      :param row: Row to insert tool to
      :type row: str
      :param parent: Parent of child (not used)
      :type parent: QModelIndex

      :returns: Void


   .. method:: removeRow(self, row, parent=QModelIndex())


      Remove row (tool specification) from model.

      :param row: Row to remove the tool from
      :type row: int
      :param parent: Parent of tool on row (not used)
      :type parent: QModelIndex

      :returns: Boolean variable


   .. method:: update_tool_specification(self, tool, row)


      Update tool specification.

      :param tool: new tool, to replace the old one
      :type tool: ToolSpecification
      :param row: Position of the tool to be updated
      :type row: int

      :returns: Boolean value depending on the result of the operation


   .. method:: tool_specification(self, row)


      Returns tool specification on given row.

      :param row: Row of tool specification
      :type row: int

      :returns: ToolSpecification from tool specification list or None if given row is zero


   .. method:: find_tool_specification(self, name)


      Returns tool specification with the given name.

      :param name: Name of tool specification to find
      :type name: str


   .. method:: tool_specification_row(self, name)


      Returns the row on which the given specification is located or -1 if it is not found.


   .. method:: tool_specification_index(self, name)


      Returns the QModelIndex on which a tool specification with
      the given name is located or invalid index if it is not found.



