import sys
from pathlib import Path

# Add the project root to the Python path, so that the app module can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))