:mod:`spinetoolbox.tool_configuration_assistants`
=================================================

.. py:module:: spinetoolbox.tool_configuration_assistants

.. autoapi-nested-parse::

   Classes for tool configuration assistants.

   :authors: M. Marin (KTH)
   :date:   10.1.2019



Module Contents
---------------

.. py:class:: SpineModelConfigurationAssistant(toolbox)

   Bases: :class:`PySide2.QtCore.QObject`

   Configuration assistant for SpineModel.jl.

   .. attribute:: toolbox

      QMainWindow instance

      :type: ToolboxUI

   Init class.

   .. attribute:: check_finished
      

      

   .. attribute:: installation_finished
      

      

   .. attribute:: msg
      

      

   .. method:: find_out_julia_version_and_project(self)



   .. method:: julia_version(self)


      Return current julia version.


   .. method:: julia_active_project(self)


      Return current julia active project.


   .. method:: spine_model_version_check(self)


      Returns execution manager for process that checks current version of SpineModel.


   .. method:: py_call_program_check(self)


      Returns execution manager for process that checks the python program used by PyCall
      in current julia version.


   .. method:: install_spine_model(self)


      Returns execution manager for process that installs SpineModel in current julia version.


   .. method:: install_py_call(self)


      Returns execution manager for process that installs PyCall in current julia version.


   .. method:: reconfigure_py_call(self, pyprogramname)


      Returns execution manager for process that reconfigures PyCall to use given python program.



