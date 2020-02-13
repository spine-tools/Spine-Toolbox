:mod:`spinetoolbox.mvcmodels.filter_checkbox_list_model`
========================================================

.. py:module:: spinetoolbox.mvcmodels.filter_checkbox_list_model

.. autoapi-nested-parse::

   Provides FilterCheckboxListModel for FilterWidget.

   :author: P. Vennström (VTT)
   :date:   1.11.2018



Module Contents
---------------

.. py:class:: FilterCheckboxListModelBase(parent, show_empty=True)

   Bases: :class:`PySide2.QtCore.QAbstractListModel`

   Init class.

   :param parent:
   :type parent: QWidget

   .. method:: reset_selection(self)



   .. method:: _select_all_clicked(self)



   .. method:: _is_all_selected(self)



   .. method:: rowCount(self, parent=QModelIndex())



   .. method:: data(self, index, role=Qt.DisplayRole)



   .. method:: _item_name(self, id_)
      :abstractmethod:



   .. method:: click_index(self, index)



   .. method:: set_list(self, id_data, all_selected=True)



   .. method:: set_selected(self, selected, select_empty=None)



   .. method:: get_selected(self)



   .. method:: get_not_selected(self)



   .. method:: set_filter(self, search_for)



   .. method:: apply_filter(self)



   .. method:: _remove_and_add_filtered(self)



   .. method:: _remove_and_replace_filtered(self)



   .. method:: remove_filter(self)



   .. method:: add_items(self, ids, selected=True)



   .. method:: remove_items(self, ids)




.. py:class:: SimpleFilterCheckboxListModel

   Bases: :class:`spinetoolbox.mvcmodels.filter_checkbox_list_model.FilterCheckboxListModelBase`

   .. method:: _item_name(self, id_)




.. py:class:: TabularViewFilterCheckboxListModel(parent, item_type, show_empty=True)

   Bases: :class:`spinetoolbox.mvcmodels.filter_checkbox_list_model.FilterCheckboxListModelBase`

   Init class.

   :param parent:
   :type parent: TabularViewMixin
   :param item_type: either "object" or "parameter definition"
   :type item_type: str, NoneType

   .. method:: _item_name(self, id_)




