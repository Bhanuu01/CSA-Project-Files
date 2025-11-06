from pathlib import Path

from tap import Tap

from constants import NETID


class Args(Tap):
    debug: bool = False
    iodir: Path = "./input/"
    output_dir: Path = None

def get_args():
    args = Args().parse_args()

    args.iodir = args.iodir.resolve()
    print("IO Directory:", args.iodir)
    if args.debug:
        args.output_dir = Path(f"./output_{NETID}_debug").resolve()
    else:
        args.output_dir = Path(f"./output_{NETID}").resolve()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    print("Output Directory:", args.output_dir)

    return args
