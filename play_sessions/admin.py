from django.contrib import admin
from .models import Session, CustomFieldValue


class CustomFieldValueInline(admin.TabularInline):
    model = CustomFieldValue
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['game', 'game_user', 'descriptor', 'source', 'started_at', 'duration_display', 'is_active']
    search_fields = ['game__title', 'game__user__username']
    list_filter = ['source', 'game__platform']
    date_hierarchy = 'started_at'
    raw_id_fields = ['game', 'descriptor']
    inlines = [CustomFieldValueInline]

    @admin.display(description='User')
    def game_user(self, obj):
        return obj.game.user.username


@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    list_display = ['field_definition', 'value', 'session']
    search_fields = ['field_definition__name', 'value']
