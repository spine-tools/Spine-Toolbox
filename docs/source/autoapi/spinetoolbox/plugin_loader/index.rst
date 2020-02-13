:mod:`spinetoolbox.plugin_loader`
=================================

.. py:module:: spinetoolbox.plugin_loader

.. autoapi-nested-parse::

   Contains a minimal plugin loader infrastructure.

   :author: P. Savolainen (VTT)
   :date:   11.6.2019



Module Contents
---------------

.. function:: get_plugins(subpath)

   Returns a list of plugin (module) names found in given subpath,
   relative to plugins main directory.
   Adds the directory to sys.path if any plugins were found.

   :param subpath: look for plugins in this subdirectory of the plugins main dir
   :type subpath: src


.. function:: load_plugin(plugin_name)

   Loads (imports) a plugin given its name.

   :param plugin_name: Name of the plugin (module) to load
   :type plugin_name: str


