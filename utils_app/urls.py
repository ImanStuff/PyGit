from django.urls import path
try:
    from . import views
except ImportError:
    from utils_app import views


app_name = 'utils_app'

urlpatterns = [
    path('<repo_name>/push', views.push_objects, name='push_objects_view'),
]