"""Command-line interface for parsing ugit commands and dispatching handlers."""

import argparse
import os
import sys
import textwrap

from . import data
from . import base

def main():
    """Parse command-line arguments and run the selected subcommand."""
    args = parse_args()
    args.func(args)

def parse_args():
    """Build the argument parser and return the parsed command namespace."""
    parser = argparse.ArgumentParser()
    
    commands = parser.add_subparsers(dest="command")
    commands.required = True

    oid = base.get_oid
    
    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')

    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object', default='@', type=oid)

    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', default='@', type=oid)

    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', default='@', type=oid, nargs='?')

    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('oid', default='@', type=oid)

    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', default='@', type=oid, nargs='?')

    k_parser = commands.add_parser('k')
    k_parser.set_defaults(func=k)

    return parser.parse_args()

def init(args):
    """Creates a new empty repo"""
    data.init()
    repo_path = os.path.join(os.getcwd(), data.GIT_DIR)
    print(f'Intialised empty ugit repository in {repo_path}')

def hash_object(args):
    """Hash a file from disk and print the resulting object ID."""
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))

def cat_file(args):
    """debug command used for printing all hashed objects"""
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

def write_tree(args):
    """Write the working tree to storage and print the resulting tree OID."""
    print(base.write_tree())

def read_tree(args):
    """Populate the working tree from the requested tree object."""
    base.read_tree(args.tree)

def commit(args):
    """Create a commit from the current tree using the provided message."""
    print(base.commit(args.message))

def log(args):
    """Print commit history starting from the selected OID."""
    oid = base.get_oid(args.oid)
    while oid:
        commit = base.get_commit(oid)

        print(f'commit {oid}\n')
        print(textwrap.indent(commit.message, '     '))
        print('')

        oid = commit.parent

def checkout(args):
    """Check out the requested commit into the working tree."""
    base.checkout(args.oid)

def tag(args):
    """Create a tag pointing at the requested or current OID."""
    oid = base.get_oid(args.oid)
    base.create_tag(args.name, oid)

def k(args):
    """Print the current reference map for debugging purposes."""
    oids = set()
    for refname, ref in data.iter_refs():
        print(refname, ref)
        oids.add(ref)
    
    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        print(oid)
        if commit.parent:
            print('Parent', commit.parent)
    # TODO visualise refs