****************************
Importing and exporting data
****************************

This section explains the different ways of importing and exporting data to and from a spine-database.

.. contents::
    :local:

Excel
-----
In this section the excel import/export functionality is explained.

To import/export an excel file, select an **Data store** and open the **Tree view** editor. From there use the File menu and click the Import or Export options.


Format
~~~~~~

The excel files are formated in the following way:

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

The import will import all sheets with a valid format and ignore all other sheets. When exporting all object classes and relationship classes will be exported. Only parameter values with timeseries data will be exported in the timeseries format.