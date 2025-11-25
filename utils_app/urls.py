from django.urls import path
try:
    from . import views
except ImportError:
    from utils_app import views


app_name = 'utils_app'

urlpatterns = [
    path('<repo_name>/push', views.push_objects, name='push_objects_view'),
    path("", views.repo_list, name="repo_list"),
    path("<str:name>/", views.repo_overview, name="repo_overview"),
    path(
        "<str:name>/tree/<str:commit_sha>/",
        views.tree_view,
        name="tree_root",
    ),
    path(
        "<str:name>/tree/<str:commit_sha>/<path:path>/",
        views.tree_view,
        name="tree_view",
    ),
    path(
        "<str:name>/blob/<str:commit_sha>/<path:path>/",
        views.blob_view,
        name="blob_view",
    ),
    path("<str:name>/commits/", views.commit_list, name="commit_list"),
    path(
        "<str:name>/commit/<str:commit_sha>/",
        views.commit_detail,
        name="commit_detail",
    ),
    path('<str:repo_name>/clone', views.clone_repo, name='clone_repo'),

]