import os
import tempfile
import unittest
from argparse import Namespace

from ugit import base
from ugit import cli
from ugit import data
from ugit import diff


class DiffTests(unittest.TestCase):
    def test_diff_trees_handles_binary_blob(self):
        repo_dir = tempfile.mkdtemp(prefix='ugit-diff-test-')
        old_cwd = os.getcwd()

        try:
            os.chdir(repo_dir)
            with data.change_git_dir(repo_dir):
                data.init()

                with open('file.txt', 'w') as f:
                    f.write('hello\n')
                base.add(['file.txt'])
                first_commit = base.commit('first')

                with open('file.txt', 'wb') as f:
                    f.write(b'hello\n\xff\xfe\xfd\n')
                base.add(['file.txt'])
                second_commit = base.commit('second')

                first_tree = base.get_tree(base.get_commit(first_commit).tree)
                second_tree = base.get_tree(base.get_commit(second_commit).tree)

                output = diff.diff_trees(first_tree, second_tree)

            self.assertIn('Binary files a/file.txt and b/file.txt differ', output)
        finally:
            os.chdir(old_cwd)

    def test_diff_modes_follow_expected_sources(self):
        repo_dir = tempfile.mkdtemp(prefix='ugit-diff-modes-')
        old_cwd = os.getcwd()

        try:
            os.chdir(repo_dir)
            with data.change_git_dir(repo_dir):
                data.init()

                with open('tracked.txt', 'w') as f:
                    f.write('one\n')
                base.add(['tracked.txt'])
                first_commit = base.commit('first')

                with open('tracked.txt', 'w') as f:
                    f.write('two\n')
                base.add(['tracked.txt'])

                with open('tracked.txt', 'w') as f:
                    f.write('three\n')

                no_args = cli._diff(Namespace(commit=None, cached=False))
                cached = cli._diff(Namespace(commit=None, cached=True))
                against_commit = cli._diff(Namespace(commit=first_commit, cached=False))
                commit_cached = cli._diff(Namespace(commit=first_commit, cached=True))

            self.assertIn('+three', no_args)
            self.assertIn('+two', cached)
            self.assertIn('+three', against_commit)
            self.assertIn('+two', commit_cached)
        finally:
            os.chdir(old_cwd)


if __name__ == '__main__':
    unittest.main()