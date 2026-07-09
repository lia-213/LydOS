# In charge of parsing and processing user input

import argparse
import os

from . import data

def main():
    args = parse_args()
    args.func(args)

def parse_args():
    parser = argparse.ArgumentParser()
    
    commands = parser.add_subparsers(dest="command")
    commands.required = True
    
    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)

    return parser.parse_args()

def init(args):
    """Creates a new empty repo"""
    data.init()
    repo_path = os.path.join(os.getcwd(), data.GIT_DIR)
    print(f'Intialised empty ugit repository in {repo_path}')