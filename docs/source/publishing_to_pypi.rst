.. _Publishing to PyPI:

Publishing to PyPI
==================

This document describes the prerequisites and workflow to publish Spine Toolbox
to `The Python Package Index (PyPI) <https://pypi.org>`_.

Versioning of Spine Toolbox packages
------------------------------------

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

Creating Git tags and publishing to PyPI
----------------------------------------

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
   this:

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

4. Push the newly created tags to GitHub.  On sh-like shells like:
   bash, zsh, or git-bash (Windows)::

     for repo in . venv/src/{spinedb-api,spine-{items,engine}}; do
         pushd $repo;
         git push origin master --tags;
         popd
     done

   With Powershell on Windows, something like this should work::

     "." , "venv/src/spinedb-api", "venv/src/spine-items", "venv/src/spine-engine" | % {
       pushd $_;
       git push origin master --tags;
       popd;
     }

5. Now you can trigger the workflow to publish the packages to PyPI
   either by using GitHub CLI, or from the `workflow dispatch menu`_
   in the `spine-conductor`_ repo.

   .. code-block::

      cat pkgtags.json | gh workflow run --repo spine-tools/spine-conductor test-n-publish.yml --json

   If you are using the `workflow dispatch menu`_, make sure you input
   the exact same package versions as shown in the summary.

Done! **Note:** Soon, (4) & (5) will be wrapped in a separate command
provided by ``spine-conductor``.

The ``release.toml`` file
-------------------------

The config file is a standard TOML file conformant with
``pyproject.toml``, meaning all configuration goes under the section
``tool.conductor``.  The configuration is split into 4 sections: a
regex to identify our packages, dependency graph between our packages,
path to the repos to be used for the release, and the branches to be
used (optional).

1. You can specify a regular expression that will be used to identify
   "our" packages.  Something like the following should work:

   .. code-block:: toml
      :caption: Spine package name regular expression
      :name: release-toml-pkgname-re

      [tool.conductor]
      packagename_regex = "spine(toolbox|(db){0,1}[_-][a-z]+)"  # package name on PyPI

   Note that PyPI treats ``-`` (hyphen) and ``_`` (underscore) as
   equivalent in package names; i.e. ``spinedb_api`` and
   ``spinedb-api`` are equivalent, the regex should accomodate that.

2. The dependency graph between our packages should be specified under
   the ``dependency_graph`` section:

   .. code-block:: toml
      :caption: Spine package dependency graph
      :name: release-toml-dependency-graph

      [tool.conductor.dependency_graph]
      spinetoolbox = ["spine_items", "spine_engine", "spinedb_api"]
      spine_items  = ["spinetoolbox", "spine_engine", "spinedb_api"]
      spine_engine = ["spinedb_api"]
      spinedb_api  = []

   Essentially it is a mapping of the "primary" package, and a list of
   its Spine dependencies.

3. Point to the repository directories *relative* to your current
   working directory.  The following example would be valid if you are
   preparing the release from the Toolbox repo, and the other Spine
   package repos are in the virtual environment.

   .. code-block:: toml
      :caption: Repository paths
      :name: release-toml-repos
   
      [tool.conductor.repos]
      spinetoolbox = "."
      spine_items  = "venv/src/spine-items"
      spine_engine = "venv/src/spine-engine"
      spinedb_api  = "venv/src/spinedb-api"

4. You can also specify the branches for each repository that should
   be used for the release.  This section is optional, and if left
   unspecified, the branch name is assumed to be ``master``.

   .. code-block:: toml
      :caption: Release branches on Spine repositories
      :name: release-toml-branches
   
      # default: master
      [tool.conductor.branches]
      spinetoolbox = "release"
      spine_items  = "release"
      spine_engine = "release"
      spinedb_api  = "release"

Manual release (in case of emergency)
-------------------------------------

This section documents what the `spine-conductor`_ CLI tool does under
the hood.  It is here in case of an emergency (e.g. there's a bug),
and the release has to be done manually.

As mentioned earlier, the package version is now derived from Git
tags.  However, because of the internal dependency between the Spine
packages, the versions of the dependencies have to synchronised with
the new version.  The steps are as follows:

1. Determine the next version for each Spine package.  This can be
   done manually with Git, or you can use ``setuptools_scm`` in a
   Python REPL.

   * You can run ``git describe --tags`` in the repo.  This will print
     out the latest tag followed by a trailer with metadata on distance
     from the tag; something like this: ``0.6.18-100-g411c13e1``.  If
     you want to make a patch release, the next version would be
     ``0.6.19`` and a minor release would be ``0.7.0``.  Repeat this
     process for all 4 Spine repos.
   
   * If using a Python REPL, you can do the following for a minor release::

       >>> from setuptools_scm import get_version
       >>> get_version(".", version_scheme="release-branch-semver")
       '0.7.0.dev100+g411c13e1.d20230823'

     For a patch release, do the following::
   
       >>> get_version(".", version_scheme="guess-next-dev")
       '0.6.19.dev100+g411c13e1.d20230823'

     Note the first argument to ``get_version`` is the path to the
     repository.  The above examples assume the repository is your
     current directory.  If it's not, you can provide the path as the
     first argument.

2. Once the new package versions are determined, you need to edit the
   ``pyproject.toml`` files in all 4 repositories with the correct
   version numbers.  For example, in the ``Spine-Toolbox`` repo if you
   were to do a minor release, i.e. ``0.6.18`` → ``0.7.0``, the
   following change would be sufficient:

   .. code-block::
      :caption: Example edit to ``pyproject.toml`` for Spine-Toolbox
      :name: pyproject-toml-diff

      diff --git a/pyproject.toml b/pyproject.toml
      index bd38a2b7..dd9c228e 100644
      --- a/pyproject.toml
      +++ b/pyproject.toml
      @@ -20,8 +20,8 @@ dependencies = [
           "jupyter-client >=6.0",
           "qtconsole >=5.1",
           "sqlalchemy >=1.3",
      -    "spinedb_api >=0.29.0",
      -    "spine_engine >=0.22.0",
      +    "spinedb_api >=0.30.0",
      +    "spine_engine >=0.23.0",
           "numpy >=1.20.2",
           "matplotlib >= 3.5",
           "scipy >=1.7.1",
      @@ -30,7 +30,7 @@ dependencies = [
           "pygments >=2.8",
           "jill >=0.9.2",
           "pyzmq >=21.0",
      -    "spine-items >= 0.20.0",
      +    "spine-items >= 0.21.0",
       ]
       
       [project.urls]

3. After updating the ``pyproject.toml`` file for all 4 Spine repos as
   above, add and commit the changes in all repos::

     git commit -i pyproject.toml -m "Release 0.7.0"

4. Create a Git tag on the latest commit::

     git tag HEAD 0.7.0

5. Push the tags to GitHub.  On sh-like shells like: bash, zsh, or
   git-bash (Windows):

   .. code-block::
      :caption: Recipe to push Git tags to GitHub on ``sh``-like shells (bash, zsh, git-bash)
      :name: git-push-tags-sh

      for repo in . venv/src/{spinedb-api,spine-{items,engine}}; do
          pushd $repo;
          git push origin master --tags;
          popd
      done

   With Powershell on Windows:

   .. code-block::
      :caption: Recipe to push Git tags to GitHub on Powershell
      :name: git-push-tags-ps1

      "." , "venv/src/spinedb-api", "venv/src/spine-items", "venv/src/spine-engine" | % {
        pushd $_;
        git push origin master --tags;
        popd;
      }

6. Now you can trigger the workflow to publish the packages to PyPI
   from the `workflow dispatch menu`_ in the `spine-conductor`_ repo.
   Ensure you input the exact same package versions as in the tags.

7. In case the workflow above also fails, you have to build the source
   distribution archive and wheels locally and upload to PyPI
   manually.

   To build, ensure you have ``build`` installed.  The ``build``
   backend ensures build isolation, and reproducibility of the wheels
   given a source distribution.

   .. code-block::
      :caption: Build distribution archives and wheels
      :name: build-wheel

      python -m pip install build
      python -m build

   Once the build completes, you can find the source tarball and the
   wheel in ``dist/``.  Now you may upload these files to PyPI.

   It is good practise to first test using TestPyPI before uploading
   to PyPI, since releases on PyPI are read-only.  You want to avoid
   mistakes.

   `Register an account <https://test.pypi.org/account/register/>`_
   and ask some of the owners of `the Spine Toolbox package
   <https://test.pypi.org/project/spinetoolbox/>`_ (or other relevant
   package) to add you as a maintainer.

   Upload the distribution using

   ::

       twine upload --repository testpypi dist/*

   See `Using TestPyPI
   <https://packaging.python.org/guides/using-testpypi/>`_ for more
   information. To avoid entering your username and password every
   time, see `Keyring support in twine documentation
   <https://twine.readthedocs.io/en/latest/#keyring-support>`_ or
   generate an `API key <https://pypi.org/help/#apitoken>`_.  If
   everything went smoothly, you are ready to upload the real index.
   Again, you need to register to PyPI and ask to become a maintainer
   of the package you want to upload to. Upload the distribution using

   ::

       $ twine upload dist/*


Done!  Now fix the bug that forced you to do the manual release ;)


.. _spine-conductor: https://github.com/spine-tools/spine-conductor
.. _workflow dispatch menu: https://github.com/spine-tools/spine-conductor/actions/workflows/test-n-publish.yml
