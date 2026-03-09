from django.urls import path
from . import views

urlpatterns = [
    path('auth/token/', views.api_token, name='api_token'),
    path('games/', views.api_games, name='api_games'),
    path('sessions/active/', views.api_active_session, name='api_active_session'),
    path('sessions/start/', views.api_start_session, name='api_start_session'),
    path('sessions/<int:pk>/end/', views.api_end_session, name='api_end_session'),
    path('notes/quick/', views.api_quick_note, name='api_quick_note'),
]
