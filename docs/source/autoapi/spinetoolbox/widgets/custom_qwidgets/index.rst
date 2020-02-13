:mod:`spinetoolbox.widgets.custom_qwidgets`
===========================================

.. py:module:: spinetoolbox.widgets.custom_qwidgets

.. autoapi-nested-parse::

   Custom QWidgets for Filtering and Zooming.

   :author: P. Vennström (VTT)
   :date:   4.12.2018



Module Contents
---------------

.. py:class:: FilterWidgetBase(parent)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Filter widget class.

   Init class.

   :param parent:
   :type parent: QWidget

   .. attribute:: okPressed
      

      

   .. attribute:: cancelPressed
      

      

   .. method:: connect_signals(self)



   .. method:: save_state(self)


      Saves the state of the FilterCheckboxListModel.


   .. method:: reset_state(self)


      Sets the state of the FilterCheckboxListModel to saved state.


   .. method:: clear_filter(self)


      Selects all items in FilterCheckBoxListModel.


   .. method:: has_filter(self)


      Returns true if any item is filtered in FilterCheckboxListModel false otherwise.


   .. method:: set_filter_list(self, data)


      Sets the list of items to filter.


   .. method:: _apply_filter(self)


      Apply current filter and save state.


   .. method:: _cancel_filter(self)


      Cancel current edit of filter and set the state to the stored state.


   .. method:: _filter_list(self)


      Filter list with current text.


   .. method:: _text_edited(self, new_text)


      Callback for edit text, starts/restarts timer.
      Start timer after text is edited, restart timer if text
      is edited before last time out.



.. py:class:: SimpleFilterWidget(parent, show_empty=True)

   Bases: :class:`spinetoolbox.widgets.custom_qwidgets.FilterWidgetBase`

   Init class.

   :param parent:
   :type parent: QWidget


.. py:class:: TabularViewFilterWidget(parent, item_type, show_empty=True)

   Bases: :class:`spinetoolbox.widgets.custom_qwidgets.FilterWidgetBase`

   Init class.

   :param parent:
   :type parent: QWidget
   :param item_type: either "object" or "parameter definition"
   :type item_type: str


.. py:class:: ZoomWidgetAction(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidgetAction`

   A zoom widget action.

   Class constructor.

   :param parent: the widget's parent
   :type parent: QWidget

   .. attribute:: minus_pressed
      

      

   .. attribute:: plus_pressed
      

      

   .. attribute:: reset_pressed
      

      

   .. method:: _handle_hovered(self)


      Runs when the zoom widget action is hovered. Hides other menus under the parent widget
      which are being shown. This is the default behavior for hovering QAction,
      but for some reason it's not the case for hovering QWidgetAction.



.. py:class:: ZoomWidget(parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   Class constructor.

   :param parent: the widget's parent
   :type parent: QWidget

   .. attribute:: minus_pressed
      

      

   .. attribute:: plus_pressed
      

      

   .. attribute:: reset_pressed
      

      

   .. method:: paintEvent(self, event)


      Overridden method.



