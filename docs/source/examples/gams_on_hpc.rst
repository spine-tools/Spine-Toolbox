.. _Spine Toolbox on HPC:

=======================================
Running Spine Toolbox projects on HPC's
=======================================

.. contents::
   :depth: 1
   :local:

************
Introduction
************

This tutorial demonstrates how to run Spine Toolbox project involving `GAMS <https://www.gams.com/>`_
workflows on a High-Performance Computing (HPC) system using the Slurm scheduler.

The guide assumes you have access to a Linux-based HPC cluster with a shared filesystem and Slurm
installed. You also need basic familiarity with the Linux command line and a valid Gams license for
real use cases. However, this tutorial can be completed with a demo license for Gams.

You will learn the full workflow:

::

   Local machine → Cluster login → Upload files → Submit job → Monitor → Retrieve results

****************************************************
HPC's with container support (apptainer/singularity)
****************************************************

The easiest way to run Spine Toolbox projects involving GAMS is to use *apptainer* containers. Log in to the Login
node of your HPC and check if *apptainer* is available in your HPC with the following command:

.. code-block:: bash

    apptainer --version

If this fails, try checking if *apptainer* is available as a module:

.. code-block:: bash

    module avail apptainer

If the response is a version number or a list of package names and version numbers, you are good to continue to the
next section. If you see an error message or something like 'module not available', skip the next section and
continue from (`HPC's without container support`_).

.. Note::

    If the previous commands failed, you can still try if `singularity` is available with `singularity --version` or
    `module avail singularity`. Apptainer was previously called singularity.


Building the container
----------------------

Apptainer is an open source container platform designed for ease-of-use on shared systems and in high performance
computing (HPC) environments. The container is a single file (.sif), which can be built by using an Apptainer
image definition (.def) file.

Building the container requires using Linux or Windows Subsystem for Linux (WSL) on Windows. The following
instructions are for WSL (v2+) on Windows with an Ubuntu distro (tested on Ubuntu 24.04). Please make sure you have
WSL version 2 or later since version 1 is being phased out as obsolete. If you don't have WSL installed,
please contact your organizations IT department for help. Building Apptainer containers is done using *.def* files.
You can `download and save hpc_container.def on your own system here <../_static/hpc_container.def>`_. Save
`hpc_container.def` file into a mounted drive (for example, `/mnt/c/users/<username>/hpc/hpc_container.def`) for easier
access. The file installs the following apps into the container:

- Ubuntu 26.04
- Python 3.13
- Spine Toolbox (latest release)
- Gams 53.5

.. note::

    Julia and SpineOpt are not included in this container. If you need them, they can be easily added to the .def
    file if you want to run Spine Toolbox projects with SpineOpt tools on an HPC as well.

To start building the container, open command prompt or powershell on Windows and type

.. code-block:: bash

    wsl

Cd to `/mnt/c/users/<username>/hpc/` or where ever you saved the **hpc_container.def** file.

Install `Go`

.. code-block:: bash

    sudo apt install -y golang

Install `apptainer` by cloning the repo and building from sources

.. code-block:: bash

    git clone https://github.com/apptainer/apptainer.git
    cd apptainer
    ./mconfig
    make -C builddir
    sudo make -C builddir install

Ensure `fakeroot` is configured

.. code-block:: bash

    sudo apt install fakeroot uidmap

Build the container by running

.. code-block:: bash

   apptainer build --fakeroot hpc_container.sif hpc_container.def

Why --fakeroot? See https://apptainer.org/docs/user/latest/fakeroot.html#fakeroot-feature

When the build process has completed, if you want to check that everything works, you can use the `shell` command
to spawn a new shell within your container and interact with it as though it were a virtual machine.

.. code-block:: bash

    apptainer shell hpc_container.sif

For example, you can check the versions of Python and Gams with `python --version` and `gams ?` respectively
inside the shell. Type `exit` to close the container shell, type `exit` to close wsl and then close the terminal.

Running a Spine Toolbox project on an HPC
-----------------------------------------

In this section, you need the following:

- Spine Toolbox project with a Gams Tool (test project available in <spinetoolbox>/execution_tests/gams_on_hpc_tutorial)
- Container file (**hpc_container.sif**)
- GAMS license file (optional for this tutorial; required for real use cases)
- Slurm script

.. attention::

    It is recommended to run all **Tool** items in your Spine Toolbox project in *"source directory"* mode.
    You can verify this by opening the project in Spine Toolbox on your local machine, selecting each Tool,
    and checking that the **source dir** option is enabled in the Tool properties.

Preparing files on the HPC
++++++++++++++++++++++++++

Upload all required files to your HPC's home directory using SCP, WinSCP or rsync. We will be using
`gams_on_hpc_tutorial` project in this tutorial:

1. Upload container:
    ``$HOME/spinetoolbox/sifs/hpc_container.sif``

2. Upload project:
    ``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial``

3. Upload GAMS license:
    ``$HOME/spinetoolbox/licenses/gamslic.txt``

4. Create a Slurm script file:
    ``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial/run_on_hpc.sh`` with the following content

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name=spinetoolbox_on_hpc
    #SBATCH --output=out.txt
    #SBATCH --error=err.txt
    #SBATCH --time=00:30:00
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=4G

    # Load apptainer. Uncomment if apptainer is available as a module.
    # module load apptainer

    set -euxo pipefail  # Exit on Error

    # ----------------------------
    # User configuration
    # ----------------------------
    PROJECT_NAME=gams_on_hpc_tutorial
    HOME_BASE="$HOME/spinetoolbox"

    # Choose ONE of these (uncomment the appropriate line)
    BASE_TMP="${SCRATCH:-}"   # Recommended if available
    # BASE_TMP="${WORK:-}"    # Alternative on some systems
    # BASE_TMP="${TMPDIR:-}"  # Often set automatically by Slurm

    # Fallback if chosen variable is empty
    if [ -z "$BASE_TMP" ]; then
        echo "Warning: selected BASE_TMP is not set, falling back to \$HOME/tmp"
        BASE_TMP="$HOME/tmp"
    fi

    SCRATCH_BASE="$BASE_TMP/spinetoolbox_runs/$SLURM_JOB_ID"
    mkdir -p "$SCRATCH_BASE"

    echo "Using temporary directory: $SCRATCH_BASE"

    # ----------------------------
    # Stage data
    # ----------------------------
    echo "Copying project to scratch..."
    cp -r $HOME_BASE/$PROJECT_NAME $SCRATCH_BASE/
    # If license is available, uncomment this
    # cp $HOME_BASE/licenses/gamslic.txt $SCRATCH_BASE/

    cd $SCRATCH_BASE/$PROJECT_NAME

    # ----------------------------
    # Run container
    # ----------------------------
    echo "Running Spine Toolbox..."

    apptainer exec \
        --bind $SCRATCH_BASE:$SCRATCH_BASE \
        --bind $HOME_BASE:$HOME_BASE \
        $HOME_BASE/sifs/hpc_container.sif \
        spinetoolbox --execute-only $SCRATCH_BASE/$PROJECT_NAME/ \
        > spinetoolbox.log 2>&1

    # ----------------------------
    # Copy results back
    # ----------------------------
    echo "Listing results directory:"
    ls -R $SCRATCH_BASE/$PROJECT_NAME

    echo "Copying results back to home..."
    rsync -avh $SCRATCH_BASE/$PROJECT_NAME/ $HOME_BASE/$PROJECT_NAME/

    echo "Done."

.. attention::

    Line endings in Slurm scripts must be Unix style (LF).

The ``run_on_hpc.sh`` script stages a Spine Toolbox project to a temporary working directory on the HPC system,
runs it inside an Apptainer container, and then copies the results back to the original project location. This
approach ensures efficient use of the HPC filesystem by performing computation on a fast scratch or temporary
storage area while preserving results in the user’s home directory.

The folder structure on your HPC should look like this now:

.. code-block:: text

    home/
    └── spinetoolbox/
        ├── sifs/
        │   └── hpc_container.sif
        ├── projects/
        │   └── gams_on_hpc_tutorial/
        │       ├── .spinetoolbox/
        │       │   ├── items/
        │       │   │   └── ...
        │       │   ├── specifications/
        │       │   │   └── ...
        │       │   └── project.json
        │       ├── run_on_hpc.sh
        │       ├── model.gms
        │       └── ...
        └── licenses/
            └── gamslic.txt

When you want to execute another Spine Toolbox project, copy the project under `/home/spinetoolbox/projects/` and add
a separate `run_on_hpc.sh` Slurm script for that project.

Editing the Slurm script for your HPC
+++++++++++++++++++++++++++++++++++++
You may need to adjust the Slurm script (``run_on_hpc.sh``) to match your HPC environment:

1. **Apptainer module**
   Check whether Apptainer is available as a module on your system.
   If it is, uncomment the following line::

       # module load apptainer

2. **Project name**
   Update the ``PROJECT_NAME`` variable to match your Spine Toolbox project folder name.
   For this tutorial, it should be::

       PROJECT_NAME=gams_on_hpc_tutorial

3. **Temporary working directory**
   Check your HPC documentation for the recommended working or scratch filesystem.

   - If your system uses ``$SCRATCH``, no changes are needed.
   - Otherwise, update the ``BASE_TMP`` setting by commenting or uncommenting the appropriate line (e.g. ``$WORK`` or ``$TMPDIR``).
   - If none of these variables are available, you can define your own custom path.

4. **Slurm job parameters**
   Adjust the resource requests and output settings as needed:

   - ``--job-name``: Job name
   - ``--time``: Maximum runtime
   - ``--cpus-per-task``: Number of CPU cores
   - ``--mem``: Memory allocation
   - ``--output``: Output log file
   - ``--error``: Error log file

Submit job to Slurm Scheduler
+++++++++++++++++++++++++++++

When you are ready to execute the project, cd to home/spinetoolbox/projects/gams_on_hpc_tutorial and run

.. code-block:: bash

    sbatch run_on_hpc.sh

The response will be something like

```
Submitted batch job 1303767
```

where 1303767 is the job id

Check status of submitted job
+++++++++++++++++++++++++++++

.. code-block:: bash

    squeue -j <job_id>

where *<job_id>* is the id returned by the `sbatch` command.
To check the status of all of your submitted tasks, run

.. code-block:: bash

    squeue -u $USER

If this command fails, replace $USER with your user name. When a job disappears from the the list returned by
the `squeue` command, it is finished.

Check job output files
++++++++++++++++++++++

Since `out.txt` and `err.txt` were given in the Slurm script as the values for *--output* and *--error*, you
can find the stdout and stderr of your job in these files. The file `err.txt` is empty if everything is Ok.
To view the files:

.. code-block:: bash

    cat out.txt
    cat err.txt

Final job status
++++++++++++++++

.. code-block:: bash

    sacct -j <job_id>

where ``<job_id>`` is the ID returned by the ``sbatch`` command.
This command should return something like:

.. code-block:: text

    JobID           JobName  Partition    Account  AllocCPUS      State ExitCode
    ------------ ---------- ---------- ---------- ---------- ---------- --------
    1303767      spinetool+        all     ba6401          1  COMPLETED      0:0
    1303767.batch      batch        all     ba6401          1  COMPLETED      0:0
    1303767.extern     extern       all     ba6401          1  COMPLETED      0:0

Live monitoring
+++++++++++++++

.. code-block:: bash

    watch -n 2 squeue -u $USER

Another option is to use `tail`:

.. code-block:: bash

   tail -f out.txt

Again, if $USER is not defined, replace it with your user name. This function tails the job progress and updates
every two seconds.

Checking the results
++++++++++++++++++++

The result files and output from executing the project will be inside the project item folders just like
when executing the project in Spine Toolbox locally. You can check the results on the HPC, or transfer the
project folder back to your local computer, start Spine Toolbox, and open the project there.

*******************************
HPC's without container support
*******************************

.. attention::

    This section is a work in progress

Verify GAMS installation:

.. code-block:: bash

   gams ?

If GAMS is installed correctly, this command prints version and usage information.

Accessing GAMS on HPC
---------------------

Option 1: Using a Module
++++++++++++++++++++++++

Many HPC systems provide GAMS via environment modules:

.. code-block:: bash

   module avail gams
   module load gams

Verify:

.. code-block:: bash

   which gams


Option 2: User Installation
+++++++++++++++++++++++++++

If GAMS is not provided:

1. Download the Linux version from the GAMS website
2. Extract it in your home or project directory
3. Add it to your PATH:

.. code-block:: bash

   export PATH=$HOME/gams:$PATH

Ensure that your license file is accessible (e.g., ``gamslice.txt``).

Common Issues and Troubleshooting
---------------------------------

License Errors
++++++++++++++

- Ensure license file is accessible on compute nodes
- Check environment variables if needed:

.. code-block:: bash

   export GAMSLICE=/path/to/gamslice.txt

File Not Found
++++++++++++++

- Verify paths are correct relative to the SLURM working directory
- Use:

.. code-block:: bash

   echo $PWD

Job Stuck in Queue
++++++++++++++++++

- Cluster is full
- Resource request too large

Memory Errors
+++++++++++++

Increase memory:

.. code-block:: bash

   #SBATCH --mem=16G


Solver Not Found
++++++++++++++++

.. code-block:: bash

   module load gurobi

Check installation:

.. code-block:: bash

   which gurobi_cl
