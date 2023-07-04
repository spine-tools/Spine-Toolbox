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
you want the link to originate form. Then to create the link just select any connector slot on the item that you
want to connect to the first one. There are no limitations for how many links one connector slot can have.
Like items, links can also have properties, depending on the types of items that
they are connecting. When a link is selected, these properties can be modified in the **Properties** dock widget.
Below is an example of what the **Properties** dock widget can look like between a Data Store and a Tool:

.. image:: img/DB_Tool_link_properties.png
   :align: center

`DB resource filters` is divided into `Scenario`- and `Tool filters`. With the scenario filters, you can select which
scenarios to include in the execution. The `Tool filter` lets you choose which tools specified in the database are active.
The `Check new filters automatically` -option allows you to choose whether new `scenario`- and `Tool filters` added to the
database should be automatically selected in this specific link. `Filter validation` allows you to force that at least
one `scenario`- and/or `Tool filter` is selected at all times in that specific link.

In the image underneath the link is facing from a Tool into a Data Store. Because of this, the available selections
in **Properties** differ from the previous image.

.. image:: img/Tool_DB_link_properties.png
   :align: center

Now the link doesn't have filters, but the write index and other various database related options become available.
The small bubble icons in a link represent the state of the link's properties. When an icon is blue, it means that the
corresponding selection is active in the **Properties** dock widget.