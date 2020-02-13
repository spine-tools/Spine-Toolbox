:mod:`spinetoolbox.project_items.exporter.worker`
=================================================

.. py:module:: spinetoolbox.project_items.exporter.worker

.. autoapi-nested-parse::

   A worker based machinery to construct the settings data structures needed for gdx export outside the UI loop.

   :author: A. Soininen (VTT)
   :date:   19.12.2019



Module Contents
---------------

.. py:class:: Worker(database_url)

   Bases: :class:`PySide2.QtCore.QThread`

   A worker thread to construct export settings for a database.

   :param database_url: database's URL
   :type database_url: str

   .. attribute:: errored
      

      Emitted when an error occurs.


   .. attribute:: finished
      

      Emitted when the worker has finished.


   .. attribute:: indexing_settings_read
      

      Sends the indexing settings away.


   .. attribute:: settings_read
      

      Sends the settings away.


   .. method:: run(self)


      Constructs settings and parameter index settings and sends them away using signals.



