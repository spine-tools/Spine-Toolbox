:mod:`spinetoolbox.widgets.graph_view_demo`
===========================================

.. py:module:: spinetoolbox.widgets.graph_view_demo

.. autoapi-nested-parse::

   Contains the GraphViewForm class.

   :author: M. Marin (KTH)
   :date:   26.11.2018



Module Contents
---------------

.. py:class:: GraphViewDemo(parent)

   Bases: :class:`spinetoolbox.live_demo.LiveDemo`

   A widget that shows a demo for the graph view.

   Initializes class.

   :param parent:
   :type parent: GraphViewForm

   .. attribute:: _overlay_color
      

      

   .. method:: _make_select_one(self)



   .. method:: _make_select_more(self)



   .. method:: _make_good_bye(self)



   .. method:: _handle_welcome_entered(self)



   .. method:: _handle_select_one_entered(self)



   .. method:: _handle_select_more_entered(self)



   .. method:: _handle_good_bye_entered(self)




.. py:class:: SelectionAnimation(parent, command, duration=2000, max_steps=4)

   Bases: :class:`PySide2.QtCore.QVariantAnimation`

   :param parent:
   :type parent: GraphViewForm
   :param command:
   :type command: QItemSelectionModel.SelectionFlags
   :param duration: milliseconds
   :type duration: int
   :param max_steps:
   :type max_steps: int

   .. method:: _random_point(rect)
      :staticmethod:



   .. method:: updateState(self, new, old)



   .. method:: _handle_value_changed(self, value)



   .. method:: _handle_current_loop_changed(self, loop)



   .. method:: _handle_finished(self)




