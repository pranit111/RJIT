from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Dyslexia, Autism, DyslexiaTestQuestion, DyslexiaTestResponse, DyslexiaTestResult

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

class DyslexiaTestQuestionAdmin(admin.ModelAdmin):
    list_display = ('section', 'question_type', 'question_text', 'correct_answer', 'has_image')
    list_filter = ('section', 'question_type', 'hide_question_text')
    search_fields = ('question_text', 'correct_answer')
    fieldsets = (
        ('Question Details', {
            'fields': ('section', 'question_type', 'question_text', 'hide_question_text')
        }),
        ('Media Files', {
            'fields': ('image_file',),
            'description': 'Upload images in JPG, PNG, or GIF format. Maximum file size: 5MB'
        }),
        ('Answer Options', {
            'fields': ('options', 'correct_answer', 'explanation'),
            'description': 'Enter options as a comma-separated list (e.g., "option1, option2, option3"). The correct answer must match one of these options exactly.'
        }),
    )

    def has_image(self, obj):
        return bool(obj.image_file)
    has_image.boolean = True
    has_image.short_description = 'Has Image'

    def save_model(self, request, obj, form, change):
        # Convert comma-separated options string to list if needed
        if isinstance(obj.options, str):
            obj.options = [opt.strip() for opt in obj.options.split(',')]
        super().save_model(request, obj, form, change)

class DyslexiaTestResponseAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'question', 'selected_answer', 'is_correct', 'response_time')
    list_filter = ('is_correct', 'question__section')
    search_fields = ('user_profile__user__username', 'question__question_text')
    readonly_fields = ('timestamp',)

class DyslexiaTestResultAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'total_score', 'completed_at')
    search_fields = ('user_profile__user__username',)
    readonly_fields = ('completed_at',)

# Register all models
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(DyslexiaTestQuestion, DyslexiaTestQuestionAdmin)
admin.site.register(DyslexiaTestResponse, DyslexiaTestResponseAdmin)
admin.site.register(DyslexiaTestResult, DyslexiaTestResultAdmin)
