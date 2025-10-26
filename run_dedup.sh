#!/usr/bin/env bash
# --------------------------------------------------------------
#  run_dedup.sh
#  Simple launcher for the Image Deduplicator GUI on Linux.
# --------------------------------------------------------------

set -e      # stop on first error

# 1️⃣  Find the directory that contains this script
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 2️⃣  Change to that directory (pushd preserves the original dir)
pushd "$ROOT_DIR" > /dev/null

# 3️⃣  Activate the virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    # Bash “source” the activation script
    #   .venv\Scripts\activate.bat  →  .venv/bin/activate
    source ".venv/bin/activate"
    echo "Using virtual‑env: .venv"
else
    echo "No virtual‑env found – using the system Python"
fi

# 4️⃣  Run the application
python "dedup_app.py"

# 5️⃣  Restore the previous working directory
popd > /dev/null

# Optional “pause” – wait for the user to press Enter
read -p "Press Enter to exit..."
