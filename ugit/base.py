import os
from pathlib import Path
from typing import Union

from . import data


def write_tree(directory="."):
    directory = Path(directory)

    with os.scandir(directory) as it:
        for entry in it:
            full = directory / entry.name

            if entry.is_file(follow_symlinks=False):
                # TODO: write the file object store
                print(full)
            elif entry.is_dir(follow_symlinks=False):
                write_tree(full)

    # TODO: actually create the tree object


def is_ignored(path: Union[str, Path]):
    return str(data.GIT_DIR) in Path(path).parts
