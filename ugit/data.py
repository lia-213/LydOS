"""Object storage and reference file helpers for ugit.
Handles everything that directly touches the disk (object database and refs)."""

import hashlib
import os

from collections import namedtuple

GIT_DIR = '.ugit'


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
    if value.symbolic:
        raise ValueError(f"Expected a concrete value, but got symbolic value: {value}")
    ref = _get_ref_internal(ref, deref)[0]
    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(value.value)

def get_ref(ref, deref=True):
    return _get_ref_internal(ref, deref)[1]

def delete_ref(ref, deref=True):
    ref = _get_ref_internal(ref, deref)[0]
    os.remote(os.path.join(GIT_DIR, ref))

def _get_ref_internal(ref, deref):
    """Helper Function: Read a reference file and return its stored OID, if it exists."""
    ref_path = os.path.join(GIT_DIR, ref)

    # 1. Return early if the reference file doesn't exist
    if not os.path.isfile(ref_path):
        return ref, RefValue(symbolic=False, value=None)

    # 2. Read file content safely
    with open(ref_path) as f:
        value = f.read().strip()

    symbolic = bool(value) and value.startswith('ref:')
    if symbolic:
        value = value.split(':', 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)
    
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
        yield refname, get_ref(refname, deref=deref)


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