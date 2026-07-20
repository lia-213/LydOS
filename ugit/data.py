import hashlib
import os

GIT_DIR = '.ugit'

def init():
    objects_dir = os.path.join(GIT_DIR, 'objects')

    if os.path.exists(GIT_DIR):
        print("(Bonus!) Reinitialised existing ugit repository!")
    else:
        # creates both .ugit (GIT_DIR) and .ugit/objects (join(GIT_DIR, 'objects')) as it creates the latter recursively
        os.makedirs(objects_dir, exist_ok=True)

def set_HEAD(oid):
    with open(os.path.join(GIT_DIR, "HEAD"), 'w') as f:
        f.write(oid)

def get_HEAD():
    if os.path.isfile(os.path.join(GIT_DIR, 'HEAD')):
        with open(os.path.join(GIT_DIR, 'HEAD')) as f:
            return f.read().strip()
        
def hash_object(data, type_='blob'):
    obj = type_.encode() + b'\x00' + data
    oid = hashlib.sha256(obj).hexdigest()

    # .ugit/objects/the_hash_string
    object_path = os.path.join(GIT_DIR, 'objects', oid)

    with open(object_path, 'wb') as out:
        out.write(obj)
    
    return oid

def get_object(oid, expected='blob'):
    object_path = os.path.join(GIT_DIR, 'objects', oid)

    with open(object_path, 'rb') as f:
        obj = f.read()
    
    type_, _, content = obj.partition(b'\x00')
    type_ = type_.decode()

    if expected is not None and type_ != expected:
        raise ValueError(f'Expected {expected}, got {type_}')

    return content