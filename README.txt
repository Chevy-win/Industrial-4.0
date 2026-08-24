OR-Tools offline bundle
=======================

Target environment
------------------
- Windows 64-bit
- CPython 3.12 64-bit
- OR-Tools 9.15.6755

Installation
------------
1. Copy this entire folder to the offline computer.
2. Activate the Python 3.12 virtual environment that will run the scheduler.
3. Run install_offline.bat.

Equivalent command:

    python -m pip install --no-index --find-links . ortools==9.15.6755

Verification
------------

    python verify_install.py

Run the scheduler example
-------------------------

    python cplex_model_ortools.py --input input_ortools_test.txt --output output.csv --time-limit 30

Important
---------
These wheels only support CPython 3.12 on 64-bit Windows. They cannot be used
with Python 3.10, Python 3.11, 32-bit Python, Linux, or macOS.
