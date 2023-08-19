.. _Publishing to PyPI:

Publishing to PyPI
==================

This document describes the prerequisites and workflow to publish Spine Toolbox
to `The Python Package Index (PyPI) <https://pypi.org>`_.

1. Versioning of Spine Toolbox packages
---------------------------------------

Spine Toolbox packages use the latest Git tag to dynamically generate
the version number.  During the build process Git tags of the form
``X.Y.Z`` are sorted and the latest is used to generate the package
version.  If the tip of the current branch (``HEAD``) is at a tag, the
version number is the tag.  However, if there have been commits since
the latest tag, the next version is guessed and a ``dev??-*``
component is included (e.g. ``'0.7.0.dev77+gf9538fee.d20230816'``).
Note that the ``dev*`` component also includes an indication of the
number of commits since the last tag.

Under this scheme, the release process is simply to create a new Git
tag, and publish it.  However since the different Spine packages
depend on each other, you need to update the different version number
requirements in their respective ``pyproject.toml`` files.  This can
be done conveniently by using the CLI tools available in the
`spine-conductor`_ repo.

2. Creating the Git tags and publishing to PyPI
-----------------------------------------------

1. Check out the `spine-conductor`_ repo, and install it, either in a
   virtual environment or using ``pipx``.

2. You can create a TOML configuration file as mentioned in the README
   of the repo; say ``release.toml``.  Something like the sample below
   should work.

   .. code-block:: toml
      :caption: release.toml
      :name: release-toml

      [tool.conductor]
      packagename_regex = "spine(toolbox|(db){0,1}[_-][a-z]+)"  # package name on PyPI

      [tool.conductor.dependency_graph]
      spinetoolbox = ["spine_items", "spine_engine", "spinedb_api"]
      spine_items  = ["spinetoolbox", "spine_engine", "spinedb_api"]
      spine_engine = ["spinedb_api"]
      spinedb_api  = []

      [tool.conductor.repos]
      spinetoolbox = "."
      spine_items  = "venv/src/spine-items"
      spine_engine = "venv/src/spine-engine"
      spinedb_api  = "venv/src/spinedb-api"

      # # default
      # [tool.conductor.branches]
      # spinetoolbox = "master"
      # spine_items  = "master"
      # spine_engine = "master"
      # spinedb_api  = "master"

3. Now you can create a release by calling the ``conduct release -c
   release.toml`` command with the TOML file as config.  This starts a
   guided session where the `spine-conductor`_ CLI tool deduces the
   next version numbers from existing Git tags, updates the
   corresponding ``pyproject.toml`` files in all the repos to reflect
   the new package versions, and finally prompts you to add any edited
   files, and create the new Git tag.  A typical session would like
   this::

   .. code-block::
      :caption: A typical release session; note the JSON summary in the end.
      :name: release-session

      $ cd /path/to/repo/Spine-Toolbox
      $ conduct release --bump patch -c release.toml  # or include in pyproject.toml
      Repository: /path/to/repo/Spine-Toolbox
      ## master...origin/master
       M pyproject.toml (1)
      Select the files to add (comma/space separated list): 1
      Creating tag: 0.6.19 @ 034fb4b
      Repository: /path/to/repo/venv/src/spine-items
      ## master...origin/master
       M pyproject.toml (1)
      Select the files to add (comma/space separated list): 1
      Creating tag: 0.20.1 @ 5848e25
      Repository: /path/to/repo/venv/src/spine-engine
      ## master...origin/master
       M pyproject.toml (1)
      Select the files to add (comma/space separated list): 1
      Creating tag: 0.22.1 @ e312db2
      Repository: /path/to/repo/venv/src/spinedb-api
      ## master...origin/master
      Select the files to add (comma/space separated list):
      Creating tag: 0.29.1 @ d9ed86e

      Package Tags summary  💾 ➡ 'pkgtags.json':
      {
        "Spine-Toolbox": "0.6.19",
        "spine-items": "0.20.1",
        "spine-engine": "0.22.1",
        "Spine-Database-API": "0.29.1"
      }

   If the session completes successfully, you will see a session
   summary with the newest Git tags that were created for each
   package.

4. Push the newly created tags to GitHub::

     for repo in . venv/src/{spinedb-api,spine-{items,engine}}; do
         pushd $repo;
         git push origin master --tags;
         popd
     done

5. Now you can trigger the workflow to publish the packages to PyPI
   either by using GitHub CLI, or from the `workflow dispatch menu`_
   in the `spine-conductor`_ repo.

   .. code-block::
      :caption: Using GitHub CLI to publish to PyPI
      :name: publish-to-pypi

      cat pkgtags.json | gh workflow run --repo spine-tools/spine-conductor test-n-publish.yml --json

   If you are using the `workflow dispatch menu`_, make sure you input
   the exact same package vesions as shown in the summary.

Done!

.. _spine-conductor: https://github.com/spine-tools/spine-conductor
.. _workflow dispatch menu: https://github.com/spine-tools/spine-conductor/actions/workflows/test-n-publish.yml
