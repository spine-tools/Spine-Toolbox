:mod:`spinetoolbox.version`
===========================

.. py:module:: spinetoolbox.version

.. autoapi-nested-parse::

   Version info for Spine Toolbox package. Inspired by python sys.version and sys.version_info.

   :author: P. Savolainen (VTT)
   :date: 8.1.2020



Module Contents
---------------

.. py:class:: VersionInfo

   Bases: :class:`typing.NamedTuple`

   A class for a named tuple containing the five components of the version number: major, minor,
   micro, releaselevel, and serial. All values except releaselevel are integers; the release level is
   'alpha', 'beta', 'candidate', or 'final'.

   .. attribute:: major
      :annotation: :int

      

   .. attribute:: minor
      :annotation: :int

      

   .. attribute:: micro
      :annotation: :int

      

   .. attribute:: releaselevel
      :annotation: :str

      

   .. attribute:: serial
      :annotation: :int

      


.. data:: major
   :annotation: = 0

   

.. data:: minor
   :annotation: = 3

   

.. data:: micro
   :annotation: = 3

   

.. data:: releaselevel
   :annotation: = alpha

   

.. data:: serial
   :annotation: = 0

   

.. data:: __version_info__
   

   

.. data:: __version__
   

   

