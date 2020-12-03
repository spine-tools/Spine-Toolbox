.. _Project item development:

Project item development
========================

This document discusses the structure of :ref:`project items<Project Items>`,
how they interact with the Toolbox GUI and how they are executed.

The core of every project item consists of two classes:
a *static* project item class which is a subclass of :class:`spinetoolbox.project_item.ProjectItem`
and an *executable*, a subclass of :class:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase`.
The static item is responsible for integrating the item with the Toolbox while
its executable counterpart exists only during execution.

Additional classes are needed to fully define a project item:

* :class:`spinetoolbox.project_item.ProjectItemFactory` assists Toolbox in constructing project items.
* Toolbox needs to know an item's type and category. This is achieved by
  :class:`spinetoolbox.project_item_info.ProjectItemInfo`
* The item's Design view icon is inherited from :class:`spinetoolbox.graphics_items.ProjectItemIcon`.
* Properties tab widget and other UI widgets are needed to change the item's settings.
* An *add project item* widget is used by Toolbox right after a new item has been created.
  Some project items use the general purpose
  :class:`spinetoolbox.widgets.add_project_item_widget.AddProjectItemWidget`
  while others may use more specialized widgets.
* Items that support specifications need
  :class:`spinetoolbox.project_item_specification_factory.ProjectItemSpecificationFactory`

Getting started
---------------

Probably the most convenient way to start developing a new project item is to work with a copy of some simple
project item. For example, **View** provides a nice starting point.

Project item packages
---------------------

Project items are mostly self-contained Python packages.
Toolbox expects certain modules to exist in the package:

* ``__init__.py`` which contains an ``ItemFactory`` class which must be a subclass of
  :class:`spinetoolbox.project_item.ProjectItemFactory` and an ``ItemInfo`` class which must be a subclass of
  :class:`spinetoolbox.project_item_info.ProjectItemInfo`
* ``executable_item.py`` which contains an ``ExecutableItem`` class, a subclass of
  :class:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase`
* optional for items that support specifications: ``specification_factory.py`` which contains a ``SpecificationFactory``
  class, a subclass of :class:`spinetoolbox.project_item_specification_factory.ProjectItemSpecificationFactory`

It is customary to structure the project item packages like the Toolbox itself: ``mvcmodels`` submodule for Qt's
models, ``ui`` module for automatically generated UI forms and ``widgets`` for the widget's business logic.

Item info
---------

:class:`spinetoolbox.project_item_info.ProjectItemInfo` is used by Toolbox to query two important pieces of knowledge
from a project item: *type* and *category*. Type identifies the project item while category is used
by the Toolbox GUI to group project items with similar function.

Categories are predefined by Toolbox. Currently available categories are: *Data Connections*, *Data Stores*,
*Importers*, *Exporters*, *Manipulators*, *Tools* and *Views*.

Executable item
---------------

Usually, most of project item's code is for setting up the item via Toolbox GUI and for integrating the
item into the Design View. The code that is run during execution by Spine Engine, the *executble item*,
is usually contained in a single class which must be a subclass of
:class:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase`.

Executable items live in a separate environment to the rest of the project item. They are constructed
by the Toolbox only during execution and mainly interact with Spine Engine. As such, the executable items
are expected to not use any GUI code or have any interaction with users.

One common aspect between executable items and 'static' project items (subclasses of
:class:`spinetoolbox.project_item.ProjectItem`) are resources. However,
executable items cannot pass ``transient_file`` type resources since all file URLs need to point to
existing files during execution.

Factories
---------

Toolbox utilizes :class:`spinetoolbox.project_item.ProjectItemFactory` to instantiate new project items
in the Design View. For this purpose, the class provides methods to create an icon to show in Toolbox toolbar,
an *add item dialog*, an icon to show on the Design view (a subclass of
:class:`spinetoolbox.graphics_items.ProjectItemIcon`), construct the project item itself,
and some methods to deal with items that support specifications.

Specifications
--------------

Project item specifications are template or predefined configurations for certain tasks. For example, a tool might have
a specification which defines input files, command line parameters and other settings for running a specific model
generator. Specifications are an opt-in feature and project items need to implement the corresponding methods
in :class:`spinetoolbox.project_item.ProjectItemFactory` such that Toolbox knows the item supports them.

Toolbox GUI integration
-----------------------

Toolbox shows a project item's icon which it gets from the item factory's
:func:`spinetoolbox.project_item.ProjectItemFactory.icon` method on the toolbar. The method returns an URL to the
icon's resource in Toolbox' resources. Items that support specifications may get their icon in the specifications
toolbar as well, if a proper specification has been added to the project.

After dragging and dropping a project item from the toolbar onto the design view, Toolbox calls
:func:`spinetoolbox.project_item.ProjectItemFactory.make_icon` to construct the item on the design view. This icon
is a subclass of :class:`spinetoolbox.graphics_items.ProjectItemIcon`. To prompt the user for the new item's name
and optionally other initial properties, Toolbox shows the Add item dialog it gets from
:func:`spinetoolbox.project_item.ProjectItemFactory.make_add_item_widget`

Once the item is on the design view, the main interaction with it goes through the properties tab which is created
by :func:`spinetoolbox.project_item.ProjectItemFactory.make_properties_widget`. The properties tab widget should have
all the needed controls to set up the item.

Every time a DAG on the design view changes, Toolbox calls
:func:`spinetoolbox.project_item.ProjectItem._do_handle_dag_changed` on the affected items. This method should be
reimplemented to update the project item and check its status, e.g. if all required inputs are available. Issues can
be reported by :func:`spinetoolbox.project_item.ProjectItem.add_notification` and the notification cleared by
:func:`spinetoolbox.project_item.ProjectItem.clear_notifications`

Saving and restoring project items
----------------------------------

Project items are saved in JSON format as part of the `project.json` file. Item saving is handled by
:func:`spinetoolbox.project_item.ProjectItem.item_dict` which should return a JSON compatible ``dict`` and
contain at least the information in the ``dict`` returned by the base class method.

File system paths are handled specifically during saving: all paths outside the project directory should be absolute
while the paths in the project directory should be relative. This is to enable self-contained projects which include
all needed files and can be easily transferred from system to system. As such, paths are saved as special dictionaries.
:func:`spinetoolbox.helpers.serialize_path`, :func:`spinetoolbox.helpers.serialize_url` and
:func:`spinetoolbox.helpers.deserialize_path` help with dealing with the paths.

:func:`spinetoolbox.project_item.ProjectItem.from_dict` is responsible for reconstructing a save project item
from the dictionary. :func:`spinetoolbox.project_item.ProjectItem.parse_item_dict` can be utilized to deserialize
the basic data needed by the base class.

Passing data between items: resources
-------------------------------------

Project items share data by files or via databases. One item writes a file which is then read by another item.
*Project item resources* are used to communicate the URLs of these files and databases.

Resources are instances of the :class:`spinetoolbox.project_item_resource.ProjectItemResource` class.

Both static items and their executable counterparts pass resources.
The major difference is that static item's may pass resource *promises*
such as files that are generated during the execution.
The full path to the promised files or even their final names may not be known until the items are executed.

During execution resources are propagated only to item's *direct* predecessors and successors.
Static items offer their resources to direct successors only.
Resources that are communicated to successor items are basically output files
that the successor items can use for input.
Currently, the only resource that is propagated to predecessor items is database URLs by Data Store project items.
As Data Stores leave the responsibility of writing to the database to other items
it has to tell these items where to write their output data.

The table below lists the resources each project item type provides during execution.

+-----------------+-------+-------------------------+----------------------------+
| Item            | Notes | Provides to predecessor | Provides to successor      |
+=================+=======+=========================+============================+
| Data Connection | [#]_  | n/a                     | File URLs                  |
+-----------------+-------+-------------------------+----------------------------+
| Data Store      | [#]_  | Database URL            | Database URL               |
+-----------------+-------+-------------------------+----------------------------+
| GdxExporter     |       | n/a                     | File URLs                  |
+-----------------+-------+-------------------------+----------------------------+
| Gimlet          |       | n/a                     | Resources from predecessor |
+-----------------+-------+-------------------------+----------------------------+
| Importer        |       | n/a                     | n/a                        |
+-----------------+-------+-------------------------+----------------------------+
| Tool            | [#]_  | n/a                     | File URLs                  |
+-----------------+-------+-------------------------+----------------------------+
| View            |       | n/a                     | n/a                        |
+-----------------+-------+-------------------------+----------------------------+

.. [#] Data connection provides paths to local files.
.. [#] Data Store provides a database URL to direct successors and predecessors. Note, that this is the
   only project item that provides resources to it's predecessors.
.. [#] Tool's output files are specified by a *Tool specification*.

The table below lists the resources that might be used by each item type during execution.

+-----------------+-------+---------------------------+------------------------+
| Item            | Notes | Accepts from predecessor  | Accepts from successor |
+=================+=======+===========================+========================+
| Data Connection |       | n/a                       | n/a                    |
+-----------------+-------+---------------------------+------------------------+
| Data Store      |       | n/a                       | n/a                    |
+-----------------+-------+---------------------------+------------------------+
| GdxExporter     |       | Database URL              | n/a                    |
+-----------------+-------+---------------------------+------------------------+
| Gimlet          | [#]_  | File URLs, database URLs  | Database URLs          |
+-----------------+-------+---------------------------+------------------------+
| Importer        | [#]_  | File URLs                 | Database URL           |
+-----------------+-------+---------------------------+------------------------+
| Tool            | [#]_  | File URLs, database URLs  | Database URLs          |
+-----------------+-------+---------------------------+------------------------+
| View            |       | Database URLs             | n/a                    |
+-----------------+-------+---------------------------+------------------------+

.. [#] Gimlet's resources can be passed to the command as command line arguments but are otherwise ignored.
.. [#] Importer requires a database URL from its successor for writing the mapped data.
   This can be provided by a Data Store.
.. [#] *Tool specification* specifies tool's optional and required input files.
   Database URLs can be passed to the tool *program* via command line arguments but are
   otherwise ignored by the Tool project item. Currently, there is no mechanism to know if a URL is
   actually required by a tool *program*. For more information, see :ref:`Tool specification editor`.


Execution
---------

The executable counterparts for project items in a DAG are created before execution.
The current settings of each item are passed to the executable
which is then sent to Spine Engine for execution.

The DAG is executed in two phases: first backwards then forwards.
During backward execution, the DAG is executed in an inverted order
and resources are propagated to direct predecessors.
No current project item actually executes any other code besides storing these resources for later use.
Forward execution is when the project items do their actions.

When executing in either direction:

#. :func:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase.execute` is invoked with a list of available resources
   and current execution direction.
#. The resources returned by :func:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase.output_resources` are
   accumulated and passed to the ``execute()`` of the successor item.

The ``execute()`` method further delegates the execution to the overridable
:func:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase._execute_forward` and
:func:`spinetoolbox.project_item.executable_item_base.ExecutableItemBase._execute_backward` methods.
Similarly, ``output_resources()`` calls the
:func:`spinetoolbox_project_item.executable_item_base.ExecutableItemBase._output_resources_forward` and
:func:`spinetoolbox_project_item.executable_item_base.ExecutableItemBase._output_resources_backward` methods.

The executable items need additional properties to function.
The table below lists the properties for each item.
Basically, these are the arguments that are provided to each executable's ``__init__`` method.

+-----------------+-------+--------------------------+
| Item            | Notes | Properties               |
+=================+=======+==========================+
| Data Connection | [#]_  | File references          |
+                 +-------+--------------------------+
|                 | [#]_  | Data files               |
+-----------------+-------+--------------------------+
| Data Store      |       | Database URL             |
+-----------------+-------+--------------------------+
| Gimlet          |       | Shell name               |
+                 +-------+--------------------------+
|                 | [#]_  | Command                  |
+                 +-------+--------------------------+
|                 |       | Work directory           |
+                 +-------+--------------------------+
|                 |       | Data files               |
+-----------------+-------+--------------------------+
| GdxExporter     |       | Export settings          |
+                 +-------+--------------------------+
|                 |       | Output directory         |
+                 +-------+--------------------------+
|                 | [#]_  | GAMS system directory    |
+                 +-------+--------------------------+
|                 | [#]_  | Cancel on error flag     |
+-----------------+-------+--------------------------+
| Importer        |       | Mapping settings         |
+                 +-------+--------------------------+
|                 |       | Log directory            |
+                 +-------+--------------------------+
|                 | [#]_  | Python system directory  |
+                 +-------+--------------------------+
|                 | [#]_  | GAMS system directory    |
+                 +-------+--------------------------+
|                 | [#]_  | Cancel on error flag     |
+-----------------+-------+--------------------------+
| Tool            |       | Work directory           |
+                 +-------+--------------------------+
|                 |       | Output directory         |
+                 +-------+--------------------------+
|                 |       | Tool specification       |
+                 +-------+--------------------------+
|                 |       | Command line arguments   |
+-----------------+-------+--------------------------+
| View            |       | n/a                      |
+-----------------+-------+--------------------------+

.. [#] A flag indicating if the combine database operation should stop when an error is encountered.
.. [#] Path to files which can be anywhere in the file system.
.. [#] Files which reside in the item's data directory.
.. [#] Including command line arguments.
.. [#] Path to the directory which contains a GAMS installation.
   Required to find the libraries needed for writing ``.gdx`` files.
.. [#] Path to the directory which contains a Python installation.
   Required to run the import operation in a separate process.
.. [#] Path to the directory which contains a GAMS installation.
   Required to find the libraries needed for reading ``.gdx`` files.
.. [#] A flag indicating if the export operation should stop when an error is encountered.
.. [#] A flag indicating if the import operation should stop when an error is encountered.
