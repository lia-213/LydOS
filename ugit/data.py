"""Object storage and reference file helpers for ugit.
Handles everything that directly touches the disk (object database and refs)."""

import hashlib
import json
import os
import shutil

from collections import namedtuple
from contextlib import contextmanager

# Will be initialised in cli.main()
""" establishes a module-level global var. that tracks where ugit looks for
repository data (like .ugit/objects, .ugit/refs, etc.)"""
GIT_DIR = None

"""Context manager designed to temporarily swap out the location of the 
.ugit directory (like running a command in a different git repository or
temporary repo) and then automatically restore it back to what is was 
when the task is done."""
"""context managers turn a simple generator function into smth you can use 
with a with block - instead of writing a full class with __enter__ and __exit__
methods, @contextmanager elts you write a single function
---- everything before "yield" runs when entering the "with" block
---- everything after "yield" runs when exiting the with block"""

@contextmanager
def change_git_dir(new_dir):
    global GIT_DIR # "global" - modifications inside this context manager function should update the module's top-level GIT_DIR variable, rather than crating a temporary local variable with the same name
    old_dir = GIT_DIR # saves current repo path before making any changes, acting as a bookmark so it knows where to return to later
    GIT_DIR = os.path.join(new_dir, '.ugit') # switches GIT_DIR to point to the .ugit folder inside new_dir
    yield # where the execution (in the context manager) pauses and control is handed over to whatever code is inside the with block
    GIT_DIR = old_dir # once the code inside the "with" block finishes executing (or raises an exception), Python jumps back here to restore GIT_DIR to its og path


def init():
    """Create the object database directory structure for a repository."""
    objects_dir = os.path.join(GIT_DIR, 'objects')

    if os.path.exists(GIT_DIR):
        print("(Bonus!) Reinitialised existing ugit repository!")
    else:
        # creates both .ugit (GIT_DIR) and .ugit/objects (join(GIT_DIR, 'objects')) as it creates the latter recursively
        os.makedirs(objects_dir, exist_ok=True)


RefValue = namedtuple('RefValue', ['symbolic', 'value'])


def update_ref(ref, value, deref=True):
    """Write an OID into a named reference under the ugit directory."""

    ref = _get_ref_internal(ref, deref)[0]
    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)

    with open(ref_path, 'w') as f:
        if value.symbolic:
            f.write(f'ref: {value.value}')
        else:
            f.write(value.value)

def get_ref(ref, deref=True):
    return _get_ref_internal(ref, deref)[1]

def delete_ref(ref, deref=True):
    ref = _get_ref_internal(ref, deref)[0]
    os.remove(os.path.join(GIT_DIR, ref))

def _get_ref_internal(ref, deref, seen=None):
    """Helper Function: Read a reference file and return its stored OID, if it exists."""
    seen = seen or set()
    ref_path = os.path.join(GIT_DIR, ref)

    # 1. Return early if the reference file doesn't exist
    if not os.path.isfile(ref_path):
        return ref, RefValue(symbolic=False, value=None)

    if ref in seen:
        return ref, RefValue(symbolic=False, value=None)

    # 2. Read file content safely
    with open(ref_path) as f:
        value = f.read().strip()

    symbolic = bool(value) and value.startswith('ref:')
    if symbolic:
        value = value.split(':', 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True, seen=seen | {ref})
    
    return ref, RefValue(symbolic=symbolic, value=value)

def iter_refs(prefix='', deref=True):
    """Yield all known references together with their resolved OIDs."""
    refs = ['HEAD']
    for root, _, filenames in os.walk(os.path.join(GIT_DIR, 'refs')):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(os.path.join(root, name) for name in filenames)

    for refname in refs:
        if not refname.startswith(prefix):
            continue
        ref = get_ref(refname, deref=deref)
        yield refname, ref

@contextmanager
def get_index():
    index = {}
    if os.path.isfile(os.path.join(GIT_DIR, 'index')):
        with open(os.path.join(GIT_DIR, 'index')) as f:
            index = json.load(f)

    yield index

    with open(os.path.join(GIT_DIR, 'index'), 'w') as f:
        json.dump(index, f)


def hash_object(data, type_='blob'):
    """Store a typed object and return the SHA-256 object ID used as its name."""
    obj = type_.encode() + b'\x00' + data
    oid = hashlib.sha256(obj).hexdigest()

    # .ugit/objects/the_hash_string
    object_path = os.path.join(GIT_DIR, 'objects', oid)

    with open(object_path, 'wb') as out:
        out.write(obj)

    return oid


def get_object(oid, expected='blob'):
    """Load an object by OID and optionally validate its stored type."""
    object_path = os.path.join(GIT_DIR, 'objects', oid)

    with open(object_path, 'rb') as f:
        obj = f.read()
    
    type_, _, content = obj.partition(b'\x00')
    type_ = type_.decode()

    if expected is not None and type_ != expected:
        raise ValueError(f'Expected {expected}, got {type_}')

    return content

def object_exists(oid):
    if not oid:
        return False
    return os.path.isfile(os.path.join(GIT_DIR, 'objects', oid))

def fetch_object_if_missing(oid, remote_git_dir):
    """conditionally copy objects from a remote repository by OID"""
    if object_exists(oid):
        return
    remote_git_dir = os.path.join(remote_git_dir, '.ugit')
    shutil.copy(os.path.join(remote_git_dir, 'objects', oid), os.path.join(GIT_DIR, 'objects', oid))

def push_object(oid, remote_git_dir):
    remote_git_dir = os.path.join(remote_git_dir, '.ugit')
    shutil.copy(os.path.join(GIT_DIR, 'objects', oid),
                os.path.join(remote_git_dir, 'objects', oid))

    