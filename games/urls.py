from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('add/', views.game_create, name='game_create'),
    path('stats/', views.overall_stats, name='overall_stats'),
    path('<int:pk>/', views.game_detail, name='game_detail'),
    path('<int:pk>/edit/', views.game_edit, name='game_edit'),
    path('<int:pk>/delete/', views.game_delete, name='game_delete'),
    path('<int:pk>/stats/', views.game_stats, name='game_stats'),
    path('<int:game_pk>/fields/add/', views.custom_field_create, name='custom_field_create'),
    path('fields/<int:pk>/delete/', views.custom_field_delete, name='custom_field_delete'),
    path('<int:game_pk>/runs/<int:pk>/', views.descriptor_detail, name='descriptor_detail'),
    path('<int:game_pk>/runs/<int:pk>/edit/', views.descriptor_edit, name='descriptor_edit'),
    path('<int:game_pk>/runs/<int:pk>/delete/', views.descriptor_delete, name='descriptor_delete'),
    path('rawg-search/', views.rawg_search, name='rawg_search'),
]