from django.contrib import admin
from .models import JournalEntry


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['game_title', 'user', 'mood', 'has_body', 'created_at']
    search_fields = ['body', 'user__username', 'game__title', 'session__game__title']
    list_filter = ['mood', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    @admin.display(description='Game')
    def game_title(self, obj):
        game = obj.get_game()
        return game.title if game else '—'

    @admin.display(description='Has Notes', boolean=True)
    def has_body(self, obj):
        return bool(obj.body)
