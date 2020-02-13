:mod:`spinetoolbox.widgets.tool_configuration_assistant_widget`
===============================================================

.. py:module:: spinetoolbox.widgets.tool_configuration_assistant_widget

.. autoapi-nested-parse::

   Widget for assisting the user in configuring tools, such as SpineModel.

   :author: M. Marin (KTH)
   :date:   9.1.2019



Module Contents
---------------

.. py:class:: ToolConfigurationAssistantWidget(toolbox, autorun=True)

   Bases: :class:`PySide2.QtWidgets.QWidget`

   A widget to assist the user in configuring external tools such as SpineModel.

   .. attribute:: toolbox

      Parent widget.

      :type: ToolboxUI

   .. attribute:: autorun

      whether or not to start configuration process at form load

      :type: bool

   Initialize class.

   .. method:: connect_signals(self)


      Connect signals.


   .. method:: add_spine_model_msg(self, msg)


      Append message to SpineModel log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_spine_model_error_msg(self, msg)


      Append error message to SpineModel log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: add_spine_model_success_msg(self, msg)


      Append success message to SpineModel log.

      :param msg: String written to QTextBrowser
      :type msg: str


   .. method:: configure_spine_model(self)


      Run when form loads. Check SpineModel version.


   .. method:: _handle_spine_model_version_check_finished(self, ret)


      Run when the Spine Model configuration assistant has finished checking SpineModel version.
      Install SpineModel if not found, otherwise check the python program used by PyCall.


   .. method:: _handle_spine_model_installation_finished(self, ret)


      Run when the Spine Model configuration assistant has finished installing SpineModel.
      Check the python program used by PyCall.


   .. method:: _handle_py_call_program_check_finished(self, ret)


      Run when the Spine Model configuration assistant has finished checking the python program used by PyCall.
      Install PyCall if not found, otherwise reconfigure PyCall to use same python as Spine Toolbox if it's not
      the case.


   .. method:: _handle_py_call_installation_finished(self, ret)


      Run when the Spine Model configuration assistant has finished installing PyCall.
      Check the python program used by PyCall.


   .. method:: _handle_py_call_reconfiguration_finished(self, ret)


      Run when the Spine Model configuration assistant has finished reconfiguring PyCall.
      End Spine Model configuration.


   .. method:: get_permission(self, title, action)


      Ask user's permission to perform an action and return True if granted.


   .. method:: closeEvent(self, event=None)


      Handle close widget.

      :param event: PySide2 event
      :type event: QEvent



