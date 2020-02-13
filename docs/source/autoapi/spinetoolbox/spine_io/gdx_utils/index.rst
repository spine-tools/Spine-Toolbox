:mod:`spinetoolbox.spine_io.gdx_utils`
======================================

.. py:module:: spinetoolbox.spine_io.gdx_utils

.. autoapi-nested-parse::

   Utility functions for .gdx import/export.

   :author: A. Soininen (VTT)
   :date:   7.1.2020



Module Contents
---------------

.. function:: _python_interpreter_bitness()

   Returns 64 for 64bit Python interpreter or 32 for 32bit interpreter.


.. function:: _windows_dlls_exist(gams_path)

   Returns True if requred DLL files exist in given GAMS installation path.


.. function:: find_gams_directory()

   Returns GAMS installation directory or None if not found.

   On Windows systems, this function looks for `gams.location` in registry;
   on other systems the `PATH` environment variable is checked.

   :returns: a path to GAMS installation directory or None if not found.


