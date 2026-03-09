from django.contrib import admin
from django.db.models import Count, Sum
from .models import Game, Descriptor, CustomFieldDefinition, CustomFieldChoice


class DescriptorInline(admin.TabularInline):
    model = Descriptor
    extra = 0


class CustomFieldChoiceInline(admin.TabularInline):
    model = CustomFieldChoice
    extra = 0


class CustomFieldDefinitionInline(admin.TabularInline):
    model = CustomFieldDefinition
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'platform', 'user', 'status', 'session_count', 'total_playtime', 'created_at']
    search_fields = ['title', 'user__username']
    list_filter = ['platform', 'status']
    raw_id_fields = ['user']
    inlines = [DescriptorInline, CustomFieldDefinitionInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _session_count=Count('sessions', distinct=True),
            _total_seconds=Sum('sessions__duration_seconds'),
        )

    @admin.display(description='Sessions', ordering='_session_count')
    def session_count(self, obj):
        return obj._session_count

    @admin.display(description='Playtime')
    def total_playtime(self, obj):
        secs = obj._total_seconds or 0
        hours, remainder = divmod(int(secs), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f'{hours}h {minutes}m'
        return f'{minutes}m'


@admin.register(Descriptor)
class DescriptorAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'game_user']
    search_fields = ['name', 'game__title', 'game__user__username']

    @admin.display(description='User')
    def game_user(self, obj):
        return obj.game.user.username


@admin.register(CustomFieldDefinition)
class CustomFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'field_type', 'game', 'order']
    search_fields = ['name', 'game__title']
    list_filter = ['field_type']
    inlines = [CustomFieldChoiceInline]
