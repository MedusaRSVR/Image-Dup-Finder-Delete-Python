@echo off
rem -------------------------------------------------------------
rem  run_dedup.bat
rem  Simple launcher for the Image Deduplicator GUI.
rem -------------------------------------------------------------

rem ---------- 1. Find the folder that contains this .bat ----------
set "ROOT_DIR=%~dp0"

rem ---------- 2. Activate the virtual environment if present ----------
pushd "%ROOT_DIR%"

rem  If a folder named .venv exists, activate it
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo Using virtual‑env: .venv
) else (
    echo No virtual‑env found – using the system Python
)

rem ---------- 3. Run the application ----------
python "%ROOT_DIR%\dedup_app.py"

rem ---------- 4. Cleanup ----------
popd
pause