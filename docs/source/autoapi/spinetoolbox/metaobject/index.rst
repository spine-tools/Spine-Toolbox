:mod:`spinetoolbox.metaobject`
==============================

.. py:module:: spinetoolbox.metaobject

.. autoapi-nested-parse::

   MetaObject class.

   :authors: E. Rinne (VTT), P. Savolainen (VTT)
   :date:   18.12.2017



Module Contents
---------------

.. function:: shorten(name)

   Returns a 'shortened' version of given name.


.. py:class:: MetaObject(name, description)

   Bases: :class:`PySide2.QtCore.QObject`

   Class for an object which has a name, type, and some description.

   :param name: Object name
   :type name: str
   :param description: Object description
   :type description: str

   .. method:: set_name(self, new_name)


      Set object name and short name.
      Note: Check conflicts (e.g. name already exists)
      before calling this method.

      :param new_name: New (long) name for this object
      :type new_name: str


   .. method:: set_description(self, desc)


      Set object description.

      :param desc: Object description
      :type desc: str



