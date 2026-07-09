import os

GIT_DIR = '.ugit'

def init():
    if os.path.exists(GIT_DIR):
        print("(Bonus!) Reinitialised existing ugit repository!")
    else:
        os.makedirs(GIT_DIR, exist_ok=True)