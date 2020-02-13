:mod:`spinetoolbox.helpers`
===========================

.. py:module:: spinetoolbox.helpers

.. autoapi-nested-parse::

   General helper functions and classes.

   :authors: P. Savolainen (VTT)
   :date:   10.1.2018



Module Contents
---------------

.. function:: set_taskbar_icon()

   Set application icon to Windows taskbar.


.. function:: supported_img_formats()

   Function to check if reading .ico files is supported.


.. function:: pyside2_version_check()

   Check that PySide2 version is older than 5.12, since this is not supported yet.
   Issue #238 in GitLab.

   qt_version is the Qt version used to compile PySide2 as string. E.g. "5.11.2"
   qt_version_info is a tuple with each version component of Qt used to compile PySide2. E.g. (5, 11, 2)


.. function:: spinedb_api_version_check()

   Check if spinedb_api is the correct version and explain how to upgrade if it is not.


.. function:: spine_engine_version_check()

   Check if spine engine package is the correct version and explain how to upgrade if it is not.


.. function:: busy_effect(func)

   Decorator to change the mouse cursor to 'busy' while a function is processed.

   :param func: Decorated function.


.. function:: get_datetime(show, date=True)

   Returns date and time string for appending into Event Log messages.

   :param show: True returns date and time string. False returns empty string.
   :type show: bool
   :param date: Whether or not the date should be included in the result
   :type date: bool


.. function:: create_dir(base_path, folder='', verbosity=False)

   Create (input/output) directories recursively.

   :param base_path: Absolute path to wanted dir
   :type base_path: str
   :param folder: (Optional) Folder name. Usually short name of item.
   :type folder: str
   :param verbosity: True prints a message that tells if the directory already existed or if it was created.
   :type verbosity: bool

   :returns: True if directory already exists or if it was created successfully.

   :raises OSError if operation failed.:


.. function:: create_output_dir_timestamp()

   Creates a new timestamp string that is used as Tool output
   directory.

   :returns: Timestamp string or empty string if failed.


.. function:: copy_files(src_dir, dst_dir, includes=None, excludes=None)

   Function for copying files. Does not copy folders.

   :param src_dir: Source directory
   :type src_dir: str
   :param dst_dir: Destination directory
   :type dst_dir: str
   :param includes: Included files (wildcards accepted)
   :type includes: list
   :param excludes: Excluded files (wildcards accepted)
   :type excludes: list

   :returns: Number of files copied
   :rtype: count (int)


.. function:: erase_dir(path, verbosity=False)

   Deletes a directory and all its contents without prompt.

   :param path: Path to directory
   :type path: str
   :param verbosity: Print logging messages or not
   :type verbosity: bool


.. function:: copy_dir(widget, src_dir, dst_dir)

   Makes a copy of a directory. All files and folders are copied.
   Destination directory must not exist. Does not overwrite files.

   :param widget: Parent widget for QMessageBoxes
   :type widget: QWidget
   :param src_dir: Absolute path to directory that will be copied
   :type src_dir: str
   :param dst_dir: Absolute path to new directory
   :type dst_dir: str


.. function:: recursive_overwrite(widget, src, dst, ignore=None, silent=True)

   Copies everything from source directory to destination directory recursively.
   Overwrites existing files.

   :param widget: Enables e.g. printing to Event Log
   :type widget: QWidget
   :param src: Source directory
   :type src: str
   :param dst: Destination directory
   :type dst: str
   :param ignore: Ignore function
   :param silent: If False, messages are sent to Event Log, If True, copying is done in silence
   :type silent: bool


.. function:: rename_dir(old_dir, new_dir, logger)

   Rename directory. Note: This is not used in renaming projects due to unreliability.
   Looks like it works fine in renaming project items though.

   :param old_dir: Absolute path to directory that will be renamed
   :type old_dir: str
   :param new_dir: Absolute path to new directory
   :type new_dir: str
   :param logger: A logger instance
   :type logger: LoggerInterface


.. function:: fix_name_ambiguity(input_list, offset=0)

   Modify repeated entries in name list by appending an increasing integer.


.. function:: tuple_itemgetter(itemgetter_func, num_indexes)

   Change output of itemgetter to always be a tuple even for one index


.. function:: format_string_list(str_list)

   Return an unordered html list with all elements in str_list.
   Intended to print error logs as returned by spinedb_api.

   :param str_list:
   :type str_list: list(str)


.. function:: rows_to_row_count_tuples(rows)

   Breaks a list of rows into a list of (row, count) tuples corresponding
   to chunks of successive rows.


.. function:: inverted(input_)

   Inverts a dictionary that maps keys to a list of values.
   The output maps values to a list of keys that include the value in the input.


.. py:class:: Singleton

   Bases: :class:`type`

   A singleton class from SO.

   .. attribute:: _instances
      

      

   .. method:: __call__(cls, *args, **kwargs)




.. py:class:: IconListManager(icon_size)

   A class to manage icons for icon list widgets.

   .. method:: init_model(self)


      Init model that can be used to display all icons in a list.


   .. method:: _model_data(self, index, role)


      Replacement method for model.data().
      Create pixmaps as they're requested by the data() method, to reduce loading time.


   .. method:: create_object_pixmap(self, display_icon)


      Create and return a pixmap corresponding to display_icon.



.. py:class:: IconManager

   A class to manage object class icons for data store forms.

   .. attribute:: ICON_SIZE
      

      

   .. method:: create_object_pixmap(self, display_icon)


      Create a pixmap corresponding to display_icon, cache it, and return it.


   .. method:: setup_object_pixmaps(self, object_classes)


      Called after adding or updating object classes.
      Create the corresponding object pixmaps and clear obsolete entries
      from the relationship class icon cache.


   .. method:: object_pixmap(self, object_class_name)


      A pixmap for the given object class.


   .. method:: object_icon(self, object_class_name)


      An icon for the given object class.


   .. method:: relationship_pixmap(self, str_object_class_name_list)


      A pixmap for the given object class name list,
      created by rendering several object pixmaps next to each other.


   .. method:: relationship_icon(self, str_object_class_name_list)


      An icon for the given object class name list.



.. py:class:: CharIconEngine(char, color)

   Bases: :class:`PySide2.QtGui.QIconEngine`

   Specialization of QIconEngine used to draw font-based icons.

   .. method:: paint(self, painter, rect, mode=None, state=None)



   .. method:: pixmap(self, size, mode=None, state=None)




.. function:: make_icon_id(icon_code, color_code)

   Take icon and color codes, and return equivalent integer.


.. function:: interpret_icon_id(display_icon)

   Take a display icon integer and return an equivalent tuple of icon and color code.


.. function:: default_icon_id()


.. py:class:: ProjectDirectoryIconProvider

   Bases: :class:`PySide2.QtWidgets.QFileIconProvider`

   QFileIconProvider that provides a Spine icon to the
   Open Project Dialog when a Spine Toolbox project
   directory is encountered.

   .. method:: icon(self, info)


      Returns an icon for the file described by info.

      :param info: File (or directory) info
      :type info: QFileInfo

      :returns: Icon for a file system resource with the given info
      :rtype: QIcon



.. function:: path_in_dir(path, directory)

   Returns True if the given path is in the given directory.


.. function:: serialize_path(path, project_dir)

   Returns a dict representation of the given path.

   If path is in project_dir, converts the path to relative.
   If path does not exist returns it as-is.

   :param path: path to serialize
   :type path: str
   :param project_dir: path to the project directory
   :type project_dir: str

   :returns: Dictionary representing the given path
   :rtype: dict


.. function:: serialize_url(url, project_dir)

   Return a dict representation of the given URL.

   If the URL is a file that is in project dir, the URL is converted to a relative path.

   :param url: a URL to serialize
   :type url: str
   :param project_dir: path to the project directory
   :type project_dir: str

   :returns: Dictionary representing the URL
   :rtype: dict


.. function:: deserialize_path(serialized, project_dir)

   Returns a deserialized path or URL.

   :param serialized: a serialized path or URL
   :type serialized: dict
   :param project_dir: path to the project directory
   :type project_dir: str

   :returns: Path or URL as string
   :rtype: str


