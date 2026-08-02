import io
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import patch

from ugit import base
from ugit import cli
from ugit import data


class CliTestCase(unittest.TestCase):
    """Base class that sets up a fresh, isolated ugit repo per test."""

    def setUp(self):
        self.repo_dir = tempfile.mkdtemp(prefix='ugit-cli-test-')
        self.old_cwd = os.getcwd()
        os.chdir(self.repo_dir)
        self._git_dir_cm = data.change_git_dir(self.repo_dir)
        self._git_dir_cm.__enter__()
        base.init()

    def tearDown(self):
        self._git_dir_cm.__exit__(None, None, None)
        os.chdir(self.old_cwd)

    def write_file(self, path, content):
        with open(path, 'w') as f:
            f.write(content)

    def capture(self, func, *args, **kwargs):
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = func(*args, **kwargs)
        return result, buf.getvalue()


class TestParseArgsWiring(CliTestCase):
    def test_merge_subcommand_uses_commit_attribute(self):
        # Regression test: the 'merge' subparser argument used to be named
        # 'merge' (add_argument('merge', ...)), giving args.merge, while
        # cli.merge() reads args.commit -- causing an AttributeError on
        # every invocation. This confirms the argparse argument name
        # matches what merge() actually reads, consistent with every other
        # subcommand in this file (checkout, reset, merge-base, diff).
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        with patch.object(sys, 'argv', ['ugit', 'merge', c1]):
            args = cli.parse_args()

        self.assertTrue(hasattr(args, 'commit'))
        self.assertEqual(args.commit, c1)

    def test_diff_subcommand_commit_defaults_to_none(self):
        with patch.object(sys, 'argv', ['ugit', 'diff']):
            args = cli.parse_args()
        self.assertIsNone(args.commit)

    def test_checkout_subcommand_requires_commit_argument(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        with patch.object(sys, 'argv', ['ugit', 'checkout', c1]):
            args = cli.parse_args()
        self.assertEqual(args.commit, c1)


class TestDiffCommand(CliTestCase):
    def test_diff_modes_follow_expected_sources(self):
        self.write_file('tracked.txt', 'one\n')
        base.add(['tracked.txt'])
        first_commit = base.commit('first')

        self.write_file('tracked.txt', 'two\n')
        base.add(['tracked.txt'])

        self.write_file('tracked.txt', 'three\n')

        no_args, no_args_out = self.capture(cli._diff, Namespace(commit=None, cached=False))
        cached, cached_out = self.capture(cli._diff, Namespace(commit=None, cached=True))
        against_commit, _ = self.capture(cli._diff, Namespace(commit=first_commit, cached=False))
        commit_cached, _ = self.capture(cli._diff, Namespace(commit=first_commit, cached=True))

        self.assertIn('+three', no_args)
        self.assertIn('+two', cached)
        self.assertIn('+three', against_commit)
        self.assertIn('+two', commit_cached)

        # Regression test: _diff() used to compute `result` and `return` it
        # without ever printing, so `ugit diff` produced no terminal output.
        self.assertIn('+three', no_args_out)
        self.assertIn('+two', cached_out)


class TestBranchCommand(CliTestCase):
    def test_branch_listing_has_no_duplicates(self):
        # Regression test: branch()'s no-args listing path used to contain
        # a redundant nested `for branch in base.iter_branch_names():` loop,
        # printing every branch once per branch (N branches -> N^2 lines).
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')
        base.create_branch('feature', c1)

        _, output = self.capture(cli.branch, Namespace(name=None, start_point=None))

        master_lines = [line for line in output.splitlines() if 'master' in line]
        feature_lines = [line for line in output.splitlines() if 'feature' in line]

        self.assertEqual(len(master_lines), 1)
        self.assertEqual(len(feature_lines), 1)

    def test_branch_creation_points_at_start_point(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        cli.branch(Namespace(name='feature', start_point=c1))

        self.assertEqual(data.get_ref('refs/heads/feature').value, c1)


class TestStatusCommand(CliTestCase):
    def test_status_reports_branch_and_staged_new_file(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        base.commit('first')

        self.write_file('b.txt', 'b')
        base.add(['b.txt'])

        _, output = self.capture(cli.status, Namespace())

        self.assertIn('On branch master', output)
        self.assertIn('new file', output)
        self.assertIn('b.txt', output)


class TestTagAndCheckoutCommands(CliTestCase):
    def test_tag_command_creates_resolvable_tag(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        cli.tag(Namespace(name='v1', oid=c1))

        self.assertEqual(base.get_oid('v1'), c1)

    def test_checkout_command_switches_working_directory(self):
        self.write_file('a.txt', 'a')
        base.add(['a.txt'])
        c1 = base.commit('first')

        self.write_file('b.txt', 'b')
        base.add(['b.txt'])
        base.commit('second')

        cli.checkout(Namespace(commit=c1))

        self.assertFalse(os.path.exists('b.txt'))


if __name__ == '__main__':
    unittest.main()
