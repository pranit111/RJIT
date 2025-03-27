from django.urls import path
from . import views


app_name = 'dyslexia'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('learning/', views.learning_modules, name='learning_modules'),
    path('learning/<str:module_type>/', views.learning_module_detail, name='module_detail'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/submit-response/', views.submit_quiz_response, name='submit_quiz_response'),
    path('quizzes/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quizzes/result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('progress/', views.progress, name='progress'),
    
    # Subject-specific chat URLs
    path('chat/<str:subject>/', views.subject_chat, name='subject_chat'),
    path('chat/<str:subject>/api/', views.subject_chat_api, name='subject_chat_api'),
    path('chat/<str:subject>/extracted-text/', views.get_extracted_text, name='get_extracted_text'),
    path('assignments/', views.assignments_list, name='assignments_list'),
    path('assignments/<int:assignment_id>/take/', views.take_assignment, name='take_assignment'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignments/<int:assignment_id>/results/', views.view_assignment_results, name='view_assignment_results'),
]
