#!/bin/bash

venv_name="venv"
script_name="./src/photo-display.py"

# Create virtual environment
python3 -m venv "$venv_name"

# Activate virtual environment
source "$venv_name/bin/activate"

# Install dependencies
pip3 install inky [rpi,example-depends]
pip3 install Pillow
pip3 install requests

# Run the script
python3 "$script_name"

