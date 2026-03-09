from django import forms
from .models import Game, CustomFieldDefinition


class GameForm(forms.ModelForm):
    rating = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'placeholder': '1–10', 'min': 1, 'max': 10}),
    )

    class Meta:
        model = Game
        fields = ['title', 'platform', 'cover_image_url', 'status', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Elden Ring',
                'autocomplete': 'off',
            }),
            'platform': forms.TextInput(attrs={'placeholder': 'e.g. PC, PS5, Xbox'}),
            'cover_image_url': forms.URLInput(attrs={'placeholder': 'https://... (auto-filled or paste manually)'}),
            'status': forms.Select(),
        }


class CustomFieldDefinitionForm(forms.ModelForm):
    class Meta:
        model = CustomFieldDefinition
        fields = ['name', 'field_type']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Character Name, Difficulty...'}),
        }
