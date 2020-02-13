:mod:`spinetoolbox.datapackage_import_export`
=============================================

.. py:module:: spinetoolbox.datapackage_import_export

.. autoapi-nested-parse::

   Functions to import/export between spine database and frictionless data's datapackage.

   :author: M. Marin (KTH)
   :date:   28.8.2018



Module Contents
---------------

.. py:class:: Signaler

   Bases: :class:`PySide2.QtCore.QObject`

   .. attribute:: finished
      

      

   .. attribute:: failed
      

      

   .. attribute:: progressed
      

      


.. py:class:: DatapackageToSpineConverter(db_url, datapackage_descriptor, datapackage_base_path)

   Bases: :class:`PySide2.QtCore.QRunnable`

   .. method:: number_of_steps(self)



   .. method:: run(self)



   .. method:: _run(self)




.. function:: datapackage_to_spine(db_map, datapackage_file_path)

   Convert datapackage from `datapackage_file_path` into Spine `db_map`.


