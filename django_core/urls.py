from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/git/', include('utils_app.urls', namespace='utils_app_')),
]
