.. Spine Engine Server
   Created 31.10.2022

.. _Spine Engine Server:

*******************
Spine Engine Server
*******************

Setting up Spine Engine Server
------------------------------

1. Make a new environment for Spine Engine Server

   - Make a miniconda environment & activate it
   - Clone and checkout spine-engine
   - cd to spine-engine repo root, run::

      pip install -e .

   - Clone and checkout spine-items
   - cd to spine-items repo root, run::

      pip install --no-deps -e .

2. Create security credentials (optional)

   - cd to <repo_root>/spine_engine/server/
   - Create security certificates by running `python certificate_creator.py`
   - The certificates are created into <repo_root>/spine_engine/server/certs/ directory.
   - Configure allowed endpoints by creating file
     *<repo_root>/spine_engine/server/connectivity/certs/allowEndpoints.txt*
   - Add IP addresses of the remote end points to the file

3. Install IPython kernel spec (*python3*) to enable Jupyter Console execution of Python Tools

   - Run::

      python -m pip install ipykernel

4. Install Julia 1.8

   - Download from https://julialang.org/downloads/ or run `apt-get install julia` on Ubuntu

5. Install IJulia kernel spec (*julia-1.8*) to enable Jupyter Console execution of Julia tools

   - Open Julia REPL and press `]` to enter pkg mode. Run::

         add IJulia

   - This installs `julia-1.8` kernel spec to *~/.local/share/jupyter/kernels* on Ubuntu or to
     *%APPDATA%\jupyter\kernels* on Windows

6. Start Spine Engine Server

   - cd to <repo_root>/spine_engine/server/
   - Without security, run::

      python start_server.py 50001

   - where 50001 is the server port number.
   - With Stonehouse security, run::

      python start_server.py 50001 StoneHouse <repo_root>/spine-engine/server/connectivity/certs

   - where, 50001 is the server port number, StoneHouse is the security model, and the path is the folder
     containing the security credentials.

.. Note:: Valid port range is 49152-65535.

Setting up Spine Toolbox (client)
---------------------------------

1. (Optional) If server is started using StoneHouse security, copy security credentials from the server to
   some directory. Server's secret key does not need to be copied.

2. Start Spine Toolbox and open a project

3. Open the **Engine** page in application settings (**File->Settings**)

   - Enable remote execution from the checkbox (Enabled)
   - Set up the Spine Engine Server settings (host, port, security model, and security folder).
     Host is 127.0.0.1 when the Server runs on the same computer as the client.
   - Click Ok, to close and save the new Settings

4. Click Play to execute the project.
