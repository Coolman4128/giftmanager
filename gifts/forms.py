from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Gift
from .validators import UnlimitedURLFormField
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




INPUT_CLASSES = 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring focus:ring-green-300'


class FamilyMemberChoiceField(forms.ModelChoiceField):
    """Lists family members by their friendly name, flagging the current user."""

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)

    def label_from_instance(self, user):
        label = user.first_name or user.username
        if self.current_user is not None and user.pk == self.current_user.pk:
            return f"{label} (You)"
        return label


class GiftForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': INPUT_CLASSES, 'rows': 4})
    )
    link = UnlimitedURLFormField(
        required=False,
        widget=forms.URLInput(attrs={'class': INPUT_CLASSES})
    )
    is_couples_gift = forms.BooleanField(
        required=False,
        label="Is this a couple's gift?",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-green-600 border-gray-300 rounded focus:ring focus:ring-green-300',
            'data-couples-toggle': 'true',
        }),
    )
    couple_partner = FamilyMemberChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Other person in the couple",
        empty_label="Select a family member",
        widget=forms.Select(attrs={
            'class': INPUT_CLASSES,
            'data-couples-select': 'true',
        }),
    )

    class Meta:
        model = Gift
        fields = ('name', 'description', 'link', 'couple_partner')

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['couple_partner'].current_user = user
        self.fields['couple_partner'].queryset = User.objects.filter(
            family=user.family
        ).order_by('first_name', 'username')
        if not self.is_bound:
            self.fields['is_couples_gift'].initial = bool(self.instance.pk and self.instance.is_couples_gift)

    def get_recipient(self):
        """Who the gift is for. Fixed on an existing gift, chosen on a new one."""
        return self.instance.user_paired if self.instance.pk else None

    def clean(self):
        cleaned_data = super().clean()
        partner = cleaned_data.get('couple_partner')

        if not cleaned_data.get('is_couples_gift'):
            cleaned_data['couple_partner'] = None
            return cleaned_data

        if partner is None:
            self.add_error('couple_partner', "Please choose the other person in the couple.")
            return cleaned_data

        recipient = self.get_recipient()
        if recipient is not None and partner.pk == recipient.pk:
            self.add_error('couple_partner', "Pick someone other than the person the gift is for.")

        return cleaned_data


class AddGiftForm(GiftForm):
    recipient = FamilyMemberChoiceField(
        queryset=User.objects.none(),
        empty_label=None,
        widget=forms.Select(attrs={'class': INPUT_CLASSES}),
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields['recipient'].current_user = user
        self.fields['recipient'].queryset = User.objects.filter(
            family=user.family
        ).order_by('first_name', 'username')
        self.fields['recipient'].initial = user

    def get_recipient(self):
        return self.cleaned_data.get('recipient')
