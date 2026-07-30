"""Core repository tree, commit, and reference operations for ugit.
Handles the higher-level concepts built on top of data.py.
This is base.py"""

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
    data.update_ref('HEAD', data.RefValue(symbolic=True, value=os.path.join('refs', 'heads', 'master')), deref=False)

def write_tree():
    """Index is flat, we need it as a tree of dicts"""
    index_as_tree = {}
    with data.get_index() as index:
        for path, oid in index.items():
            dirpath, filename = os.path.split(path)

            current = index_as_tree
            # Find the dict for the directory of this file
            if dirpath:
                for dirname in dirpath.split(os.sep):
                    current = current.setdefault(dirname, {})
            current[filename] = oid

    def write_tree_recursive(tree_dict):
        entries = []
        for name, value in tree_dict.items():
            if type(value) is dict:
                type_ = 'tree'
                oid = write_tree_recursive(value)
            else:
                type_ = 'blob'
                oid = value
            entries.append((name, oid, type_))

        tree = ''.join(f'{type_} {oid} {name}\n'
                       for name, oid, type_ in sorted(entries))
        return data.hash_object(tree.encode(), 'tree')

    return write_tree_recursive(index_as_tree)

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
                # result['src/main.py'] = [{oid}]
                result[path] = data.hash_object(f.read()) 
    return result

def get_index_tree():
    with data.get_index() as index:
        return index

def _empty_current_directory():
    """Remove empty directories from the current tree while preserving ignored paths."""
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(os.path.join(root, filename))
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
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

def read_tree(tree_oid, update_working=False):
    """uses get_tree to get the file OIDs and writes them into the working dir.
    Mimics git checkout <old-commit hash>, which never deletes brand-new, untracked files. It instead leaves them alone precisely so I don't accidentally lose hours of uncommitted work just becuase I wanted to look at an old snapshot."""
    with data.get_index() as index:
        old_index = dict(index)
        index.clear()
        index.update(get_tree(tree_oid))

        if update_working:
            _checkout_index(index, old_index)

def read_tree_merged(t_base, t_HEAD, t_other, update_working=False):
    with data.get_index() as index:
        old_index = dict(index)
        index.clear()
        index.update(diff.merge_trees(
            get_tree(t_base),
            get_tree(t_HEAD), 
            get_tree(t_other)
        ))

        if update_working:
            _checkout_index(index, old_index)

def _checkout_index(index, old_index=None):
    old_index = old_index or {}

    # Remove files that were tracked before but aren't in the new tree
    for path in old_index:
        if path not in index and os.path.exists(path):
            os.remove(path)

    # Write/update files that are in the new tree
    for path, oid in index.items():
        os.makedirs(os.path.dirname(os.path.join('.', path)) or '.', exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid, 'blob'))

def commit(message):
    """Create a commit object for the current tree and move HEAD to it."""
    commit = f'tree {write_tree()}\n'

    HEAD = data.get_ref('HEAD').value
    if HEAD:
        commit += f'parent {HEAD}\n'
    MERGE_HEAD = data.get_ref('MERGE_HEAD').value
    if MERGE_HEAD:
        commit += f'parent {MERGE_HEAD}\n'
        data.delete_ref('MERGE_HEAD', deref=False)

    commit += '\n'
    commit += f'{message}\n'

    oid = data.hash_object(commit.encode(), 'commit')

    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))

    return oid

def checkout(name):
    """Replace the working tree with the snapshot referenced by a commit OID."""
    oid = get_oid(name)
    commit = get_commit(oid)
    read_tree(commit.tree, update_working=True)
    
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
    merge_base = get_merge_base(other, HEAD)
    c_other = get_commit(other)

    # Handle fast-forward merge
    if merge_base == HEAD:
        read_tree(c_other.tree, update_working=True)
        data.update_ref('HEAD',
                        data.RefValue(symbolic=False, value=other))
        print('Fast-forward merge, no need to commit')
        return
    
    data.update_ref('MERGE_HEAD', data.RefValue(symbolic=False, value=other))

    c_base = get_commit(merge_base)
    c_HEAD = get_commit(HEAD)
    read_tree_merged(c_base.tree, c_HEAD.tree, c_other.tree, update_working=True)
    print('Merged in working tree\nPlease commit')

def get_merge_base(oid1, oid2):
    parents1 = set(iter_commits_and_parents({oid1}))

    for oid in iter_commits_and_parents({oid2}):
        if oid in parents1:
            return oid

def is_ancestor_of(commit, maybe_ancestor):
    """Returns True if maybe_ancestor exists within the commit history of the commit."""
    return maybe_ancestor in iter_commits_and_parents({commit}) 
   
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
    # N.B. must yield the oid before accessing it (to allow caller to fetch it if needed)
    # modified BFS with double ended queue so the main-line history is prioritised
    oids = deque(oids) # converts input list of starting commit hashes into a collections.deque so items can be efficiently popped and pushed from both the left and right ends
    visited = set() # keeps track of commit OIDs we have already processed to prevent infinite loops when encountering merge commits or duplicate paths

    while oids:
        oid = oids.popleft() # takes next commit hash from the left side of the queue
        if not oid or oid in visited: # skips None values or commit hashes alr processed
            continue
        # marks the commit as visited and yields its hash before attempting to fetch its data
        visited.add(oid)
        yield oid # yielding first lets callers pull or download the object dynamically before get_commit(oid) tries to parse it

        commit = get_commit(oid) # retrieves and pares the commit object from the database to extract its parent references
        # Return first parent next
        oids.extendleft(commit.parents[:1]) # pushes the first parent (the main lineage) to the left of the queue so it gets processed next on the very next iteration
        # Return other parents later
        oids.extend(commit.parents[1:]) # pushes any additional parents (from merge commits) to the right of the queue so they get processed later

def iter_objects_in_commits(oids):
    # N.B. Must yield the oid before accessing it (to allow caller to fetch it if needed)
    """yields every single object inside commit objects, including all tree directories and file blobs
    --- this is how Git knows every object needed to package a commit for transfer.
    Note: before accessing an OID, we yield it, to give the caller a chance to fetch it if it is missing."""
    visited = set() # tracks all object hashes (commits, trees and blobs) to ensure each unique object is onlly yielded once
    def iter_objects_in_tree(oid): # recursive generator (inner helper) that deeply walks directory trees
        visited.add(oid)
        yield oid # yields the tree object itself and marks it visited
        for type_, oid, _ in _iter_tree_entries(oid): # iterates through every entry inside the tree
            if oid not in visited:
                # if the entry is a sub-directory tree, it recursively yields all objects inside that tree
                if type_ == 'tree':
                    yield from iter_objects_in_tree(oid)
                else:
                    visited.add(oid) # if it's a file blob, it marks the blob visited and yields its OID
                    yield oid

    # calls iter_commits_and_parents(oids) to iterate through every commit reachable from the initial oids
    for oid in iter_commits_and_parents(oids):
        yield oid # yields commit oid
        commit = get_commit(oid)
        if commit.tree not in visited: # gets the root tree oid of that commit and if tree not yet visited, ...
            yield from iter_objects_in_tree(commit.tree) # streams all sub-trees and file blobs belonging to that commit snapshot

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

def add(filenames):
    # TODO: add "ugit add ." functionality
    # if not filenames:
        
    def add_file(filename):
        # Normalise path
        filename = os.path.relpath(filename)
        with open(filename, 'rb') as f:
            oid = data.hash_object(f.read())
        index[filename] = oid

    def add_directory(dirname):
        for root, _, filenames in os.walk(dirname):
            for filename in filenames:
                # Normalise path
                path = os.path.relpath(os.path.join(root, filename))
                if is_ignored(path) or not os.path.isfile(path):
                    continue
                add_file(path)

    with data.get_index() as index:
        for name in filenames:
            if os.path.isfile(name):
                add_file(name)
            elif os.path.isdir(name):
                add_directory(name)

def is_ignored(path):
    """Return True when a path belongs to ugit internals or the local virtualenv."""
    parts = Path(path).parts
    
    # Blocking ugit, real git and the venv from being scanned/deleted
    return ('.ugit' in parts or
            '.git' in parts or
            '.venv' in parts or
            'ugit.egg-info' in parts)