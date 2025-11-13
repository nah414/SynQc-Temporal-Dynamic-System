
# Contributing to SynQc: Temporal Dynamics

Thanks for helping improve the project!

## Dev quickstart
1. Create a virtual environment for Python 3.10+
2. `pip install -e .`
3. `python -m unittest discover -s tests -v`
4. Run `python examples/simulate_dpd.py` to visually validate changes.

## Coding standards
- Keep functions short and focused.
- Write unit tests for new features (prefer `unittest` to avoid extra deps).
- Avoid hard-coding hardware values in library code; use `HardwareSignature`.
- Document any new public functions in the README.

## Pull requests
- Describe the problem and the fix.
- Include before/after behavior if you change numerical behavior.
- CI must pass on Python 3.10–3.12.
