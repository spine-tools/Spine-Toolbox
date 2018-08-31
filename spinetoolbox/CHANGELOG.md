# Changelog
All **notable** changes to this project will be documented in this file from v0.1 onwards.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## [Unreleased]
This section is for upcoming changes. This serves two purposes:
1. People can see what changes they might expect in upcoming releases
2. At release time, Unreleased section changes can be moved into a new release version section

### Added (for new features)
- Advanced copy/pasting support for the treeview
- Import data from Excel files into the treeview
- Export treeview into an Excel file
- Tool-Tool interface
- Widget for viewing the code of Tool templates
- Undo-redo functionality for the main view
- Add metadata to database commits (v0.3)
- Visualize database commit history (v0.3)

### Fixed (for bug fixes)

### Changed (for changes in existing functionality)
- Changed DBAPI package mysqlclient (GPL license, not good) to pymysql (MIT license, good)
- spinedatabase_api is not included in Spine Toolbox repository anymore. It is a required 
package from now on. 
### Deprecated (for soon-to-be removed features)

### Removed (for now removed features)
- Connections tab on the main window is useless and should be removed.

### Security (in case of vulnerabilities)

## [0.1] - 2018-08-20
### Added
- Basic functionality
