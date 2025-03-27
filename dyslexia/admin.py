from django.contrib import admin

# Register your models here.
from .models import Quiz, Question, Option, QuizAttempt, QuestionResponse, SubjectMaterial

class OptionInline(admin.TabularInline):
    model = Option
    extra = 3

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'pass_mark', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')
    inlines = [QuestionInline]

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_type', 'order')
    list_filter = ('quiz', 'question_type')
    search_fields = ('text', 'quiz__title')
    inlines = [OptionInline]
    ordering = ['quiz', 'order']

@admin.register(SubjectMaterial)
class SubjectMaterialAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'created_at', 'updated_at')
    list_filter = ('subject', 'created_at')
    search_fields = ('subject', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('subject', 'title', 'description')
        }),
        ('PDF File', {
            'fields': ('pdf_file',),
            'description': 'Upload the PDF file for this subject material.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
admin.site.register(QuizAttempt)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
