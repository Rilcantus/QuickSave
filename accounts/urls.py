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
    path('settings/discord/', views.discord_settings, name='discord_settings'),
    path('settings/discord/oauth/', views.discord_oauth, name='discord_oauth'),
    path('discord/callback/', views.discord_callback, name='discord_callback'),
    path('settings/discord/disconnect/', views.discord_disconnect, name='discord_disconnect'),
    path('settings/discord/toggle/', views.discord_toggle_polling, name='discord_toggle_polling'),
    path('settings/steam/poll/', views.steam_poll_now, name='steam_poll_now'),

]