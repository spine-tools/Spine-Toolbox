:mod:`spinetoolbox.project_upgrader`
====================================

.. py:module:: spinetoolbox.project_upgrader

.. autoapi-nested-parse::

   Contains ProjectUpgrader class used in upgrading and converting projects
   and project dicts from earlier versions to the latest version.

   :authors: P. Savolainen (VTT)
   :date:   8.11.2019



Module Contents
---------------

.. py:class:: ProjectUpgrader(toolbox)

   Class to upgrade/convert projects from earlier versions to the current version.

   :param toolbox: toolbox of this project
   :type toolbox: ToolboxUI

   .. method:: is_valid(self, p)


      Checks that the given project JSON dictionary contains
      a valid version 1 Spine Toolbox project. Valid meaning, that
      it contains all required keys and values are of the correct
      type.

      :param p: Project information JSON
      :type p: dict

      :returns: True if project is a valid version 1 project, False if it is not
      :rtype: bool


   .. method:: upgrade(self, project_dict, old_project_dir, new_project_dir)


      Converts the project described in given project description file to the latest version.

      :param project_dict: Full path to project description file, ie. .proj or .json
      :type project_dict: dict
      :param old_project_dir: Path to the original project directory
      :type old_project_dir: str
      :param new_project_dir: New project directory
      :type new_project_dir: str

      :returns: Latest version of the project info dictionary
      :rtype: dict


   .. method:: upgrade_to_latest(v, project_dict)
      :staticmethod:


      Upgrades the given project dictionary to the latest version.

      NOTE: Implement this when the structure of the project file needs
      to be changed.

      :param v: project version
      :type v: int
      :param project_dict: Project JSON to be converted
      :type project_dict: dict

      :returns: Upgraded project information JSON
      :rtype: dict


   .. method:: upgrade_from_no_version_to_version_1(self, old, old_project_dir, new_project_dir)


      Converts project information dictionaries without 'version' to version 1.

      :param old: Project information JSON
      :type old: dict
      :param old_project_dir: Path to old project directory
      :type old_project_dir: str
      :param new_project_dir: Path to new project directory
      :type new_project_dir: str

      :returns: Project information JSON upgraded to version 1
      :rtype: dict


   .. method:: upgrade_connections(self, item_names, connections_old)


      Upgrades connections from old format to the new format.

      - Old format. List of lists, e.g.

      .. code-block::

          [
              [False, False, ["right", "left"], False],
              [False, ["bottom", "left"], False, False],
              ...
          ]

      - New format. List of dicts, e.g.

      .. code-block::

          [
              {"from": ["DC1", "right"], "to": ["Tool1", "left"]},
              ...
          ]


   .. method:: upgrade_tool_specification_paths(spec_paths, old_project_dir)
      :staticmethod:


      Upgrades a list of tool specifications paths to new format.
      Paths in (old) project directory (yes, old is correct) are converted
      to relative, others as absolute.


   .. method:: open_proj_json(self, proj_file_path)


      Opens an old style project file (.proj) for reading,

      :param proj_file_path: Full path to the old .proj project file
      :type proj_file_path: str

      :returns: Upgraded project information JSON or None if the operation failed
      :rtype: dict


   .. method:: get_project_directory(self)


      Asks the user to select a new project directory. If the selected directory
      is already a Spine Toolbox project directory, asks if overwrite is ok. Used
      when opening a project from an old style project file (.proj).

      :returns: Path to project directory or an empty string if operation is canceled.
      :rtype: str


   .. method:: copy_data(self, proj_file_path, project_dir)


      Copies project item directories from the old project to the new project directory.

      :param proj_file_path: Path to .proj file
      :type proj_file_path: str
      :param project_dir: New project directory
      :type project_dir: str

      :returns: True if copying succeeded, False if it failed
      :rtype: bool



