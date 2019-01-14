# Changelog
All **notable** changes to this project are documented here.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [Unreleased]
This section is for upcoming changes.

### Added
- New Setting (F1). You can now select whether to delete project item's data directory
when removing a project item.
- Graph View is also available from Data Store items, allowing to insert new 
relationships more graphically.
- You can now execute Tools in the work directory or the source directory (where the 
main program file is located). The setting is in the Tool template editor and in Tool 
properties.
- Tool properties now shows the Tool template main program file and the optional input
files
- Tabular view: New view for Data Store items, allowing to view and edit data in a
pivot table.

### Fixed
- Tool template optional input files. You can now use Unix style wildcards (`*` and `?`) 
to specify the optional files that a Tool may exploit, e.g. `*.csv`.
- Better support for scaling screen resolutions

### Changed
- Importing items with names into a spinedatabase moved to spinedatabase_api to
allow for easier adding of new import formats in future verisions.

### Deprecated

### Removed

### Security

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
