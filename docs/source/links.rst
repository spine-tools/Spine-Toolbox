.. Links documentation
   Created 28.6.2023

.. |play-all| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-solid.svg
            :width: 16
.. |play-selected| image:: ../../spinetoolbox/ui/resources/menu_icons/play-circle-regular.svg
            :width: 16
.. |stop| image:: ../../spinetoolbox/ui/resources/menu_icons/stop-circle-regular.svg
            :width: 16

.. _Links:

*****
Links
*****

Links are the things that connect project items to each other. If Tool is the heart of a DAG, then
links are the veins that connect the heart to other vital organs.

Creating a new link between items is simple. First you need to select any of the connector slots on the item where
you want the link to originate form. Then select any connector slot on the item that you
want to connect to. There are no limitations for how many links one connector slot can have.
Like items, links can also have properties, depending on the types of items that
they are connecting. When a link is selected, these properties can be modified in the **Properties** dock widget.

The small bubble icons in a link represent the state of the link's properties. When an icon is blue, the
corresponding selection is active in the **Properties** dock widget.

Data Store as Source
--------------------

Below is an example of what the **Properties** dock widget can look like when a link originating from a Data Store
is selected:

.. image:: img/DB_Tool_link_properties.png
   :align: center

`DB resource filters` is divided into `Scenario` and `Tool filters`. With the scenario filters, you can select which
scenarios to include in the execution. The `Tool filter` lets you choose which tools specified in the database are active.
The `Check new filters automatically` option allows you to choose whether new `Scenario` and `Tool filters` added to the
database should be automatically selected in this specific link. `Filter validation` allows you to force that at least
one `Scenario` and/or `Tool filter` is selected at all times in that specific link.

Data Store as Destination
-------------------------

In the image below, the selected link ends in a Data Store. Because of this,
the available selections in **Properties** differ from the previous image.

.. image:: img/Tool_DB_link_properties.png
   :align: center

Now the link has no filters, but the write index and other various database related options become available.

**Write index** controls which items write to the database first.
Smaller indices take precedence over larger ones
while items with the same index write in an undefined order.

**Purge before writing** option purges the target Data Store before write operations.
Click on **Settings...** to set up which items to purge.

.. warning:: This purge has no undo available.

Using Memory Databases
----------------------

**Use memory DB for Tool execution** allows using a temporary in-memory database while executing a Tool which may
speed up execution if the Tool accesses the database a lot.

.. _Setting up datapackages in Links:

Packing CSV files into datapackage
----------------------------------

When the source item may provide output files, the **Pack CSV files (as datapackage.json)** option becomes enabled.
This option may be handy when an item provides a lot of CSV files that e.g. need to imported into a Data Store.
Checking this options does two things:

- A ``datapackage.json`` file is created in the common parent directory of all CSV files the source item provides.
  This file defines a datapackage that consists of the CSV files.
- The destination item receives only the ``datapackage.json`` file instead of any CSV files from the source item.

See `the datapackage specification <https://specs.frictionlessdata.io/data-package/>`_
for more information on datapackages.
