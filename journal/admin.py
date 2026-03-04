from django.contrib import admin
from .models import JournalEntry


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user', 'mood', 'created_at']
    search_fields = ['body', 'user__username']
    list_filter = ['mood', 'created_at']
    readonly_fields = ['created_at', 'updated_at']