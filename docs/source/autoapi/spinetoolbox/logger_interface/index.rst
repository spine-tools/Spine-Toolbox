:mod:`spinetoolbox.logger_interface`
====================================

.. py:module:: spinetoolbox.logger_interface

.. autoapi-nested-parse::

   A logger interface.

   :authors: A. Soininen (VTT)
   :date:   16.1.2020



Module Contents
---------------

.. py:class:: LoggerInterface

   Bases: :class:`PySide2.QtCore.QObject`

   Placeholder for signals that can be emitted to send messages to an output device.

   The signals should be connected to a concrete logging system.

   Currently, this is just a 'model interface'. ToolboxUI contains the same signals so it can be used
   instead of this class.

   .. attribute:: msg
      

      Emits a notification message.


   .. attribute:: msg_success
      

      Emits a message on success


   .. attribute:: msg_warning
      

      Emits a warning message.


   .. attribute:: msg_error
      

      Emits an error message.


   .. attribute:: msg_proc
      

      Emits a message originating from a subprocess (usually something printed to stdout).


   .. attribute:: information_box
      

      Requests an 'information message box' (e.g. a message window) to be opened with a given title and message.


   .. attribute:: error_box
      

      Requests an 'error message box' to be opened with a given title and message.



