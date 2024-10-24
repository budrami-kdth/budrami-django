# myproject/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gemini_app.urls')),  # myapp의 urls.py 파일 포함
]
