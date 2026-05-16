"""Package entrypoint for python -m angis."""
import sys
from pathlib import Path

package_dir = Path(__file__).resolve().parent
parent_dir = package_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
