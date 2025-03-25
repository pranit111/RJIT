from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.IntegerField(help_text="Duration in minutes")
    pass_mark = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pass mark percentage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = (
        ('text', 'Text Only'),
        ('image', 'Image Based'),
        ('text_to_speech', 'Text to Speech'),
    )

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    text = models.TextField()
    image = models.ImageField(upload_to='quiz_images/', null=True, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"

class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.question.quiz.title} - {self.text}"

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, related_name='quiz_attempts', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name='attempts', on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    time_taken = models.IntegerField(help_text="Time taken in seconds")
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'quiz']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"

class QuestionResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, related_name='responses', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='responses', on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, related_name='responses', on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    response_time = models.IntegerField(help_text="Response time in seconds")

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.user.username} - {self.question.quiz.title} - Q{self.question.order}"

class SubjectMaterial(models.Model):
    SUBJECT_CHOICES = [
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('history', 'History'),
    ]
    
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to='subject_pdfs/', null=True, blank=True)
    vector_db_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['subject', 'title']
        ordering = ['subject', 'title']

    def __str__(self):
        return f"{self.get_subject_display()} - {self.title}"

    def get_vector_db_path(self):
        """Returns the full path where the vector database should be stored"""
        return f"vector_dbs/{self.subject}/{self.title.lower().replace(' ', '_')}"

    def save(self, *args, **kwargs):
        if not self.vector_db_path:
            self.vector_db_path = self.get_vector_db_path()
        super().save(*args, **kwargs)

class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('initial', 'Initial Diagnosis'),
        ('practice', 'Practice Assignment'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='practice')
    questions = models.ManyToManyField(Question, related_name='assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_assignment_type_display()} - {self.title}"

class AssignmentSubmission(models.Model):
    user = models.ForeignKey(User, related_name='assignment_submissions', on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, related_name='submissions', on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'assignment']

    def __str__(self):
        return f"{self.user.username} - {self.assignment.title}"

class AssignmentResponse(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, related_name='responses', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='assignment_responses', on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, related_name='assignment_responses', on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    response_time = models.IntegerField(help_text="Response time in seconds")

    class Meta:
        unique_together = ['submission', 'question']

    def __str__(self):
        return f"{self.submission.user.username} - {self.submission.assignment.title} - Q{self.question.order}"
