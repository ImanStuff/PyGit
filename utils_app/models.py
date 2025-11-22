from django.db import models

class Repository(models.Model):
    name = models.CharField(max_length=100, unique=True)

class GitObject(models.Model):
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    sha1 = models.CharField(max_length=40, db_index=True)
    type = models.CharField(max_length=10, choices=[('blob', 'Blob'), ('tree', 'Tree'), ('commit', 'Commit')])
    data = models.BinaryField()

    class Meta:
        unique_together = ('repo', 'sha1')

class Reference(models.Model):
    """Stores branch pointers like 'refs/heads/main'"""
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    commit_hash = models.CharField(max_length=40)
