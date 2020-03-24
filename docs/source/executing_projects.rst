.. Executing Projects documentation
   Created 16.1.2019

.. _Executing Projects:

.. |play-all| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-solid.svg
            :width: 16
.. |play-selected| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-regular.svg
            :width: 16

******************
Executing Projects
******************

This section describes how executing a project works and what resources are passed between project
items at execution time. Execution happens by pressing the |play-all|
(Execute project) or the |play-selected| (Execute selection) buttons in the main window tool bar.
A project consists of project items and connections (yellow arrows) that are visualized on the
*Design View*. You use the project items and the connections to build a **Directed Acyclic Graph
(DAG)**, with the project items as *nodes* and the connections as *edges*. A DAG is traversed using
the **breadth-first-search** algorithm.

Rules of DAGs:

1. A single project item with no connections is a DAG.
2. All project items that are connected, are considered as a single DAG (no matter, which
   direction the arrows go). If there is a path between two items, they are considered as belonging
   to the same DAG.
3. Loops are not allowed (this is what acyclic means).

You can connect the nodes in the *Design View* how ever you want but you cannot execute the resulting
DAGs if they break the rules above. Here is an example project with three DAGs.

.. image:: img/example_dags.png
   :align: center

- DAG 1: items: a, b, c, d. connections: a-b, a-c, b-d, c-d
- DAG 2: items: e, f. connections: e-f
- DAG 3: items: g. connections: None

When you press the |play-all| button, all three DAGs are executed in a row. You can see the progress
and the current executed item in the *Event Log*. Execution order of DAG 1 is *a->b->c->d* or
*a->c->b->d* since items b and c are **siblings**. DAG 2 execution order is *e->f* and DAG 3 is just
*g*. If you have a DAG in your project that breaks the rules above, that DAG is skipped and the
execution continues with the next DAG.

We use the words **predecessor** and **successor** to refer to project items that are upstream or
dowstream from a project item. **Direct predecessor** is a project item that is the immediate predecessor.
**Direct Successor** is a project item that is the immediate successor. For example, in DAG 1 above, the
successors of *a* are project items *b*, *c* and *d*. The direct successor of *b* is *d*. The
predecessor of *b* is *a*, which is also its direct predecessor.

You can also execute only the selected parts of a project by multi-selecting the items you want to
execute and pressing the |play-selected| button in the tool bar. For example, to execute only items
*b*, *d* and *f*, select the items in *Design View* or in the project item list in *Project* dock
widget and then press the |play-selected| button.

.. tip::
   You can select multiple project items by pressing the Ctrl-button down and clicking on
   desired items.


Passing Resources between Project Items
=======================================

All project items are visited when a DAG is executed but the actual processing only happens when a
Tool, an Importer, or an Exporter project item is visited. The processing is done in a subprocess, in
order to not clog the GUI until the project item has been executed.

When project items are connected to each other, the resources that are passed between project items at
execution depends on the project item type. The following table describes the resources that project
items use from their predecessors and what resources are passed to their successors.

.. note::
   Resources are only transmitted to **direct successors** and **direct predecessors**.

+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
| Type            | Notes | Accepts from predecessor  | Accepts from successor | Provides to predecessor | Provides to successor | Properties               |
+=================+=======+===========================+========================+=========================+=======================+==========================+
| Data Connection | 1     | n/a                       | n/a                    | n/a                     | File URLs             | File paths               |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
| Data Store      | 2     | n/a                       | n/a                    | Database URL            | Database URL          | Database URL             |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
| Exporter        |       | Database URL              | n/a                    | n/a                     | File URLs             | Export settings          |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
| Importer        | 3     | File URLs                 | Database URL           | n/a                     | n/a                   | Import mappings          |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
| Tool            | 4     | File URLs, database URLs  | Database URLs          | n/a                     | File URLs             | Tool specification,      |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
|                 |       |                           |                        |                         |                       | cmd line arguments,      |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
|                 |       |                           |                        |                         |                       | execute in work dir      |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+
| View            |       | Database URLs             | n/a                    | n/a                     | n/a                   | n/a                      |
+-----------------+-------+---------------------------+------------------------+-------------------------+-----------------------+--------------------------+

Notes:

1. Data connection provides paths to local files.
2. Data Store provides a database URL to direct successors and predecessors. Note, that this is the
   only project item that provides resources to it's predecessor.
3. Importer requires a database URL from its successor for writing the mapped data. This can be
   provided by a Data Store.
4. Tool *program* is defined by its *Tool specification*, which also contains the required files,
   optional files, and output files of the *program*. The output files are provided to successors as
   file URLs. Database URLs can be passed to the tool *program* via command line arguments but are
   otherwise ignored by the Tool project item. Currently, there is no mechanism to know if an URL is
   actually required by a tool *program*. For more information, see :ref:`Tool specification editor`.
5. The **Properties** column describes the resources that the user is expected to set for each project
   item in Spine Toolbox.

To learn more about Project items and their responsibilities, please see :ref:`Project Items`.

Example DAG
===========

When you have created at least one Tool specification, you can execute a Tool as part of the DAG. The
Tool specification defines the process that is depicted by the Tool project item. As an example, below
we have two project items; *Julia Model* Tool and *Data File* Data Connection connected to each other.

.. image:: img/execution_julia_tool_selected.png
   :align: center

Selecting the *Julia Model* shows its properties in the *Properties* dock widget. In the top of the Tool
Properties, there is a specification drop-down menu. From this drop-down menu, you can select the Tool specification
for this particular Tool item. The *Julia Model Specification* tool specification has been selected for the Tool
*Julia Model*. Below the drop-down menu, you can see the details of the Tool specification, command line arguments,
Source files (the first one is the main program file), Input files, Optional input files and Output files.
*Results...* button opens the Tool's result archive directory in the File Explorer (all Tools have their own result
directory). The *Execute in* radio buttons control, whether this Tool is first copied to a work directory and executed
there, or if the execution should happen in the source directory where the main program file is located.

When you click on the |play-all| button, the execution starts from the *Data File* Data Connection. When executed,
Data Connection items *advertise* their files and references to project items that are in the same DAG and
executed after them. In this particular example, the *Data File* item contains a file called *data.csv* as depicted
in the picture below.

.. image:: img/execution_data_connection_selected.png
   :align: center

When it's the *Julia Model* tools turn to be executed, it checks if it finds the file *data.csv* from project items,
that have already been executed. When the DAG is set up like this, the Tool finds the input file that it requires
and then starts processing the Tool specification starting with the main program file *script.jl*. Note that if the
connection would be the other way around (from *Julia Model* to *Data File*) execution would start from the
*Julia Model* and it would fail because it cannot find the required file *data.csv*. The same thing happens if there
is no connection between the two project items. In this case the project items would be in separate DAGs.

Since the Tool specification type was set as *Julia* and the main program is a Julia script, Spine Toolbox starts the
execution in the Julia Console (if you have selected this in the application *Settings*, See :ref:`Settings` section).

Tool execution algorithm
========================
The below figure depicts what happens when a Tool item with a valid Tool specification is executed.

.. image:: img/execution_algorithm.png
   :align: center
