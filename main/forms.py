from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class UserProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    BOARD_CHOICES = [
        ('', 'Select Board'),
        ('cbse', 'CBSE'),
        ('state', 'State Board'),
        ('icse', 'ICSE'),
    ]
    STANDARD_CHOICES = [
        ('', 'Select Standard'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        
    ]

    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    board = forms.ChoiceField(choices=BOARD_CHOICES, required=False)
    standard = forms.ChoiceField(choices=STANDARD_CHOICES, required=False)
    class Meta:
        model = UserProfile
        fields = ['age', 'gender', 'standard', 'school', 'board', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        } 