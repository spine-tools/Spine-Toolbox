
Importing and exporting data
----------------------------

This section describes the available tools to import and export data.

.. contents::
   :local:

Overview
========

Data store form supports importing and exporting data in three different formats: SQLite, JSON, and Excel.
The SQLite import/export uses the Spine database format.
The JSON and Excel import/export use a specific format described below.


.. tip:: To get a JSON or Excel file template you can simply export an existing Spine database
   into one of those formats.

Excel format
~~~~~~~~~~~~

The Excel format consists of one sheet per object and relationship class.
Each sheet can have one of four different formats:

1. Object class with scalar parameter data:

  .. image:: img/excel_object_sheet.png
     :align: center

2. Object class with time-series parameter data:

   .. image:: img/excel_object_sheet_timeseries.png
      :align: center

3. Relationship class with scalar parameter data:

   .. image:: img/excel_relationship_sheet.png
      :align: center

4. Relationship class with time-series parameter data:

   .. image:: img/excel_relationship_sheet_timeseries.png
      :align: center

JSON format
~~~~~~~~~~~


Importing
=========

To import a file, go to **File --> Import**.
The *Import file* dialog pops up.
Select the file type (SQLite, JSON, or Excel), enter the path of the source file for import, and accept the dialog.

.. note:: Changes from import operations are not committed immediately to any databases.
   You need to commit them separately (see :ref:`committing_and_rolling_back`).

.. tip:: You can undo import operations using **Edit -> Undo**.

Exporting
=========

Mass export
~~~~~~~~~~~

To export all items of certain types, go to **File --> Export**.
The *Mass export items* dialog pops up:

.. image:: img/mass_export_items_dialog.png
   :align: center

Select the databases you want to export under *Databases*, and the type of items under *Items*,
then press **Ok**.
The *Export file* dialog pops up now.
Select the file type (SQLite, JSON, or Excel), enter the path of the file you want to export, and accept the dialog.


Selective export
~~~~~~~~~~~~~~~~

To export a specific subset of items, select the correspoding items in either *Object tree*
and *Relationship tree*, click on the selection to bring the context menu,
and select **Export selected**.

The *Export file* dialog pops up.
Select the file type (SQLite, JSON, or Excel), enter the path of the target file for export, and accept the dialog.


Session export
~~~~~~~~~~~~~~

To export only the changes made in the current session, go to **File --> Export session**.

The *Export file* dialog pops up.
Select the file type (SQLite, JSON, or Excel), enter the path of the target file for export, and accept the dialog.

.. note:: The databases are exported in their current status, i.e., including all uncommitted changes.