from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import zlib
from .models import Repository, GitObject, Reference

@csrf_exempt
def push_objects(request, repo_name):
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

def get_ref(request, repo_name):    
    try:
        ref = Reference.objects.get(repo__name=repo_name, name='refs/heads/main')
        return JsonResponse({"head": ref.commit_hash})
    except Reference.DoesNotExist:
        return JsonResponse({"head": None})
