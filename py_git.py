import os
import hashlib
import json
import requests
import argparse
import time

REPO_DIR = ".py_git"
OBJECTS_DIR = os.path.join(REPO_DIR, "objects")
INDEX_FILE = os.path.join(REPO_DIR, "index.json")
HEAD_FILE = os.path.join(REPO_DIR, "HEAD")
REMOTE_URL = "http://localhost:8000/api/git"

def hash_object(data, obj_type, write=True):
    header = f"{obj_type} {len(data)}\0".encode()
    full_data = header + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    
    if write:
        path = os.path.join(OBJECTS_DIR, sha1)
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(full_data)
    return sha1

def init():
    os.makedirs(OBJECTS_DIR, exist_ok=True)
    with open(INDEX_FILE, 'w') as f:
        json.dump({}, f)
    print("Initialized empty py_git repository.")


def write_tree(path):
    entries = []
    for entry in sorted(os.listdir(path)):
        if entry == '.py_git' or entry.startswith('.'):
            continue
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            sha1 = write_tree(full_path)
            entries.append(f"tree {sha1} {entry}")
        else:
            with open(full_path, 'rb') as f:
                content = f.read()
            sha1 = hash_object(content, 'blob')
            entries.append(f"blob {sha1} {entry}")
    tree_content = "\n".join(entries)
    tree_sha = hash_object(tree_content.encode(), 'tree')
    return tree_sha


def add(path):
    tree_sha = write_tree(path)
    
    index = {"root_tree": tree_sha}
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f)
    
    print(f"Added files and folders recursively. Root tree SHA: {tree_sha}")


def commit(message):
    with open(INDEX_FILE, 'r') as f:
        index = json.load(f)
    tree_content = ""
    for filename, sha1 in index.items():
        tree_content += f"blob {sha1} {filename}\n"
    tree_sha = hash_object(tree_content.encode(), 'tree')
    parent = None
    if os.path.exists(HEAD_FILE):
        with open(HEAD_FILE, 'r') as f:
            parent = f.read().strip()

    timestamp = int(time.time())
    commit_content = f"tree {tree_sha}\n"
    if parent:
        commit_content += f"parent {parent}\n"
    commit_content += f"author User <user@example.com> {timestamp}\n\n{message}"
    
    commit_sha = hash_object(commit_content.encode(), 'commit')
    with open(HEAD_FILE, 'w') as f:
        f.write(commit_sha)
    
    print(f"Committed {commit_sha[:7]}: {message}")


def push(repo_name):
    objects_data = []
    for sha1 in os.listdir(OBJECTS_DIR):
        with open(os.path.join(OBJECTS_DIR, sha1), 'rb') as f:
            raw = f.read()
            null_index = raw.find(b'\0')
            header = raw[:null_index].decode().split(' ')
            obj_type = header[0]
            content = raw
            objects_data.append({
                "sha1": sha1,
                "type": obj_type,
                "data": content.hex()
            })
    with open(HEAD_FILE, 'r') as f:
        head_sha = f.read().strip()
    payload = {"objects": objects_data, "head": head_sha, "ref": "refs/heads/main"}
    resp = requests.post(f"{REMOTE_URL}/{repo_name}/push", json=payload)
    print("Push response:", resp.status_code)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="py_git command")
    parser.add_argument('command', choices=['init', 'add', 'commit', 'push', 'pull'], help='py_git commands')
    parser.add_argument('-p', '--path', type=str, help='Path for add command')
    parser.add_argument('-m', '--message', type=str, help='Commit message')
    parser.add_argument('-r', '--repo_name', type=str, help='Repo Name for push command')

    args = parser.parse_args()

    if args.command == 'init':
        init()
    elif args.command == 'add':
        if not args.path:
            parser.error('add requires a -p path')
        add(args.path)
    elif args.command == 'commit':
        if not args.message:
            parser.error("the commit command requires a -m message")
        commit(args.message)
    elif args.command == 'push':
        if not args.repo_name:
            parser.error('push command requires -r repo name')
        push(args.repo_name)
    else:
        print('No command.')

    
    