import os

from . import data

def write_tree(directory='.'):
    """returns an OID"""
    with os.scandir(directory) as it:
        for entry in it:
            full = os.path.join(directory, entry.name)
            if entry.is_file(follow_symlinks=False):
                print(full)
            elif entry.is_dir(follow_symlinks=False):
                write_tree(full)

    # TODO: create tree object