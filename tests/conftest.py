import sys
from pathlib import Path
TC = Path(__file__).resolve().parent.parent / "skills" / "trail-commons"
if str(TC) not in sys.path:
    sys.path.insert(0, str(TC))
