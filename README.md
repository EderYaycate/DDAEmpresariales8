# DDAEmpresariales8 — Servicios web con Django REST Framework

Laboratorio 08 de Desarrollo de Aplicaciones Empresariales (4-C24-A).
API REST de cuestionarios con la aplicación `quiz`: exámenes, preguntas y opciones, publicados con `ModelSerializer`, `ModelViewSet` y `DefaultRouter`.

## Cómo ejecutarlo

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_quiz      # 2 exámenes, 13 preguntas, 39 opciones y el superusuario "admin"
python manage.py runserver
```

- API navegable: http://127.0.0.1:8000/api/
- Inicio de sesión de la API navegable: http://127.0.0.1:8000/api-auth/login/ (usuario `admin`, contraseña de demostración `Admin12345!`, modificable con `DEMO_ADMIN_PASSWORD` antes de `seed_quiz`; no usar fuera del laboratorio).
- Panel de administración: http://127.0.0.1:8000/admin/
- `SECRET_KEY` y `DEBUG` se leen de `DJANGO_SECRET_KEY` y `DJANGO_DEBUG`.

## Pruebas y cliente HTTP externo

```powershell
python manage.py test                 # 32 pruebas
python scripts/api_client.py          # con el servidor en marcha: recorre todas las operaciones por HTTP
```

`scripts/api_client.py` es el cliente externo del paso 8: envía JSON con `urllib` y autenticación básica, e imprime cada operación con su código de estado. También sirve `curl.exe` (en PowerShell, con el cuerpo en un archivo para evitar problemas de comillas):

```powershell
curl.exe -u admin:Admin12345! -H "Content-Type: application/json" -d "@scripts/example_question.json" http://127.0.0.1:8000/api/questions/
```

## Decisiones de diseño

- **Relaciones (paso 4):** las **opciones viajan anidadas dentro de la pregunta** (solo tienen sentido con ella, se leen y se escriben en una misma petición) y el **examen se refiere por su identificador** (`"exam": 1`), porque un examen se gestiona por separado y anidarlo repetiría su contenido en cada pregunta. Las opciones también existen como recurso propio (`/api/options/`), donde la pregunta se refiere por identificador.
- **Validación propia (paso 5):** `QuestionSerializer.validate_options` rechaza toda pregunta que no tenga **exactamente una** opción correcta. Con `PATCH` sin `options` las opciones existentes no se tocan; con `options` se reemplazan todas, y si la nueva lista es inválida no se cambia nada (todo ocurre en una transacción).
- **Regla en las opciones sueltas:** para que la regla no se rompa desde `/api/options/`, `OptionSerializer` rechaza una segunda opción correcta o dejar la pregunta sin ninguna, y `DELETE` no permite eliminar la opción correcta. Para cambiar cuál es la correcta se modifica la pregunta enviando todas sus opciones.
- **Campos de solo lectura:** `id` y `created_at` (examen); `id` (pregunta y opción). `question_count` del examen se calcula en una sola consulta con `annotate`.
- **Configuración (paso 2):** paginación por número de página con `PAGE_SIZE = 5` (con los datos de demostración hay 3 páginas de preguntas) y permiso de partida `IsAuthenticatedOrReadOnly`: cualquiera lee, solo un usuario autenticado escribe.
- **Rutas (paso 6):** un `DefaultRouter` en `quiz/urls.py` registra `exams`, `questions` y `options`, y `config/urls.py` lo incluye bajo `api/`.
- **Filtro y búsqueda (paso 10):** `?exam=<id>` filtra las preguntas por examen (un valor no numérico responde 400), `?question=<id>` filtra las opciones, y `?search=<texto>` busca en el enunciado de las preguntas (en el título de los exámenes y el texto de las opciones en sus recursos). Se combinan entre sí y con `?page=`.

## Tabla de la API (paso 11)

Las lecturas son públicas; las escrituras (POST, PUT, PATCH, DELETE) requieren autenticación. Las respuestas listadas son las reales, obtenidas con `scripts/api_client.py`.

| Recurso | Dirección | Método | Cuerpo de ejemplo | Respuesta esperada |
|---|---|---|---|---|
| Examen | `/api/exams/` | GET | — | `200` `{"count": 2, "next": null, "previous": null, "results": [{"id": 1, "title": "Fundamentos de Python", "description": "Conceptos básicos del lenguaje.", "created_at": "…", "question_count": 7}, …]}` |
| Examen | `/api/exams/` | POST | `{"title": "Bases de datos", "description": "SQL básico"}` | `201` `{"id": 3, "title": "Bases de datos", "description": "SQL básico", "created_at": "…", "question_count": 0}` |
| Examen | `/api/exams/{id}/` | GET | — | `200` el examen; `404` `{"detail": "No Exam matches the given query."}` si no existe |
| Examen | `/api/exams/{id}/` | PATCH | `{"description": "SQL y diseño"}` | `200` el examen con el campo cambiado |
| Examen | `/api/exams/{id}/` | PUT | `{"title": "…", "description": "…"}` (todos los campos) | `200` el examen reemplazado |
| Examen | `/api/exams/{id}/` | DELETE | — | `204` sin cuerpo; elimina también sus preguntas y opciones |
| Pregunta | `/api/questions/` | GET | — | `200` `{"count": 13, "next": ".../api/questions/?page=2", "previous": null, "results": [{"id": 1, "exam": 1, "text": "¿Qué función muestra texto en pantalla?", "options": [{"id": 1, "text": "print()", "is_correct": true}, …]}, …]}` (5 por página) |
| Pregunta | `/api/questions/?exam=2&search=lista&page=1` | GET | — | `200` solo las preguntas del examen 2 cuyo enunciado contiene «lista» (aquí `count: 1`); `404` `{"detail": "Página inválida."}` si la página no existe; `400` `{"exam": "Debe ser un número entero."}` si `exam` no es numérico |
| Pregunta | `/api/questions/` | POST | `{"exam": 1, "text": "¿Qué método ordena una lista?", "options": [{"text": "sort()", "is_correct": true}, {"text": "order()", "is_correct": false}]}` | `201` la pregunta con los `id` de sus opciones; `400` si falta un campo, el tipo es incorrecto o no hay exactamente una opción correcta |
| Pregunta | `/api/questions/{id}/` | GET | — | `200` la pregunta con sus opciones anidadas; `404` si no existe |
| Pregunta | `/api/questions/{id}/` | PATCH | `{"text": "Texto nuevo"}` o `{"options": [...]}` | `200` la pregunta actualizada (sin `options` no se tocan las opciones; con `options` se reemplazan) |
| Pregunta | `/api/questions/{id}/` | DELETE | — | `204` sin cuerpo; elimina también sus opciones |
| Opción | `/api/options/` | GET | — | `200` lista paginada de opciones; `?question=<id>` filtra por pregunta |
| Opción | `/api/options/` | POST | `{"question": 1, "text": "Otra", "is_correct": false}` | `201` la opción; `400` si se marca como correcta una segunda o la pregunta quedaría sin correcta |
| Opción | `/api/options/{id}/` | GET / PATCH / PUT | `{"text": "Nuevo texto"}` | `200` la opción; `400` si el cambio rompe la regla de la opción correcta |
| Opción | `/api/options/{id}/` | DELETE | — | `204` si es una opción incorrecta; `400` `{"detail": "No se puede eliminar la opción correcta de una pregunta."}` si es la correcta |
| Cualquiera | cualquier recurso | POST / PUT / PATCH / DELETE sin sesión | — | `403` `{"detail": "Las credenciales de autenticación no se proveyeron."}` |

### Errores provocados a propósito (paso 9)

| Error | Cuerpo enviado a `POST /api/questions/` | Código | Mensaje |
|---|---|---|---|
| Campo obligatorio ausente | `{"exam": 1, "options": [{"text": "A", "is_correct": true}]}` | `400` | `{"text": ["Este campo es requerido."]}` |
| Tipo incorrecto | `{"exam": "abc", "text": "Pregunta", "options": [...]}` | `400` | `{"exam": ["Tipo incorrecto. Se esperaba valor de clave primaria y se recibió str."]}` |
| Dos opciones correctas | `{"exam": 1, "text": "Pregunta", "options": [{"text": "A", "is_correct": true}, {"text": "B", "is_correct": true}]}` | `400` | `{"options": ["La pregunta debe tener exactamente una opción correcta (recibidas: 2)."]}` |
| Ninguna opción correcta | igual, con las dos en `false` | `400` | `{"options": ["La pregunta debe tener exactamente una opción correcta (recibidas: 0)."]}` |

## Recorrido por la API navegable (paso 7)

1. Abre http://127.0.0.1:8000/api/ y entra a «Log in» (arriba a la derecha) con `admin`.
2. **Listar:** `/api/questions/` → `200 OK`. **Detalle:** `/api/questions/1/` → `200 OK`.
3. **Crear:** en `/api/questions/`, pestaña «Raw data», pega el JSON de `scripts/example_question.json` y pulsa POST → `201 Created`.
4. **Modificar parcialmente:** en `/api/questions/<id>/`, «Raw data» con `{"text": "Texto nuevo"}` y PATCH → `200 OK`.
5. **Eliminar:** botón DELETE → `204 No Content`.

## Estructura

```
config/            # proyecto: settings (bloque REST_FRAMEWORK) y urls (api/, api-auth/, admin/)
quiz/
├── models.py      # Exam, Question, Option
├── serializers.py # ExamSerializer, QuestionSerializer (con opciones anidadas), OptionSerializer
├── views.py       # ExamViewSet, QuestionViewSet, OptionViewSet
├── urls.py        # DefaultRouter
├── admin.py
├── tests.py       # 32 pruebas de la API
└── management/commands/seed_quiz.py
scripts/api_client.py
```
