"""Object storage and reference file helpers for ugit."""

import hashlib
import os

GIT_DIR = '.ugit'


def init():
    """Create the object database directory structure for a repository."""
    objects_dir = os.path.join(GIT_DIR, 'objects')

    if os.path.exists(GIT_DIR):
        print("(Bonus!) Reinitialised existing ugit repository!")
    else:
        # creates both .ugit (GIT_DIR) and .ugit/objects (join(GIT_DIR, 'objects')) as it creates the latter recursively
        os.makedirs(objects_dir, exist_ok=True)


def update_ref(ref, oid):
    """Write an OID into a named reference under the ugit directory."""
    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    print(f'writing {oid} to {ref_path}')
    with open(ref_path, 'w') as f:
        f.write(oid)


def get_ref(ref):
    """Read a reference file and return its stored OID, if it exists."""
    ref_path = os.path.join(GIT_DIR, ref)
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            return f.read().strip()


def iter_refs():
    """Yield all known references together with their resolved OIDs."""
    refs = ['HEAD']
    for root, _, filenames in os.walk(os.path.join(GIT_DIR, 'refs')):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(os.path.join(root, name) for name in filenames)

    for refname in refs:
        yield refname, get_ref(refname)


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