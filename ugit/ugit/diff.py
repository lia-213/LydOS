"""Tree and blob diff helpers for ugit."""

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
            f.close()
            if os.path.exists(f.name):
                os.remove(f.name)

def compare_trees(*trees):
    """Yield each path together with the object IDs from all supplied trees."""
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield(path, *oids)

def iter_changed_files(t_from, t_to):
    """Yield the paths whose blob IDs differ between two trees."""
    # o_from: OID (blob hash) of file in t_from, or None if OID didn't exist
    # o_to: OID (blob hash) of file in t_to, or None if doesn't exist anymore
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to: # filters out unchanged files (o_from == o_to)
            action = ('new file' if not o_from else
                      'deleted' if not o_to else
                      'modified')
            yield path, action

def diff_trees(t_from, t_to):
    """Return a unified diff for every changed path between two trees."""
    output = ''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += diff_blobs(o_from, o_to, path)
    return output

def diff_blobs(o_from, o_to, path='a/file'):
    """Compares two blob contents and returns a unified diff string."""
    # Get text from object database (or empty list if file didn't exist)
    try:
        from_lines = data.get_object(o_from).decode('utf-8').splitlines(keepends=True) if o_from else []
        to_lines = data.get_object(o_to).decode('utf-8').splitlines(keepends=True) if o_to else []
    except UnicodeDecodeError:
        return f'Binary files a/{path} and b/{path} differ\n'

    # Generate unified diff lines
    diff = difflib.unified_diff(
        from_lines,
        to_lines,
        fromfile=f'a/{path}',
        tofile=f'b/{path}'
    )

    return ''.join(diff)

def merge_trees(t_base, t_HEAD, t_other):
    """Merge three tree snapshots path by path and return the merged tree."""
    tree = {}
    for path, o_base, o_HEAD, o_other in compare_trees(t_base, t_HEAD, t_other):
        tree[path] = data.hash_object(merge_blobs(o_base, o_HEAD, o_other))
    return tree

def merge_blobs(o_base, o_HEAD, o_other):
    """Merge three blob versions with diff3 and return the merged bytes."""
    with Temp() as f_base, Temp() as f_HEAD, Temp() as f_other:
        for oid, f in ((o_base, f_base), (o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        with subprocess.Popen(
            ['diff3', '-m',
            '-L', 'HEAD', '-L', 'BASE', '-L', 'MERGE_HEAD',
            f_HEAD.name, f_base.name, f_other.name
            ], stdout=subprocess.PIPE) as proc:
            output, _ = proc.communicate()
            if proc.returncode not in (0, 1):
                raise RuntimeError(f"'diff3' failed with return code {proc.returncode}")

        return output