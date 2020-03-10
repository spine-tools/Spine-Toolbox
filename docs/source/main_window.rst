.. Main Window documentation
   Created 16.1.2019

.. |play-all| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-solid.svg
            :width: 16
.. |play-selected| image:: ../../spinetoolbox/ui/resources/project_item_icons/play-circle-regular.svg
            :width: 16
.. |stop| image:: ../../spinetoolbox/ui/resources/project_item_icons/stop-circle-regular.svg
            :width: 16
.. |trash| image:: ../../spinetoolbox/ui/resources/menu_icons/trash-alt.svg
            :width: 16

***********
Main Window
***********

This section describes the different components in the application main window.

The first time you start the application you will see the main window like this.

.. image:: img/main_window_no_project.png
   :align: center

The application main window contains six dock widgets (*Project*, *Properties*, *Event Log*, *Process Log*, *Julia
Console*, and *Python Console*), a tool bar, a *Design View*, and a menu bar with *File*,
*Edit*, *View*, and *Help* menus. The *Project* dock widget contains a list of project items and Tool specifications
that are available in your project. The *Properties* dock widget shows the properties of the selected project item.
*Event Log* shows messages depending on what you do in Spine Toolbox. *Process Log* shows messages from processes that
are spawned by the application, i.e. it shows the stdout and stderr streams of GAMS, Julia, Python (if Tools are
executed without embedded Julia and Python Consoles, see :ref:`Settings` section), and executable
programs. Julia and Python Consoles provide full iJulia and a iPython consoles. If you choose to execute Julia tools
in the embedded Julia Console, the Julia code will be included into the Julia Console and executed there. You can
interact with the iJulia in the Julia Console like you would with any iJulia you use.

.. tip:: You can configure the Julia and Python versions you want to use in ``File->Settings``.

The menu bar in the top of the application contains *File*, *Edit*, *View*, and *Help* menus. In the *File* menu
you can create a new project, open an existing project, save the project,  upgrade an old project to modern
directory-based project, and open the application Settings among other things.
Spine Toolbox is project based, which means that you need to create
a new project or open an existing one before you can do anything. You can create a new project by selecting
``File->New project...`` from the menu bar. *Drag & Drop Icon* tool bar contains the available
:ref:`project item <Project Items>` types. The |trash| button can be used to remove all items from your project.
The *Execute* icons control the execution of the items in the *Design view* where you build your project.
The |play-all| button executes all Directed-Acyclic Graphs (DAG) in the project in a row. The |play-selected| button
executes the selected project items only. The |stop| button terminates the execution (if running).

You can add a new project item to your project by pointing your mouse cursor on any of the draggable items
in the *Drag & Drop Icon* tool bar, then click-and-drag the item on to the *Design view*.
After this you will be presented a dialog, which asks you to fill in basic information about the new project
item (name, description, etc.).

The main window is very customizable so you can e.g. close the dock widgets that you do not need and/or you can
resize the views to fit your needs and display size or resolution.

.. note:: If you want to restore all dock widgets to their default place use the menu item
   ``View->Dock Widgets->Restore Dock Widgets``.
   This will show all hidden dock widgets and restore them to the main window.

Below is an example on how you can customize the main window. In the picture, a user has created a project *My First
Project*, and created one project item from each of the six categories. A Data Store called *Database*, a Data
Connection called *Data files*, A Tool called *Julia model*, a View called *View*, an Importer called *Mapper*,
and an Exporter called *Exporter*. The project items are also listed in the *Project* dock widget.

.. image:: img/main_window_my_first_project_six_project_items.png
   :align: center
