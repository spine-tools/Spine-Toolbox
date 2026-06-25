.. _Spine Toolbox on HPC:

=============================================
Running Spine Toolbox projects on HPC systems
=============================================

.. contents::
   :depth: 1
   :local:

************
Introduction
************

This tutorial demonstrates how to run Spine Toolbox project involving `GAMS <https://www.gams.com/>`_
workflows on a High-Performance Computing (HPC) system using the Slurm scheduler.

The guide assumes you have access to a Linux-based HPC cluster with a shared filesystem and Slurm
installed. You also need basic familiarity with the Linux command line and a valid GAMS license for
real use cases. However, this tutorial can be completed with a demo license for GAMS.

You will learn the full workflow:

::

   Local machine → Cluster login → Upload files → Submit job → Monitor → Retrieve results

********************************************
Running on HPC using Apptainer (Recommended)
********************************************

The recommended approach for running Spine Toolbox projects involving GAMS on HPC systems is to use
:program:`Apptainer` (formerly Singularity). Apptainer is specifically designed for HPC environments and provides a
portable and reproducible way to execute containerized workflows.

Log in to the login node of your HPC system and check whether Apptainer is available:

.. code-block:: bash

    apptainer --version

If this command is not found, it may still be available as a module:

.. code-block:: bash

    module avail apptainer

If you see a version number or a list of available module versions, you can proceed with this (recommended) approach.

If Apptainer is not available on your system, do not worry — an alternative approach without containers is described
in `HPC without container support`_.

.. note::

    Apptainer was previously known as Singularity. If the above commands do not work, you can also check:

    .. code-block:: bash

        singularity --version

    or:

    .. code-block:: bash

        module avail singularity


Building the container
----------------------

Apptainer is an open source container platform designed for ease-of-use on shared systems and in high performance
computing (HPC) environments. The container is a single file (``.sif``), which can be built by using an Apptainer
image definition (``.def``) file.

Building the container requires using Linux or Windows Subsystem for Linux (WSL) on Windows. The following
instructions are for WSL (v2+) on Windows with an Ubuntu distro (tested on Ubuntu 24.04). Please make sure you have
WSL version 2 or later since version 1 is being phased out as obsolete. If you don't have WSL installed,
please contact your organizations IT department for help. Apptainer containers are built using ``.def`` files.
You can `download and save hpc_container.def on your own system here <../_static/hpc_container.def>`_. Save
``hpc_container.def`` file into a mounted drive (for example, ``/mnt/c/users/<username>/hpc/hpc_container.def``) for
easier access. The definition file installs the following software into the container:

- Ubuntu 26.04
- Python 3.13
- Spine Toolbox (latest release)
- GAMS 53.5

.. note::

    Julia and SpineOpt are not included in this container. If you need them, they can be easily added to the ``.def``
    file if you want to run Spine Toolbox projects with SpineOpt tools on an HPC as well.

To start building the container, open command prompt or powershell on Windows and type

.. code-block:: bash

    wsl

Cd to ``/mnt/c/users/<username>/hpc/`` or where ever you saved the ``hpc_container.def`` file.

Install Go

.. code-block:: bash

    sudo apt install -y golang

Install Apptainer by cloning the repo and building from sources

.. code-block:: bash

    git clone https://github.com/apptainer/apptainer.git
    cd apptainer
    ./mconfig
    make -C builddir
    sudo make -C builddir install

Ensure ``fakeroot`` is configured

.. code-block:: bash

    sudo apt install -y fakeroot uidmap

Build the container by running

.. code-block:: bash

   apptainer build --fakeroot hpc_container.sif hpc_container.def

Why :literal:`--fakeroot`? See https://apptainer.org/docs/user/latest/fakeroot.html#fakeroot-feature

When the build process has completed, if you want to check that everything works, you can use the ``shell`` command
to spawn a new shell within your container and interact with it as though it were a virtual machine.

.. code-block:: bash

    apptainer shell hpc_container.sif

For example, you can check the versions of Python and GAMS with ``python --version`` and ``gams ?`` respectively
inside the shell. Type ``exit`` to close the container shell, type ``exit`` to close wsl and then close the terminal.

Running a Spine Toolbox project on an HPC
-----------------------------------------

In this section, you will need the following:

- A Spine Toolbox project with a GAMS Tool (a suitable example project for this tutorial is available in the
  Spine Toolbox repository at ``<repo_root>/execution_tests/gams_on_hpc_tutorial``)
- A container file (``hpc_container.sif``)
- A GAMS license file (optional for this tutorial, but required in real use cases)
- A Slurm script

.. attention::

    It is recommended to run all **Tool** items in your Spine Toolbox project in **"source directory"** mode.
    This ensures that execution on the HPC uses high-performance temporary storage (such as $SCRATCH) rather
    than slower persistent storage (such as your $HOME directory).

    While execution may also work in **"work directory"** mode, performance is typically lower, and this approach
    is generally discouraged by HPC administrators.

    You can verify your setup by opening the project in Spine Toolbox on your local machine, selecting each Tool,
    and checking that the **source dir** option is enabled in the Tool properties.

Preparing files on the HPC
++++++++++++++++++++++++++

Upload all required files to your HPC's home directory using e.g. SCP, WinSCP or rsync. We will be using
`gams_on_hpc_tutorial` project in this tutorial:

1. Upload container:
    ``$HOME/spinetoolbox/sifs/hpc_container.sif``

2. Upload project:
    ``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial``

3. Upload GAMS license (not required for this tutorial):
    ``$HOME/spinetoolbox/licenses/gamslic.txt``

4. Create a Slurm script file:
    ``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial/run_on_hpc.sh`` with the following content

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name=spinetoolbox_on_hpc
    #SBATCH --output=%j.out
    #SBATCH --error=%j.out
    #SBATCH --time=00:30:00
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=4G

    # Make folder for Slurm output logs
    mkdir -p logs

    # Load apptainer. Uncomment if apptainer is available as a module.
    # module load apptainer

    set -euo pipefail  # Exit on Error

    START=$(date +%s)

    # ----------------------------
    # User configuration
    # ----------------------------
    SUBMIT_DIR="$SLURM_SUBMIT_DIR"
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

    rsync -av \
      --exclude '.git*' \
      --exclude 'logs' \
      --exclude '*.out' \
      --exclude '*.err' \
      --exclude '.spinetoolbox/items/*/output/*' \
      "$HOME_BASE/projects/$PROJECT_NAME/" \
      "$SCRATCH_BASE/$PROJECT_NAME/"

    echo "Copying project finished"

    # If license is available, uncomment this
    # rsync -av "$HOME_BASE/licenses/gamslic.txt" "$SCRATCH_BASE/"

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

    echo "Spine Toolbox execution finished. See spinetoolbox.log for output"

    # ----------------------------
    # Copy results back
    # ----------------------------
    echo "Copying results back to home..."
    rsync -avh $SCRATCH_BASE/$PROJECT_NAME/ $HOME_BASE/projects/$PROJECT_NAME/

    # -----------------------------------
    # Move log files to dedicated folder
    # -----------------------------------
    LOG_DIR="$HOME_BASE/projects/$PROJECT_NAME/logs/$SLURM_JOB_ID"
    mkdir -p "$LOG_DIR"
    mv "$SUBMIT_DIR/${SLURM_JOB_ID}.out" "$LOG_DIR/out.txt" 2>/dev/null || true
    mv "$HOME_BASE/projects/$PROJECT_NAME/spinetoolbox.log" "$LOG_DIR/spinetoolbox.log"

    END=$(date +%s)
    echo "Done. Runtime: $((END - START)) seconds"

.. attention::

    Line endings in Slurm scripts must be Unix style (LF). You can make sure that the line endings are in the
    correct style by running ``dos2unix run_on_hpc.sh`` on your HPC.

The folder structure on your HPC should look like this. The ``logs/`` directory is created automatically after you
run the Slurm script for the first time:

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
        │       ├── logs/
        │       │   └── <SLURM_JOB_ID>/
        │       │       ├── out.txt
        │       │       └── spinetoolbox.log
        │       ├── run_on_hpc.sh
        │       ├── model.gms
        │       └── ...
        └── licenses/
            └── gamslic.txt

When you want to run a different Spine Toolbox project, copy the project to ``/home/spinetoolbox/projects/`` and
create a dedicated ``run_on_hpc.sh`` Slurm script for it.

Editing the Slurm script for your HPC
+++++++++++++++++++++++++++++++++++++
You may need to adjust the Slurm script (``run_on_hpc.sh``) to match your HPC environment:

1. **Slurm job parameters**
   Adjust the resource requests as needed:

   - ``--job-name``: Job name
   - ``--time``: Maximum runtime
   - ``--cpus-per-task``: Number of CPU cores
   - ``--mem``: Memory allocation

2. **Apptainer module**
   Check whether Apptainer is available as a module on your system.
   If it is, uncomment the following line::

       # module load apptainer

3. **Project name**
   Update the ``PROJECT_NAME`` variable to match your Spine Toolbox project folder name.
   For this tutorial, it should be::

       PROJECT_NAME=gams_on_hpc_tutorial

4. **Temporary working directory**
   Check your HPC documentation for the recommended working or scratch filesystem.

   - If your system uses ``$SCRATCH``, no changes are needed.
   - Otherwise, update the ``BASE_TMP`` setting by commenting or uncommenting the appropriate line (e.g. ``$WORK`` or ``$TMPDIR``).
   - If none of these variables are available, you can define your own custom path.

5. **GAMS License file**
    If you have a GAMS license, uncomment the following line::

        # rsync -av "$HOME_BASE/licenses/gamslic.txt" "$SCRATCH_BASE/"

What the Slurm script does
++++++++++++++++++++++++++

The ``run_on_hpc.sh`` script stages a Spine Toolbox project to a temporary working directory on the HPC system,
runs it inside an Apptainer container, and then copies the results back to the original project location. This
approach ensures efficient use of the HPC filesystem by performing computation on a fast scratch or temporary
storage area while preserving results in the user’s home directory.

During execution, all model output is written to the staged project directory in scratch space. After completion,
the results are synchronized back to the original project directory in the user’s home folder.

For reproducibility and debugging, the script collects log files for each run.

- Slurm standard output and error streams are written to a single file:
  ``out.txt``
- Spine Toolbox execution output is written to:
  ``spinetoolbox.log``

After each job finishes, these log files are organized into a dedicated directory:

``logs/<SLURM_JOB_ID>/``

This directory is created inside the project folder and contains the logs associated with that specific job. This
ensures that logs from different runs are preserved and can be easily traced back to a particular execution. If a
Slurm job fails, check the ``<SLURM_JOB_ID>.out`` file in the same directory as ``run_on_hpc.sh`` for error messages
and diagnostics.

Submit Job to Slurm Scheduler
+++++++++++++++++++++++++++++

Now that everything has been setup, we are finally ready to execute the project. Navigate to
``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial`` and run:

.. code-block:: bash

    sbatch run_on_hpc.sh

The response will look something like::

    Submitted batch job 1303767

where ``1303767`` is the Slurm job ID.

For an alternative approach, see `Submit and monitor a job`_.

Check job status
++++++++++++++++

After submitting a job, you can monitor its status using Slurm commands.

To check the status of a specific job:

.. code-block:: bash

    squeue -j <SLURM_JOB_ID>

where ``<SLURM_JOB_ID>`` is the ID returned by the ``sbatch`` command. To see all of your jobs:

.. code-block:: bash

    squeue -u $USER

If this command fails, replace ``$USER`` with your username. When a job no longer appears in the output
of ``squeue``, it has finished.

To view the final status of a completed job, use:

.. code-block:: bash

    sacct -j <SLURM_JOB_ID>

This command returns information such as:

.. code-block:: text

    JobID           JobName  Partition    Account  AllocCPUS      State ExitCode
    ------------ ---------- ---------- ---------- ---------- ---------- --------
    1303767      spinetool+        all     ba6401          1  COMPLETED      0:0
    1303767.batch      batch        all     ba6401          1  COMPLETED      0:0
    1303767.extern     extern       all     ba6401          1  COMPLETED      0:0

.. note::

    The tutorial project runs very quickly and typically completes in under 10 seconds, unless the job is waiting
    in the queue.

Live monitoring
+++++++++++++++

.. code-block:: bash

    watch -n 2 squeue -u $USER

Another option is to use ``tail``:

.. code-block:: bash

    tail -f <SLURM_JOB_ID>.out

Replace ``<SLURM_JOB_ID>`` with the job ID for that run.

.. note::

    The tutorial project runs very quickly and has likely already finished by the time you run these commands.
    In that case, the output files have already been moved to ``logs/<SLURM_JOB_ID>/`` in your project directory.

Inspecting Job Output and Results
+++++++++++++++++++++++++++++++++

After the job has finished, the output files are collected into
``logs/<SLURM_JOB_ID>/`` within the project directory. To view the log files, navigate to:

``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial/logs/<SLURM_JOB_ID>``

and run:

.. code-block:: bash

    cat out.txt
    cat spinetoolbox.log

The results generated by the project are stored in the project’s item folders
(``$HOME/spinetoolbox/projects/gams_on_hpc_tutorial/.spinetoolbox/items/``), just as when running the project locally
in Spine Toolbox.

You can inspect these results directly on the HPC system, or transfer the project folder back to your local machine,
open it in Spine Toolbox, and explore the results there.

Submit and monitor a job
************************

As an alternative to running ``sbatch run_on_hpc.sh`` directly, you can use a helper script to both submit the job
and monitor its progress until completion. This allows you to see the job’s final status as soon as it finishes,
without needing to check it manually.

To do this, copy the script below into a file named ``submit_job.sh`` and run it with:

``bash submit_job.sh``.

.. code-block:: bash

    #!/bin/bash
    JOBID=$(sbatch run_on_hpc.sh | awk '{print $4}')
    echo "Submitted job $JOBID"
    # Wait until job disappears from queue
    while [ -n "$(squeue -j "$JOBID" -h)" ]; do
        sleep 2
    done
    # Get final job state
    STATE=$(sacct -j "$JOBID" --format=State --noheader | head -n 1 | awk '{print $1}')

    echo "Final state: $STATE"
    if [[ "$STATE" == "COMPLETED" ]]; then
        echo "COMPLETED. Logs available at logs/$JOBID"
    else
        echo "FAILED. Check $JOBID.out or logs/$JOBID for info"
    fi

*****************************
HPC without container support
*****************************

If your HPC system does not provide Apptainer, the recommended first step is to contact your HPC support or
administration team and request that Apptainer be installed. It is widely supported on HPC systems and is the
preferred approach for running reproducible containerized workflows.

If installing Apptainer is not possible, you can still run Spine Toolbox projects directly on the HPC environment.
In this case, you must ensure that all required software (e.g., GAMS) is available and correctly configured in your
environment.

Verifying GAMS installation
---------------------------

First, check whether GAMS is available:

.. code-block:: bash

    gams ?

If GAMS is installed correctly, this command prints version and usage
information.

Accessing GAMS on HPC
---------------------

Option 1: Using a module
++++++++++++++++++++++++

Many HPC systems provide GAMS via environment modules:

.. code-block:: bash

    module avail gams
    module load gams

Verify that GAMS is available:

.. code-block:: bash

    which gams

Option 2: User installation
+++++++++++++++++++++++++++

If GAMS is not provided by your HPC:

1. Download the Linux version from the GAMS website
2. Extract it into your home or project directory
3. Add it to your ``PATH``:

.. code-block:: bash

    export PATH=$HOME/gams:$PATH

Ensure that your license file (e.g., ``gamslice.txt``) is available.

Running Spine Toolbox without Apptainer
---------------------------------------

When running without containers, Spine Toolbox executes directly in the
HPC environment. This means:

- All required tools (GAMS and any dependencies) must be installed and
  available in your environment
- Paths to executables must be correctly configured
- Environment variables (e.g., ``PATH``) must be set before running jobs

A minimal Slurm workflow follows the same structure as the container-based
approach, but without the ``apptainer exec`` command.

Example Slurm script
++++++++++++++++++++

.. code-block:: bash

    #!/bin/bash
    #SBATCH --job-name=spinetoolbox_no_container
    #SBATCH --output=logs/%j.log
    #SBATCH --error=logs/%j.log
    #SBATCH --time=00:30:00
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=4G

    set -euo pipefail

    PROJECT_DIR="$HOME/spinetoolbox/projects/gams_on_hpc_tutorial"

    echo "Running Spine Toolbox without container..."

    # Load modules if needed (example)
    # module load gams
    # module load python

    # Ensure required tools are available
    which gams
    which spinetoolbox

    # Run Spine Toolbox project
    spinetoolbox --execute-only "$PROJECT_DIR"

    echo "Run completed successfully."

Ensure that:

- The ``spinetoolbox`` command is available in your environment
- The GAMS executable is discoverable (i.e., ``which gams`` works)
- Any required input files and licenses are accessible

.. note::

    Running without containers may lead to differences in behavior across systems due to variations in installed
    software and libraries. Using Apptainer is strongly recommended whenever possible for reproducibility.

*********************************
Common Issues and Troubleshooting
*********************************

Error on sbatch
---------------

If you see the following error when trying to run `sbatch run_on_hpc.sh`::

    sbatch: error: Batch script contains DOS line breaks (\r\n)
    sbatch: error: instead of expected UNIX line breaks (\n).

You need to change the line endings into Unix/Linux line breaks. You can do this in your hpc with the command::

    dos2unix run_on_hpc.sh

Then try running `sbatch run_on_hpc.sh` again.

License Errors
--------------

- Ensure license file is accessible on compute nodes
- Check environment variables if needed:

.. code-block:: bash

   export GAMSLICE=/path/to/gamslice.txt

File Not Found
--------------

- Verify paths are correct relative to the SLURM working directory
- Use:

.. code-block:: bash

   echo $PWD

Job Stuck in Queue
------------------

- Cluster is full
- Resource request too large

Memory Errors
-------------

Increase memory:

.. code-block:: bash

   #SBATCH --mem=16G

Solver Not Found
----------------

.. code-block:: bash

   module load gurobi

Check installation:

.. code-block:: bash

   which gurobi_cl
