from django.http import JsonResponse, Http404, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .models import Repository, GitObject, Reference
from .helpers import load_object, parse_tree, parse_commit
import json
import zlib

@csrf_exempt
def push_objects(request: HttpRequest, repo_name: str) -> JsonResponse:
    if request.method == 'POST':
        data = json.loads(request.body)
        repo, _ = Repository.objects.get_or_create(name=repo_name)
        for obj in data.get('objects', []):
            if not GitObject.objects.filter(repo=repo, sha1=obj['sha1']).exists():
                GitObject.objects.create(
                    repo=repo, 
                    sha1=obj['sha1'], 
                    type=obj['type'], 
                    data=bytes.fromhex(obj['data'])
                )
        ref_name = data.get('ref', 'refs/heads/main')
        new_hash = data.get('head')
        Reference.objects.update_or_create(repo=repo, name=ref_name, defaults={'commit_hash': new_hash})
        return JsonResponse({"status": "pushed"})
    return JsonResponse({'status': "online"})


def repo_list(request: HttpRequest) -> HttpResponse:
    repos = Repository.objects.all()
    return render(request, "pygit/repo_list.html", {"repos": repos})


def repo_overview(request: HttpRequest, name: str) -> HttpResponse:
    repo = get_object_or_404(Repository, name=name)
    ref = get_object_or_404(Reference, repo=repo, name="refs/heads/main")
    head_sha = ref.commit_hash
    commit_obj = get_object_or_404(GitObject, repo=repo, sha1=head_sha)
    _, commit_body = load_object(commit_obj)
    commit = parse_commit(commit_body)

    tree_sha = commit["tree"]
    tree_obj = get_object_or_404(GitObject, repo=repo, sha1=tree_sha)
    _, tree_body = load_object(tree_obj)
    entries = parse_tree(tree_body)
    context = {
        "repo": repo,
        "head_sha": head_sha,
        "commit": commit,
        "entries": entries,
    }
    return render(request, "pygit/repo_overview.html", context)

def _resolve_tree_sha(repo, commit_sha, rel_path):
    commit_obj = get_object_or_404(GitObject, repo=repo, sha1=commit_sha)
    _, commit_body = load_object(commit_obj)
    commit = parse_commit(commit_body)

    current_tree_sha = commit["tree"]
    if not rel_path:
        return current_tree_sha, commit

    parts = [p for p in rel_path.strip("/").split("/") if p]
    for part in parts:
        tree_obj = get_object_or_404(GitObject, repo=repo, sha1=current_tree_sha)
        _, tree_body = load_object(tree_obj)
        entries = parse_tree(tree_body)
        match = next(
            (e for e in entries if e["name"] == part and e["type"] == "tree"),
            None,
        )
        if not match:
            raise Http404(f"Directory '{rel_path}' not found")
        current_tree_sha = match["sha"]

    return current_tree_sha, commit


def tree_view(request, name, commit_sha, path=""):
    repo = get_object_or_404(Repository, name=name)
    tree_sha, commit = _resolve_tree_sha(repo, commit_sha, path)

    tree_obj = get_object_or_404(GitObject, repo=repo, sha1=tree_sha)
    _, tree_body = load_object(tree_obj)
    entries = parse_tree(tree_body)

    return render(
        request,
        "pygit/tree.html",
        {
            "repo": repo,
            "commit": commit,
            "commit_sha": commit_sha,
            "path": path,
            "entries": entries,
        },
    )

def blob_view(request, name, commit_sha, path):
    repo = get_object_or_404(Repository, name=name)
    parent_path, _, leaf = path.rstrip("/").rpartition("/")
    tree_sha, commit = _resolve_tree_sha(repo, commit_sha, parent_path)

    tree_obj = get_object_or_404(GitObject, repo=repo, sha1=tree_sha)
    _, tree_body = load_object(tree_obj)
    entries = parse_tree(tree_body)
    file_entry = next(
        (e for e in entries if e["name"] == leaf and e["type"] == "blob"),
        None,
    )
    if not file_entry:
        raise Http404("File not found")

    blob_obj = get_object_or_404(GitObject, repo=repo, sha1=file_entry["sha"])
    _, body = load_object(blob_obj)
    content = body.decode(errors="replace")

    return render(
        request,
        "pygit/blob.html",
        {
            "repo": repo,
            "commit": commit,
            "commit_sha": commit_sha,
            "path": path,
            "content": content,
        },
    )


def commit_list(request, name):
    repo = get_object_or_404(Repository, name=name)
    ref = get_object_or_404(Reference, repo=repo, name="refs/heads/main")
    sha = ref.commit_hash
    commits = []
    seen = set()
    while sha and sha not in seen:
        seen.add(sha)
        obj = get_object_or_404(GitObject, repo=repo, sha1=sha)
        _, body = load_object(obj)
        info = parse_commit(body)
        info["sha"] = sha
        commits.append(info)
        parents = info.get("parents", [])
        sha = parents[0] if parents else None

    return render(request, "pygit/commits.html", {"repo": repo, "commits": commits})


def commit_detail(request, name, commit_sha):
    repo = get_object_or_404(Repository, name=name)
    obj = get_object_or_404(GitObject, repo=repo, sha1=commit_sha)
    _, body = load_object(obj)
    commit = parse_commit(body)
    commit["sha"] = commit_sha
    return render(request, "pygit/commit_detail.html", {"repo": repo, "commit": commit})