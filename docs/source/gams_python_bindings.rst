..  GAMS Python bindings
    Created: 2.10.2019

.. _GAMS Python bindings:

********************
GAMS Python bindings
********************

Please follow the official `GAMS Python tutorial <https://www.gams.com/latest/docs/API_PY_TUTORIAL.html>`__
for instructions on how to install the bindings.

Important things to note:

- You need to install bindings for Python 3.6 (from :literal:`api_36` directory in GAMS)
  since this is the only version supported by both GAMS and Spinetoolbox.
  This means you may need to upgrade/downgrade Python as well.
- Make sure GAMS and Python have the same bitness, i.e. both are 32 or 64 bit.
- If you have more than one GAMS version installed, you may need to set the *GAMS executable* in Spinetoolbox settings
  to point to the correct executable, i.e. the one whose Python bindings were installed.
