from django.urls import path
from . import views

app_name = 'main'  # Add namespace

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path('features/', views.features, name='features'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('select-condition/', views.select_condition, name='select_condition'),
    path('dyslexia-test/', views.dyslexia_test, name='dyslexia_test'),
    path('submit-test-response/', views.submit_test_response, name='submit_test_response'),
    path('submit-test-results/', views.submit_test_results, name='submit_test_results'),
]