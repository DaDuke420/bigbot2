import sys
from pathlib import Path

# Ensure the repository root (parent of tests/) is on sys.path so `import bot.*` works
project_root = Path(__file__).resolve().parent.parent
root_str = str(project_root)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
