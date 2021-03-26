# Changelog
All **notable** changes to this project are documented here.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [Unreleased]

### Added
- Support for Experimental Spine Engine. This can be enabled in app Settings->General tab. Experimental 
  engine provides the latest in-development features (e.g. parallel/multicore processing, etc.).
- New project item: Data Transformer. Can be used to configure Spine database filters for successor items.
  Currently, it supports renaming entity classes.
- Support for version 3 Spine Toolbox projects and an automatic upgrade of version 2 projects to version 3.
- Support for version 4 Spine Toolbox projects.
- Support for version 5 Spine Toolbox projects.
- Support for version 6 Spine Toolbox projects.
- Support to create sysimages for Julia tools.
- New requirement: jill, for installing Julia.
- The SpineOpt configuration assistant has been moved from File->Configuration assistants,
  to File->Settings->Tools->Julia, and renamed to SpineOpt Installer.
- New wizard to install Julia, accessible from File->Settings->Tools->Julia.
- New Exporter project item, a general-purpose tabular data exporter. The old .gdx exporter has been
  renamed to GdxExporter.
- File->Close project option
- Support for Python 3.8

### Changed
- Project Item (Tool, Data Store, Importer, etc.) code has been removed from Spine Toolbox. 
  Project Items are now in a separate package called spine_items, which is upgraded at Spine 
  Toolbox's startup. 
- Importer item now applies the same mapping to all input files. If the user needs to apply different 
  mappings, they need to create different Importers. The specification can be shared using the json file.
- Exporter is now called GdxExporter.

### Deprecated

### Removed
- Combiner project item. The same functionality can be achieved by connecting a Data Store to another Data Store.
- Upgrade support for original (.proj file based) Spine Toolbox projects.
- Python 3.6 is no longer supported.

### Fixed
### Security

##[0.5.0-final.1] - 2020-02-03

### Added
- Tutorial for case study A5 in the documentation

### Fixed
- [win-x64] Fixed /tools/python.exe by adding sitecustomize.py and a missing python37.dll

## [0.5.0-final.0] - 2020-12-14

### Added
- Exporting graphs as PDF files from the *Graph* menu in the Data Store form.
- Pruning entire classes from the graph view. The option is available both from the *Graph* menu and
  from *Entity Graph* context menus. Also, pruned items can be restored gradually.
- A new Input type *Indexed parameter expansion* is now available in Data Store view's Pivot table.
  In this Input type the indexes, e.g. time stamps of time series get expanded as a new dimension in the table.
- Import editor now has a new Source type: Table name. It can be used e.g. to pick an Excel sheet's
  or GAMS domain's name as the object class name.
- Import editor now supports multidimensional maps. The number of dimensions can be set using the 
  *Map dimensions* spin box in mappings options.
- Executing a project from the command line without opening the Toolbox GUI (i.e. headless execution).
  The headless execution is enabled by the new command line option ``--execute-only``.
- Toolbox now supports scenarios and alternatives. They can be accessed via Data store view's new Alternative tree.
- New Project Item: Gimlet. Can be used to run any command as part of the workflow 
  with or without a shell. Supported shells at the moment are cmd and powershell for 
  Windows and bash for other OS's.
- Python and Julia Kernel spec Editor. Provides the means to make new kernel specs for Python Console and Julia 
  Console without leaving Spine Toolbox. Kernel (spec) Editor can be found in Settings->Tools tab.
- [win-x64] Includes Tools/python.exe for running Python Tools for systems that do not have a Python installation.
  Also, pyvenv.cfg and path.pth files for configuring the included python.exe.

### Fixed
- Signal disconnection issue in Graph View
- Bugs in removing objects and object classes in Spine db editor's Graph View

### Changed
- Data Store Form is now called 'Spine database editor'
- Spine db editor Graph View behavior. Now selecting objects in the object tree not only shows those objects but also 
  all the cascading relationships. One can still go back to the previous behavior in Settings.
- Moving object items in the graph view also causes relationship icons to follow. This behavior can be disabled in the
  Settings.
- Required PySide2 version is now 5.14. The version is checked at startup.
- Indexed parameter handling has been overhauled in Exporter allowing parameters to share indexing domains.
  **Note**: Due to numerous changes in the backend, Exporters in old project files will not load properly
  and need to be re-configured.
- The way Exporter handles missing parameter values and None values has changed. The item now ignores missing
  values instead of replacing them by the default value. Further, there is a new option to replace None values by
  the default value and another option to replace Nones by not-a-numbers or skip exporting them.
- The numerical indicator on the upper left corner of project items no longer indicates the execution order for
  each individual item because the exact order is not know before the Execute button is actually clicked.
  The number still indicates the execution order but may show the same numbers for items in different parallel
  branches.
- Project.json file format has been upgraded to version 2. Version 1 project.json files are upgraded to version 2
  automatically when a project is opened.
- Default Python interpreter is now {sys.executable} i.e. the one that was used in launching the app.
  This affects the Python used by Python Tool specifications and the PyCall used by SpineOpt.jl configuration 
  assistant.
- [win-x64] Default Python interpreter is the Python in user's PATH if available. If Python is not defined in
  user's PATH, the default Python interpreter is the <app_install_dir>/Tools/python.exe.
- User's now need to explicitly choose the kernel specs for the Python Console and the Julia Console. They are 
  not chosen (nor created) automatically anymore. The kernel specs can be selected in the drop-down menus 
  in application Settings->Tools.
- Database revision handling has been improved. Id est, the app does not offer to upgrade databases 
  that are more recent than the current version of Spine Toolbox can handle.
- Links to User Guide and Getting Started documents open only the online versions. The docs have been 
  published on readthedocs.org.
- Clearing the line edits for Julia executable and Python Interpreter (in Settings->Tools) shows
  the full paths to their respective files as placeholder text.

### Deprecated
- CustomQtKernelManager class

### Removed
- python_repl_widget.py
- julia_repl_widget.py

## [0.4.0-final.0] - 2020-04-03

### Added
- A small notification icon is painted next to project items in the design view whenever they 
  are missing some configuration. Hovering the icon shows tips for completing the 
  configuration.
- A small icon is painted next to the project items in the design view to show the order in 
  which they will be executed
- Main Window menu 'File -> Open recent'. Shortcut for opening a recent project.
- A new project item *Exporter* allows a database contained in a *Data Store* to be exported 
  as GAMS `.gdx` file.
- It is now possible to copy and paste project items for example between projects.
- It is now possible to duplicate project items.
- Changes made in the tree view are also seen in the graph view and viceversa.
- New Setting: *Sticky selection in Graph View*. Enables users to select if they want to use 
  multi-selection or single selection in the Graph view Object tree when selecting items with 
  the **left-mouse button**.
- Projects can be saved to any directory
- Project name can be changed in Settings
- The graph view features a short live demonstration that new users can follow to discover 
  the basic functionality.
- New Setting: *Curved links*. When active, links on the Design View follow a smooth curve 
  rather than a straight line.
- When execution traverses a link, a small animation is played to denote the flow of data. 
  Users can set how quick they want this animation to be in Settings. The fastest setting 
  effectively disables the animation.
- Special 'tag' command line arguments are now available in Tool Specification which expand 
  to, for example, input database URLS or paths to optional input files when a Tool is executed.
- It is now possible to undo/redo database changes in the Data Store form.
- It is now possible to visualize the history of database changes in the Data Store form. The 
  option is available in the Session menu.
- Support for Tool command line arguments. You can now give Tool (project item) command line 
  arguments in addition to Tool Specification command line arguments.
- Undo/Redo in Design View
- It is now possible to add new plots to existing plot windows in Data Store View.
- Objects in Data Store's Tree View are sorted alphabetically
- A new parameter value type, *map* has been added. There is now a dedicated editor to 
  modify maps. Plotting of non-nested maps is supported, as well.
- [win-x64] importer_program.py has been built as an independent application. This program is 
  now distributed with the Spine Toolbox single-file installer. When installing Spine Toolbox,
  the Importer Program app can be found in the Spine Toolbox install directory 
  (/importer_program).
- Import preview window now supports copy-pasting mappings and options from a source table to 
  another
- Import preview window header context-menus for the preview table which, allows users to 
  change all data types at once.
- Provide data for EditRole for nicer editor experience in MappingSpecModel.
- Red background is displayed for invalid values in MappingSpecModel
- Object tooltips now show the descriptions Data Store view's

### Fixed
- Data advertised by a project item during execution is only accessible by its direct 
  successors. In other words, resources are passed to the next items in line but not beyond.
- [win-x64] Executing the Importer project item has been fixed on Windows release version
- Bug fixes for Data Store View
  - Disappearing object names in entity graph
  - Spine db manager error dialogs
- Tool configuration assistant for SpineModel.jl
- [win-x64] A problem with displaying special characters in Process Log when executing the 
  Importer project item.
- The context menu in Graph view's pivot table resulted in a traceback when an entity class 
  did not have parameter definitions.
- Combobox delegate in Import preview window had wrong list of choices.
- Don't set mapping to NoneMapping if user gives a None value.
- Exporter now also exports empty object classes and empty parameters into GDX files
- A bug that sometimes made duplicate entries to File->Open recents menu
- Bug where an Excel import with empty rows would return a None in it's get_data_iterator
- [win-x64] Executing Julia tools in the embedded Julia Console
- [win-x64] Setting up Python Console. Installing ipykernel and kernel specs now works.
- [win-x64] Setting up Julia Console. Installing IJulia and kernel specs now works.
- Column indexing in Import Editor. When entering a time or time pattern index column 
  manually in Import Editor's lower right corner table, the colors in the preview table 
  failed to update. This should fix the bug and allow column selection both by column index 
  or column header text.

### Changed
- spinetoolbox is now a Python package. To start the app, use command 
  `python -m spinetoolbox` or `python spinetoolbox.py` as spinetoolbox.py has been moved to 
  repository root. 
- Tool templates are now called Tool specifications
- File->Open Project opens a file dialog, where you can open projects by selecting an old 
  <project_name>.proj file or a Spine Toolbox Project directory. Valid Spine Toolbox projects 
  are decorated with the Spine logo.
- Old style projects (.proj files) cannot be opened anymore. The old style projects need to 
  be upgraded before opening. You can upgrade your .proj file projects into new ones with 
  *Project Upgrade Wizard* found in `File->Upgrade project` menu item.
- Project information is not saved to a <project_name>.proj file anymore. This information 
  is now located in file <project_dir>/.spinetoolbox/project.json. Every Spine Toolbox project 
  has this file.
- Work directory is now a global setting instead of a project setting
- Renamed *Data Interface* project item to *Importer*. The corresponding category 
  *Data Importers* was renamed to *Importers*.
- Tree, graph, and tabular views have been merged into one consolidated view. You can choose 
  your preferred style from the Data Store View's `View` menu.
- The graph view behavior has changed. Now selecting objects in the object tree not only 
  shows those objects but also all the cascading relationships. This is to facilitate exploring 
  the system without a previous knowledge.
- importer_program.py now uses the Python interpreter that the app was started with and not 
  the one that is given by user in Settings -> Tools.
- Importer now uses QProcessExecutionManager for running the importer_program.py

### Removed
- The status bar of the Data store view is gone. Instead, notifications are printed in a box 
  on the right side of the form.
- Saving project information to .proj files is not happening anymore

## [0.3] - 2019-09-06

### Added
- Welcome message including a link to Getting Started guide.
- Zooming (by using the mouse wheel) is now enabled in Design View. You can also select multiple project.
  items by pressing the Ctrl-key down and dragging the mouse.
- New project item icons on Design View.
- Two options for the Design View background (grid or solid). See Settings (F1).
- Python Console (menu View -> Dock Widgets -> Python Console).
- Python interpreter can be selected in Settings (Also Python 2.7 supported).
- Support for Python Tool templates
- Python Tool execution using the command line approach.
- Python Tool execution using the embedded Python Console (checkbox in Settings)
- The Data Store treeview now also has a relationship tree.
- Support for reordering columns in the treeview.
- Selecting 'edit object classes' in the treeview now also allows the icon to be selected.
- Play button to main window Toolbar that executes all Directed Acyclic Graphs in the Project one after another.
- Another Play button to main window Toolbar to execute selected Directed Acyclic Graph. Selecting a DAG happens by
  selecting one or more project items belonging to the wanted DAG in the Design View or in Project Items list.
- Stop button to main window Toolbar, which terminates execution.
- Possibility to specify a dedicated Julia project or environment for Spine Toolbox in the settings.
- Feature to Export project to GraphML format. Each graph in Design View is written to its own file. To do this, just
  select *Export project to GraphML* from the Project Item list context-menu or from *File ->
  Export project to GraphML*.
- New project item: *Data Interface*
- Parameter and relationship parameter values can now be edited in a dedicated editor window in Tree, Graph and Tabular
  views. The editor is accessible by right-clicking a value and selecting `Open in editor...`.
- It is now possible to plot parameter and relationship parameter values in Tree, Graph and Tabular views.

### Fixed
- There is now an upper limit on how much text is logged in Event Log and Process Log. The oldest lines are removed
  if the limit is exceeded. This fixes a problem with excessive memory usage when running long processes.
- Mouse click problems in Design View
- Mouse cursor problem in Tool Configuration Assistant
- Welcome message is now shown for first time users
- NameError: SpineDBAPIError when executing Data Stores.
- .py files in *spinedb_api\alembic\versions* are now copied to the installation bundle without compiling them to
  .pyc files first. Also, if there's a previous version installed, *spinedb_api\alembic* directory is deleted
  before installation begins [Win-x64].
- Added missing modules from *spinedb_api\alembic\versions* package into installation bundle [Win-x64].
- *numpy* is now deleted before installation begins so installing over an existing installation of Spine Toolbox
  works again [Win-x64].
- *packaging* and *appdirs* packages are now included in the installation bundle [Win-x64].

### Changed
- Selecting the Julia environment in Settings now requires picking the Julia interpreter **file**
  (e.g. julia.exe on Windows) instead of the directory where the Julia interpreter is located.
- Selecting the GAMS program (**file**) in Settings now requires picking the GAMS program (e.g. gams.exe
  on Windows) instead of the directory where the GAMS program is located.
- All application Settings are now saved using Qt's QSettings class. Old configuration file,
  *conf/settings.conf* file has been removed.
- New Spine databases can be created in any backend supported by spinedb_api. The Data Store item properties
  have been changed to allow for this.
- Executing Directed Acyclic Graphs instead of just Tools.
- Executing project items does not happen from the Tool Properties anymore. It happens instead by pressing the
  Play button in the main window Toolbar.

### Removed
- An unnecessary error dialog in Import Preview widget.
- ConfigurationParser class in configuration.py.
- Execute button in Tool Properties.
- Stop button in Tool Properties.
- Console window that opened in addition to the application window is not shown anymore [Win-x64].

## [0.2] - 2019-01-17

### Added
- New Setting. You can now select whether to delete project item's data directory
  when removing a project item.
- Graph View is also available from Data Store items, allowing to insert new
  relationships more graphically.
- You can now execute Tools in the work directory or the source directory (where the
  main program file is located). The Setting is in the Tool template editor and in Tool
  properties.
- Tabular view: New view for Data Store items, allowing to view and edit data in a
  pivot table.
- Tool Properties now shows all information about the attached Tool template
- Context-menus for Data Connection Properties, Tool Properties, and View Properties
- Support for optional input files for Tool templates. You can now use Unix style wildcards (`*` and `?`)
  to specify the optional files that a Tool may exploit, e.g. `*.csv`.
- Wildcard support for Tool template output files
- Tool template output files now support subdirectories
- You can now create a new (blank) main program file in the Tool template editor by pressing the the *+* button
  and selecting `Make new main program`
- A shortcut to Tool template main directory, accessible e.g. in Tool Properties context-menu
- New Setting. You can select whether the zoom in the Graph view is smooth or discrete
- Windows installer default location is /Program Files/SpineToolbox/. When new versions are released, the
  installer will automatically upgrade Spine Toolbox to a new version in that directory.
- Support for executing Executable type tools in Linux&Mac. (Windows support was added previously)
- Tool configuration assistant. Available in menu `File->Tool configuration assistant`. Checks automatically
  if the Julia you have selected in Settings supports running Spine Model. If not, the required packages are
  automatically installed.

### Fixed
- Better support for scaling screen resolutions
- Exporting a datapackage to Spine format failed if datapackage.json was not explicitly saved

### Changed
- Importing items with names into a spinedatabase moved to spinedatabase_api to
  allow for easier adding of new import formats in future versions.
- Tool template list is now located in the Project dock widget below the list of Project items
- New look for Spine Datapackage editor

### Removed
- Templates tab in `Project` dock widget.

## [0.1.75] - 2018-11-23

### Added
- New Setting (F1). You can now select whether to delete project item's data
  directory when removing a project item.
- Application icon (Spine symbol)
- New installer for 64-bit Windows:
    - Installation file extension is now *.exe* instead of *.msi*
    - Show license file before installation (users must agree to continue)
    - Default install folder is now `C:\Program Files\ `.
    - **No** need to *Run as Administrator* even if installed to the default location
    because write permissions for sub-folders that need them (\conf, \projects,
    \work) are set automatically
    - Create a shortcut on desktop (if wanted)
    - Create a Start Menu folder (if wanted)
    - Uninstaller. Available in the Start Menu folder or in Windows
    Add/Remove Programs
    - Remove app related registry entries when uninstalling (if wanted)

### Fixed
- Data Package editor. Some files were missing from the tabulator package.
- Bug when exiting the app when there is no project open in close_view_forms() when
  exiting the application without a project open

### Changed
- settings.conf file is now in /conf directory

## [0.1.71] - 2018-11-19

### Added
- Added PyMySQL package, which was missing from the previous release
- Improved Graph View for the View project item (work in progress)

### Changed
- Some main window components have been renamed
    - Main view is now called *Design View*
    - Julia REPL is now called *Julia Console*
    - Subprocess Output is now called *Process Log*
    - Project item info window is now called *Properties*

## [0.1.7] - 2018-11-01

### Added
- New option to refresh the data store tree view and get latest changes from the database.
- Several performance enhancements in tree view form (accessing internal data more efficiently,
  optimizing queries to the database.)
- Now the data store tree view offers to commit pending changes at exit.
- Better support for batch operations in data store tree view.
- data store tree view can be fully operated by using the keyboard.
- New options to edit object tree items in the data store tree view, including changing the objects involved
  in a relationship.
- The dialogs to add/edit tree view items are not closed in case of an error, so the user can adjust their choices
  and try again.
- Stop button now terminates tool execution.
- New context menu options to fully expand and collapse object tree items in the data store tree view.
- The autofilter in the data store tree view now also filters work in progress rows.
- In the Data store item controls, the path to the SQLite file can be specified by dropping a file.
- Parameter and parameter value tables in the data store tree view now have an empty row at the end,
  which can be used to enter data more easily.
- JSON data can be visualized and edited more easily in the data store tree view.
- Tools can now execute (Windows) batch files and other executables (.exe). Linux support pending.
- About Qt dialog added to Help menu

### Fixed
- Clicking on the open treeview button while the data store tree view is open now raises it, rather than opening a
  second one.
- Work folder is not created for Tools if the Tool template requirements are not met.
- Result folder is not created if the Tool template fails to start.
- The embedded Julia REPL now uses the Julia that is given in application Settings (F1).
  Previously, this used the default Julia of your OS.

### Removed
- Connections tab has been removed (actually, it is just hidden and can be restored with a keyboard shortcut)
- Refresh Tools button on Templates tab has been removed as it was not needed anymore
- Set Debug message level in Settings has been removed

## [0.1.5] - 2018-09-28

### Added
- Advanced copy/pasting and multiple selection support for the data store tree view.
- Import data from Excel files into the data store tree view.
- Export Spine database from the data store tree view into an Excel file.
- Save at exit prompt.
- Import data from datapackage into the data store tree view.
- Restore Dock Widgets in the main window.
- Parameter tables can be filtered by clicking on their headings in the data store tree view.
- Parameter and parameter values are added and edited directly in the data store tree view,
  without need for an additional dialog.
- On-the-fly creation of necessary relationships when entering parameters in data store tree view.
- View item feature for visualizing networks from a Spine database. A view item can visualize databases
  from all data store items connected to it.
- Packages numpy, scipy, and matplotlib are now mandatory requirements.
- Drag files between data connections. File items can be dragged from the references and data lists.
  Data connection items can be selected by hovering them while dragging a file. Dropping files onto a Data Connection
  item copies them to its data directory.
- datapackage.json files in data connections are now opened with the Spine datapackage form. This is a dedicated
  interface to prepare the datapackage for importing in the data store tree view.
- The data store tree view does not lock the database when there are uncommitted changes anymore.

### Changed
- Changed DBAPI package mysqlclient (GPL license, not good) to pymysql (MIT license, good)
- spinedatabase_api is not included in Spine Toolbox repository anymore. It is a required
  package from now on.
- Data Store item can have only one database, not many. When opening a project created with a
  previous version, the first database in the list of saved references will be loaded for each Data Store.
- In the data store tree view, the object tree presents all relationship classes at the same level,
  regardless of how many object classes are involved. The same applies for relationships and objects.
- In the data store tree view, the relationship parameter value view now has different columns for each object
  in the relationship.

## [0.1] - 2018-08-20

### Added
- Basic functionality
