#!/usr/bin/env bash
# ---------------------------------------------------------------
#  setup.sh
#  Create a Python virtual‑env, activate it, and install
#  the dependencies listed in requirements.txt.
# ---------------------------------------------------------------

set -e   # Stop immediately if a command fails
set -o pipefail

# 1️⃣  Create the virtual‑environment (use python3 if that's the
#     default on the system, otherwise adjust the command).
python3 -m venv .venv
echo "Virtual‑env created in .venv"

# 2️⃣  Activate it
#     On Linux the activation script lives in .venv/bin/activate
source .venv/bin/activate
echo "Activated virtual‑env: .venv"

# 3️⃣  Install the required packages
pip install -r requirements.txt
echo "All packages installed"

# 4️⃣  (Optional) Show the active environment
echo "Python in use: $(which python)"
echo "pip in use: $(which pip)"
