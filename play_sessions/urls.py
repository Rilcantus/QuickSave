from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('games/<int:game_pk>/start/', views.session_start, name='session_start'),
    path('sessions/<int:pk>/active/', views.session_active, name='session_active'),
    path('sessions/<int:pk>/done/', views.session_end_prompt, name='session_end_prompt'),
    path('sessions/', views.session_history, name='session_history'),
]