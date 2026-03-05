from django import forms
from .models import Game


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'platform', 'cover_image_url']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Elden Ring'}),
            'platform': forms.TextInput(attrs={'placeholder': 'e.g. PC, PS5, Xbox'}),
            'cover_image_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }