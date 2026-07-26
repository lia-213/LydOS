"""Core repository tree, commit, and reference operations for ugit.
Handles the higher-level concepts built on top of data.py."""

import itertools
import operator
import os
import string

from collections import namedtuple, deque
from . import data
from . import diff
from pathlib import Path

def init():
    data.init()
    data.update_ref('HEAD', data.RefValue(symbolic=True, value=os.path.join('refs', 'heads', 'master')))

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

def get_working_tree():
    """Scan the current directory and map every (un)tracked file path
    to its current blob hash (OID) on disk without actually saving the
    files to .ugit permanently."""
    result = {} # file_path:file_oid
    for root, _, filenames in os.walk('.'):
        for filename in filenames:
            path = os.path.relpath(os.path.join(root, filename))
            if is_ignored(path) or not os.path.isfile(path):
                continue
            with open(path, 'rb') as f:
                result[path] = data.hash_object(f.read()) # result['src/main.py'] = [{oid}]
    return result

def _empty_current_directory():
    """Remove empty directories from the current tree while preserving ignored paths."""
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

def read_tree_merged(t_HEAD, t_other):
    _empty_current_directory()
    for path, blob in diff.merge_trees(get_tree(t_HEAD), get_tree(t_other)).items():
        os.makedirs(os.path.join('.', os.path.dirname(path)), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(blob)

def commit(message):
    """Create a commit object for the current tree and move HEAD to it."""
    commit = f'tree {write_tree()}\n'

    HEAD = data.get_ref('HEAD').value
    if HEAD:
        commit += f'parent {HEAD}\n'
    commit += '\n'
    commit += f'{message}\n'

    oid = data.hash_object(commit.encode(), 'commit')

    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))

    return oid

def checkout(name):
    """Replace the working tree with the snapshot referenced by a commit OID."""
    oid = get_oid(name)
    commit = get_commit(oid)
    read_tree(commit.tree)
    
    if is_branch(name):
        HEAD = data.RefValue(symbolic=True, value=os.path.join('refs', 'heads', name))
    else:
        HEAD = data.RefValue(symbolic=False, value=oid)

    data.update_ref('HEAD', HEAD, deref=False)

def reset(oid):
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))

def merge(other):
    HEAD = data.get_ref('HEAD').value
    assert HEAD
    c_HEAD = get_commit(HEAD)
    c_other = get_commit(other)

    read_tree_merged(c_HEAD.tree, c_other.tree)
    print('Merged in working tree')

def create_tag(name, oid):
    """Create or update a tag reference for the given object ID."""
    oid = oid or data.get_ref('HEAD')
    data.update_ref(os.path.join('refs', 'tags', name), data.RefValue(symbolic=False, value=oid))

def create_branch(name, oid):
    data.update_ref(os.path.join('refs', 'heads', name), data.RefValue(symbolic=False, value=oid))

def iter_branch_names():
    for refname, _ in data.iter_refs(os.path.join('refs', 'heads')):
        yield os.path.relpath(refname, os.path.join('refs', 'heads'))
        
def is_branch(branch):
    return data.get_ref(os.path.join('refs', 'heads', branch)).value is not None

def get_branch_name():
    HEAD = data.get_ref('HEAD', deref=False)
    if not HEAD.symbolic:
        return None
    HEAD = HEAD.value

    if HEAD.startswith(os.path.join('refs', 'heads')):
        return os.path.relpath(HEAD, os.path.join('refs', 'heads'))
    
Commit = namedtuple('Commit', ['tree', 'parents', 'message'])

def get_commit(oid):
    """Parse a commit object into its tree, parent, and message fields."""
    parents = []
    
    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())

    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parents.append(value)
        else: assert False, f'Unknown field {key}'

    message = '\n'.join(lines)

    return Commit(tree=tree, parents=parents, message=message)

def iter_commits_and_parents(oids):
    """generator that returns all commits that it can reach from a given set of OIDs"""
    oids = deque(oids)
    visited = set()

    while oids:
        oid = oids.popleft()
        if not oid or oid in visited:
            continue
        visited.add(oid)
        yield oid

        commit = get_commit(oid)
        # Return first parent next
        oids.extendleft(commit.parents[:1])
        # Return other parents later
        oids.extend(commit.parents[1:])
        
def get_oid(name):
    """Resolve a ref name, tag, branch, or raw object ID into an OID."""

    if name == '@': name = 'HEAD'

    refs_to_try = [
        name,
        os.path.join('refs', name),
        os.path.join('refs', 'tags', name),
        os.path.join('refs', 'heads', name)
    ]

    for ref in refs_to_try:
        if data.get_ref(ref, deref=False).value:
            return data.get_ref(ref).value
        
        # name is SHA256 (64 hex characters)
        # all = effectively one big AND gate
        is_hex = all(c in string.hexdigits for c in name)
        if len(name) == 64 and is_hex:
            return name
        
    raise ValueError(f'unknown name {name}')

def is_ignored(path):
    """Return True when a path belongs to ugit internals or the local virtualenv."""
    parts = Path(path).parts
    
    # Blocking ugit, real git and the venv from being scanned/deleted
    return ('.ugit' in parts or
            '.git' in parts or
            '.venv' in parts or
            'ugit.egg-info' in parts)