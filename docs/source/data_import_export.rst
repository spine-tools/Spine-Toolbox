****************************
Importing and exporting data
****************************

This section explains the different ways of importing and exporting data to and from a Spine database.

.. contents::
    :local:

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


Datapackage
-----------

This section explains how to convert a datapackage into a Spine database. **The other way around,
i.e., converting a Spine database into a datapackage is not yet supported.**

.. note:: It is a good idea to get familiar with
   the `tabular datapackage specification <https://frictionlessdata.io/specs/tabular-data-package/>`_
   before continuing.

To convert a datapackage into a Spine database you have two options:

A. Using the **Spine datapackage editor**:
   select **File -> Export to Spine format** from the main menu, and then enter the name and location of the
   destination Spine database file.
B. Using the **Tree view**:
   select **File -> Import** from the main menu, and then select a valid 'datapackage.json' file.


Basic mapping rules
~~~~~~~~~~~~~~~~~~~

* Each resource in the datapackage is mapped to an *object class* in the Spine database.
* If no primary or foreign keys are specified,
  each field in a resource's schema is mapped to a *parameter*,
  associated with the *object class* mapped by the resource.
* Each row in a resource's data is mapped to an *object* of the *object class* mapped by the resource.
* The value of each field in a row is mapped to a *parameter value*, for the *object* mapped by the row and the
  *parameter* mapped by the field.

Example
=======

Let's say we have a datapackage with two resources named 'dog' and 'guy', with no primary or foreign keys, and
data given by the following CSV files:

``dog.csv``::

    name, breed, owner
    pluto, bloodhound, mickey
    scooby, great dane, shaggy
    brian, labrador, peter


``guy.csv``::

   name, age
   peter, 40
   shaggy, 20
   mickey, 5

After conversion, the following content will be in the Spine database (empty fields are not shown):

* **object class**

  +---------+-----------+
  | **id**  | **name**  |
  +---------+-----------+
  | 1       | dog       |
  +---------+-----------+
  | 2       | guy       |
  +---------+-----------+

* **object**

  +---------+---------------+-----------+
  | **id**  | **class_id**  | **name**  |
  +---------+---------------+-----------+
  | 1       | 1 (dog)       | dog_1     |
  +---------+---------------+-----------+
  | 2       | 1 (dog)       | dog_2     |
  +---------+---------------+-----------+
  | 3       | 1 (dog)       | dog_3     |
  +---------+---------------+-----------+
  | 4       | 2 (guy)       | guy_1     |
  +---------+---------------+-----------+
  | 5       | 2 (guy)       | guy_2     |
  +---------+---------------+-----------+
  | 6       | 2 (guy)       | guy_3     |
  +---------+---------------+-----------+


* **parameter**

  +---------+----------------------+------------+
  | **id**  | **object_class_id**  | **name**   |
  +---------+----------------------+------------+
  | 1       | 1 (dog)              | dog_name   |
  +---------+----------------------+------------+
  | 2       | 1 (dog)              | dog_breed  |
  +---------+----------------------+------------+
  | 3       | 1 (dog)              | dog_owner  |
  +---------+----------------------+------------+
  | 4       | 2 (guy)              | guy_name   |
  +---------+----------------------+------------+
  | 5       | 2 (guy)              | guy_age    |
  +---------+----------------------+------------+

* **parameter value**

  +----------------+------------------+------------+
  | **object_id**  | **parameter_id** | **value**  |
  +----------------+------------------+------------+
  | 1 (dog_1)      | 1 (dog_name)     | pluto      |
  +----------------+------------------+------------+
  | 2 (dog_2)      | 1 (dog_name)     | scooby     |
  +----------------+------------------+------------+
  | 3 (dog_3)      | 1 (dog_name)     | brian      |
  +----------------+------------------+------------+
  | 1 (dog_1)      | 2 (dog_breed)    | bloodhound |
  +----------------+------------------+------------+
  | 2 (dog_2)      | 2 (dog_breed)    | great dane |
  +----------------+------------------+------------+
  | 3 (dog_3)      | 2 (dog_breed)    | labrador   |
  +----------------+------------------+------------+
  | 1 (dog_1)      | 3 (dog_owner)    | mickey     |
  +----------------+------------------+------------+
  | 2 (dog_2)      | 3 (dog_owner)    | shaggy     |
  +----------------+------------------+------------+
  | 3 (dog_3)      | 3 (dog_owner)    | peter      |
  +----------------+------------------+------------+
  | 4 (guy_1)      | 4 (guy_name)     | peter      |
  +----------------+------------------+------------+
  | 5 (guy_2)      | 4 (guy_name)     | shaggy     |
  +----------------+------------------+------------+
  | 6 (guy_3)      | 4 (guy_name)     | mickey     |
  +----------------+------------------+------------+
  | 4 (guy_1)      | 5 (guy_age)      | 40         |
  +----------------+------------------+------------+
  | 5 (guy_2)      | 5 (guy_age)      | 20         |
  +----------------+------------------+------------+
  | 6 (guy_3)      | 5 (guy_age)      | 5          |
  +----------------+------------------+------------+


Handling primary keys
~~~~~~~~~~~~~~~~~~~~~

If a primary key is specified for a resource, then fields in the primary key **are not** mapped to
*parameters* in the database. Consequently, the values of these fields in a given row **are not** mapped to
*parameter values*. Instead, these values are used to compose the name of the *object* mapped by that row.


Example
=======

Let's say we specify a primary key for our 'dog' and 'guy' resources, so that our ``datapackage.json``
looks as follows (irrelevant fields are skipped):

``datapackage.json``::

  {
    "profile": "tabular-data-resource",
    ...
    "resources": [
      "name": "dog",
      ...
      "schema": {
        ...
        "primaryKey": "name"
      },
      "name": "guy",
      ...
      "schema": {
        ...
        "primaryKey": "name"
      }
    ]
  }

So in both cases, the primary key is uniquely composed by the field 'name'.
After conversion, the following content will be in the Spine database (empty fields are not shown):

* **object class**

  +---------+-----------+
  | **id**  | **name**  |
  +---------+-----------+
  | 1       | dog       |
  +---------+-----------+
  | 2       | guy       |
  +---------+-----------+

* **object**

  +---------+---------------+-------------+
  | **id**  | **class_id**  | **name**    |
  +---------+---------------+-------------+
  | 1       | 1 (dog)       | dog_pluto   |
  +---------+---------------+-------------+
  | 2       | 1 (dog)       | dog_scooby  |
  +---------+---------------+-------------+
  | 3       | 1 (dog)       | dog_brian   |
  +---------+---------------+-------------+
  | 4       | 2 (guy)       | guy_peter   |
  +---------+---------------+-------------+
  | 5       | 2 (guy)       | guy_shaggy  |
  +---------+---------------+-------------+
  | 6       | 2 (guy)       | guy_mickey  |
  +---------+---------------+-------------+


* **parameter**

  +---------+----------------------+------------+
  | **id**  | **object_class_id**  | **name**   |
  +---------+----------------------+------------+
  | 1       | 1 (dog)              | dog_breed  |
  +---------+----------------------+------------+
  | 2       | 1 (dog)              | dog_owner  |
  +---------+----------------------+------------+
  | 3       | 2 (guy)              | guy_age    |
  +---------+----------------------+------------+

* **parameter value**

  +-----------------+------------------+------------+
  | **object_id**   | **parameter_id** | **value**  |
  +-----------------+------------------+------------+
  | 1 (dog_pluto)   | 1 (dog_breed)    | bloodhound |
  +-----------------+------------------+------------+
  | 2 (dog_scooby)  | 1 (dog_breed)    | great dane |
  +-----------------+------------------+------------+
  | 3 (dog_brian)   | 1 (dog_breed)    | labrador   |
  +-----------------+------------------+------------+
  | 1 (dog_pluto)   | 2 (dog_owner)    | mickey     |
  +-----------------+------------------+------------+
  | 2 (dog_scooby)  | 2 (dog_owner)    | shaggy     |
  +-----------------+------------------+------------+
  | 3 (dog_brian)   | 2 (dog_owner)    | peter      |
  +-----------------+------------------+------------+
  | 4 (guy_peter)   | 3 (guy_age)      | 40         |
  +-----------------+------------------+------------+
  | 5 (guy_shaggy)  | 3 (guy_age)      | 20         |
  +-----------------+------------------+------------+
  | 6 (guy_mickey)  | 3 (guy_age)      | 5          |
  +-----------------+------------------+------------+


Handling foreign keys
~~~~~~~~~~~~~~~~~~~~~

If foreign keys are specified for a given resource, then fields in any foreign key **are not** mapped to
*parameters* in the database. Instead, these fields are mapped to a *relationship class*, between the
*object classes* mapped by the resource and the reference resources.


Let's say we specify a foreign key for our 'dog' resource, so that our ``datapackage.json``
looks as follows (irrelevant fields are skipped):

``datapackage.json``::

  {
    "profile": "tabular-data-resource",
    ...
    "resources": [
      "name": "dog",
      ...
      "schema": {
        ...
        "foreignKeys": [
          "fields": "owner"
          "reference": {
            "resource": "guy",
            "fields": "name"
          }
        ]
      },
      ...
    ]
  }

So the field 'owner' of 'dog' points to the field 'name' of 'guy'.
After conversion, the following content will be in the Spine database (empty fields are not shown):

* **object class**

  +---------+-----------+
  | **id**  | **name**  |
  +---------+-----------+
  | 1       | dog       |
  +---------+-----------+
  | 2       | guy       |
  +---------+-----------+

* **object**

  +---------+---------------+-------------+
  | **id**  | **class_id**  | **name**    |
  +---------+---------------+-------------+
  | 1       | 1 (dog)       | dog_pluto   |
  +---------+---------------+-------------+
  | 2       | 1 (dog)       | dog_scooby  |
  +---------+---------------+-------------+
  | 3       | 1 (dog)       | dog_brian   |
  +---------+---------------+-------------+
  | 4       | 2 (guy)       | guy_peter   |
  +---------+---------------+-------------+
  | 5       | 2 (guy)       | guy_shaggy  |
  +---------+---------------+-------------+
  | 6       | 2 (guy)       | guy_mickey  |
  +---------+---------------+-------------+

* **relationship_class**

  +--------+---------------+---------------------+----------+
  | **id** | **dimension** | **object_class_id** | **name** |
  +--------+---------------+---------------------+----------+
  | 1      | 1             | 1 (dog)             | dog__guy |
  +--------+---------------+---------------------+----------+
  | 1      | 2             | 2 (guy)             | dog__guy |
  +--------+---------------+---------------------+----------+

* **relationship**

+--------+---------------+----------------+--------------+-------------+
| **id** | **dimension** | **object_id**  | **class_id** | **name**    |
+--------+---------------+----------------+--------------+-------------+
| 1      | 1             | 1 (dog_pluto)  | 1 (dog__guy) | *undefined* |
+--------+---------------+----------------+--------------+-------------+
| 1      | 2             | 6 (guy_mickey) | 1 (dog__guy) | *undefined* |
+--------+---------------+----------------+--------------+-------------+
| 2      | 1             | 2 (dog_scooby) | 1 (dog__guy) | *undefined* |
+--------+---------------+----------------+--------------+-------------+
| 2      | 2             | 5 (guy_shaggy) | 1 (dog__guy) | *undefined* |
+--------+---------------+----------------+--------------+-------------+
| 3      | 1             | 3 (dog_brian)  | 1 (dog__guy) | *undefined* |
+--------+---------------+----------------+--------------+-------------+
| 3      | 2             | 4 (guy_peter)  | 1 (dog__guy) | *undefined* |
+--------+---------------+----------------+--------------+-------------+


* **parameter**

  +---------+----------------------+------------+
  | **id**  | **object_class_id**  | **name**   |
  +---------+----------------------+------------+
  | 1       | 1 (dog)              | dog_breed  |
  +---------+----------------------+------------+
  | 2       | 2 (guy)              | guy_age    |
  +---------+----------------------+------------+

* **parameter value**

  +-----------------+------------------+------------+
  | **object_id**   | **parameter_id** | **value**  |
  +-----------------+------------------+------------+
  | 1 (dog_pluto)   | 1 (dog_breed)    | bloodhound |
  +-----------------+------------------+------------+
  | 2 (dog_scooby)  | 1 (dog_breed)    | great dane |
  +-----------------+------------------+------------+
  | 3 (dog_brian)   | 1 (dog_breed)    | labrador   |
  +-----------------+------------------+------------+
  | 4 (guy_peter)   | 2 (guy_age)      | 40         |
  +-----------------+------------------+------------+
  | 5 (guy_shaggy)  | 2 (guy_age)      | 20         |
  +-----------------+------------------+------------+
  | 6 (guy_mickey)  | 2 (guy_age)      | 5          |
  +-----------------+------------------+------------+
