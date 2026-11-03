"""Where the data lives: `data/` beside this code in the public repository, `../data` in the working copy
(where `data/0_raw` also holds licensed inputs that are never published), or the folder named by SCIENCE_DATA."""
import os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(os.environ.get("SCIENCE_DATA") or (ROOT / "data" if (ROOT / "data").exists() else ROOT.parent / "data"))


def out(*parts):
    """Path under DATA whose parent folder exists."""
    p = DATA.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
