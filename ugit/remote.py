import os

from . import base
from . import data

REMOTE_REFS_BASE = os.path.join('refs', 'heads')
LOCAL_REFS_BASE = os.path.join('refs', 'remote')

def fetch(remote_path):
    """Iterate over all objects and fetch missing ones"""
    # Get refs from server
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    # Fetch missing objects by iterating and fetching on demand
    for oid in base.iter_objects_in_commits(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    # Update local refs to match server
    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE) 
        data.update_ref(os.path.join(LOCAL_REFS_BASE, refname),
                        data.RefValue(symbolic=False, value=value))

def push(remote_path, refname):
    # Get refs data
    remote_refs = _get_remote_refs(remote_path)
    remote_ref = remote_refs.get(refname)
    local_ref = data.get_ref(refname).value # resolve the local reference - reading it to see what oid (commit hash) it currently points to, unwrapping the RefValue object to get the raw hash string with .value

    if not local_ref: raise ValueError(f"Cannot push: reference '{refname}' doesn't exist locally.") # ensures the refernce (e.g. refs/heads/main) actually exists in local repo before proceeding; if it doesn't, execution stops immediately

    if remote_ref and not base.is_ancestor_of(local_ref, remote_ref): raise ValueError(f"Cannot push to '{refname}' on remote: "
                                                                                       "Updates were rejected because the remote commit is not an ancestor of your local commit. "
                                                                                       "(Force push disabled)")

    # Computing which objects the server doesn't have so no need to redownload
    # filter(function, iterable): function -> predicate function (data.object_exists) that takes one item and returns True or False, iterable -> an iterable collection (remote_refs.values(); the list/dict of values we want to test)
    known_remote_refs = filter(data.object_exists, remote_refs.values())
    """
    Functionally equivalent:
    known_remote_refs = [
        oid for oid in remote_refs.values() if data.object_exists(oid)]
    """
    remote_objects = set(base.iter_objects_in_commits(known_remote_refs)) # iter_objects_in_commits only streams new/missing commits down from the remote
    local_objects = set(base.iter_objects_in_commits({local_ref})) # starting from local_ref, it walks backwards through the commit graph and yields every single required oid (inc. parent commits, tree directories and file blobs) needed to fully represent the history up to local ref
    objects_to_push = local_objects - remote_objects

    # Push missing objects
    for oid in objects_to_push:
        data.push_object(oid, remote_path) # copies the actual binary object file (from .ugit/objects/<oid>) over to the destination repository's object store (<remote_path>/.ugit/objects/<oid>)

    # Update server ref to our value
    with data.change_git_dir(remote_path): #uses the context manager to temporarily switch global operations so that any ref/data updates target the remote .ugit directory instead of my local one
        data.update_ref(refname,
                        data.RefValue(symbolic=False, value=local_ref)) # writes or updates the reference file on the remote repo (e.g. <remote_path>/.ugit/refs/heads/main) so that it points directly to local_ref

    # exiting the with block: automatically switches GIT_DIR back to local repo directory
            
def _get_remote_refs(remote_path, prefix=''):
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}