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

def hash_object(data):
    oid = hashlib.sha256(data).hexdigest()

    # .ugit/objects/the_hash_string
    object_path = os.path.join(GIT_DIR, 'objects', oid)

    with open(object_path, 'wb') as out:
        out.write(data)
    
    return oid

def get_object(oid):
    object_path = os.path.join(GIT_DIR, 'objects', oid)

    with open(object_path, 'rb') as f:
        return f.read()