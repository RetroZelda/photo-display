#!/bin/bash

venv_name="venv"
script_name="./src/photo-display.py"

# Activate virtual environment
source "$venv_name/bin/activate"

# Run the script
python3 "$script_name" "$@"

