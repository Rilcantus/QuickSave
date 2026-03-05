from django.urls import path
from django.shortcuts import render, redirect
from . import views


def home(request):
    if request.user.is_authenticated:
        return redirect('game_list')
    return render(request, 'home.html')


urlpatterns = [
    path('', home, name='home'),
    path('games/<int:game_pk>/start/', views.session_start, name='session_start'),
    path('sessions/<int:pk>/active/', views.session_active, name='session_active'),
    path('sessions/<int:pk>/done/', views.session_end_prompt, name='session_end_prompt'),
]
