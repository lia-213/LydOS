from collections import defaultdict
import difflib

from . import data


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
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
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