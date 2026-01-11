from .celery import app as celery_app
from pathlib import Path
import sys

# Get the current file's directory
current_dir = Path(__file__).resolve().parent

# Append the listings directory to sys.path
sys.path.append(str(current_dir / 'listings'))


__all__ = ("celery_app",)

