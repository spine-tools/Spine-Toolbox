:mod:`spinetoolbox.project_items.exporter.widgets.parameter_index_settings`
===========================================================================

.. py:module:: spinetoolbox.project_items.exporter.widgets.parameter_index_settings

.. autoapi-nested-parse::

   Parameter indexing settings window for .gdx export.

   :author: A. Soininen (VTT)
   :date:   26.11.2019



Module Contents
---------------

.. py:class:: IndexSettingsState

   Bases: :class:`enum.Enum`

   An enumeration indicating the state of the settings window.

   .. attribute:: OK
      

      

   .. attribute:: DOMAIN_MISSING_INDEXES
      

      

   .. attribute:: DOMAIN_NAME_MISSING
      

      

   .. attribute:: DOMAIN_NAME_CLASH
      

      


.. py:class:: ParameterIndexSettings(parameter_name, indexing_setting, available_existing_domains, new_domains, parent)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget showing setting for a parameter with indexed values.

   :param parameter_name: parameter's name
   :type parameter_name: str
   :param indexing_setting: indexing settings for the parameter
   :type indexing_setting: IndexingSetting
   :param available_existing_domains: a dict from existing domain name to a list of its record keys
   :type available_existing_domains: dict
   :param new_domains: a dict from new domain name to a list of its record keys
   :type new_domains: dict
   :param parent: a parent widget
   :type parent: QWidget

   .. method:: new_domain_name(self)
      :property:


      name of the new domain


   .. method:: state(self)
      :property:


      widget's state


   .. method:: is_using_domain(self, domain_name)



   .. method:: indexing_domain(self)


      Provides information needed to expand the parameter's indexed values.

      :returns: a tuple of IndexingDomain and a Set if a new domain is needed for indexing, otherwise None
      :rtype: tuple


   .. method:: notification_message(self, message)


      Shows a notification message on the widget.


   .. method:: warning_message(self, message)


      Shows a warning message on the widget.


   .. method:: error_message(self, message)


      Shows an error message on the widget.


   .. method:: reorder_indexes(self, first, last, target)



   .. method:: _check_state(self)


      Updated the widget's state.


   .. method:: _check_errors(self, mapped_values_balance)


      Checks if the parameter is correctly indexed.


   .. method:: _check_warnings(self, mapped_values_balance)


      Checks if there are non-fatal issues with parameter indexing.


   .. method:: _update_indexing_domains_name(self, domain_name=None)


      Updates the model's header and the label showing the indexing domains.

      :param domain_name: indexing domain's name or None to read it from the other widgets.
      :type domain_name: str


   .. method:: _domain_name_changed(self, text)


      Reacts to changes in indexing domain name.


   .. method:: _set_enabled_use_existing_domain_widgets(self, enabled)


      Enables and disables controls used to set up indexing based on an existing domain.


   .. method:: _set_enabled_create_domain_widgets(self, enabled)


      Enables and disables controls used to set up indexing based on a new domain.


   .. method:: _existing_domain_changed(self, index)


      Reacts to changes in existing domains combo box.


   .. method:: _update_index_list_selection(self, expression, clear_selection_if_expression_empty=True)


      Updates selection according to changed selection expression.


   .. method:: _update_model_to_selection(self, selected, deselected)


      Updates the model after table selection has changed.


   .. method:: _generate_index(self, expression)


      Builds indexes according to given expression.


   .. method:: _extract_index_from_parameter(self, _=True)


      Assigns indexes from the parameter to the model.


   .. method:: _move_indexing_domain_left(self, _)


      Moves the indexing domain name left on the indexing label.


   .. method:: _move_indexing_domain_right(self, _)


      Moves the indexing domain name right on the indexing label.



.. py:class:: _IndexingTableModel(parameter)

   Bases: :class:`PySide2.QtCore.QAbstractTableModel`

   A table model for parameter value indexing.

   First column contains the proposed new index keys.
   The rest of the columns contain the parameter values for each set of existing index keys.
   Only selected new index keys are used for indexing.
   Unselected rows are left empty.

   :param parameter: a parameter to model
   :type parameter: Parameter

   .. method:: indexes(self)
      :property:


      a string list of all new indexing keys


   .. method:: index_selection(self)
      :property:


      a boolean list of selected index keys, so called pick list


   .. method:: clear(self)


      Clears the model.


   .. method:: columnCount(self, parent=QModelIndex())


      Returns the number of columns.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns data associated with given model index and role.


   .. method:: headerData(self, section, orientation, role=Qt.DisplayRole)


      Returns header data.


   .. method:: mapped_values_balance(self)


      Returns the balance between available indexes and parameter values.

      Zero means that there is as many indexes available as there are values,
      i.e. the parameter is 'perfectly' indexed.
      A positive value means there are more indexes than values
      while a negative value means there are not enough indexes for all values.

      :returns: mapped values' balance
      :rtype: int


   .. method:: reorder_indexes(self, first, last, target)


      Moves indexes around.

      :param first: first index to move
      :type first: int
      :param last: last index to move (inclusive)
      :type last: int
      :param target: where to move the first index
      :type target: int


   .. method:: rowCount(self, parent=QModelIndex())


      Return the number of rows.


   .. method:: selection_changed(self, selected, deselected)


      Updates selected and deselected rows on the table.


   .. method:: set_index_name(self, name)


      Sets the indexing domain name.


   .. method:: set_indexes(self, indexes)


      Overwrites all new indexes.



