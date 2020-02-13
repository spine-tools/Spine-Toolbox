:mod:`spinetoolbox.widgets.toolbars`
====================================

.. py:module:: spinetoolbox.widgets.toolbars

.. autoapi-nested-parse::

   Functions to make and handle QToolBars.

   :author: P. Savolainen (VTT)
   :date:   19.1.2018



Module Contents
---------------

.. py:class:: ItemToolBar(parent)

   Bases: :class:`PySide2.QtWidgets.QToolBar`

   A toolbar to add items using drag and drop actions.

   :param parent: QMainWindow instance
   :type parent: ToolboxUI

   .. method:: add_draggable_widgets(self, category_icon)


      Adds draggable widgets from the given list.

      :param category_icon: List of tuples (item_type (str), item category (str), icon path (str))
      :type category_icon: list


   .. method:: remove_all(self, checked=False)


      Slot for handling the remove all tool button clicked signal.
      Calls ToolboxUI remove_all_items() method.


   .. method:: execute_project(self, checked=False)


      Slot for handling the Execute project tool button clicked signal.


   .. method:: execute_selected(self, checked=False)


      Slot for handling the Execute selected tool button clicked signal.


   .. method:: stop_execution(self, checked=False)


      Slot for handling the Stop execution tool button clicked signal.



.. py:class:: DraggableWidget(parent, pixmap, item_type, category)

   Bases: :class:`PySide2.QtWidgets.QLabel`

   A draggable QLabel.

   :param parent: Parent widget
   :type parent: QWidget
   :param pixmap: Picture for the label
   :type pixmap: QPixMap
   :param item_type: Item type (e.g. Data Store, Data Connection, etc...)
   :type item_type: str
   :param category: Item category (e.g. Data Stores, Data Connetions, etc...)
   :type category: str

   .. method:: mousePressEvent(self, event)


      Register drag start position


   .. method:: mouseMoveEvent(self, event)


      Start dragging action if needed


   .. method:: mouseReleaseEvent(self, event)


      Forget drag start position



.. py:class:: ParameterTagToolBar(parent, db_mngr, *db_maps)

   Bases: :class:`PySide2.QtWidgets.QToolBar`

   A toolbar to add items using drag and drop actions.

   :param parent: tree or graph view form
   :type parent: DataStoreForm
   :param db_mngr: the DB manager for interacting with the db
   :type db_mngr: SpineDBManager
   :param db_maps: DiffDatabaseMapping instances
   :type db_maps: iter

   .. attribute:: tag_button_toggled
      

      

   .. attribute:: manage_tags_action_triggered
      

      

   .. method:: init_toolbar(self)



   .. method:: receive_parameter_tags_added(self, db_map_data)



   .. method:: _add_db_map_tag_actions(self, db_map, parameter_tags)



   .. method:: receive_parameter_tags_removed(self, db_map_data)



   .. method:: _remove_db_map_tag_actions(self, db_map, parameter_tag_ids)



   .. method:: receive_parameter_tags_updated(self, db_map_data)



   .. method:: _update_db_map_tag_actions(self, db_map, parameter_tags)




