import os
import tempfile
import unittest

from ugit import data


class DataTestCase(unittest.TestCase):
    """Base class that sets up a fresh, isolated .ugit repo per test."""

    def setUp(self):
        self.repo_dir = tempfile.mkdtemp(prefix='ugit-data-test-')
        self.old_cwd = os.getcwd()
        os.chdir(self.repo_dir)
        self._git_dir_cm = data.change_git_dir(self.repo_dir)
        self._git_dir_cm.__enter__()
        data.init()

    def tearDown(self):
        self._git_dir_cm.__exit__(None, None, None)
        os.chdir(self.old_cwd)


class TestObjectStorage(DataTestCase):
    def test_hash_and_get_object_roundtrip(self):
        oid = data.hash_object(b'hello world', 'blob')
        content = data.get_object(oid, 'blob')
        self.assertEqual(content, b'hello world')

    def test_hash_object_is_content_addressed(self):
        oid1 = data.hash_object(b'same content')
        oid2 = data.hash_object(b'same content')
        self.assertEqual(oid1, oid2)

    def test_get_object_raises_on_type_mismatch(self):
        oid = data.hash_object(b'a tree entry', 'tree')
        with self.assertRaises(ValueError):
            data.get_object(oid, 'blob')

    def test_object_exists_true_for_stored_object(self):
        oid = data.hash_object(b'exists')
        self.assertTrue(data.object_exists(oid))

    def test_object_exists_false_for_missing_oid(self):
        fake_oid = 'f' * 64
        self.assertFalse(data.object_exists(fake_oid))

    def test_object_exists_false_for_none(self):
        # Regression test: object_exists(None) used to raise TypeError from
        # os.path.join(GIT_DIR, 'objects', None) -- e.g. when pushing to a
        # brand new empty remote whose HEAD resolves to None.
        self.assertFalse(data.object_exists(None))


class TestRefs(DataTestCase):
    def test_update_and_get_ref_simple(self):
        data.update_ref('refs/heads/master', data.RefValue(symbolic=False, value='deadbeef'))
        ref = data.get_ref('refs/heads/master')
        self.assertFalse(ref.symbolic)
        self.assertEqual(ref.value, 'deadbeef')

    def test_symbolic_ref_dereferences_to_target(self):
        data.update_ref('refs/heads/master', data.RefValue(symbolic=False, value='deadbeef'))
        data.update_ref('HEAD', data.RefValue(symbolic=True, value='refs/heads/master'), deref=False)

        deref_value = data.get_ref('HEAD')
        self.assertFalse(deref_value.symbolic)
        self.assertEqual(deref_value.value, 'deadbeef')

        raw_value = data.get_ref('HEAD', deref=False)
        self.assertTrue(raw_value.symbolic)
        self.assertEqual(raw_value.value, 'refs/heads/master')

    def test_get_ref_missing_returns_none_value(self):
        ref = data.get_ref('refs/heads/does-not-exist')
        self.assertIsNone(ref.value)

    def test_iter_refs_finds_nested_refs(self):
        master_ref = os.path.join('refs', 'heads', 'master')
        tag_ref = os.path.join('refs', 'tags', 'v1')

        data.update_ref(master_ref, data.RefValue(symbolic=False, value='aaaa'))
        data.update_ref(tag_ref, data.RefValue(symbolic=False, value='bbbb'))

        found = dict(data.iter_refs())
        self.assertIn(master_ref, found)
        self.assertIn(tag_ref, found)

    def test_iter_refs_respects_prefix(self):
        master_ref = os.path.join('refs', 'heads', 'master')
        tag_ref = os.path.join('refs', 'tags', 'v1')

        data.update_ref(master_ref, data.RefValue(symbolic=False, value='aaaa'))
        data.update_ref(tag_ref, data.RefValue(symbolic=False, value='bbbb'))

        found = dict(data.iter_refs(prefix=os.path.join('refs', 'heads')))
        self.assertIn(master_ref, found)
        self.assertNotIn(tag_ref, found)


class TestIndex(DataTestCase):
    def test_index_roundtrip_empty(self):
        with data.get_index() as index:
            self.assertEqual(index, {})

    def test_index_roundtrip_populated(self):
        with data.get_index() as index:
            index['file.txt'] = 'someoid'

        with data.get_index() as index:
            self.assertEqual(index, {'file.txt': 'someoid'})


class TestChangeGitDir(unittest.TestCase):
    def test_change_git_dir_restores_previous_value_on_exit(self):
        original = data.GIT_DIR
        temp_dir = tempfile.mkdtemp(prefix='ugit-changedir-test-')

        with data.change_git_dir(temp_dir):
            self.assertEqual(data.GIT_DIR, os.path.join(temp_dir, '.ugit'))

        self.assertEqual(data.GIT_DIR, original)


if __name__ == '__main__':
    unittest.main()
