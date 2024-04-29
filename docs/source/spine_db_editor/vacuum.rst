
.. |broom| image:: ../../../spinetoolbox/ui/resources/menu_icons/broom.svg
            :width: 16

.. _vacuum:

Vacuum
======

Vacuuming is available for Spine Databases in the SQLite format. Basically it tries to free up some unnecessary
memory from the ``.sqlite`` -file. If you have very large databases, it might be beneficial to vacuum it once in a while.
More detailed explanation on what vacuuming does to the SQLite database can be found
`here <https://www.sqlite.org/lang_vacuum.html>`_.

To vacuum a database, either press the |broom| Vacuum -button from the Data Store **Properties** -panel, or
straight from the Spine Database Editors hamburger menu **Edit->Vacuum**.

After the vacuum is finished, a message informing the amount of bytes freed from the database is shown.
