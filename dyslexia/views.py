from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, F
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Quiz, QuizAttempt, QuestionResponse, Option, SubjectMaterial, Assignment, AssignmentSubmission, AssignmentResponse, Question
from main.models import UserProfile, Dyslexia, DyslexiaTestResult
from django.contrib import messages
from django.views import View
import json
import os
from aichat.dyslexia_tutor import DyslexiaTutorAI
from django.views.decorators.http import require_POST
from django.urls import reverse

# Dictionary to store AI instances for different subjects
subject_ai_instances = {}

def get_subject_ai(subject):
    """Get or create an AI instance for a specific subject."""
    try:
        # Get the subject material
        subject_material = SubjectMaterial.objects.get(subject=subject)
        
        if not subject_material.pdf_file:
            raise ValueError(f"No PDF file uploaded for subject: {subject}")
            
        # Get the full path to the PDF file
        pdf_path = os.path.join(settings.MEDIA_ROOT, str(subject_material.pdf_file))
        
        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF file not found at: {pdf_path}")
            
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        # Create a unique vector database path for this subject
        vector_db_path = os.path.join(settings.MEDIA_ROOT, 'vector_dbs', subject.lower())
        os.makedirs(vector_db_path, exist_ok=True)
        
        # Create new AI instance for this subject
        subject_ai_instances[subject] = DyslexiaTutorAI(
            google_api_key=api_key,
            data_path=pdf_path,
            persist_directory=vector_db_path
        )
        
        return subject_ai_instances[subject]
        
    except SubjectMaterial.DoesNotExist:
        raise ValueError(f"Subject material not found for: {subject}")
    except Exception as e:
        raise ValueError(f"Error initializing AI for subject {subject}: {str(e)}")

@login_required
def quiz_list(request):
    """Display list of available quizzes and user's progress."""
    quizzes = Quiz.objects.annotate(
        question_count=Count('questions'),
        avg_score=Avg('attempts__score')
    )
    
    # Get user's attempts
    user_attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz')
    
    # Create a dictionary of quiz attempts for easy lookup
    attempt_dict = {
        attempt.quiz_id: attempt 
        for attempt in user_attempts
    }
    
    context = {
        'quizzes': quizzes,
        'attempt_dict': attempt_dict
    }
    return render(request, 'dyslexia/quiz_list.html', context)

@login_required
def quiz_detail(request, quiz_id):
    """Display quiz details and questions."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user has a completed attempt
    completed_attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        completed=True
    ).first()
    
    if completed_attempt:
        messages.info(request, f'You have already completed this quiz with a score of {completed_attempt.score}%. You can view your results or retry the quiz.')
        return redirect('dyslexia:quiz_result', attempt_id=completed_attempt.id)
    
    # Check if user has an incomplete attempt
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        completed=False
    ).first()
    
    if not attempt:
        # Create new attempt with initial time_taken set to 0
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            time_taken=0  # Initialize time_taken to 0
        )
    
    context = {
        'quiz': quiz,
        'attempt': attempt
    }
    return render(request, 'dyslexia/quiz_detail.html', context)

@login_required
def submit_quiz_response(request, quiz_id):
    """Handle individual question responses via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(
        QuizAttempt,
        user=request.user,
        quiz=quiz,
        completed=False
    )
    
    try:
        question_id = request.POST.get('question_id')
        option_id = request.POST.get('option_id')
        response_time = request.POST.get('response_time')
        
        selected_option = get_object_or_404(Option, id=option_id)
        
        # Create or update response
        response, created = QuestionResponse.objects.update_or_create(
            attempt=attempt,
            question_id=question_id,
            defaults={
                'selected_option': selected_option,
                'is_correct': selected_option.is_correct,
                'response_time': response_time
            }
        )
        
        return JsonResponse({
            'success': True,
            'is_correct': selected_option.is_correct,
            'explanation': selected_option.explanation
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def update_dyslexia_level(user):
    """Update user's dyslexia level based on their progress in quizzes and assignments."""
    try:
        user_profile = UserProfile.objects.get(user=user)
        if user_profile.condition_type != 'dyslexia':
            return

        # Get all quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(
            user=user,
            completed=True
        ).order_by('-completed_at')[:5]  # Look at last 5 attempts

        # Get all assignment submissions
        assignment_submissions = AssignmentSubmission.objects.filter(
            user=user,
            completed=True
        ).order_by('-completed_at')[:5]  # Look at last 5 submissions

        # Calculate average scores
        quiz_scores = [attempt.score for attempt in quiz_attempts]
        assignment_scores = [submission.score for submission in assignment_submissions]

        # Calculate overall progress
        total_attempts = len(quiz_scores) + len(assignment_scores)
        if total_attempts == 0:
            return

        avg_score = (sum(quiz_scores) + sum(assignment_scores)) / total_attempts

        # Update dyslexia level based on progress
        dyslexia_profile = user_profile.dyslexia
        current_level = dyslexia_profile.level

        if avg_score >= 80:
            # Significant improvement
            if current_level == 'high':
                dyslexia_profile.level = 'medium'
            elif current_level == 'medium':
                dyslexia_profile.level = 'low'
        elif avg_score >= 60:
            # Moderate improvement
            if current_level == 'high':
                dyslexia_profile.level = 'medium'
        elif avg_score < 40:
            # Decline in performance
            if current_level == 'low':
                dyslexia_profile.level = 'medium'
            elif current_level == 'medium':
                dyslexia_profile.level = 'high'

        dyslexia_profile.save()

    except (UserProfile.DoesNotExist, Dyslexia.DoesNotExist):
        pass

@login_required
def submit_quiz(request, quiz_id):
    """Handle final quiz submission."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        responses_data = data.get('responses', [])
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        attempt = get_object_or_404(
            QuizAttempt,
            user=request.user,
            quiz=quiz,
            completed=False
        )
        
        # Save all responses
        for response_data in responses_data:
            question_id = response_data.get('question_id')
            option_id = response_data.get('selected_option_id')
            
            if not question_id or not option_id:
                continue
                
            try:
                question = Question.objects.get(id=question_id)
                selected_option = Option.objects.get(id=option_id)
                
                QuestionResponse.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_option=selected_option,
                    is_correct=selected_option.is_correct,
                    response_time=response_data.get('response_time', 0)
                )
            except (Question.DoesNotExist, Option.DoesNotExist) as e:
                print(f"Error saving response: {str(e)}")
                continue
        
        # Calculate score
        total_questions = quiz.questions.count()
        correct_answers = attempt.responses.filter(is_correct=True).count()
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Update attempt
        attempt.score = score
        attempt.completed = True
        attempt.completed_at = timezone.now()
        attempt.time_taken = (attempt.completed_at - attempt.started_at).seconds
        attempt.save()
        
        # Update dyslexia level based on progress
        update_dyslexia_level(request.user)
        
        # Generate redirect URL
        redirect_url = reverse('dyslexia:quiz_result', args=[attempt.id])
        
        return JsonResponse({
            'success': True,
            'score': score,
            'passed': score >= quiz.pass_mark,
            'redirect_url': redirect_url
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Unexpected error in submit_quiz: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def quiz_result(request, attempt_id):
    """Display quiz results and detailed feedback."""
    try:
        # Get the attempt with related data
        attempt = get_object_or_404(
            QuizAttempt.objects.select_related('quiz', 'user'),
            id=attempt_id,
            user=request.user,  # Ensure user can only see their own attempts
            completed=True
        )
        
        # Get all responses with related data
        responses = attempt.responses.select_related(
            'question',
            'selected_option'
        ).order_by('question__order')
        
        # Calculate statistics
        total_questions = responses.count()
        correct_answers = responses.filter(is_correct=True).count()
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Get time taken in minutes
        time_taken_minutes = attempt.time_taken // 60
        time_taken_seconds = attempt.time_taken % 60
        
        context = {
            'attempt': attempt,
            'responses': responses,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'score_percentage': round(score_percentage, 2),
            'time_taken_minutes': time_taken_minutes,
            'time_taken_seconds': time_taken_seconds,
            'passed': score_percentage >= attempt.quiz.pass_mark,
            'user': request.user
        }
        
        return render(request, 'dyslexia/quiz_result.html', context)
        
    except QuizAttempt.DoesNotExist:
        messages.error(request, 'Quiz attempt not found or you do not have permission to view it.')
        return redirect('dyslexia:quiz_list')
    except Exception as e:
        messages.error(request, f'Error displaying quiz results: {str(e)}')
        return redirect('dyslexia:quiz_list')

@login_required
def dashboard(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Check if user has dyslexia
        if user_profile.condition_type != 'dyslexia':
            messages.error(request, 'Access denied. This dashboard is for users with dyslexia.')
            return redirect('main:home')
            
        # Get dyslexia profile and test results
        dyslexia_profile = user_profile.dyslexia
        test_result = user_profile.dyslexiatestresult
        
        # Calculate section percentages
        total_questions = {
            'phonological': 5,  # Assuming 5 questions per section
            'surface': 5,
            'visual': 5
        }
        
        section_percentages = {
            'phonological': (test_result.phonological_score / total_questions['phonological'] * 100) if total_questions['phonological'] > 0 else 0,
            'surface': (test_result.surface_score / total_questions['surface'] * 100) if total_questions['surface'] > 0 else 0,
            'visual': (test_result.visual_score / total_questions['visual'] * 100) if total_questions['visual'] > 0 else 0
        }
        
        # Calculate overall percentage
        total_score = test_result.total_score
        total_questions_count = sum(total_questions.values())
        overall_percentage = (total_score / total_questions_count * 100) if total_questions_count > 0 else 0

        # Get quiz history
        quiz_history = QuizAttempt.objects.filter(
            user=request.user,
            completed=True
        ).select_related('quiz').order_by('-completed_at')[:5]  # Last 5 attempts

        # Calculate quiz statistics
        total_quizzes = QuizAttempt.objects.filter(user=request.user, completed=True).count()
        passed_quizzes = QuizAttempt.objects.filter(user=request.user, completed=True, score__gte=F('quiz__pass_mark')).count()
        average_score = QuizAttempt.objects.filter(user=request.user, completed=True).aggregate(Avg('score'))['score__avg'] or 0
        
        context = {
            'user_profile': user_profile,
            'dyslexia_profile': dyslexia_profile,
            'test_result': test_result,
            'section_percentages': section_percentages,
            'overall_percentage': round(overall_percentage, 2),
            'total_questions': total_questions,
            'quiz_history': quiz_history,
            'total_quizzes': total_quizzes,
            'passed_quizzes': passed_quizzes,
            'average_score': round(average_score, 2)
        }
        
        return render(request, 'dyslexia/dashboard.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('main:login')
    except Dyslexia.DoesNotExist:
        messages.error(request, 'Dyslexia profile not found. Please complete the assessment.')
        return redirect('main:dyslexia_test')
    except DyslexiaTestResult.DoesNotExist:
        messages.error(request, 'Test results not found. Please complete the assessment.')
        return redirect('main:dyslexia_test')

@login_required
def learning_modules(request):
    """Display available learning modules and subject materials."""
    subjects = SubjectMaterial.objects.all().order_by('subject')
    context = {
        'subjects': subjects
    }
    return render(request, 'dyslexia/learning.html', context)

def learning_module_detail(request, module_type):
    return render(request, f'dyslexia/learning_module_{module_type}.html')

@login_required
def progress(request):
    # Get user's quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's learning module progress
    module_progress = {
        'phonological': {
            'completed': 0,
            'total': 3,
            'current_module': 'Phonological Awareness'
        },
        'visual': {
            'completed': 0,
            'total': 3,
            'current_module': 'Visual Processing'
        },
        'reading': {
            'completed': 0,
            'total': 3,
            'current_module': 'Reading Comprehension'
        }
    }
    
    # Calculate overall progress
    total_modules = sum(module['total'] for module in module_progress.values())
    completed_modules = sum(module['completed'] for module in module_progress.values())
    overall_progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
    
    context = {
        'quiz_attempts': quiz_attempts,
        'module_progress': module_progress,
        'overall_progress': overall_progress,
    }
    
    return render(request, 'dyslexia/progress.html', context)

@login_required
def subject_chat(request, subject):
    """Display the chat interface for a specific subject."""
    # Verify the subject exists and has materials
    subject_material = get_object_or_404(SubjectMaterial, subject=subject)
    
    context = {
        'subject': subject,
        'subject_material': subject_material
    }
    return render(request, 'dyslexia/subject_chat.html', context)

@login_required
def get_extracted_text(request, subject):
    """Return extracted text from the subject's PDF."""
    try:
        # Get the AI instance for this subject
        ai = get_subject_ai(subject)
        # Get extracted text
        extracted_text = ai.get_extracted_text()
        if not extracted_text:
            return JsonResponse({
                'error': 'No text could be extracted from the PDF'
            }, status=500)
            
        return JsonResponse({'text': extracted_text})
            
    except ValueError as e:
        return JsonResponse({
            'error': str(e)
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def subject_chat_api(request, subject):
    """Handle chat API requests for a specific subject."""
    if request.method == "POST":
        try:
            print(f"Received chat request for subject: {subject}")  # Debug log
            data = json.loads(request.body)
            user_query = data.get("message", "")
            context = data.get("context", "")

            print(f"User query: {user_query}")  # Debug log

            if not user_query:
                return JsonResponse({"error": "No message provided"}, status=400)

            # Get the AI instance for this subject
            try:
                ai = get_subject_ai(subject)
                print("AI instance created successfully")  # Debug log
            except Exception as e:
                print(f"Error creating AI instance: {str(e)}")  # Debug log
                return JsonResponse({"error": f"Error initializing AI: {str(e)}"}, status=500)
            
            # Process the query
            try:
                response = ai.process_query(user_query, context=context)
                print(f"Generated response: {response[:100]}...")  # Debug log (first 100 chars)
            except Exception as e:
                print(f"Error processing query: {str(e)}")  # Debug log
                return JsonResponse({"error": f"Error processing query: {str(e)}"}, status=500)
            
            if not response:
                return JsonResponse({"error": "No response generated"}, status=500)
                
            return JsonResponse({"response": response})
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")  # Debug log
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except ValueError as e:
            print(f"Value error: {str(e)}")  # Debug log
            return JsonResponse({"error": str(e)}, status=404)
        except Exception as e:
            print(f"Unexpected error in subject_chat_api: {str(e)}")  # Debug log
            return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def assignments_list(request):
    assignments = Assignment.objects.filter(is_active=True).prefetch_related('submissions')
    return render(request, 'dyslexia/assignments.html', {'assignments': assignments})

@login_required
def take_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, is_active=True)
    
    # Get or create submission
    submission, created = AssignmentSubmission.objects.get_or_create(
        user=request.user,
        assignment=assignment,
        defaults={'completed': False}
    )

    if submission.completed:
        return redirect('dyslexia:view_assignment_results', assignment_id=assignment_id)

    questions = assignment.questions.all().order_by('order')
    return render(request, 'dyslexia/take_assignment.html', {
        'assignment': assignment,
        'questions': questions,
        'submission': submission
    })

@login_required
@require_POST
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = get_object_or_404(AssignmentSubmission, user=request.user, assignment=assignment)
    
    data = json.loads(request.body)
    responses = data.get('responses', [])
    
    total_questions = len(responses)
    correct_answers = 0
    
    for response_data in responses:
        question = Question.objects.get(id=response_data['question_id'])
        selected_option = Option.objects.get(id=response_data['selected_option_id'])
        
        AssignmentResponse.objects.create(
            submission=submission,
            question=question,
            selected_option=selected_option,
            is_correct=selected_option.is_correct,
            response_time=response_data.get('response_time', 0)
        )
        
        if selected_option.is_correct:
            correct_answers += 1
    
    submission.score = int((correct_answers / total_questions) * 100)
    submission.completed = True
    submission.save()
    
    # Update dyslexia level based on progress
    update_dyslexia_level(request.user)
    
    return JsonResponse({
        'status': 'success',
        'score': submission.score,
        'redirect_url': reverse('dyslexia:view_assignment_results', args=[assignment_id])
    })

@login_required
def view_assignment_results(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = get_object_or_404(AssignmentSubmission, user=request.user, assignment=assignment)
    responses = submission.responses.all().select_related('question', 'selected_option')
    
    return render(request, 'dyslexia/assignment_results.html', {
        'assignment': assignment,
        'submission': submission,
        'responses': responses
    })
