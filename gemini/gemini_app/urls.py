# myapp/urls.py
from django.urls import path
from .views import index, process_speech

urlpatterns = [
    path('', index, name='index'),
    path('process_speech/', process_speech, name='process_speech'),
]
