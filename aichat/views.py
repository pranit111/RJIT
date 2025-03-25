import os
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from .dyslexia_tutor import DyslexiaTutorAI  # Import your AI class

# Initialize AI model
api_key = os.getenv("GOOGLE_API_KEY")
ai = DyslexiaTutorAI(
    google_api_key=api_key,
    data_path=r"C:\Users\ASUS\Desktop\rgit tut\studybuddy\aichat\eng_10_book.pdf",
    persist_directory="./vector_db"
)

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_query = data.get("message", "")

        if not user_query:
            return JsonResponse({"error": "No message provided"}, status=400)

        response = ai.process_query(user_query)
        return JsonResponse({"response": response})

    return JsonResponse({"error": "Invalid request"}, status=400)
def chat(request):
    return render(request, "index.html")