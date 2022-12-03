#!/bin/bash

source venv/bin/activate
trap ctrl_c INT

function ctrl_c() {
    python kill.py
}

python runner.py
python kill.py
