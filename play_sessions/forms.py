from django import forms
from games.models import Descriptor
from .models import Session, CustomFieldValue


class SessionStartForm(forms.ModelForm):
    descriptor = forms.ModelChoiceField(
        queryset=Descriptor.objects.none(),
        required=False,
        empty_label="No run label",
    )
    new_descriptor = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Modded Run, STR Build...'})
    )
    goal = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': "e.g. Beat the final boss, reach level 20..."})
    )

    class Meta:
        model = Session
        fields = ['descriptor', 'new_descriptor', 'goal']

    def __init__(self, game, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.fields['descriptor'].queryset = Descriptor.objects.filter(game=game)

    def save(self, commit=True):
        session = super().save(commit=False)
        session.game = self.game

        # If user typed a new descriptor, create or get it
        new_name = self.cleaned_data.get('new_descriptor', '').strip()
        if new_name:
            descriptor, _ = Descriptor.objects.get_or_create(
                game=self.game,
                name=new_name
            )
            session.descriptor = descriptor

        if commit:
            session.save()
        return session


class SessionEndForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Any quick notes before you close out? (optional)'
        })
    )