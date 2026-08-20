"""Tests for the ugit.remote fetch and push helpers."""

import os
import tempfile
import unittest
from contextlib import contextmanager

from ugit import base
from ugit import data
from ugit import remote


@contextmanager
def repo(path):
    """Point both cwd and GIT_DIR at `path` for the duration of the block,
    restoring both on exit. ugit's file-writing helpers (base.add, etc.)
    use the current working directory, while object/ref storage uses
    data.GIT_DIR -- both need to agree on which repo is 'active'."""
    old_cwd = os.getcwd()
    os.chdir(path)
    with data.change_git_dir(path):
        yield
    os.chdir(old_cwd)


def make_repo_with_commit(message='first', filename='file.txt', content='hello\n'):
    """Create a temporary repository containing a single commit."""
    repo_dir = tempfile.mkdtemp(prefix='ugit-remote-test-')
    with repo(repo_dir):
        base.init()
        with open(filename, 'w') as f:
            f.write(content)
        base.add([filename])
        oid = base.commit(message)
    return repo_dir, oid


class TestFetch(unittest.TestCase):
    def test_fetch_copies_objects_and_creates_local_ref(self):
        """fetch() should copy remote objects and create remote-tracking refs."""
        remote_dir, remote_commit = make_repo_with_commit()
        local_dir = tempfile.mkdtemp(prefix='ugit-remote-local-')

        with repo(local_dir):
            base.init()
            remote.fetch(remote_dir)

            self.assertTrue(data.object_exists(remote_commit))

            local_remote_ref = data.get_ref(os.path.join('refs', 'remote', 'master'))
            self.assertEqual(local_remote_ref.value, remote_commit)

    def test_fetch_does_not_touch_local_master(self):
        """fetch() should not overwrite the local branch tip."""
        remote_dir, remote_commit = make_repo_with_commit()
        local_dir, local_commit = make_repo_with_commit(message='local first', filename='local.txt')

        with repo(local_dir):
            remote.fetch(remote_dir)
            master_ref = data.get_ref(os.path.join('refs', 'heads', 'master'))
            self.assertEqual(master_ref.value, local_commit)


class TestPush(unittest.TestCase):
    def test_push_to_empty_remote_succeeds(self):
        """push() should initialize an empty remote repository."""
        # Regression test: pushing to a brand-new remote with no commits
        # used to crash with TypeError, because _get_remote_refs() returns
        # {'HEAD': None} for an empty repo, and that None oid was passed
        # straight into data.object_exists() -> os.path.join(..., None).
        local_dir, local_commit = make_repo_with_commit()
        remote_dir = tempfile.mkdtemp(prefix='ugit-remote-empty-')

        with repo(remote_dir):
            base.init()

        with repo(local_dir):
            remote.push(remote_dir, os.path.join('refs', 'heads', 'master'))

        with repo(remote_dir):
            self.assertTrue(data.object_exists(local_commit))
            remote_master = data.get_ref(os.path.join('refs', 'heads', 'master'))
            self.assertEqual(remote_master.value, local_commit)

    def test_push_updates_existing_remote_ref(self):
        """push() should advance an existing remote ref on fast-forward."""
        remote_dir, remote_commit = make_repo_with_commit(message='remote first')
        local_dir = tempfile.mkdtemp(prefix='ugit-remote-local2-')

        with repo(local_dir):
            base.init()
            remote.fetch(remote_dir)

        # Build local history on top of the fetched remote commit so the
        # push is a legitimate fast-forward from the remote's perspective.
        with repo(local_dir):
            data.update_ref(os.path.join('refs', 'heads', 'master'),
                             data.RefValue(symbolic=False, value=remote_commit))
            base.checkout('master')
            with open('local-addition.txt', 'w') as f:
                f.write('more content\n')
            base.add(['local-addition.txt'])
            local_commit = base.commit('local addition')

            remote.push(remote_dir, os.path.join('refs', 'heads', 'master'))

        with repo(remote_dir):
            remote_master = data.get_ref(os.path.join('refs', 'heads', 'master'))
            self.assertEqual(remote_master.value, local_commit)

    def test_push_rejects_non_fast_forward(self):
        """push() should reject non-fast-forward updates."""
        remote_dir, remote_commit = make_repo_with_commit(message='remote first')
        local_dir, local_commit = make_repo_with_commit(message='unrelated local history')

        with repo(local_dir):
            with self.assertRaises(ValueError):
                remote.push(remote_dir, os.path.join('refs', 'heads', 'master'))

    def test_push_raises_if_local_ref_missing(self):
        """push() should raise when the requested local ref is absent."""
        remote_dir, _ = make_repo_with_commit()
        local_dir = tempfile.mkdtemp(prefix='ugit-remote-nolocal-')

        with repo(local_dir):
            base.init()
            with self.assertRaises(ValueError):
                remote.push(remote_dir, os.path.join('refs', 'heads', 'master'))


if __name__ == '__main__':
    unittest.main()
