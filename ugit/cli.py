"""Command-line interface for parsing ugit commands and dispatching handlers."""

import argparse
import os
import sys
import textwrap
import subprocess
import shutil
import urllib.parse
import webbrowser

from . import data
from . import base
from . import diff

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

    show_parser = commands.add_parser('show')
    show_parser.set_defaults(func=show)
    show_parser.add_argument('oid', default='@', type=oid, nargs='?')

    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('commit')

    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', default='@', type=oid, nargs='?')

    branch_parser = commands.add_parser('branch')
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument('name', nargs='?')
    branch_parser.add_argument('start_point', default='@', type=oid, nargs='?')

    k_parser = commands.add_parser('k')
    k_parser.set_defaults(func=k)

    status_parser = commands.add_parser('status')
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser('reset')
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument('commit', type=oid)

    return parser.parse_args()

def init(args):
    """Creates a new empty repo"""
    base.init()
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

def _print_commit(oid, commit, refs=None):
    refs_str = f' ({", ".join(refs)})' if refs else ''
    print(f'commit {oid}{refs_str}\n')
    print(textwrap.indent(commit.message, '     '))
    print('')

def log(args):
    """Print commit history starting from the selected OID."""
    refs = {}
    for refname, ref in data.iter_refs():
        refs.setdefault(ref.value, []).append(refname)

    for oid in base.iter_commits_and_parents({args.oid}):
        commit = base.get_commit(oid)
        _print_commit(oid, commit, refs.get(oid))

def show(args):
    if not args.oid:
        return
    commit = base.get_commit(args.oid)
    parent_tree = None
    if commit.parent:
        parent_tree = base.get_commit(commit.parent).tree

    _print_commit(args.oid, commit)
    result = diff.diff_trees(
        base.get_tree(parent_tree), base.get_tree(commit.tree))

    print(result)

def checkout(args):
    """Check out the requested commit into the working tree."""
    base.checkout(args.commit)

def tag(args):
    """Create a tag pointing at the requested or current OID."""
    oid = base.get_oid(args.oid)
    base.create_tag(args.name, oid)

def branch(args):
    if not args.name:
        current = base.get_branch_name()
        for branch in base.iter_branch_name():
            for branch in base.iter_branch_names():
                prefix = '*' if branch == current else ' '
                print(f'{prefix} {branch}')
    else:
        base.create_branch(args.name, args.start_point)
        print(f'Branch {args.name} created at {args.start_point[:10]}')

def k(args):
    """Print the current reference map for debugging purposes."""
    oids = set()
    for refname, ref in data.iter_refs():
        oids.add(ref.value)
    
    for oid in base.iter_commits_and_parents(oids):
        dot = 'digraph commits {\n'

        oids = set()
        for refname, ref in data.iter_refs(deref=False):
            dot += f'"{refname}" [shape=note]\n'
            dot += f'"{refname}" -> "{ref.value}"\n'
            if not ref.symbolic:
                oids.add(ref.value)
        
        for oid in base.iter_commits_and_parents(oids):
            commit = base.get_commit(oid)
            dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
            if commit.parent:
                dot += f'"{oid}" -> "{commit.parent}"\n'

        dot += '}\n'

        # 1. check if 'dot' executable exists on system PATH
        if shutil.which('dot'):
            try:
                # generate image using Graphviz dot
                proc = subprocess.Popen(
                    ['dot, '-Tpng],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
                png_data, _ = proc.communicate(dot.encode())

                # pipe output to macOS Preview app
                preview_proc = subprocess.Popen(
                    ['open', '-a', 'Preview.app', '-f'], 
                    stdin=subprocess.PIPE
                )
                preview_proc.communicate(png_data)
            except Exception as e:
                print(f'Failed to render locally: {e}')
                print(dot)
        else:
            # 2. fallback: print DOT string and launch online renderer
            print("Graphviz 'dot' not found on system PATH.")
            print("--- DOT GRAPH DATA ---")
            print(dot)
            print("----------------------")

            # open web visualiser automatically in browser
            encoded_dot = urllib.parse.quote(dot)
            url = f"https://quickchart.io/graphviz?graph={encoded_dot}"
            print(f"Opening graph visually at: {url}")
            webbrowser.open(url)

def status(args):
    HEAD = base.get_oid('@')
    branch = base.get_branch_name()

    if branch:
        print(f'On branch {branch}')
    else:
        print(f'HEAD detached at {HEAD[:10]}')

def reset(args):
    base.reset(args.commit)