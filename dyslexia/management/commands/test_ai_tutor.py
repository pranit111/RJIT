from django.core.management.base import BaseCommand
from dyslexia.ai.tutor import DyslexiaTutorAI
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Test the AI tutor with a sample PDF'

    def handle(self, *args, **options):
        try:
            # Test file paths
            test_pdf_path = os.path.join(settings.MEDIA_ROOT, 'test.pdf')
            vector_db_path = os.path.join(settings.VECTOR_DB_ROOT, 'test_db')
            
            # Initialize tutor
            tutor = DyslexiaTutorAI(
                data_path=test_pdf_path,
                persist_directory=vector_db_path
            )
            
            # Test questions
            questions = [
                "What is addition?",
                "How does multiplication work?",
                "Can you explain division in a simple way?"
            ]
            
            for question in questions:
                self.stdout.write(f"\nQuestion: {question}")
                response = tutor.process_query(question)
                self.stdout.write(f"Answer: {response}\n")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 