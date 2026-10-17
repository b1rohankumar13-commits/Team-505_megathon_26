"""Launch the integrated React UI and model API."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("run_integrated.py")), run_name="__main__")
