# myapp/urls.py
from django.urls import path
from .views import index, process_speech
from . import views

urlpatterns = [
    path('', index, name='index'),
    path('process_speech/', process_speech, name='process_speech'),
    path('tts_view/', views.TextView.as_view(), name='tts_view/'),
]
