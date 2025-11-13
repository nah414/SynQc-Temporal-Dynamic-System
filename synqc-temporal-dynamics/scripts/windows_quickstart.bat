
@echo off
python -m venv .venv
call .venv\Scripts\activate
pip install -e .
python examples\simulate_dpd.py
