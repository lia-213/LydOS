import os

from . import data
from pathlib import Path

def write_tree(directory='.'):
    """returns an OID"""
    entries = []
    with os.scandir(directory) as it:
        for entry in it:
            full = os.path.join(directory, entry.name)

            if is_ignored(full):
                continue

            if entry.is_file(follow_symlinks=False):
                type_ = 'blob'
                with open(full, 'rb') as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir(follow_symlinks=False):
                type_ = 'tree'
                oid = write_tree(full)
            entries.append((entry.name, oid, type_))

    tree = ''.join(f'{type_} {oid} {name}\n'
                   for name, oid, type_ in sorted(entries))
    return data.hash_object(tree.encode(), 'tree')

def _iter_tree_entries(oid):
    """a generator that will take an OID of a tree, tokenise it line-by-line and yield the raw string values"""
    if not oid:
        return
    tree = data.get_object(oid, 'tree')
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(' ', 2)
        # yield returns a line-by-line tuple, one at a time
        yield type_, oid, name

def get_tree(oid, base_path=''):
    """uses _iter_tree_entries to recursively parse a tree into a dict"""
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        if '/' in name or name in ('..', '.'):
            raise ValueError(f"Malicious or invalid filename detected in tree: {name}")
        path = base_path + name
        if type_ == 'blob':
            result[path] = oid
        elif type_ == 'tree':
            result.update(get_tree(oid, f'{path}/'))
        else:
            raise ValueError(f'Unknown tree entry {type_}')
    return result

def read_tree(tree_oid):
    """uses get_tree to get the file OIDs and writes them into the working dir"""
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid))
            
def is_ignored(path):
    return '.ugit' in Path(path).parts