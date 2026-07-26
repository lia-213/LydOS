from collections import defaultdict
import difflib
import subprocess
from tempfile import NamedTemporaryFile as temp

from . import data

import os
from contextlib import contextmanager

@contextmanager
def Temp():
    """Custom temp file manager that safely closes files before subprocess operations."""
    with temp(delete=False) as f:
        try:
            yield f
        finally:
            if os.path.exists(f.name):
                os.remove(f.name)

def compare_trees(*trees):
    """Handles arbitrary tree comparisos cleanly using generator unpacking of *oids"""
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield(path, *oids)

def iter_changed_files(t_from, t_to):
    """Generator function that takes two tree objects 
    (e.g. HEAD_tree as t_from, working_tree as t_to)"""
    # o_from: OID (blob hash) of file in t_from, or None if OID didn't exist
    # o_to: OID (blob hash) of file in t_to, or None if doesn't exist anymore
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to: # filters out unchanged files (o_from == o_to)
            action = ('new file' if not o_from else
                      'deleted' if not o_to else
                      'modified')
            yield path, action

def diff_trees(t_from, t_to):
    """Filters out unchanged files early: o_from != o_to"""
    output = ''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += diff_blobs(o_from, o_to, path)
    return output

def diff_blobs(o_from, o_to, path='a/file'):
    """Compares two blob contents and returns a unified diff string."""
    # Get text from object database (or empty list if file didn't exist)
    from_lines = data.get_object(o_from).decode().splitlines(keepends=True) if o_from else []
    to_lines = data.get_object(o_to).decode().splitlines(keepends=True) if o_to else []

    # Generate unified diff lines
    diff = difflib.unified_diff(
        from_lines,
        to_lines,
        fromfile=f'a/{path}',
        tofile=f'b/{path}'
    )

    return ''.join(diff)

def merge_trees(t_base, t_HEAD, t_other):
    tree = {}
    for path, o_base, o_HEAD, o_other in compare_trees(t_base, t_HEAD, t_other):
        tree[path] = data.hash_object(merge_blobs(o_base, o_HEAD, o_other))
    return tree

def merge_blobs(o_base, o_HEAD, o_other):
    with Temp() as f_base, Temp() as f_HEAD, Temp() as f_other:
        for oid, f in ((o_base, f_base), (o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        with subprocess.Popen(
            ['diff3', 'm'
             '-L', 'HEAD', f_HEAD.name,
             '-L', 'BASE', f_base.name,
             '-L', 'MERGE_HEAD', f_other.name
             ], stdout=subprocess.PIPE) as proc:
             output, _ = proc.communicate()
             if proc.returncode not in (0, 1):
                raise RuntimeError(f"'diff3' failed with return code {proc.returncode}")

        return output