from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Gift

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User  # Use your custom user model
        fields = ('username', 'email', 'password1', 'password2')

class GiftForm(forms.ModelForm):
    class Meta:
        model = Gift
        fields = ['name', 'description', 'link']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }