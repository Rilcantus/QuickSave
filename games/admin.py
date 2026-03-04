from django.contrib import admin
from .models import Game, Descriptor, CustomFieldDefinition, CustomFieldChoice


class DescriptorInline(admin.TabularInline):
    model = Descriptor
    extra = 1


class CustomFieldChoiceInline(admin.TabularInline):
    model = CustomFieldChoice
    extra = 1


class CustomFieldDefinitionInline(admin.TabularInline):
    model = CustomFieldDefinition
    extra = 1


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'platform', 'user', 'created_at']
    search_fields = ['title', 'user__username']
    list_filter = ['platform']
    inlines = [DescriptorInline, CustomFieldDefinitionInline]


@admin.register(Descriptor)
class DescriptorAdmin(admin.ModelAdmin):
    list_display = ['name', 'game']
    search_fields = ['name', 'game__title']


@admin.register(CustomFieldDefinition)
class CustomFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'field_type', 'game', 'order']
    search_fields = ['name', 'game__title']
    list_filter = ['field_type']
    inlines = [CustomFieldChoiceInline]