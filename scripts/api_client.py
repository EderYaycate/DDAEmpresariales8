"""External HTTP client: walks through every operation of the API and prints the status codes.

Usage (with the server running):
    python scripts/api_client.py
Credentials come from API_USER / API_PASSWORD (default: the demo superuser).
"""
import base64
import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get('API_BASE', 'http://127.0.0.1:8000/api')
USER = os.environ.get('API_USER', 'admin')
PASSWORD = os.environ.get('API_PASSWORD', os.environ.get('DEMO_ADMIN_PASSWORD', 'Admin12345!'))
TOKEN = base64.b64encode(f'{USER}:{PASSWORD}'.encode()).decode()


def call(method, path, body=None, auth=True):
    """Send one request and return (status code, parsed JSON or None)."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Accept', 'application/json')
    if auth:
        request.add_header('Authorization', f'Basic {TOKEN}')
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as error:
        raw = error.read().decode()
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, raw


def show(label, method, path, status, body):
    text = json.dumps(body, ensure_ascii=False) if body is not None else '(sin cuerpo)'
    print(f'{label:<34} {method:<6} {path:<28} -> {status}  {text[:150]}')


def step(label, method, path, body=None, auth=True):
    status, payload = call(method, path, body, auth)
    show(label, method, path, status, payload)
    return status, payload


print('--- Operaciones sobre exámenes ---')
step('Listar exámenes', 'GET', '/exams/')
step('Detalle del examen 1', 'GET', '/exams/1/')
_, created = step('Crear examen', 'POST', '/exams/', {'title': 'Bases de datos', 'description': 'SQL básico'})
exam_id = created['id']
step('Modificar parcialmente (PATCH)', 'PATCH', f'/exams/{exam_id}/', {'description': 'SQL y diseño'})
step('Eliminar examen', 'DELETE', f'/exams/{exam_id}/')
step('Detalle del examen eliminado', 'GET', f'/exams/{exam_id}/')

print('\n--- Operaciones sobre preguntas ---')
step('Listar preguntas (página 1)', 'GET', '/questions/')
step('Detalle de la pregunta 1', 'GET', '/questions/1/')
_, question = step('Crear pregunta', 'POST', '/questions/', {
    'exam': 1,
    'text': '¿Qué método ordena una lista?',
    'options': [{'text': 'sort()', 'is_correct': True}, {'text': 'order()', 'is_correct': False}],
})
question_id = question['id']
step('Modificar parcialmente (PATCH)', 'PATCH', f'/questions/{question_id}/', {'text': '¿Qué método ordena una lista en el sitio?'})
step('Eliminar pregunta', 'DELETE', f'/questions/{question_id}/')

print('\n--- Tres errores provocados ---')
step('Campo obligatorio ausente', 'POST', '/questions/', {
    'exam': 1, 'options': [{'text': 'A', 'is_correct': True}],
})
step('Tipo incorrecto (exam = "abc")', 'POST', '/questions/', {
    'exam': 'abc', 'text': 'Pregunta', 'options': [{'text': 'A', 'is_correct': True}],
})
step('Dos opciones correctas', 'POST', '/questions/', {
    'exam': 1, 'text': 'Pregunta', 'options': [
        {'text': 'A', 'is_correct': True}, {'text': 'B', 'is_correct': True}],
})
step('Ninguna opción correcta', 'POST', '/questions/', {
    'exam': 1, 'text': 'Pregunta', 'options': [
        {'text': 'A', 'is_correct': False}, {'text': 'B', 'is_correct': False}],
})
step('Sin credenciales (escritura)', 'POST', '/exams/', {'title': 'Intruso'}, auth=False)

print('\n--- Filtrado, búsqueda y paginación ---')
step('Preguntas del examen 2', 'GET', '/questions/?exam=2')
step('Búsqueda "lista"', 'GET', '/questions/?search=lista')
step('Búsqueda + filtro', 'GET', '/questions/?exam=2&search=lista')
step('Página 2 de preguntas', 'GET', '/questions/?page=2')
step('Página 3 (última)', 'GET', '/questions/?page=3')
step('Página 99 (no existe)', 'GET', '/questions/?page=99')
step('Filtro con valor no numérico', 'GET', '/questions/?exam=abc')
