from django.contrib import admin
from .models import Session, CustomFieldValue


class CustomFieldValueInline(admin.TabularInline):
    model = CustomFieldValue
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['game', 'descriptor', 'started_at', 'ended_at', 'duration_display', 'is_active']
    search_fields = ['game__title']
    list_filter = ['game']
    inlines = [CustomFieldValueInline]


@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    list_display = ['field_definition', 'value', 'session']
    search_fields = ['field_definition__name', 'value']