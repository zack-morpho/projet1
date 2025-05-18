from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from .models import Utilisateur, Commentaire
from django import forms


class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'nom', 'prenom', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords don't match")

        if Utilisateur.objects.filter(username=cleaned_data['username']).exists():
            raise ValidationError("Username already exists")

        return cleaned_data



class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['texte', 'note']
        widgets = {
            'texte': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Votre commentaire...'}),
            'note': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }
        labels = {
            'texte': '',
            'note': 'Note (1 à 5)',
        }

# class LoginForm(forms.Form):
#     username = forms.CharField()
#     password = forms.CharField(widget=forms.PasswordInput)


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter username',
            'class': 'form-input'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-input'
        })
    )

