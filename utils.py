import os
from pathlib import Path


def fix_path(p):
    if p:
        f = os.path.expandvars(os.path.expanduser(os.path.normpath(p)))
        return Path(f)
    else:
        return None
