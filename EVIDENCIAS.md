# Evidencias — Servicios web con Django REST Framework

Alumno: Eder Yaycate · Sección 4-C24-A · Laboratorio 08

> El código, las pruebas y las salidas de este documento se generaron con ayuda de un asistente de
> IA (Claude). Las capturas, el reparto de trabajo del equipo y las conclusiones deben reflejar lo
> que cada integrante hizo y comprobó realmente; ajusta lo que haga falta.

## Reparto del trabajo (completar)

| Integrante | Tarea | Evidencia (commit / captura) |
|---|---|---|
| _por completar_ | _por completar_ | _por completar_ |

## Capturas a incluir en el entregable

1. **Estructura del proyecto** en VS Code (`config/`, `quiz/`, `scripts/`).
2. **`REST_FRAMEWORK` en `settings.py`** y `config/urls.py` con `api/`.
3. **API navegable** en `/api/` mostrando los tres recursos (`exams`, `questions`, `options`).
4. **Cinco operaciones en la API navegable** con su código: listar (200), detalle (200), crear (201), PATCH (200), eliminar (204).
5. **Las mismas operaciones con el cliente externo:** salida de `python scripts/api_client.py`.
6. **Los tres errores del paso 9:** campo ausente, tipo incorrecto y opción correcta (los cuatro 400 del script).
7. **Filtrado, búsqueda y paginación:** `?exam=2`, `?search=lista`, `?page=2` y `?page=99` (404).
8. **Suite de pruebas:** `python manage.py test` → 32 pruebas OK.
9. **Tabla de la API** (copiar la del `README.md`).

## Resultado del cliente externo (`python scripts/api_client.py`)

| Operación | Método y dirección | Código |
|---|---|---|
| Listar exámenes | `GET /api/exams/` | 200 |
| Detalle del examen 1 | `GET /api/exams/1/` | 200 |
| Crear examen | `POST /api/exams/` | 201 |
| Modificar parcialmente | `PATCH /api/exams/{id}/` | 200 |
| Eliminar examen | `DELETE /api/exams/{id}/` | 204 |
| Detalle del examen eliminado | `GET /api/exams/{id}/` | 404 |
| Listar preguntas (página 1) | `GET /api/questions/` | 200 |
| Detalle de la pregunta 1 | `GET /api/questions/1/` | 200 |
| Crear pregunta | `POST /api/questions/` | 201 |
| Modificar parcialmente | `PATCH /api/questions/{id}/` | 200 |
| Eliminar pregunta | `DELETE /api/questions/{id}/` | 204 |
| Campo obligatorio ausente | `POST /api/questions/` | 400 |
| Tipo incorrecto (`exam = "abc"`) | `POST /api/questions/` | 400 |
| Dos opciones correctas | `POST /api/questions/` | 400 |
| Ninguna opción correcta | `POST /api/questions/` | 400 |
| Escritura sin credenciales | `POST /api/exams/` | 403 |
| Preguntas del examen 2 | `GET /api/questions/?exam=2` | 200 (6 resultados, 2 páginas) |
| Búsqueda «lista» | `GET /api/questions/?search=lista` | 200 (2 resultados) |
| Búsqueda y filtro | `GET /api/questions/?exam=2&search=lista` | 200 (1 resultado) |
| Página 2 y 3 | `GET /api/questions/?page=2` / `?page=3` | 200 (5 y 3 resultados; 13 en total) |
| Página inexistente | `GET /api/questions/?page=99` | 404 |
| Filtro no numérico | `GET /api/questions/?exam=abc` | 400 |

## Efecto de la paginación (paso 10)

Con 13 preguntas y `PAGE_SIZE = 5` la lista se reparte en tres páginas de 5, 5 y 3 resultados. La
respuesta incluye `count` (13), `next` y `previous` (`null` en los extremos). El filtro y la búsqueda
se aplican antes de paginar, por eso `?exam=2` (6 preguntas) ya necesita dos páginas y
`?exam=2&search=lista` cabe en una. Pedir una página que no existe devuelve 404 («Página inválida.»).

## Conclusiones (borrador)

1. Un `ModelSerializer` deriva del modelo los campos, los tipos y las validaciones básicas, y deja
   escribir solo lo propio del caso: aquí, que una pregunta tenga exactamente una opción correcta.
2. Decidir cómo viajan las relaciones define la API: las opciones anidadas en la pregunta se leen y
   se escriben en una sola petición, y el examen por identificador evita repetir su contenido.
3. Con `ModelViewSet` y `DefaultRouter`, tres clases dan los cinco recorridos de cada recurso sin
   escribir rutas a mano, y la API navegable permite probarlos de inmediato.
4. Probar por HTTP con un cliente externo comprueba lo que la API navegable oculta: los códigos de
   estado (200, 201, 204, 400, 403, 404) y los mensajes de error que recibiría cualquier cliente.
