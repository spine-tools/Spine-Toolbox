:mod:`spinetoolbox.widgets.custom_delegates`
============================================

.. py:module:: spinetoolbox.widgets.custom_delegates

.. autoapi-nested-parse::

   Custom item delegates.

   :author: M. Marin (KTH)
   :date:   1.9.2018



Module Contents
---------------

.. py:class:: ComboBoxDelegate(parent, choices)

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   .. method:: createEditor(self, parent, option, index)



   .. method:: paint(self, painter, option, index)



   .. method:: setEditorData(self, editor, index)



   .. method:: setModelData(self, editor, model, index)



   .. method:: updateEditorGeometry(self, editor, option, index)



   .. method:: currentItemChanged(self)




.. py:class:: LineEditDelegate

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A delegate that places a fully functioning QLineEdit.

   .. attribute:: parent

      either data store or spine datapackage widget

      :type: QMainWindow

   .. attribute:: data_committed
      

      

   .. method:: createEditor(self, parent, option, index)


      Return CustomLineEditor. Set up a validator depending on datatype.


   .. method:: setEditorData(self, editor, index)


      Init the line editor with previous data from the index.


   .. method:: setModelData(self, editor, model, index)


      Send signal.



.. py:class:: CheckBoxDelegate(parent, centered=True)

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A delegate that places a fully functioning QCheckBox.

   .. attribute:: parent

      either toolbox or spine datapackage widget

      :type: QMainWindow

   .. attribute:: centered

      whether or not the checkbox should be center-aligned in the widget

      :type: bool

   .. attribute:: data_committed
      

      

   .. method:: createEditor(self, parent, option, index)


      Important, otherwise an editor is created if the user clicks in this cell.
      ** Need to hook up a signal to the model.


   .. method:: paint(self, painter, option, index)


      Paint a checkbox without the label.


   .. method:: editorEvent(self, event, model, option, index)


      Change the data in the model and the state of the checkbox
      when user presses left mouse button and this cell is editable.
      Otherwise do nothing.


   .. method:: setModelData(self, editor, model, index)


      Do nothing. Model data is updated by handling the `data_committed` signal.


   .. method:: get_checkbox_rect(self, option)




.. py:class:: PivotTableDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.CheckBoxDelegate`

   .. attribute:: parameter_value_editor_requested
      

      

   .. attribute:: data_committed
      

      

   .. method:: setModelData(self, editor, model, index)


      Send signal.


   .. method:: _is_entity_index(self, index)



   .. method:: paint(self, painter, option, index)



   .. method:: editorEvent(self, event, model, option, index)



   .. method:: createEditor(self, parent, option, index)




.. py:class:: GetObjectClassIdMixin

   Allows getting the object class id from the name.

   .. method:: _get_object_class_id(self, index, db_map)




.. py:class:: GetRelationshipClassIdMixin

   Allows getting the relationship class id from the name.

   .. method:: _get_relationship_class_id(self, index, db_map)




.. py:class:: ParameterDelegate(parent, db_mngr)

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   Base class for all custom parameter delegates.

   .. attribute:: parent

      tree or graph view form

      :type: DataStoreForm

   .. attribute:: db_mngr

      

      :type: SpineDBManager

   .. attribute:: data_committed
      

      

   .. method:: setModelData(self, editor, model, index)


      Send signal.


   .. method:: updateEditorGeometry(self, editor, option, index)



   .. method:: _close_editor(self, editor, index)


      Closes editor. Needed by SearchBarEditor.


   .. method:: _get_db_map(self, index)


      Returns the db_map for the database at given index or None if not set yet.



.. py:class:: DatabaseNameDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the database name.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ParameterValueOrDefaultValueDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the either the value or the default value.

   .. attribute:: parameter_value_editor_requested
      

      

   .. method:: setModelData(self, editor, model, index)


      Emits the data_committed signal with new data.


   .. method:: _str_to_int_or_float(string)
      :staticmethod:



   .. method:: _create_or_request_parameter_value_editor(self, parent, option, index, db_map)


      Returns a CustomLineEditor or NumberParameterInlineEditor if the data from index is not of special type.
      Otherwise, emit the signal to request a standalone `ParameterValueEditor` from parent widget.



.. py:class:: ParameterDefaultValueDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterValueOrDefaultValueDelegate`

   A delegate for the either the default value.

   .. method:: createEditor(self, parent, option, index)


      Returns or requests a parameter value editor.



.. py:class:: ParameterValueDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterValueOrDefaultValueDelegate`

   A delegate for the parameter value.

   .. method:: _get_entity_class_id(self, index, db_map)
      :abstractmethod:



   .. method:: _get_value_list(self, index, db_map)


      Returns a value list item for the given index and db_map.


   .. method:: createEditor(self, parent, option, index)


      If the parameter has associated a value list, returns a SearchBarEditor .
      Otherwise returns or requests a dedicated parameter value editor.



.. py:class:: ObjectParameterValueDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.GetObjectClassIdMixin`, :class:`spinetoolbox.widgets.custom_delegates.ParameterValueDelegate`

   A delegate for the object parameter value.

   .. method:: entity_class_id_key(self)
      :property:



   .. method:: _get_entity_class_id(self, index, db_map)




.. py:class:: RelationshipParameterValueDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.GetRelationshipClassIdMixin`, :class:`spinetoolbox.widgets.custom_delegates.ParameterValueDelegate`

   A delegate for the relationship parameter value.

   .. method:: entity_class_id_key(self)
      :property:



   .. method:: _get_entity_class_id(self, index, db_map)




.. py:class:: TagListDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the parameter tag list.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ValueListDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the parameter value-list.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ObjectClassNameDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the object class name.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: RelationshipClassNameDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the relationship class name.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ObjectParameterNameDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.GetObjectClassIdMixin`, :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the object parameter name.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: RelationshipParameterNameDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.GetRelationshipClassIdMixin`, :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the relationship parameter name.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ObjectNameDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.GetObjectClassIdMixin`, :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the object name.

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ObjectNameListDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.GetRelationshipClassIdMixin`, :class:`spinetoolbox.widgets.custom_delegates.ParameterDelegate`

   A delegate for the object name list.

   .. attribute:: object_name_list_editor_requested
      

      

   .. method:: createEditor(self, parent, option, index)


      Returns editor.



.. py:class:: ManageItemsDelegate

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A custom delegate for the model in {Add/Edit}ItemDialogs.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. attribute:: data_committed
      

      

   .. method:: setModelData(self, editor, model, index)


      Send signal.


   .. method:: close_editor(self, editor, index, model)



   .. method:: updateEditorGeometry(self, editor, option, index)



   .. method:: connect_editor_signals(self, editor, index)


      Connect editor signals if necessary.


   .. method:: _create_database_editor(self, parent, option, index)




.. py:class:: ManageObjectClassesDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ManageItemsDelegate`

   A delegate for the model and view in {Add/Edit}ObjectClassesDialog.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. attribute:: icon_color_editor_requested
      

      

   .. method:: createEditor(self, parent, option, index)


      Return editor.


   .. method:: paint(self, painter, option, index)


      Get a pixmap from the index data and paint it in the middle of the cell.



.. py:class:: ManageObjectsDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ManageItemsDelegate`

   A delegate for the model and view in {Add/Edit}ObjectsDialog.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. method:: createEditor(self, parent, option, index)


      Return editor.



.. py:class:: ManageRelationshipClassesDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ManageItemsDelegate`

   A delegate for the model and view in {Add/Edit}RelationshipClassesDialog.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. method:: createEditor(self, parent, option, index)


      Return editor.



.. py:class:: ManageRelationshipsDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ManageItemsDelegate`

   A delegate for the model and view in {Add/Edit}RelationshipsDialog.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. method:: createEditor(self, parent, option, index)


      Return editor.



.. py:class:: RemoveEntitiesDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ManageItemsDelegate`

   A delegate for the model and view in RemoveEntitiesDialog.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. method:: createEditor(self, parent, option, index)


      Return editor.



.. py:class:: ManageParameterTagsDelegate

   Bases: :class:`spinetoolbox.widgets.custom_delegates.ManageItemsDelegate`

   A delegate for the model and view in ManageParameterTagsDialog.

   .. attribute:: parent

      parent dialog

      :type: ManageItemsDialog

   .. method:: createEditor(self, parent, option, index)


      Return editor.



.. py:class:: ForeignKeysDelegate(parent)

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A QComboBox delegate with checkboxes.

   .. attribute:: parent

      spine datapackage widget

      :type: SpineDatapackageWidget

   .. attribute:: data_committed
      

      

   .. method:: close_field_name_list_editor(self, editor, index, model)



   .. method:: createEditor(self, parent, option, index)


      Return editor.


   .. method:: setEditorData(self, editor, index)


      Set editor data.


   .. method:: setModelData(self, editor, model, index)


      Send signal.



