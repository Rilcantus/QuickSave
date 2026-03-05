from django import forms
from .models import JournalEntry


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['body', 'accomplishments', 'blockers', 'next_goals', 'mood']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': "What happened this session? Any thoughts, stories, or observations..."
            }),
            'accomplishments': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': "What did you accomplish?"
            }),
            'blockers': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': "Anything frustrating or blocking you?"
            }),
            'next_goals': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': "What do you want to do next session?"
            }),
            'mood': forms.TextInput(attrs={
                'placeholder': "e.g. flow state, frustrated, relaxed..."
            }),
        }