#!/usr/bin/env bash
# Mac / Linux: conda env create -f environment.yml  (once), then ./run_app.sh
set -e
cd "$(dirname "$0")"
eval "$(conda shell.bash hook)"
conda activate it2
streamlit run app/app.py
