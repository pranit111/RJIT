from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import UserProfile, Dyslexia, Autism, DyslexiaTestQuestion, DyslexiaTestResponse, DyslexiaTestResult
from .forms import CustomUserCreationForm, UserProfileForm
import json

# Create your views here.
def index(request):
    return render(request, 'main/index.html')

def about(request):
    return render(request, 'main/about.html')

def contact(request):
    return render(request, 'main/contact.html')

def pricing(request):
    return render(request, 'main/pricing.html')

def features(request):
    return render(request, 'main/features.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('main:home')
        
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            login(request, user)
            messages.success(request, 'Registration successful! Please complete your profile.')
            return redirect('main:select_condition')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        user_form = CustomUserCreationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'main/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def login_user(request):
    if request.user.is_authenticated:
        return redirect('main:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            
            # Check if user has a profile and condition
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.condition_type == 'none':
                    # No condition set, redirect to dyslexia test
                    return redirect('main:dyslexia_test')
                elif user_profile.condition_type == 'dyslexia':
                    # User has dyslexia, redirect to dyslexia dashboard
                    return redirect('dyslexia:dashboard')
                else:
                    # User has another condition, redirect to home
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('main:home')
            except UserProfile.DoesNotExist:
                # If profile doesn't exist, create one and redirect to dyslexia test
                user_profile = UserProfile.objects.create(user=user, condition_type='none')
                return redirect('main:dyslexia_test')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'main/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('main:login')

def home(request):
    if not request.user.is_authenticated:
        return redirect('main:login')
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Redirect users with dyslexia to the dyslexia dashboard
        if user_profile.condition_type == 'dyslexia':
            return redirect('dyslexia:dashboard')
            
        context = {
            'user_profile': user_profile,
        }
        
        # Add condition-specific information to context
        if user_profile.condition_type == 'autism':
            try:
                autism_profile = user_profile.autism
                context.update({
                    'condition_profile': autism_profile,
                    'condition_type': 'Autism',
                    'type_label': autism_profile.get_autism_type_display(),
                    'level_label': autism_profile.get_autism_level_display(),
                })
            except Autism.DoesNotExist:
                messages.warning(request, 'Autism profile not found. Please contact support.')
                
        elif user_profile.condition_type == 'none':
            messages.info(request, 'Please complete the dyslexia assessment to get started.')
            return redirect('main:dyslexia_test')
            
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found. Please contact support.')
        return redirect('main:login')
    
    return render(request, 'main/home.html', context)

def select_condition(request):
    if not request.user.is_authenticated:
        return redirect('main:login')
    
    user_profile = UserProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        condition_type = request.POST.get('condition_type')
        if condition_type in ['dyslexia', 'autism', 'none']:
            user_profile.condition_type = condition_type
            user_profile.save()
            
            if condition_type == 'dyslexia':
                Dyslexia.objects.create(user_profile=user_profile)
                messages.success(request, 'Dyslexia profile created successfully!')
            elif condition_type == 'autism':
                Autism.objects.create(user_profile=user_profile)
                messages.success(request, 'Autism profile created successfully!')
            
            return redirect('main:home')
        else:
            messages.error(request, 'Invalid condition type selected.')
    
    return render(request, 'main/dyslexia_test.html')

def dyslexia_test(request):
    if not request.user.is_authenticated:
        return redirect('main:login')
    
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user has already completed the test
    if hasattr(user_profile, 'dyslexiatestresult'):
        messages.info(request, 'You have already completed the dyslexia test.')
        return redirect('main:home')
    
    # Get questions for each section
    phonological_questions = DyslexiaTestQuestion.objects.filter(section='phonological')
    surface_questions = DyslexiaTestQuestion.objects.filter(section='surface')
    visual_questions = DyslexiaTestQuestion.objects.filter(section='visual')
    
    context = {
        'phonological_questions': phonological_questions,
        'surface_questions': surface_questions,
        'visual_questions': visual_questions,
    }
    
    return render(request, 'main/dyslexia_test.html', context)

@require_POST
def submit_test_response(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)

        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer = data.get('answer')
        response_time = data.get('response_time')

        if not all([question_id, answer, response_time]):
            return JsonResponse({
                'success': False, 
                'error': 'Missing required fields'
            }, status=400)

        try:
            question = DyslexiaTestQuestion.objects.get(id=question_id)
            user_profile = UserProfile.objects.get(user=request.user)
        except DyslexiaTestQuestion.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Question not found'
            }, status=404)
        except UserProfile.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'User profile not found'
            }, status=404)

        # Create the response
        is_correct = answer == question.correct_answer
        response = DyslexiaTestResponse.objects.create(
            user_profile=user_profile,
            question=question,
            selected_answer=answer,
            is_correct=is_correct,
            response_time=response_time
        )

        # Calculate section scores
        section_responses = DyslexiaTestResponse.objects.filter(
            user_profile=user_profile,
            question__section=question.section
        )
        
        section_total = section_responses.count()
        section_correct = section_responses.filter(is_correct=True).count()
        section_score = (section_correct / section_total * 100) if section_total > 0 else 0

        # Calculate overall score
        all_responses = DyslexiaTestResponse.objects.filter(user_profile=user_profile)
        total_questions = all_responses.count()
        total_correct = all_responses.filter(is_correct=True).count()
        total_score = (total_correct / total_questions * 100) if total_questions > 0 else 0

        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'section_score': round(section_score, 2),
            'total_score': round(total_score, 2),
            'section': question.section
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)

@require_POST
def submit_test_results(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)

        data = json.loads(request.body)
        user_profile = UserProfile.objects.get(user=request.user)

        # Get scores for each section
        phonological_score = data.get('phonological', 0)
        surface_score = data.get('surface', 0)
        visual_score = data.get('visual', 0)
        total_score = data.get('total', 0)

        # Get total questions for each section
        phonological_total = DyslexiaTestQuestion.objects.filter(section='phonological').count()
        surface_total = DyslexiaTestQuestion.objects.filter(section='surface').count()
        visual_total = DyslexiaTestQuestion.objects.filter(section='visual').count()
        total_questions = phonological_total + surface_total + visual_total

        # Calculate percentages for each section
        phonological_percentage = (phonological_score / phonological_total * 100) if phonological_total > 0 else 0
        surface_percentage = (surface_score / surface_total * 100) if surface_total > 0 else 0
        visual_percentage = (visual_score / visual_total * 100) if visual_total > 0 else 0
        total_percentage = (total_score / total_questions * 100) if total_questions > 0 else 0

        # Determine dyslexia type based on lowest scoring section
        section_scores = {
            'phonological': phonological_percentage,
            'surface': surface_percentage,
            'visual': visual_percentage
        }
        
        # Find the section with the lowest score
        lowest_section = min(section_scores.items(), key=lambda x: x[1])
        dyslexia_type = lowest_section[0]  # 'phonological', 'surface', or 'visual'

        # Determine dyslexia level based on total percentage
        if total_percentage < 30:
            dyslexia_level = 'high'
            condition_level = 'high'
        elif total_percentage < 50:
            dyslexia_level = 'medium'
            condition_level = 'medium'
        elif total_percentage < 80:
            dyslexia_level = 'low'
            condition_level = 'low'
        else:
            dyslexia_level = 'none'
            condition_level = None

        # Create or update test result
        test_result, created = DyslexiaTestResult.objects.get_or_create(
            user_profile=user_profile,
            defaults={
                'phonological_score': phonological_score,
                'surface_score': surface_score,
                'visual_score': visual_score,
                'total_score': total_score
            }
        )

        if not created:
            test_result.phonological_score = phonological_score
            test_result.surface_score = surface_score
            test_result.visual_score = visual_score
            test_result.total_score = total_score
            test_result.save()

        # Create or update dyslexia profile
        dyslexia_profile, created = Dyslexia.objects.get_or_create(
            user_profile=user_profile,
            defaults={
                'dyslexia_type': dyslexia_type,
                'dyslexia_level': dyslexia_level
            }
        )

        if not created:
            dyslexia_profile.dyslexia_type = dyslexia_type
            dyslexia_profile.dyslexia_level = dyslexia_level
            dyslexia_profile.save()

        # Update user profile condition type and level
        user_profile.condition_type = 'dyslexia'
        user_profile.condition_level = condition_level
        user_profile.save()

        return JsonResponse({
            'success': True,
            'dyslexia_type': dyslexia_type,
            'dyslexia_level': dyslexia_level,
            'condition_level': condition_level,
            'total_percentage': round(total_percentage, 2),
            'section_scores': {
                'phonological': round(phonological_percentage, 2),
                'surface': round(surface_percentage, 2),
                'visual': round(visual_percentage, 2)
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)


