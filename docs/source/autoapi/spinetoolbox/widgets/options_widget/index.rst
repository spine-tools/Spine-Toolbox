:mod:`spinetoolbox.widgets.options_widget`
==========================================

.. py:module:: spinetoolbox.widgets.options_widget

.. autoapi-nested-parse::

   Contains OptionsWidget class.

   :author: P. Vennström (VTT)
   :date:   1.6.2019



Module Contents
---------------

.. py:class:: OptionsWidget(options, header='Options', parent=None)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget for handling simple options. Used by ConnectionManager.


   Creates OptionWidget

   :param options: Dict describing what options to build a widget around.
   :type options: Dict

   :keyword header: Title of groupbox (default: {"Options"})
   :kwtype header: str
   :keyword parent: parent of widget
   :kwtype parent: QWidget, None

   .. attribute:: optionsChanged
      

      

   .. method:: _build_ui(self)


      Builds ui from specification in dict


   .. method:: set_options(self, options=None, set_missing_default=True)


      Sets state of options

      :keyword options {Dict} -- Dict with option name as key and value as value (default: {None})
      :keyword set_missing_default {bool} -- Sets missing options to default if True (default: {True})


   .. method:: get_options(self)


      Returns current state of option widget

      :returns: [Dict] -- Dict with option name as key and value as value



