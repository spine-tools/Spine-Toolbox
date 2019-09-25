..  Importing and exporting data
    Created: 15.5.2019

****************************
Importing and exporting data
****************************

.. note:: This section is a work in progress.

This section explains the different ways of importing and exporting data to and from a Spine database.

Excel
-----
In this section the excel import/export functionality is explained.

To import/export an excel file, select a **Data store** and open the **Tree view**.
Then select **File -> Import** or **File -> Export** from the main menu.


Format
~~~~~~

The excel files for import/export are formatted in the following way:

.. tip:: An easy way to get a excel template is to export an existing spine-database to excel.

Object classes:

.. image:: img/excel_object_sheet.png
   :align: center

Object timeseries:

.. image:: img/excel_object_sheet_timeseries.png
   :align: center

Relationship classes:

.. image:: img/excel_relationship_sheet.png
   :align: center

Relationship timeseries:

.. image:: img/excel_relationship_sheet_timeseries.png
   :align: center

When importing, all sheets with a valid format are imported, whereas sheets with invalid format are simply ignored.
When exporting all object classes and relationship classes are exported.
Only parameter values with timeseries data are exported in the timeseries format.
