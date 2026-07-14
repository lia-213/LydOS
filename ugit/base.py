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

def _empty_current_directory():
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(os.path.join(root, filename))
            if is_ignored(path) or not os.path.isfile(path):
                continue
        for dirname in dirnames:
            path = os.path.relpath(os.path.join(root, dirname))
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except(OSError):
                # FileNotFoundError, PermissionError and AlreadyExistsError inherit directly from OSError
                # deletion might fail if the directory contains ignored files, so it's ok :)
                pass

def read_tree(tree_oid):
    """uses get_tree to get the file OIDs and writes them into the working dir.
    Mimics git checkout <old-commit hash>, which never deletes brand-new, untracked files. It instead leaves them alone precisely so I don't accidentally lose hours of uncommitted work just becuase I wanted to look at an old snapshot."""
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid))

def commit(message):
    commit = f'tree {write_tree()}\n'
    commit += '\n'
    commit += f'{message}\n'

    oid = data.hash_object(commit.encode(), 'commit')

    data.set_HEAD(oid)

    return oid

def is_ignored(path):
    parts = Path(path).parts
    
    # Blocking ugit, real git and the venv from being scanned/deleted
    return ('.ugit' in parts or
            '.git' in parts or
            '.venv' in parts or
            'ugit.egg-info' in parts)