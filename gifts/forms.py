from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Gift
from django.contrib.auth import get_user_model

User = get_user_model()  # Ensure you're using your custom user model

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring focus:ring-green-300',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring focus:ring-green-300',
            'placeholder': 'Enter your first name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']  # Ensure email is saved
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
        return user




class GiftForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring focus:ring-green-300'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring focus:ring-green-300',
            'rows': 4,
        })
    )
    link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring focus:ring-green-300'
        })
    )
    def save(self, commit=True):
        gift = Gift()
        gift.name = self.cleaned_data['name']
        gift.description = self.cleaned_data['description']
        gift.link = self.cleaned_data['link']
          # Ensure email is saved
        if commit:
            gift.save()
        return gift

