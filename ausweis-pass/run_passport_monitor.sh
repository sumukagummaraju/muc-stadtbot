#!/bin/bash

# Run from the same directory as passport_monitor.py
cd "$(dirname "$0")"

# First-time setup: create venv and install dependencies
if [ ! -d "passport-virtual-env" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv passport-virtual-env
    source passport-virtual-env/bin/activate
    pip install requests
else
    source passport-virtual-env/bin/activate
fi

python passport_monitor.py
