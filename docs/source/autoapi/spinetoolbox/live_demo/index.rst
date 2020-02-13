:mod:`spinetoolbox.live_demo`
=============================

.. py:module:: spinetoolbox.live_demo

.. autoapi-nested-parse::

   Contains the GraphViewForm class.

   :author: M. Marin (KTH)
   :date:   26.11.2018



Module Contents
---------------

.. py:class:: LiveDemo(window_title, parent)

   Bases: :class:`PySide2.QtWidgets.QDockWidget`

   A widget for showing live demonstrations.

   Initializes class.

   :param window_title:
   :type window_title: str
   :param parent:
   :type parent: QMainWindow

   .. attribute:: _overlay_color
      

      

   .. attribute:: _tutorial_data_path
      

      

   .. method:: is_running(self)



   .. method:: show(self)



   .. method:: _make_welcome(self)



   .. method:: _make_abort(self)



   .. method:: setup(self)



   .. method:: _handle_welcome_entered(self)
      :abstractmethod:




