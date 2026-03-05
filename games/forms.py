from django import forms
from .models import Game, CustomFieldDefinition


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'platform', 'cover_image_url']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Elden Ring'}),
            'platform': forms.TextInput(attrs={'placeholder': 'e.g. PC, PS5, Xbox'}),
            'cover_image_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

class CustomFieldDefinitionForm(forms.ModelForm):
    class Meta:
        model = CustomFieldDefinition
        fields = ['name', 'field_type']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Character Name, Difficulty...'}),
        }