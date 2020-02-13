:mod:`spinetoolbox.project_items.exporter.widgets.gdx_export_settings`
======================================================================

.. py:module:: spinetoolbox.project_items.exporter.widgets.gdx_export_settings

.. autoapi-nested-parse::

   Export item's settings window for .gdx export.

   :author: A. Soininen (VTT)
   :date:   9.9.2019



Module Contents
---------------

.. py:class:: State

   Bases: :class:`enum.Enum`

   Gdx Export Settings window state

   .. attribute:: OK
      

      Settings are ok.


   .. attribute:: BAD_INDEXING
      

      Not all indexed parameters are set up correctly.



.. py:class:: GdxExportSettings(settings, indexing_settings, new_indexing_domains, database_path, parent)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A setting window for exporting .gdx files.

   :param settings: export settings
   :type settings: Settings
   :param indexing_settings: indexing domain information for indexed parameter values
   :type indexing_settings: dict
   :param new_indexing_domains: list of additional domains needed for indexed parameter
   :type new_indexing_domains: list
   :param database_path: database URL
   :type database_path: str
   :param parent: a parent widget
   :type parent: QWidget

   .. attribute:: reset_requested
      

      Emitted when Reset Defaults button has been clicked.


   .. attribute:: settings_accepted
      

      Emitted when the OK button has been clicked.


   .. attribute:: settings_rejected
      

      Emitted when the Cancel button has been clicked.


   .. method:: settings(self)
      :property:


      the settings object


   .. method:: indexing_settings(self)
      :property:


      indexing settings dict


   .. method:: new_domains(self)
      :property:


      list of additional domain needed for indexing


   .. method:: reset_settings(self, settings, indexing_settings, new_indexing_domains)


      Resets all settings.


   .. method:: _check_state(self)


      Checks if there are parameters in need for indexing.


   .. method:: _populate_global_parameters_combo_box(self, settings)


      (Re)populates the global parameters combo box.


   .. method:: settings_state_changed(self, state)



   .. method:: _accepted(self)


      Emits the settings_accepted signal.


   .. method:: _move_sets_up(self, checked=False)


      Moves selected domains and sets up one position.


   .. method:: _move_sets_down(self, checked=False)


      Moves selected domains and sets down one position.


   .. method:: _move_records_up(self, checked=False)


      Moves selected records up and position.


   .. method:: _move_records_down(self, checked=False)


      Moves selected records down on position.


   .. method:: _rejected(self)


      Hides the window.


   .. method:: _reset_settings(self, button)



   .. method:: _update_global_parameters_domain(self, text)



   .. method:: _populate_set_contents(self, selected, _)


      Populates the record list by the selected domain's or set's records.


   .. method:: _sort_records_alphabetically(self, _)


      Sorts the lists of set records alphabetically.


   .. method:: _show_indexed_parameter_settings(self, _)


      Shows the indexed parameter settings window.


   .. method:: _parameter_settings_approved(self)


      Gathers settings from the indexed parameters settings window.


   .. method:: _dispose_parameter_settings_window(self)


      Removes references to the indexed parameter settings window.



.. function:: _move_selected_elements_by(list_view, delta)

   Moves selected items in a QListView by given delta.

   :param list_view: a list view
   :type list_view: QListView
   :param delta: positive values move the items up, negative down
   :type delta: int


.. py:class:: GAMSSetListModel(settings)

   Bases: :class:`PySide2.QtCore.QAbstractListModel`

   A model to configure the domain and set name lists in gdx export settings.

   This model combines the domain and set name lists into a single list.
   The two 'parts' are differentiated by different background colors.
   Items from each part cannot be mixed with the other.
   Both the ordering of the items within each list as well as their exportability flags are handled here.

   :param settings: settings whose domain and set name lists should be modelled
   :type settings: spine_io.exporters.gdx.Settings

   .. method:: add_domain(self, domain)


      Adds a new domain.


   .. method:: drop_domain(self, domain)


      Removes a domain.


   .. method:: update_domain(self, domain)


      Updates an existing domain.


   .. method:: data(self, index, role=Qt.DisplayRole)


      Returns the value for given role at given index.

      Qt.DisplayRole returns the name of the domain or set
      while Qt.CheckStateRole returns whether the exportable flag has been set or not.
      Qt.BackgroundRole gives the item's background depending whether it is a domain or a set.

      :param index: an index to the model
      :type index: QModelIndex
      :param role: the query's role
      :type role: int

      :returns: the requested value or `None`


   .. method:: flags(self, index)


      Returns an item's flags.


   .. method:: headerData(self, section, orientation, role=Qt.DisplayRole)


      Returns an empty string for horizontal header and row number for vertical header.


   .. method:: index_for_domain(self, domain_name)


      Returns the model index for a domain.


   .. method:: is_domain(self, index)


      Returns True if index points to a domain name, otherwise returns False.


   .. method:: moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild)


      Moves the domain and set names around.

      The names cannot be mixed between domains and sets.

      :param sourceParent: parent from which the rows are moved
      :type sourceParent: QModelIndex
      :param sourceRow: index of the first row to be moved
      :type sourceRow: int
      :param count: number of rows to move
      :type count: int
      :param destinationParent: parent to which the rows are moved
      :type destinationParent: QModelIndex
      :param destinationChild: index where to insert the moved rows
      :type destinationChild: int

      :returns: True if the operation was successful, False otherwise


   .. method:: rowCount(self, parent=QModelIndex())


      Returns the number of rows.


   .. method:: setData(self, index, value, role=Qt.EditRole)


      Sets the exportable flag status for given row.



.. py:class:: GAMSRecordListModel

   Bases: :class:`PySide2.QtCore.QAbstractListModel`

   A model to manage record ordering within domains and sets.

   .. attribute:: domain_records_reordered
      

      

   .. method:: data(self, index, role=Qt.DisplayRole)


      With `role == Qt.DisplayRole` returns the record's keys as comma separated string.


   .. method:: headerData(self, section, orientation, role=Qt.DisplayRole)


      Returns row and column header data.


   .. method:: moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild)


      Moves the records around.

      :param sourceParent: parent from which the rows are moved
      :type sourceParent: QModelIndex
      :param sourceRow: index of the first row to be moved
      :type sourceRow: int
      :param count: number of rows to move
      :type count: int
      :param destinationParent: parent to which the rows are moved
      :type destinationParent: QModelIndex
      :param destinationChild: index where to insert the moved rows
      :type destinationChild: int

      :returns: True if the operation was successful, False otherwise


   .. method:: reset(self, records, set_name)


      Resets the model's record data.


   .. method:: rowCount(self, parent=QModelIndex())


      Return the number of records in the model.


   .. method:: sort_alphabetically(self)




