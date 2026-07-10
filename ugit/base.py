import os

from . import data
from pathlib import Path

def write_tree(directory='.'):
    """returns an OID"""
    with os.scandir(directory) as it:
        for entry in it:
            full = os.path.join(directory, entry.name)

            if is_ignored(full):
                continue

            if entry.is_file(follow_symlinks=False):
                print(full)
            elif entry.is_dir(follow_symlinks=False):
                write_tree(full)

    # TODO: create tree object

def is_ignored(path):
    return '.ugit' in Path(path).parts