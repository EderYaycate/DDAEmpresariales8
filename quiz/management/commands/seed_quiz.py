import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from quiz.models import Exam, Option, Question

# Each question: (text, [options], index of the correct option)
EXAMS = {
    'Fundamentos de Python': {
        'description': 'Conceptos básicos del lenguaje.',
        'questions': [
            ('¿Qué función muestra texto en pantalla?', ['print()', 'show()', 'echo()'], 0),
            ('¿Cuál es el tipo de dato de 3.14?', ['int', 'float', 'str'], 1),
            ('¿Qué estructura es inmutable?', ['list', 'dict', 'tuple'], 2),
            ('¿Cómo se define una función?', ['def', 'func', 'function'], 0),
            ('¿Qué operador eleva a una potencia?', ['^', '**', '//'], 1),
            ('¿Qué palabra clave maneja errores?', ['try', 'catch', 'handle'], 0),
            ('¿Qué método agrega un elemento a una lista?', ['add()', 'push()', 'append()'], 2),
        ],
    },
    'Django básico': {
        'description': 'Modelos, vistas y plantillas.',
        'questions': [
            ('¿Qué archivo define las rutas de un proyecto?', ['urls.py', 'models.py', 'admin.py'], 0),
            ('¿Qué comando crea las migraciones?', ['migrate', 'makemigrations', 'runserver'], 1),
            ('¿Qué clase base usan los modelos?', ['models.Model', 'forms.Form', 'views.View'], 0),
            ('¿Qué comando levanta el servidor de desarrollo?', ['startapp', 'runserver', 'shell'], 1),
            ('¿Qué etiqueta recorre una lista en una plantilla?', ['{% loop %}', '{% for %}', '{% each %}'], 1),
            ('¿Qué relación usa ForeignKey?', ['Uno a muchos', 'Muchos a muchos', 'Uno a uno'], 0),
        ],
    },
}


class Command(BaseCommand):
    help = 'Load demo exams, questions and options, and the demo superuser.'

    def handle(self, *args, **options):
        if not Exam.objects.exists():
            for title, data in EXAMS.items():
                exam = Exam.objects.create(title=title, description=data['description'])
                for text, choices, correct in data['questions']:
                    question = Question.objects.create(exam=exam, text=text)
                    Option.objects.bulk_create(
                        Option(question=question, text=choice, is_correct=(i == correct))
                        for i, choice in enumerate(choices)
                    )

        password = os.environ.get('DEMO_ADMIN_PASSWORD', 'Admin12345!')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', password)

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Exam.objects.count()} exámenes, {Question.objects.count()} preguntas, '
            f'{Option.objects.count()} opciones.'
        ))
