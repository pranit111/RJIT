from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    CONDITION_CHOICES = [
        ('none', 'None'),
        ('dyslexia', 'Dyslexia'),
        ('autism', 'Autism'),
    ]
    
    BOARD_CHOICES = [
        ('cbse', 'CBSE'),
        ('state', 'State Board'),
        ('icse', 'ICSE'),
    ]
    
    LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='images/profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    standard = models.CharField(max_length=10, null=True, blank=True)
    school = models.CharField(max_length=100, null=True, blank=True)
    board = models.CharField(max_length=10, choices=BOARD_CHOICES, null=True, blank=True)
    condition_type = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='none')
    condition_level = models.CharField(max_length=10, choices=LEVEL_CHOICES, null=True, blank=True)
    conditions = models.TextField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Dyslexia(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='dyslexia')
    CONDITION_TYPE = [
       
        ('phonological', 'Phonological'),
        ('surface', 'Surface'),
        ('visual', 'Visual'),
        
    ]
    LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    dyslexia_type = models.CharField(max_length=100, choices=CONDITION_TYPE, blank=True)
    dyslexia_level = models.CharField(max_length=100, choices=LEVEL_CHOICES, blank=True)
    dyslexia_description = models.TextField(max_length=500, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user_profile.user.username}'s Dyslexia Profile"

class Autism(models.Model):
    CONDITION_TYPE = [
        ('classic', 'Classic'),
        ('visual', 'Visual'),
    ]
    LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='autism')
    autism_type = models.CharField(max_length=100, choices=CONDITION_TYPE, blank=True)
    autism_level = models.CharField(max_length=100, choices=LEVEL_CHOICES, blank=True)
    autism_description = models.TextField(max_length=500, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user_profile.user.username}'s Autism Profile"

class DyslexiaTestQuestion(models.Model):
    SECTION_CHOICES = [
        ('phonological', 'Phonological'),
        ('surface', 'Surface'),
        ('visual', 'Visual'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('text_to_speech', 'Text to Speech'),
        ('image', 'Image Based'),
    ]
    initial_or_assignment = models.CharField(max_length=20,null=True,blank=True,choices=[('initial', 'Initial'), ('assignment', 'Assignment')])
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_text = models.TextField()
    hide_question_text = models.BooleanField(default=False, help_text="If checked, question text will only be available through text-to-speech")
    image_file = models.ImageField(upload_to='images/dyslexia_test/', null=True, blank=True)
    correct_answer = models.CharField(max_length=100)
    options = models.JSONField()  # Store options as a JSON array
    explanation = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.section} - {self.question_text[:50]}"

class DyslexiaTestResponse(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    question = models.ForeignKey(DyslexiaTestQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=100)
    is_correct = models.BooleanField()
    response_time = models.IntegerField(help_text="Response time in seconds")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user_profile.user.username}'s response to {self.question}"

class DyslexiaTestResult(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    phonological_score = models.IntegerField(default=0)
    surface_score = models.IntegerField(default=0)
    visual_score = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_dyslexia_type(self):
        scores = {
            'phonological': self.phonological_score,
            'surface': self.surface_score,
            'visual': self.visual_score
        }
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def calculate_dyslexia_level(self):
        total_errors = 15 - self.total_score  # Assuming 15 questions total
        if total_errors <= 2:
            return 'low'
        elif total_errors <= 4:
            return 'medium'
        else:
            return 'high'
    
    def __str__(self):
        return f"{self.user_profile.user.username}'s Test Results"
    
    
