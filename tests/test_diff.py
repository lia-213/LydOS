import os
import shutil
import tempfile
import unittest

from ugit import base
from ugit import data
from ugit import diff


class DiffTestCase(unittest.TestCase):
    """Base class that sets up a fresh, isolated ugit repo per test."""

    def setUp(self):
        self.repo_dir = tempfile.mkdtemp(prefix='ugit-diff-test-')
        self.old_cwd = os.getcwd()
        os.chdir(self.repo_dir)
        self._git_dir_cm = data.change_git_dir(self.repo_dir)
        self._git_dir_cm.__enter__()
        base.init()

    def tearDown(self):
        self._git_dir_cm.__exit__(None, None, None)
        os.chdir(self.old_cwd)


class TestCompareTrees(unittest.TestCase):
    def test_compare_two_trees_reports_all_paths(self):
        t_from = {'a.txt': 'oid1', 'b.txt': 'oid2'}
        t_to = {'a.txt': 'oid1', 'b.txt': 'oid3', 'c.txt': 'oid4'}

        results = dict((path, (o_from, o_to)) for path, o_from, o_to in diff.compare_trees(t_from, t_to))

        self.assertEqual(results['a.txt'], ('oid1', 'oid1'))
        self.assertEqual(results['b.txt'], ('oid2', 'oid3'))
        self.assertEqual(results['c.txt'], (None, 'oid4'))

    def test_compare_trees_supports_arbitrary_arity(self):
        t1 = {'x.txt': 'a'}
        t2 = {'x.txt': 'b'}
        t3 = {'x.txt': 'c'}

        results = list(diff.compare_trees(t1, t2, t3))
        self.assertEqual(results, [('x.txt', 'a', 'b', 'c')])


class TestIterChangedFiles(unittest.TestCase):
    def test_reports_new_modified_and_deleted(self):
        t_from = {'unchanged.txt': 'oid1', 'modified.txt': 'oid2', 'deleted.txt': 'oid3'}
        t_to = {'unchanged.txt': 'oid1', 'modified.txt': 'oidX', 'new.txt': 'oid4'}

        changes = dict(diff.iter_changed_files(t_from, t_to))

        self.assertNotIn('unchanged.txt', changes)
        self.assertEqual(changes['modified.txt'], 'modified')
        self.assertEqual(changes['deleted.txt'], 'deleted')
        self.assertEqual(changes['new.txt'], 'new file')


class TestDiffBlobs(DiffTestCase):
    def test_diff_blobs_shows_added_line(self):
        oid_from = data.hash_object(b'line one\n')
        oid_to = data.hash_object(b'line one\nline two\n')

        result = diff.diff_blobs(oid_from, oid_to, path='file.txt')

        self.assertIn('+line two', result)
        self.assertIn('a/file.txt', result)
        self.assertIn('b/file.txt', result)

    def test_diff_blobs_handles_new_file(self):
        oid_to = data.hash_object(b'brand new\n')
        result = diff.diff_blobs(None, oid_to, path='new.txt')
        self.assertIn('+brand new', result)

    def test_diff_blobs_handles_binary_content(self):
        oid_from = data.hash_object(b'hello\n')
        oid_to = data.hash_object(b'hello\n\xff\xfe\xfd\n')

        result = diff.diff_blobs(oid_from, oid_to, path='file.txt')

        self.assertEqual(result, 'Binary files a/file.txt and b/file.txt differ\n')


class TestDiffTrees(DiffTestCase):
    def test_diff_trees_only_diffs_changed_paths(self):
        self.write_file('a.txt', 'a\n')
        self.write_file('b.txt', 'b\n')
        base.add(['a.txt', 'b.txt'])
        c1 = base.commit('first')

        self.write_file('b.txt', 'b\nb again\n')
        base.add(['b.txt'])
        c2 = base.commit('second')

        t1 = base.get_tree(base.get_commit(c1).tree)
        t2 = base.get_tree(base.get_commit(c2).tree)

        result = diff.diff_trees(t1, t2)

        self.assertIn('b.txt', result)
        self.assertNotIn('a.txt', result)

    def write_file(self, path, content):
        with open(path, 'w') as f:
            f.write(content)


@unittest.skipUnless(shutil.which('diff3'), "requires 'diff3' (GNU diffutils) on PATH")
class TestMergeBlobs(unittest.TestCase):
    def setUp(self):
        self.repo_dir = tempfile.mkdtemp(prefix='ugit-merge-blobs-test-')
        self.old_cwd = os.getcwd()
        os.chdir(self.repo_dir)
        self._git_dir_cm = data.change_git_dir(self.repo_dir)
        self._git_dir_cm.__enter__()
        base.init()

    def tearDown(self):
        self._git_dir_cm.__exit__(None, None, None)
        os.chdir(self.old_cwd)

    def test_merge_blobs_non_conflicting_change(self):
        o_base = data.hash_object(b'line one\nline two\nline three\n')
        o_head = data.hash_object(b'line one CHANGED\nline two\nline three\n')
        o_other = data.hash_object(b'line one\nline two\nline three CHANGED\n')

        result = diff.merge_blobs(o_base, o_head, o_other)

        self.assertIn(b'line one CHANGED', result)
        self.assertIn(b'line three CHANGED', result)
        self.assertNotIn(b'<<<<<<<', result)

    def test_merge_blobs_conflicting_change_inserts_markers(self):
        o_base = data.hash_object(b'shared line\n')
        o_head = data.hash_object(b'head version\n')
        o_other = data.hash_object(b'other version\n')

        result = diff.merge_blobs(o_base, o_head, o_other)

        self.assertIn(b'<<<<<<<', result)
        self.assertIn(b'=======', result)
        self.assertIn(b'>>>>>>>', result)


if __name__ == '__main__':
    unittest.main()