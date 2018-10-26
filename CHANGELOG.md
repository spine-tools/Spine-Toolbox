# Changelog
All **notable** changes to this project will be documented in this file from v0.1 onwards.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [Unreleased]
This section is for upcoming changes.

### Added
- New option to refresh the Data store form and get latest changes from the database.
- Several performance enhancements in Data store form (accessing internal data more efficiently,
optimizing queries to the database.)
- Now the Data store form offers to commit pending changes at exit.
- Better support for batch operations in Data store form.
- Data store form can be fully operated by using the keyboard.
- New options to edit items in the object tree view, including changing the objects involved in a relationship.
- The dialogs to add/edit tree view items are not closed in case there's an error in the user choices.
In this way you can correct your work and try again.
- Stop button now terminates tool execution.
- New context menu options to fully expand and collapse object tree items in the Data store form.
- The autofilter in the Data store form now can also filter work in progress rows.
- In the Data store item controls, the path to the Sqlite file can be specified by dropping a file.

### Fixed
- Clicking on the open treeview button while the Data store form is open now raises it, rather than opening a
second one.

### Changed

### Deprecated

### Removed
- Connections tab has been removed (actually, it is just hidden and can be restored with a keyboard shortcut)
- Refresh Tools button on Templates tab has been removed as it was not needed anymore
- Set Debug message level in Settings has been removed
 
### Security

## [0.1.5] - 2018-09-28

### Added
- Advanced copy/pasting and multiple selection support for the Data store form.
- Import data from Excel files into the Data store form.
- Export Spine database from the Data store form into an Excel file.
- Save at exit prompt.
- Import data from datapackage into the Data store form.
- Restore Dock Widgets in the main window.
- Parameter tables can be filtered by clicking on their headings in the Data store form.
- Parameter and parameter values are added and edited directly in the Data store form,
without need for an additional dialog.
- On-the-fly creation of necessary relationships when entering parameters in Data store form.
- View item feature for visualizing networks from a Spine database. A view item can visualize databases
from all data store items connected to it.
- Packages numpy, scipy, and matplotlib are now mandatory requirements.
- Drag files between data connections. File items can be dragged from the references and data lists.
Data connection items can be selected by hovering them while dragging a file. Dropping files onto a Data Connection
item copies them to its data directory.
- datapackage.json files in data connections are now opened with the Spine datapackage form. This is a dedicated
interface to prepare the datapackage for importing in the Data store form.
- The Data store form does not lock the database when there are uncommitted changes anymore.

### Changed
- Changed DBAPI package mysqlclient (GPL license, not good) to pymysql (MIT license, good)
- spinedatabase_api is not included in Spine Toolbox repository anymore. It is a required
package from now on.
- Data Store item can have only one database, not many. When opening a project created with a
previous version, the first database in the list of saved references will be loaded for each Data Store.
- In the Data store form, the object tree view presents all relationship classes at the same level,
regardless of how many object classes are involved. The same applies for relationships and objects.
- In the Data Store form, the relationship parameter value view now has different columns for each object
in the relationship.

## [0.1] - 2018-08-20

### Added
- Basic functionality
