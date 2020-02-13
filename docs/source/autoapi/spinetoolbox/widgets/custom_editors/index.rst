:mod:`spinetoolbox.widgets.custom_editors`
==========================================

.. py:module:: spinetoolbox.widgets.custom_editors

.. autoapi-nested-parse::

   Custom editors for model/view programming.


   :author: M. Marin (KTH)
   :date:   2.9.2018



Module Contents
---------------

.. py:class:: CustomLineEditor

   Bases: :class:`PySide2.QtWidgets.QLineEdit`

   A custom QLineEdit to handle data from models.

   .. method:: set_data(self, data)



   .. method:: data(self)



   .. method:: keyPressEvent(self, event)


      Prevents shift key press to clear the contents.



.. py:class:: CustomComboEditor

   Bases: :class:`PySide2.QtWidgets.QComboBox`

   A custom QComboBox to handle data from models.

   .. attribute:: data_committed
      

      

   .. method:: set_data(self, current_text, items)



   .. method:: data(self)




.. py:class:: CustomLineEditDelegate

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A delegate for placing a CustomLineEditor on the first row of SearchBarEditor.

   .. attribute:: text_edited
      

      

   .. method:: setModelData(self, editor, model, index)



   .. method:: createEditor(self, parent, option, index)


      Create editor and 'forward' `textEdited` signal.


   .. method:: eventFilter(self, editor, event)


      Handle all sort of special cases.



.. py:class:: SearchBarEditor(parent, tutor=None)

   Bases: :class:`PySide2.QtWidgets.QTableView`

   A Google-like search bar, implemented as a QTableView with a CustomLineEditDelegate in the first row.


   Initializes instance.

   :param parent: parent widget
   :type parent: QWidget
   :param tutor: another widget used for positioning.
   :type tutor: QWidget, NoneType

   .. attribute:: data_committed
      

      

   .. method:: set_data(self, current, items)


      Populates model.

      :param current:
      :type current: str
      :param items:
      :type items: Sequence(str)


   .. method:: set_base_size(self, size)



   .. method:: update_geometry(self)


      Updates geometry.


   .. method:: refit(self)



   .. method:: data(self)



   .. method:: _handle_delegate_text_edited(self, text)


      Filters model as the first row is being edited.


   .. method:: _proxy_model_filter_accepts_row(self, source_row, source_parent)


      Always accept first row.


   .. method:: keyPressEvent(self, event)


      Sets data from current index into first index as the user navigates
      through the table using the up and down keys.


   .. method:: currentChanged(self, current, previous)



   .. method:: edit_first_index(self)


      Edits first index if valid and not already being edited.


   .. method:: mouseMoveEvent(self, event)


      Sets the current index to the one hovered by the mouse.


   .. method:: mousePressEvent(self, event)


      Commits data.



.. py:class:: CheckListEditor(parent, tutor=None)

   Bases: :class:`PySide2.QtWidgets.QTableView`

   A check list editor.

   Initialize class.

   .. method:: keyPressEvent(self, event)


      Toggles checked state if the user presses space.


   .. method:: toggle_checked_state(self, index)


      Toggles checked state of given index.

      :param index:
      :type index: QModelIndex


   .. method:: mouseMoveEvent(self, event)


      Sets the current index to the one under mouse.


   .. method:: mousePressEvent(self, event)


      Toggles checked state of pressed index.


   .. method:: set_data(self, items, checked_items)


      Sets data and updates geometry.

      :param items: All items.
      :type items: Sequence(str)
      :param checked_items: Initially checked items.
      :type checked_items: Sequence(str)


   .. method:: data(self)


      Returns a comma separated list of checked items.

      Returns
          str


   .. method:: set_base_size(self, size)



   .. method:: update_geometry(self)


      Updates geometry.



.. py:class:: IconPainterDelegate

   Bases: :class:`PySide2.QtWidgets.QItemDelegate`

   A delegate to highlight decorations in a QListWidget.

   .. method:: paint(self, painter, option, index)


      Paints selected items using the highlight brush.



.. py:class:: IconColorEditor(parent)

   Bases: :class:`PySide2.QtWidgets.QDialog`

   An editor to let the user select an icon and a color for an object class.


   Init class.

   .. method:: _proxy_model_filter_accepts_row(self, source_row, source_parent)


      Overridden method to filter icons according to search terms.


   .. method:: connect_signals(self)


      Connect signals to slots.


   .. method:: set_data(self, data)



   .. method:: data(self)




.. py:class:: NumberParameterInlineEditor(parent)

   Bases: :class:`PySide2.QtWidgets.QDoubleSpinBox`

   An editor widget for numeric (datatype double) parameter values.

   .. method:: set_data(self, data)



   .. method:: data(self)




