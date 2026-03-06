from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.account_settings, name='account_settings'),
    path('settings/profile/', views.update_profile, name='update_profile'),
    path('settings/password/', views.change_password, name='change_password'),
    path('settings/delete/', views.delete_account, name='delete_account'),
    path('settings/steam/', views.steam_settings, name='steam_settings'),
    path('settings/steam/connect/', views.steam_connect, name='steam_connect'),
    path('settings/steam/disconnect/', views.steam_disconnect, name='steam_disconnect'),
    path('settings/steam/toggle/', views.steam_toggle_polling, name='steam_toggle_polling'),
]