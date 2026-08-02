import os
import tempfile
import unittest

from ugit import base
from ugit import data


class BaseTestCase(unittest.TestCase):
    """Base class that sets up a fresh, isolated ugit repo per test."""

    def setUp(self):
        self.repo_dir = tempfile.mkdtemp(prefix='ugit-base-test-')
        self.old_cwd = os.getcwd()
        os.chdir(self.repo_dir)
        self._git_dir_cm = data.change_git_dir(self.repo_dir)
        self._git_dir_cm.__enter__()
        base.init()

    def tearDown(self):
        self._git_dir_cm.__exit__(None, None, None)
        os.chdir(self.old_cwd)

    def write_file(self, path, content):
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)


class TestWriteTree(BaseTestCase):
    def test_write_tree_flat_files(self):
        self.write_file('a.txt', 'a')
        self.write_file('b.txt', 'b')
        base.add(['a.txt', 'b.txt'])

        tree_oid = base.write_tree()
        tree = base.get_tree(tree_oid)

        self.assertEqual(set(tree.keys()), {'a.txt', 'b.txt'})

    def test_write_tree_nested_paths(self):
        # Regression test: write_tree() used to do `for dirname in dirpath`,
        # which iterates a path string character-by-character instead of by
        # path segment, mangling nested paths like 'sub/deeper/deep.txt'
        # into 's/u/b/...'. This confirms the fix (splitting on os.sep).
        self.write_file(os.path.join('sub', 'deeper', 'deep.txt'), 'nested content')
        base.add(['sub'])

        tree_oid = base.write_tree()
        tree = base.get_tree(tree_oid)

        expected_path = 'sub/deeper/deep.txt'
        self.assertIn(expected_path, tree)

    def test_write_tree_is_deterministic(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        oid1 = base.write_tree()
        oid2 = base.write_tree()
        self.assertEqual(oid1, oid2)


class TestCommitAndOid(BaseTestCase):
    def test_first_commit_has_no_parent(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')
        commit_obj = base.get_commit(c1)
        self.assertEqual(commit_obj.parents, [])

    def test_second_commit_has_first_as_parent(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        self.write_file('b.txt', 'b')
        base.add(['b.txt'])
        c2 = base.commit('second')

        commit_obj = base.get_commit(c2)
        self.assertEqual(commit_obj.parents, [c1])

    def test_get_oid_resolves_raw_oid_tag_and_branch(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')
        base.create_tag('v1', c1)
        base.create_branch('feature', c1)

        self.assertEqual(base.get_oid(c1), c1)
        self.assertEqual(base.get_oid('v1'), c1)
        self.assertEqual(base.get_oid('feature'), c1)
        self.assertEqual(base.get_oid('@'), c1)

    def test_get_oid_raises_for_unknown_name(self):
        with self.assertRaises(ValueError):
            base.get_oid('does-not-exist')


class TestCheckout(BaseTestCase):
    def test_checkout_by_oid_detaches_head(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        base.checkout(c1)

        head = data.get_ref('HEAD', deref=False)
        self.assertFalse(head.symbolic)
        self.assertEqual(head.value, c1)

    def test_checkout_by_branch_name_reattaches_head(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        base.checkout(c1)  # detach
        base.checkout('master')  # reattach

        head = data.get_ref('HEAD', deref=False)
        self.assertTrue(head.symbolic)
        self.assertEqual(head.value, os.path.join('refs', 'heads', 'master'))

    def test_checkout_only_touches_tracked_files(self):
        # Regression test for the old _empty_current_directory() behaviour,
        # which deleted every untracked file in the working directory on
        # every checkout. Untracked files must survive.
        self.write_file('tracked.txt', 'v1')
        base.add(['tracked.txt'])
        c1 = base.commit('first')

        self.write_file('untracked.txt', 'never added')

        self.write_file('tracked.txt', 'v2')
        base.add(['tracked.txt'])
        base.commit('second')

        base.checkout(c1)

        self.assertTrue(os.path.exists('untracked.txt'))
        with open('tracked.txt') as f:
            self.assertEqual(f.read(), 'v1')


class TestResetAndMerge(BaseTestCase):
    def test_reset_moves_ref_but_not_working_directory(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        self.write_file('b.txt', 'b')
        base.add(['b.txt'])
        base.commit('second')

        base.reset(c1)

        master_oid = data.get_ref('refs/heads/master').value
        self.assertEqual(master_oid, c1)
        # reset does not touch disk -- b.txt should still be sitting there
        self.assertTrue(os.path.exists('b.txt'))

    def test_fast_forward_merge_advances_master(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')
        base.create_branch('feature', c1)

        base.checkout('feature')
        self.write_file('b.txt', 'b')
        base.add(['b.txt'])
        c2 = base.commit('second on feature')

        base.checkout('master')
        base.merge(c2)

        master_oid = data.get_ref('refs/heads/master').value
        self.assertEqual(master_oid, c2)
        self.assertTrue(os.path.exists('b.txt'))


class TestIsIgnored(unittest.TestCase):
    def test_ignores_ugit_internals(self):
        self.assertTrue(base.is_ignored(os.path.join('.ugit', 'objects', 'abc')))

    def test_ignores_venv(self):
        self.assertTrue(base.is_ignored(os.path.join('.venv', 'lib', 'thing.py')))

    def test_does_not_ignore_regular_paths(self):
        self.assertFalse(base.is_ignored(os.path.join('src', 'main.py')))


if __name__ == '__main__':
    unittest.main()
