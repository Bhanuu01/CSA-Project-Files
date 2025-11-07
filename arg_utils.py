import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from constants import NETID


@dataclass
class Args:
    """Typed container for CLI parameters.

    Public attributes must remain the same for compatibility with callers.
    """
    debug: bool = False
    iodir: Path = Path("./input/")
    output_dir: Optional[Path] = None


def get_args() -> Args:
    """Parse command-line flags and prepare IO locations.

    Returns an instance of `Args` with absolute paths and an ensured
    output directory. The filesystem layout and folder names are preserved.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--iodir", type=Path, default=Path("./input/"), help="Input directory")
    ns = parser.parse_args()

    cfg = Args(debug=ns.debug, iodir=ns.iodir)

    # Normalize input directory first
    cfg.iodir = cfg.iodir.resolve()
    print("IO dir ->", cfg.iodir)

    # Decide output directory based on debug flag (names unchanged)
    base = f"./output_{NETID}_debug" if cfg.debug else f"./output_{NETID}"
    cfg.output_dir = Path(base).resolve()

    # Ensure destination exists
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    print("Output dir ->", cfg.output_dir)

    return cfg
