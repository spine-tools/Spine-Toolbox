:mod:`spinetoolbox.project_items.exporter.settings_state`
=========================================================

.. py:module:: spinetoolbox.project_items.exporter.settings_state

.. autoapi-nested-parse::

   Provides the SettingsState enum.

   :author: A. Soininen (VTT)
   :date:   20.12.2019



Module Contents
---------------

.. py:class:: SettingsState

   Bases: :class:`enum.Enum`

   State of export settings.

   .. attribute:: OK
      

      Settings OK.


   .. attribute:: FETCHING
      

      Settings are still being fetched/constructed.


   .. attribute:: INDEXING_PROBLEM
      

      There is a parameter value indexing issue.


   .. attribute:: ERROR
      

      An error prevents the creation of export settings.



