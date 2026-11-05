"""Compatibility entrypoint: rebuild the V0.6 high-detail item models, not old low-poly ones."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("generate_fine_models.py")))
