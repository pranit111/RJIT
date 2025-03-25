from django.core.management.base import BaseCommand
from dyslexia.models import SubjectMaterial
from dyslexia.ai.tutor import DyslexiaTutorAI
import os

class Command(BaseCommand):
    help = 'Process subject materials and create vector databases'

    def handle(self, *args, **options):
        materials = SubjectMaterial.objects.all()
        for material in materials:
            try:
                # Create vector db directory if it doesn't exist
                os.makedirs(os.path.dirname(material.vector_db_path), exist_ok=True)
                
                # Initialize tutor to process the material
                tutor = DyslexiaTutorAI.from_subject_material(material)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed {material}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {material}: {str(e)}')
                ) 