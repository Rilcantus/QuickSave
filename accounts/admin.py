from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'is_pro_badge', 'platforms_connected',
        'is_staff', 'date_joined',
    ]
    list_filter = ['is_pro', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['-date_joined']
    actions = ['grant_pro', 'revoke_pro']

    fieldsets = UserAdmin.fieldsets + (
        ('QuickSave Pro', {
            'fields': ('is_pro',),
        }),
        ('Steam', {
            'fields': ('steam_id', 'steam_username', 'steam_avatar', 'steam_polling_enabled'),
            'classes': ('collapse',),
        }),
        ('Xbox', {
            'fields': ('xbox_id', 'xbox_gamertag', 'xbox_avatar', 'xbox_polling_enabled'),
            'classes': ('collapse',),
        }),
        ('Discord', {
            'fields': ('discord_id', 'discord_username', 'discord_avatar', 'discord_polling_enabled'),
            'classes': ('collapse',),
        }),
        ('PSN', {
            'fields': ('psn_username', 'psn_account_id', 'psn_avatar', 'psn_polling_enabled'),
            'classes': ('collapse',),
        }),
        ('Roblox', {
            'fields': ('roblox_username', 'roblox_user_id', 'roblox_avatar', 'roblox_polling_enabled'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Pro', boolean=False)
    def is_pro_badge(self, obj):
        if obj.is_pro:
            return format_html('<span style="color:#22c55e;font-weight:bold;">✦ Pro</span>')
        return format_html('<span style="color:#6b7280;">Free</span>')

    @admin.display(description='Platforms')
    def platforms_connected(self, obj):
        platforms = []
        if obj.steam_id:
            platforms.append('Steam')
        if obj.xbox_id:
            platforms.append('Xbox')
        if obj.discord_id:
            platforms.append('Discord')
        if obj.psn_username:
            platforms.append('PSN')
        if obj.roblox_username:
            platforms.append('Roblox')
        return ', '.join(platforms) if platforms else '—'

    @admin.action(description='Grant Pro to selected users')
    def grant_pro(self, request, queryset):
        updated = queryset.update(is_pro=True)
        self.message_user(request, f'{updated} user(s) granted Pro.')

    @admin.action(description='Revoke Pro from selected users')
    def revoke_pro(self, request, queryset):
        updated = queryset.update(is_pro=False)
        self.message_user(request, f'{updated} user(s) revoked Pro.')
