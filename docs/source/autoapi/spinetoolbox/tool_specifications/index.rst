:mod:`spinetoolbox.tool_specifications`
=======================================

.. py:module:: spinetoolbox.tool_specifications

.. autoapi-nested-parse::

   Contains Tool specification classes.

   :authors: P. Savolainen (VTT), E. Rinne (VTT), M. Marin (KTH)
   :date:   24.1.2018



Module Contents
---------------

.. data:: CMDLINE_TAG_EDGE
   :annotation: = @@

   

.. py:class:: CmdlineTag

   .. attribute:: URL
      

      

   .. attribute:: URL_INPUTS
      

      

   .. attribute:: URL_OUTPUTS
      

      

   .. attribute:: OPTIONAL_INPUTS
      

      


.. py:class:: ToolSpecification(name, tooltype, path, includes, settings, logger, description=None, inputfiles=None, inputfiles_opt=None, outputfiles=None, cmdline_args=None, execute_in_work=True)

   Bases: :class:`spinetoolbox.metaobject.MetaObject`

   Super class for all tool specifications.

   :param name: Name of the tool
   :type name: str
   :param tooltype: Type of Tool (e.g. Python, Julia, ..)
   :type tooltype: str
   :param path: Path to tool
   :type path: str
   :param includes: List of files belonging to the tool specification (relative to 'path')
   :type includes: list
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: a logger instance
   :type logger: LoggerInterface
   :param description: Description of the Tool specification
   :type description: str
   :param inputfiles: List of required data files
   :type inputfiles: list
   :param inputfiles_opt: List of optional data files (wildcards may be used)
   :type inputfiles_opt: list, optional
   :param outputfiles: List of output files (wildcards may be used)
   :type outputfiles: list, optional
   :param cmdline_args: Tool command line arguments (read from tool definition file)
   :type cmdline_args: str, optional
   :param execute_in_work: Execute in work folder
   :type execute_in_work: bool

   .. method:: set_return_code(self, code, description)


      Sets a return code and an associated text description for the tool specification.

      :param code: Return code
      :type code: int
      :param description: Description
      :type description: str


   .. method:: set_def_path(self, path)


      Sets the file path for this tool specification.

      :param path: Absolute path to the specification file.
      :type path: str


   .. method:: get_def_path(self)


      Returns tool specification file path.


   .. method:: check_definition(data, logger)
      :staticmethod:


      Checks that a tool specification contains
      the required keys and that it is in correct format.

      :param data: Tool specification
      :type data: dict
      :param logger: A logger instance
      :type logger: LoggerInterface

      :returns: Dictionary or None if there was a problem in the tool definition.


   .. method:: get_cmdline_args(self, optional_input_files, input_urls, output_urls)


      Returns tool specification's command line args as list.

      Replaces special tags in arguments:

      - @@optional_inputs@@ expands to a space-separated list of Tool's optional input files
      - @@url:<Data Store name>@@ expands to the URL provided by a named data store
      - @@url_inputs@@ expands to a space-separated list of Tool's input database URLs
      - @@url_outputs@@ expands to a space-separated list of Tool's output database URLs

      :param optional_input_files: a list of Tool's optional input file names
      :type optional_input_files: list
      :param input_urls: a mapping from URL provider (input Data Store name) to URL string
      :type input_urls: dict
      :param output_urls: a mapping from URL provider (output Data Store name) to URL string
      :type output_urls: dict

      :returns: a list of expanded command line arguments
      :rtype: list


   .. method:: create_tool_instance(self, basedir)
      :abstractmethod:


      Returns an instance of the tool specification configured to run in the given directory.
      Needs to be implemented in subclasses.

      :param basedir: Path to directory where the instance will run
      :type basedir: str


   .. method:: split_cmdline_args(arg_string)
      :staticmethod:


      Splits a string of command line into a list of tokens.

      Things in single ('') and double ("") quotes are kept as single tokens
      while the quotes themselves are stripped away.
      Thus, `--file="a long quoted 'file' name.txt` becomes ["--file=a long quoted 'file' name.txt"]

      :param arg_string: command line arguments as a string
      :type arg_string: str

      :returns: a list of tokens
      :rtype: list


   .. method:: _expand_tags(args, optional_input_files, input_urls, output_urls)
      :staticmethod:


      "
      Expands first @@ tags found in given list of command line arguments.

      :param args: a list of command line arguments
      :type args: list
      :param optional_input_files: a list of Tool's optional input file names
      :type optional_input_files: list
      :param input_urls: a mapping from URL provider (input Data Store name) to URL string
      :type input_urls: dict
      :param output_urls: a mapping from URL provider (output Data Store name) to URL string
      :type output_urls: dict

      :returns:

                a boolean flag, if True, indicates that tags were expanded and a list of
                    expanded command line arguments
      :rtype: tuple



.. py:class:: GAMSTool(name, tooltype, path, includes, settings, logger, description=None, inputfiles=None, inputfiles_opt=None, outputfiles=None, cmdline_args=None, execute_in_work=True)

   Bases: :class:`spinetoolbox.tool_specifications.ToolSpecification`

   Class for GAMS tool specifications.

   :param name: GAMS Tool name
   :type name: str
   :param tooltype: Tool specification type
   :type tooltype: str
   :param path: Path to model main file
   :type path: str
   :param includes: List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
   :type includes: list
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: a logger instance
   :type logger: LoggerInterface
   :param First file in the list is the main GAMS program.:
   :param description: GAMS Tool description
   :type description: str
   :param inputfiles: List of required data files
   :type inputfiles: list
   :param inputfiles_opt: List of optional data files (wildcards may be used)
   :type inputfiles_opt: list, optional
   :param outputfiles: List of output files (wildcards may be used)
   :type outputfiles: list, optional
   :param cmdline_args: GAMS tool command line arguments (read from tool definition file)
   :type cmdline_args: str, optional

   .. method:: __repr__(self)


      [OBSOLETE]. Returns instance of this class as a string.


   .. method:: update_gams_options(self, key, value)


      [OBSOLETE?] Updates GAMS command line options. Only 'cerr and 'logoption' keywords supported.

      :param key: Option name
      :type key: str
      :param value: Option value
      :type value: int, float


   .. method:: load(path, data, settings, logger)
      :staticmethod:


      Creates a GAMSTool according to a tool specification file.

      :param path: Base path to tool files
      :type path: str
      :param data: Dictionary of tool definitions
      :type data: dict
      :param settings: Toolbox settings
      :type settings: QSettings
      :param logger: A logger instance
      :type logger: LoggerInterface

      :returns: GAMSTool instance or None if there was a problem in the tool specification file.


   .. method:: create_tool_instance(self, basedir)


      Returns an instance of this tool specification that is configured to run in the given directory.

      :param basedir: the path to the directory where the instance will run
      :type basedir: str



.. py:class:: JuliaTool(toolbox, name, tooltype, path, includes, settings, logger, description=None, inputfiles=None, inputfiles_opt=None, outputfiles=None, cmdline_args=None, execute_in_work=True)

   Bases: :class:`spinetoolbox.tool_specifications.ToolSpecification`

   Class for Julia tool specifications.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param name: Julia Tool name
   :type name: str
   :param tooltype: Tool specification type
   :type tooltype: str
   :param path: Path to model main file
   :type path: str
   :param includes: List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
   :type includes: list
   :param First file in the list is the main Julia program.:
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: A logger instance
   :type logger: LoggerInterface
   :param description: Julia Tool description
   :type description: str
   :param inputfiles: List of required data files
   :type inputfiles: list
   :param inputfiles_opt: List of optional data files (wildcards may be used)
   :type inputfiles_opt: list, optional
   :param outputfiles: List of output files (wildcards may be used)
   :type outputfiles: list, optional
   :param cmdline_args: Julia tool command line arguments (read from tool definition file)
   :type cmdline_args: str, optional

   .. method:: __repr__(self)


      [OBSOLETE]. Returns instance of this class as a string.


   .. method:: update_julia_options(self, key, value)


      [OBSOLETE?] Updates Julia command line options.

      :param key: Option name
      :type key: str
      :param value: Option value
      :type value: int, float


   .. method:: load(toolbox, path, data, settings, logger)
      :staticmethod:


      Creates a JuliaTool according to a tool specification file.

      :param toolbox: QMainWindow instance
      :type toolbox: ToolboxUI
      :param path: Base path to tool files
      :type path: str
      :param data: Dictionary of tool definitions
      :type data: dict
      :param settings: Toolbox settings
      :type settings: QSetting
      :param logger: A logger instance
      :type logger: LoggerInterface

      :returns: JuliaTool instance or None if there was a problem in the tool definition file.


   .. method:: create_tool_instance(self, basedir)


      Returns an instance of this tool specification that is configured to run in the given directory.

      :param basedir: the path to the directory where the instance will run
      :type basedir: str



.. py:class:: PythonTool(toolbox, name, tooltype, path, includes, settings, logger, description=None, inputfiles=None, inputfiles_opt=None, outputfiles=None, cmdline_args=None, execute_in_work=True)

   Bases: :class:`spinetoolbox.tool_specifications.ToolSpecification`

   Class for Python tool specifications.

   :param toolbox: QMainWindow instance
   :type toolbox: ToolboxUI
   :param name: Python Tool name
   :type name: str
   :param tooltype: Tool specification type
   :type tooltype: str
   :param path: Path to model main file
   :type path: str
   :param includes: List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
   :type includes: list
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: A logger instance
   :type logger: LoggerInterface
   :param First file in the list is the main Python program.:
   :param description: Python Tool description
   :type description: str
   :param inputfiles: List of required data files
   :type inputfiles: list
   :param inputfiles_opt: List of optional data files (wildcards may be used)
   :type inputfiles_opt: list, optional
   :param outputfiles: List of output files (wildcards may be used)
   :type outputfiles: list, optional
   :param cmdline_args: Python tool command line arguments (read from tool definition file)
   :type cmdline_args: str, optional

   .. method:: __repr__(self)


      [OBSOLETE]. Returns instance of this class as a string.


   .. method:: update_python_options(self, key, value)


      [OBSOLETE?] Updates Python command line options.

      :param key: Option name
      :type key: str
      :param value: Option value
      :type value: int, float


   .. method:: load(toolbox, path, data, settings, logger)
      :staticmethod:


      Creates a PythonTool according to a tool specification file.

      :param toolbox: Toolbox main window
      :type toolbox: ToolboxUI
      :param path: Base path to tool files
      :type path: str
      :param data: Dictionary of tool definitions
      :type data: dict
      :param settings: Toolbox settings
      :type settings: QSettings
      :param logger: A logger instance
      :type logger: LoggerInterface

      :returns: PythonTool instance or None if there was a problem in the tool definition file.


   .. method:: create_tool_instance(self, basedir)


      Returns an instance of this tool specification that is configured to run in the given directory.

      :param basedir: the path to the directory where the instance will run
      :type basedir: str



.. py:class:: ExecutableTool(name, tooltype, path, includes, settings, logger, description=None, inputfiles=None, inputfiles_opt=None, outputfiles=None, cmdline_args=None, execute_in_work=True)

   Bases: :class:`spinetoolbox.tool_specifications.ToolSpecification`

   Class for Executable tool specifications.

   :param name: Tool name
   :type name: str
   :param tooltype: Tool specification type
   :type tooltype: str
   :param path: Path to main script file
   :type path: str
   :param includes: List of files belonging to the tool (relative to 'path').  # TODO: Change to src_files
   :type includes: list
   :param First file in the list is the main script file.:
   :param settings: Toolbox settings
   :type settings: QSettings
   :param logger: A logger instance
   :type logger: LoggerInterface
   :param description: Tool description
   :type description: str
   :param inputfiles: List of required data files
   :type inputfiles: list
   :param inputfiles_opt: List of optional data files (wildcards may be used)
   :type inputfiles_opt: list, optional
   :param outputfiles: List of output files (wildcards may be used)
   :type outputfiles: list, optional
   :param cmdline_args: Tool command line arguments (read from tool definition file)
   :type cmdline_args: str, optional

   .. method:: __repr__(self)


      [OBSOLETE]. Returns instance of this class as a string.


   .. method:: load(path, data, settings, logger)
      :staticmethod:


      Creates an ExecutableTool according to a tool specification file.

      :param path: Base path to tool files
      :type path: str
      :param data: Tool specification
      :type data: dict
      :param settings: Toolbox settings
      :type settings: QSettings
      :param logger: A logger instance
      :type logger: LoggerInterface

      :returns: ExecutableTool instance or None if there was a problem in the tool specification.


   .. method:: create_tool_instance(self, basedir)


      Returns an instance of this tool specification that is configured to run in the given directory.

      :param basedir: the path to the directory where the instance will run
      :type basedir: str



