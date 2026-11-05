"""Compatibility entry point. Checks the upgraded V0.8.0 invariants."""
from runpy import run_path
from pathlib import Path
run_path(str(Path(__file__).with_name('validate_v08.py')),run_name='__main__')
