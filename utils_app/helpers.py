from .models import GitObject


def load_object(obj: GitObject):
    raw = obj.data
    null_index = raw.find(b'\0')
    header = raw[:null_index].decode()
    obj_type, size = header.split(' ')
    body = raw[null_index+1:]
    return obj_type, body

def parse_tree(body: bytes):
    entries = []
    for line in body.decode().splitlines():
        kind, sha, name = line.split(' ', 2)
        entries.append({"type": kind, "sha": sha, "name": name})
    return entries

def parse_commit(body: bytes):
    text = body.decode()
    header, message = text.split("\n\n", 1)
    info = {"message": message}
    for line in header.splitlines():
        if line.startswith("tree "):
            info["tree"] = line.split(" ", 1)[1]
        elif line.startswith("parent "):
            info.setdefault("parents", []).append(line.split(" ", 1)[1])
        elif line.startswith("author "):
            info["author_line"] = line[7:]
    return info
