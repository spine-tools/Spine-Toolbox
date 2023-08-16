.. _Metadata description:

**************************
Spine Metadata Description
**************************

This is the metadata description for Spine, edited from `<https://frictionlessdata.io/specs/data-package/>`_.

Required properties
-------------------

``title``
  One sentence description for the data sources.

``sources``
  The raw sources of the data. Each source must have a ``title`` property and optionally a ``path`` property.
  Example::

    "sources": [{
      "title": "World Bank and OECD",
      "path": "http://data.worldbank.org/indicator/NY.GDP.MKTP.CD"
    }]

``contributors``
  The people or organisations who contributed to the data.
  Must include ``title`` and may include ``path``, ``email``, ``role`` and ``organization``.
  Example::

    "contributors": [{
      "title": "Joe Bloggs",
      "email": "joe@bloggs.com",
      "path": "http://www.bloggs.com",
      "role": "author"
    }]


  Role is one of ``author``, ``publisher``, ``maintainer``, ``wrangler``, or ``contributor``.


``created``
  The date this data was created or put together, in ISO8601 format (YYYY-MM-DDTHH:MM)

Optional properties
-------------------

``description``
  A description of the data. Describe here how the data was collected, how it was processed etc.

  The description MUST be markdown formatted
  – this also allows for simple plain text as plain text is itself valid markdown.
  The first paragraph (up to the first double line break) should be usable as summary information for the package.

``spine_results_metadata``
  Key contains results metadata (described in a separate document).

``keywords``
  An array of keywords

``homepage``
  A URL for the home on the web that is related to this data package.

``name``
  Name of the data package, url-usable, all-lowercase string.

``id``
  Globally unique id, such as UUID or DOI

``licenses``
  Licences that apply to the data.
  Each item must have a ``name`` property (`Open Definition license ID <https://opendefinition.org/licenses/api/>`_)
  or a ``path`` property and may contain ``title``.
  Example::

    "licenses": [{
      "name": "ODC-PDDL-1.0",
      "path": "http://opendatacommons.org/licenses/pddl/",
      "title": "Open Data Commons Public Domain Dedication and License v1.0"
    }]

``temporal``
  Temporal properties of the data (if applicable).
  Example using `DCMI Period Encoding Scheme <http://dublincore.org/specifications/dublin-core/dcmi-period/>`_::

    "temporal": {
      "start": "2000-01-01",
      "end": "2000-12-31",
      "name": "The first year of the 21st century"
    }

``spatial``
  Spatial properties of the data (if applicable).
  Example using `DCMI Point Encoding Scheme <http://www.dublincore.org/specifications/dublin-core/dcmi-point/>`_::

    "spatial": {
      "east": 23.766667,
      "north": 61.5,
      "projection": "geographic coordinates (WGS 84)",
      "name": "Tampere, Finland"
    }

``unitOfMeasurement``
  Unit of measurement. Can also be embedded in ``description``.
