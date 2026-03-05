from django.urls import path
from . import views

urlpatterns = [
    path('', views.journal_list, name='journal_list'),
    path('session/<int:session_pk>/', views.journal_create_for_session, name='journal_create_for_session'),
    path('game/<int:game_pk>/new/', views.journal_create_standalone, name='journal_create_standalone'),
    path('<int:pk>/', views.journal_detail, name='journal_detail'),
    path('<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('<int:pk>/delete/', views.journal_delete, name='journal_delete'),
]