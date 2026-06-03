# Django REST API — Todo App

API REST construida con Django 5 + Django REST Framework como proyecto de aprendizaje. Incluye autenticación JWT, registro de usuarios y CRUD de tareas (todos) por usuario.

---

## Stack

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.12 | Lenguaje |
| Django | 5.1 | Framework web |
| Django REST Framework | 3.15 | API REST |
| SimpleJWT | 5.3 | Autenticación JWT |
| PostgreSQL | 16 | Base de datos |
| psycopg2 | 2.9 | Driver DB |
| python-decouple | 3.8 | Variables de entorno |
| django-cors-headers | 4.4 | CORS |

---

## Setup y arranque

### Requisitos

- Docker
- Docker Compose v2+

### Levantar el proyecto

```bash
# 1. Clonar y entrar al directorio
cd python-todo-app

# 2. Copiar el archivo de variables de entorno
cp .env.example .env

# 3. Construir y levantar los contenedores
docker compose up --build
```

Al levantar, el contenedor web:
1. Ejecuta `makemigrations` (genera los archivos de migración en `apps/todos/migrations/`)
2. Ejecuta `migrate` (aplica todas las migraciones a PostgreSQL)
3. Inicia el servidor en `http://localhost:8000`

### Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f web

# Acceder al shell de Django (equivalente a un REPL con acceso a todos los modelos)
docker compose exec web python manage.py shell

# Acceder a la base de datos
docker compose exec db psql -U todouser -d tododb

# Parar los contenedores
docker compose down

# Parar y eliminar volúmenes (borra la base de datos)
docker compose down -v
```

---

## Estructura del proyecto

```
python-todo-app/
├── .env                  ← Variables reales (nunca commitear)
├── .env.example          ← Template de variables
├── .gitignore
├── requirements.txt      ← Dependencias de app + testing
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── pytest.ini            ← Configuración del runner de tests
│
├── config/               ← Proyecto Django (settings, urls raíz)
│   ├── settings.py       ← Toda la configuración, variables via python-decouple
│   ├── urls.py           ← Router principal: conecta /api/auth/ y /api/todos/
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                 ← Utilidades compartidas entre apps
│   ├── responses.py      ← ApiResponse: formato uniforme de respuestas
│   ├── exceptions.py     ← custom_exception_handler: mapea errores de DRF al formato uniforme
│   └── permissions.py    ← IsOwner: permiso a nivel de objeto
│
└── apps/
    ├── users/
    │   ├── migrations/
    │   ├── apps.py
    │   ├── models.py       ← Usa el User built-in de Django
    │   ├── serializers.py  ← RegisterSerializer, UserSerializer
    │   ├── views.py        ← RegisterView, LoginView, LogoutView, MeView
    │   ├── urls.py         ← /api/auth/register|login|logout|me/
    │   └── tests/
    │       ├── factories.py       ← UserFactory (factory-boy)
    │       ├── test_serializers.py  ← Tests unitarios de serializers
    │       └── test_views.py        ← Tests de integración de endpoints
    │
    └── todos/
        ├── migrations/
        │   └── 0001_initial.py   ← Generada automáticamente al levantar
        ├── apps.py
        ├── models.py       ← Modelo Todo con ForeignKey a User
        ├── serializers.py  ← TodoSerializer con validación de título
        ├── views.py        ← TodoViewSet (ModelViewSet)
        ├── urls.py         ← DefaultRouter → /api/todos/{id}/
        └── tests/
            ├── factories.py       ← TodoFactory
            ├── test_serializers.py
            └── test_views.py
```

---

## Endpoints y formato de respuesta

Todas las respuestas siguen un formato uniforme:

```json
// Éxito
{ "success": true, "data": { ... }, "message": "opcional" }

// Error
{ "success": false, "error": { "code": "validation_error", "message": "...", "details": {...} } }
```

### Auth

| Método | URL | Auth | Descripción |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Crea un usuario |
| POST | `/api/auth/login/` | No | Login, retorna access + refresh token |
| POST | `/api/auth/logout/` | Bearer | Invalida el refresh token |
| GET | `/api/auth/me/` | Bearer | Perfil del usuario autenticado |

### Todos

| Método | URL | Descripción |
|---|---|---|
| GET | `/api/todos/` | Listar todos del usuario |
| POST | `/api/todos/` | Crear un todo |
| GET | `/api/todos/{id}/` | Obtener un todo |
| PUT | `/api/todos/{id}/` | Actualizar completo |
| PATCH | `/api/todos/{id}/` | Actualizar parcialmente |
| DELETE | `/api/todos/{id}/` | Eliminar (204 No Content) |

---

## Probar con curl

```bash
BASE="http://localhost:8000/api"

# ── 1. Registro ───────────────────────────────────────────────────────────────
curl -s -X POST "$BASE/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }' | python3 -m json.tool

# ── 2. Login (guarda el access token en variable) ─────────────────────────────
LOGIN=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "SecurePass123!"}')

ACCESS=$(echo $LOGIN | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")
REFRESH=$(echo $LOGIN | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['refresh'])")

echo "Access token: $ACCESS"

# ── 3. Perfil del usuario ─────────────────────────────────────────────────────
curl -s "$BASE/auth/me/" \
  -H "Authorization: Bearer $ACCESS" | python3 -m json.tool

# ── 4. Crear un todo ──────────────────────────────────────────────────────────
curl -s -X POST "$BASE/todos/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"title": "Aprender Django", "description": "Terminar el tutorial"}' \
  | python3 -m json.tool

# ── 5. Listar todos ───────────────────────────────────────────────────────────
curl -s "$BASE/todos/" \
  -H "Authorization: Bearer $ACCESS" | python3 -m json.tool

# ── 6. Obtener un todo específico ─────────────────────────────────────────────
curl -s "$BASE/todos/1/" \
  -H "Authorization: Bearer $ACCESS" | python3 -m json.tool

# ── 7. Actualizar parcialmente (marcar como completado) ───────────────────────
curl -s -X PATCH "$BASE/todos/1/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}' | python3 -m json.tool

# ── 8. Actualizar completo ────────────────────────────────────────────────────
curl -s -X PUT "$BASE/todos/1/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"title": "Aprender Django (actualizado)", "description": "Nueva descripción", "completed": false}' \
  | python3 -m json.tool

# ── 9. Eliminar un todo ───────────────────────────────────────────────────────
curl -s -X DELETE "$BASE/todos/1/" \
  -H "Authorization: Bearer $ACCESS" \
  -w "HTTP status: %{http_code}\n"
# Respuesta: HTTP status: 204 (sin body)

# ── 10. Logout ────────────────────────────────────────────────────────────────
curl -s -X POST "$BASE/auth/logout/" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}" | python3 -m json.tool

# ── 11. Verificar aislamiento ─────────────────────────────────────────────────
# Crear segundo usuario y verificar que no ve los todos de alice
curl -s -X POST "$BASE/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "email": "bob@example.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}' \
  | python3 -m json.tool

BOB_ACCESS=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "SecurePass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access'])")

# Bob no debe ver ningún todo (lista vacía)
curl -s "$BASE/todos/" -H "Authorization: Bearer $BOB_ACCESS" | python3 -m json.tool

# Bob no puede acceder a los todos de Alice (403 permission_denied)
curl -s "$BASE/todos/1/" -H "Authorization: Bearer $BOB_ACCESS" | python3 -m json.tool
```

---

## Guía educativa

### Cómo crear un nuevo endpoint desde cero

A modo de ejemplo, vamos a crear un recurso `Tag` (etiquetas para los todos). Estos son los pasos exactos que seguirías para cualquier recurso nuevo.

#### Paso 1 — Crear la app

```bash
# Dentro del contenedor
docker compose exec web python manage.py startapp tags apps/tags
```

Esto genera la estructura base en `apps/tags/`.

#### Paso 2 — Registrar la app en settings.py

```python
# config/settings.py
INSTALLED_APPS = [
    ...
    'apps.tags.apps.TagsConfig',
]
```

#### Paso 3 — Definir el modelo (`apps/tags/models.py`)

```python
from django.contrib.auth.models import User
from django.db import models

class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50, unique=False)
    color = models.CharField(max_length=7, default='#000000')  # ej: '#FF5733'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Evitar que el mismo usuario tenga dos tags con el mismo nombre
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return f'[{self.user.username}] {self.name}'
```

#### Paso 4 — Generar y aplicar la migración

```bash
# Generar el archivo de migración
docker compose exec web python manage.py makemigrations tags

# Ver el SQL que va a ejecutar antes de aplicar
docker compose exec web python manage.py sqlmigrate tags 0001

# Aplicar
docker compose exec web python manage.py migrate
```

#### Paso 5 — Crear el serializer (`apps/tags/serializers.py`)

```python
from rest_framework import serializers
from apps.tags.models import Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Tag name cannot be empty.')
        return value.strip().lower()

    def validate_color(self, value):
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError('Color must be a valid hex code (e.g. #FF5733).')
        return value
```

#### Paso 6 — Crear la vista (`apps/tags/views.py`)

```python
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from apps.tags.models import Tag
from apps.tags.serializers import TagSerializer
from core.permissions import IsOwner
from core.responses import ApiResponse

class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return ApiResponse.success(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return ApiResponse.success(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        return ApiResponse.success(data=self.get_serializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return ApiResponse.success(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return ApiResponse.success(status=status.HTTP_204_NO_CONTENT)
```

#### Paso 7 — Registrar las URLs (`apps/tags/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tags import views

router = DefaultRouter()
router.register(r'', views.TagViewSet, basename='tag')

urlpatterns = [path('', include(router.urls))]
```

#### Paso 8 — Conectar al router principal (`config/urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/todos/', include('apps.todos.urls')),
    path('api/tags/', include('apps.tags.urls')),  # ← nuevo
]
```

Listo. Los endpoints `GET/POST /api/tags/` y `GET/PUT/PATCH/DELETE /api/tags/{id}/` ya están activos.

---

### Cómo hace queries el ORM de Django

El ORM de Django convierte objetos Python en SQL. No tenés que escribir SQL directamente.

```python
from apps.todos.models import Todo
from django.contrib.auth.models import User

# ── Obtener registros ──────────────────────────────────────────────────────────

# SELECT * FROM todos_todo
Todo.objects.all()

# SELECT * FROM todos_todo WHERE user_id = 1
Todo.objects.filter(user_id=1)

# SELECT * FROM todos_todo WHERE user_id = 1 AND completed = true
Todo.objects.filter(user=request.user, completed=True)

# SELECT * FROM todos_todo WHERE id = 5 (lanza Todo.DoesNotExist si no existe)
Todo.objects.get(pk=5)

# SELECT * FROM todos_todo WHERE id = 5 (retorna None si no existe, nunca lanza)
Todo.objects.filter(pk=5).first()

# SELECT * FROM todos_todo WHERE title LIKE '%django%' (case-insensitive)
Todo.objects.filter(title__icontains='django')

# SELECT * FROM todos_todo ORDER BY created_at DESC LIMIT 10
Todo.objects.order_by('-created_at')[:10]

# SELECT COUNT(*) FROM todos_todo WHERE user_id = 1
Todo.objects.filter(user=request.user).count()

# ── Crear registros ────────────────────────────────────────────────────────────

# INSERT INTO todos_todo (user_id, title, ...) VALUES (...)
todo = Todo.objects.create(user=request.user, title='Nueva tarea')

# Alternativa: crear instancia y guardar (útil cuando querés hacer validaciones antes)
todo = Todo(user=request.user, title='Nueva tarea')
todo.full_clean()   # ejecuta validaciones del model
todo.save()         # INSERT

# ── Actualizar registros ───────────────────────────────────────────────────────

# UPDATE todos_todo SET completed = true WHERE id = 5
todo = Todo.objects.get(pk=5)
todo.completed = True
todo.save()

# UPDATE masivo (más eficiente que cargar y guardar uno por uno)
Todo.objects.filter(user=request.user).update(completed=True)

# ── Eliminar registros ─────────────────────────────────────────────────────────

# DELETE FROM todos_todo WHERE id = 5
todo = Todo.objects.get(pk=5)
todo.delete()

# DELETE masivo
Todo.objects.filter(user=request.user, completed=True).delete()

# ── Relacionar modelos ─────────────────────────────────────────────────────────

# Acceder a los todos de un usuario via related_name='todos'
user = User.objects.get(username='alice')
user.todos.all()                    # SELECT * FROM todos_todo WHERE user_id = ?
user.todos.filter(completed=False)  # con filtro adicional

# Acceder al usuario desde un todo
todo = Todo.objects.get(pk=1)
todo.user.username  # SELECT * FROM auth_user WHERE id = ? (lazy load)
```

**Lookup fields útiles** (se usan en `filter(campo__lookup=valor)`):

| Lookup | SQL equivalente |
|---|---|
| `exact` (default) | `= valor` |
| `iexact` | `= valor` (case-insensitive) |
| `contains` | `LIKE '%valor%'` |
| `icontains` | `ILIKE '%valor%'` |
| `startswith` | `LIKE 'valor%'` |
| `gt`, `gte`, `lt`, `lte` | `>`, `>=`, `<`, `<=` |
| `in` | `IN (v1, v2, ...)` |
| `isnull` | `IS NULL` / `IS NOT NULL` |

---

### Cómo crear validaciones

En DRF hay tres lugares donde validar datos:

#### 1. Validación de campo individual — `validate_<nombre_campo>()`

Se ejecuta solo para ese campo, recibe el valor ya deserializado.

```python
class TodoSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError('Title cannot be empty.')
        if len(value) > 255:
            raise serializers.ValidationError('Title is too long.')
        return value.strip()  # siempre retornar el valor (limpio si es necesario)
```

#### 2. Validación cruzada entre campos — `validate()`

Recibe `attrs`: un dict con todos los campos ya validados individualmente.

```python
class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError(
                {'end_date': 'end_date must be after start_date.'}
            )
        return attrs
```

#### 3. Validators reutilizables

Funciones que se pasan al campo y se reutilizan en múltiples serializers.

```python
import re
from rest_framework import serializers

def validate_hex_color(value):
    if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
        raise serializers.ValidationError('Must be a valid hex color (e.g. #FF5733).')
    return value

class TagSerializer(serializers.ModelSerializer):
    # Se puede pasar la función directamente al campo
    color = serializers.CharField(validators=[validate_hex_color])
```

#### 4. UniqueTogetherValidator

Para validar unicidad de combinación de campos (equivale al `unique_together` del modelo):

```python
from rest_framework.validators import UniqueTogetherValidator

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color')
        validators = [
            UniqueTogetherValidator(
                queryset=Tag.objects.all(),
                fields=['user', 'name'],
                message='You already have a tag with this name.'
            )
        ]
```

---

### Ciclo completo de migraciones

Las migraciones son la forma que tiene Django de versionar los cambios en los modelos y aplicarlos a la base de datos.

```bash
# ── Crear una migración ────────────────────────────────────────────────────────

# 1. Modificar el modelo (ej: agregar campo 'priority' a Todo)
#    En apps/todos/models.py:
#    priority = models.IntegerField(default=0, choices=[(0,'Low'),(1,'Medium'),(2,'High')])

# 2. Generar el archivo de migración
docker compose exec web python manage.py makemigrations todos
# Crea: apps/todos/migrations/0002_todo_priority.py

# 3. Previsualizar el SQL antes de aplicar (útil para entender qué va a hacer)
docker compose exec web python manage.py sqlmigrate todos 0002

# 4. Aplicar la migración a la base de datos
docker compose exec web python manage.py migrate

# ── Ver estado de migraciones ──────────────────────────────────────────────────

# Lista todas las migraciones y cuáles están aplicadas ([X]) o pendientes ([ ])
docker compose exec web python manage.py showmigrations

# Solo ver las de una app específica
docker compose exec web python manage.py showmigrations todos

# ── Deshacer una migración (rollback) ──────────────────────────────────────────

# Volver al estado anterior a 0002 (aplica 0001 como último estado)
docker compose exec web python manage.py migrate todos 0001

# ── Generar migraciones para todas las apps a la vez ──────────────────────────
docker compose exec web python manage.py makemigrations
```

**Reglas importantes:**
- Nunca edites un archivo de migración ya aplicado en producción.
- Commitear los archivos de migración junto con los cambios del modelo.
- Si dos desarrolladores crean migraciones en paralelo, Django las maneja con un `merge` migration:
  ```bash
  python manage.py makemigrations --merge
  ```

---

## Testing

### Librerías utilizadas

| Librería | Rol |
|---|---|
| **pytest** | Runner de tests. Más potente que `unittest`, mejor output, fixtures declarativas |
| **pytest-django** | Plugin que conecta pytest con Django (manejo de DB, settings, `django_db` marker) |
| **factory-boy** | Crea objetos de prueba (factories). Reemplaza fixtures estáticas/JSON que se desactualizan |
| **pytest-cov** | Reportes de cobertura de código |

> **¿Por qué pytest en lugar del `TestCase` de Django?**
> Django trae su propio runner basado en `unittest.TestCase`. pytest es más moderno:
> fixtures como funciones (en vez de `setUp`/`tearDown`), marcadores, mejor output.
> Con `pytest-django`, podés usar `@pytest.mark.django_db` en lugar de heredar de `TestCase`.

### Estructura de tests

```
apps/
  users/tests/
    factories.py      ← UserFactory (genera usuarios de prueba)
    test_serializers.py  ← tests unitarios
    test_views.py        ← tests de integración
  todos/tests/
    factories.py      ← TodoFactory
    test_serializers.py
    test_views.py
pytest.ini            ← configuración de pytest
```

### Correr los tests

```bash
# Correr todos los tests
docker compose exec web pytest

# Con reporte de cobertura en terminal
docker compose exec web pytest --cov=apps --cov-report=term-missing

# Solo una app
docker compose exec web pytest apps/todos/

# Solo un archivo
docker compose exec web pytest apps/todos/tests/test_views.py

# Solo un test específico
docker compose exec web pytest apps/todos/tests/test_views.py::TestTodoList::test_returns_only_own_todos

# Mostrar print() dentro de tests (útil para debug)
docker compose exec web pytest -s

# Parar en el primer fallo
docker compose exec web pytest -x
```

### Tests unitarios vs integración

| | Unitario | Integración |
|---|---|---|
| **Qué testea** | Una clase/función aislada | Un endpoint HTTP completo |
| **Capa** | Serializer, model, validator | View → Serializer → DB |
| **Velocidad** | Más rápido (sin HTTP) | Más lento |
| **Ejemplo en este proyecto** | `test_serializers.py` | `test_views.py` |

### Cómo escribir un test

#### Test unitario de un serializer

```python
# Sin @pytest.mark.django_db si no hace queries a la BD
class TestMiSerializer:

    def test_campo_requerido(self):
        serializer = MiSerializer(data={})   # datos inválidos
        assert not serializer.is_valid()
        assert 'campo' in serializer.errors

    def test_dato_valido(self):
        serializer = MiSerializer(data={'campo': 'valor'})
        assert serializer.is_valid(), serializer.errors  # el mensaje ayuda a debuggear
```

#### Test de integración de un endpoint

```python
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.tests.factories import UserFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client(api_client, db):
    user = UserFactory()
    api_client.force_authenticate(user=user)  # bypass JWT, testea tu lógica, no SimpleJWT
    return api_client

@pytest.mark.django_db
class TestMiEndpoint:

    def test_get_lista(self, auth_client):
        response = auth_client.get('/api/mi-recurso/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)
```

### Factories con factory-boy

Las factories generan datos de prueba de forma programática. Evitan tener que crear objetos manualmente en cada test o mantener fixtures JSON desactualizadas.

```python
# Crear un usuario con datos automáticos
user = UserFactory()
# → username='user0', email='user0@example.com', password='TestPass123!'

# Sobreescribir campos específicos
admin = UserFactory(username='admin', email='admin@company.com')

# Crear múltiples instancias
users = UserFactory.create_batch(5)

# Crear un todo con usuario propio (SubFactory crea el user si no se pasa)
todo = TodoFactory()

# Crear un todo asignado a un usuario existente
todo = TodoFactory(user=mi_usuario, title='Tarea especial', completed=True)
```

**Cómo crear una factory nueva:**

```python
# apps/tags/tests/factories.py
import factory
from apps.tags.models import Tag
from apps.users.tests.factories import UserFactory

class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'tag-{n}')  # garantiza unicidad
    color = '#FF5733'
```

### Cobertura de código

```bash
# Reporte en terminal con líneas no cubiertas
docker compose exec web pytest --cov=apps --cov-report=term-missing

# Reporte HTML (útil para ver qué líneas específicas no están cubiertas)
docker compose exec web pytest --cov=apps --cov-report=html
# Genera htmlcov/index.html — abrir en browser
```

Ejemplo de output:

```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
apps/todos/models.py                   14      0   100%
apps/todos/serializers.py              10      0   100%
apps/todos/views.py                    35      2    94%
apps/users/serializers.py             30      0   100%
apps/users/views.py                   45      3    93%
-------------------------------------------------------
TOTAL                                 134      5    96%
```

### Buenas prácticas de testing

- **Un test = una aserción conceptual.** Un test con 10 asserts es difícil de debuggear cuando falla.
- **`assert serializer.is_valid(), serializer.errors`** — el segundo argumento es el mensaje si el assert falla. Evita "assert failed" sin contexto.
- **`force_authenticate(user=user)`** — no uses JWT real en los tests. Estás testeando tu código, no SimpleJWT.
- **Factories en vez de fixtures JSON** — las factories son código, se refactorizan. Los JSON fixtures se desactualizan silenciosamente.
- **No testees código de terceros** — no escribas tests para que DRF o Django funcionen. Testea que TU código los usa correctamente.
- **Nombres descriptivos** — `test_retrieve_other_user_todo_returns_404` dice exactamente qué hace el test y cuál es el resultado esperado.

### La base de datos de tests

Este es un punto que confunde mucho al principio: **los tests NO usan `tododb`**, la base de datos que levantaste con Docker.

#### Cómo funciona

Cuando corrés `pytest`, Django crea automáticamente una base de datos separada llamada `test_tododb` (prefija `test_` al `DB_NAME` de `.env`). Esta DB:

1. Se crea al inicio de la sesión de tests con todas las migraciones aplicadas.
2. Cada test que usa `@pytest.mark.django_db` corre dentro de una **transacción que se hace rollback** al finalizar. El dato escrito en un test no persiste al siguiente.
3. Se destruye al terminar todos los tests.

```
pytest arranca
    │
    ├── Django crea test_tododb (aplica todas las migraciones)
    │
    ├── test_1 empieza  ←─┐
    │   User.objects.create(...)  │ wrapeado en transacción
    │   assert ...                │
    │   test_1 termina ─── ROLLBACK ─┘ (dato eliminado)
    │
    ├── test_2 empieza  ←─┐  (DB limpia)
    │   ...                │
    │   test_2 termina ─── ROLLBACK
    │
    └── pytest termina → test_tododb eliminada
```

Esto significa que:
- Cada test arranca con la DB **vacía** (solo las tablas, sin datos).
- No hay que hacer limpieza manual entre tests.
- Los tests son **independientes entre sí** por diseño.

#### @pytest.mark.django_db

Sin este marker, cualquier acceso a la DB lanza un error. Esto es intencional: fuerza a ser explícito sobre qué tests necesitan DB.

```python
# ✗ Falla: no tiene acceso a DB
def test_sin_marker():
    User.objects.all()  # DatabaseError

# ✓ Funciona
@pytest.mark.django_db
def test_con_marker():
    User.objects.all()  # OK

# ✓ En clases, el marker se pone una vez arriba
@pytest.mark.django_db
class TestMiVista:
    def test_uno(self): ...
    def test_dos(self): ...

# ✓ La fixture 'db' también da acceso (para fixtures que crean datos)
@pytest.fixture
def user(db):
    return UserFactory()
```

#### Transacciones reales en tests

Por defecto, el rollback se hace a nivel de savepoint (no transacción real), lo que es más rápido pero no testea código que depende de signals de commit o transacciones anidadas. Para esos casos:

```python
@pytest.mark.django_db(transaction=True)
def test_con_transaccion_real():
    # Este test hace commit real; la limpieza se hace borrando todos los datos
    # al finalizar, no con rollback. Es más lento pero necesario si tu código
    # usa on_commit() o transacciones explícitas.
    ...
```

#### Ver en qué DB está corriendo

```bash
# Durante los tests, podés imprimir la DB que usa Django:
docker compose exec web python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from django.db import connection
print(connection.settings_dict['NAME'])
"
# Output: tododb (la DB real, fuera de tests)

# Dentro de pytest con -s:
# django.test.utils crea test_tododb automáticamente
```

#### Reusar la DB de tests (para correr tests más rápido)

Crear y destruir la DB toma tiempo. Con `--reuse-db` (requiere `pytest-django`):

```bash
# Primera vez: crea test_tododb y aplica migraciones
docker compose exec web pytest --reuse-db

# Segunda vez: reutiliza la DB existente (más rápido)
docker compose exec web pytest --reuse-db

# Si cambiaste modelos (nueva migración), forzar recreación:
docker compose exec web pytest --reuse-db --create-db
```

---

## Debugging — machete

### Ver logs del servidor

```bash
# Seguir logs en tiempo real (Ctrl+C para salir)
docker compose logs -f web

# Ver los últimos 50 logs
docker compose logs --tail=50 web

# Ver logs de ambos servicios a la vez
docker compose logs -f

# Ver solo los logs de un request específico (grep por ruta)
docker compose logs web | grep "/api/todos"
```

#### Qué mirar en los logs de Django

Un log de request típico se ve así:

```
web-1  | [03/Jun/2026 13:05:12] "POST /api/auth/login/ HTTP/1.1" 200 312
web-1  | [03/Jun/2026 13:05:15] "GET /api/todos/ HTTP/1.1" 401 89
web-1  | [03/Jun/2026 13:05:20] "POST /api/todos/ HTTP/1.1" 400 145
```

Formato: `[timestamp] "MÉTODO /ruta/ PROTOCOLO" STATUS_CODE bytes_de_respuesta`

Códigos que buscar:
- `200` / `201` — OK / Creado correctamente
- `400` — Bad Request: validación falló, payload malformado
- `401` — Unauthorized: falta o es inválido el token JWT
- `403` — Forbidden: token válido pero sin permisos sobre el objeto
- `404` — Not Found: objeto no existe (o pertenece a otro usuario)
- `500` — Error interno del servidor → mirar el traceback en los logs

#### Traceback de un error 500

Cuando hay un error no manejado, Django imprime el traceback completo:

```
web-1  | Internal Server Error: /api/todos/
web-1  | Traceback (most recent call last):
web-1  |   File "/usr/local/lib/python3.12/site-packages/django/core/handlers/exception.py", line 55, in inner
web-1  |     response = get_response(request)
web-1  |   File "/app/apps/todos/views.py", line 42, in create
web-1  |     serializer.save(user=request.user)
web-1  |   File "...", line 212, in save
web-1  |     ...
web-1  | AttributeError: 'NoneType' object has no attribute 'id'
```

Lo que mirar:
1. La última línea — el tipo de error y el mensaje.
2. `File "/app/apps/..."` — el archivo de tu código donde ocurrió.
3. El número de línea.

### Django shell — REPL con acceso completo

El shell de Django es un intérprete Python con el proyecto cargado. Ideal para probar queries, ver datos reales, debuggear comportamiento del ORM.

```bash
docker compose exec web python manage.py shell
```

Dentro del shell:

```python
# Importar modelos
from apps.todos.models import Todo
from django.contrib.auth.models import User

# Ver todos los usuarios
User.objects.all()
User.objects.values('id', 'username', 'email')

# Ver todos los todos de alice
alice = User.objects.get(username='alice')
alice.todos.all()

# Ver el SQL que ejecuta una query
qs = Todo.objects.filter(user=alice, completed=False)
print(qs.query)
# → SELECT "todos_todo"."id", ... FROM "todos_todo"
#   WHERE "todos_todo"."user_id" = 1 AND NOT "todos_todo"."completed"

# Crear datos de prueba directamente
user = User.objects.create_user('testuser', 'test@test.com', 'pass123')
Todo.objects.create(user=user, title='Test desde shell')

# Ver todas las queries SQL ejecutadas en esta sesión
from django.db import connection
for q in connection.queries:
    print(q['sql'])
```

### Logging de queries SQL en desarrollo

Podés ver cada query que Django hace en tiempo real agregando esto a `config/settings.py`:

```python
# Solo activar cuando DEBUG=True
if DEBUG:
    LOGGING = {
        'version': 1,
        'handlers': {
            'console': {'class': 'logging.StreamHandler'},
        },
        'loggers': {
            'django.db.backends': {
                'level': 'DEBUG',
                'handlers': ['console'],
            },
        },
    }
```

Con esto en los logs verás cada SQL en tiempo real:

```
web-1  | (0.001) SELECT "todos_todo"."id", "todos_todo"."title" ...
web-1  |         FROM "todos_todo" WHERE "todos_todo"."user_id" = 1; args=(1,)
```

> **Tip**: activar esto en producción puede exponer datos sensibles en los logs. Solo usar con `DEBUG=True`.

### Conectarse directo a PostgreSQL

```bash
# Abrir psql
docker compose exec db psql -U todouser -d tododb

# Comandos útiles dentro de psql:
\dt              -- listar tablas
\d todos_todo    -- describir estructura de una tabla
SELECT * FROM auth_user;
SELECT * FROM todos_todo ORDER BY created_at DESC LIMIT 5;
\q               -- salir
```

### Debuggear dentro del código con breakpoint()

Python 3.7+ tiene `breakpoint()` built-in, que lanza el debugger `pdb`:

```python
# En apps/todos/views.py
def create(self, request, *args, **kwargs):
    breakpoint()  # ← ejecución se pausa aquí
    serializer = self.get_serializer(data=request.data)
    ...
```

```bash
# Para que funcione, el contenedor tiene que correr sin -d (en foreground)
docker compose up  # sin -d

# Cuando el código llegue a breakpoint(), la terminal muestra:
# (Pdb) _
```

Comandos de pdb:
```
n          → next: ejecutar la línea siguiente
s          → step: entrar dentro de la función
c          → continue: seguir hasta el próximo breakpoint
p variable → print: imprimir el valor de una variable
pp obj     → pretty-print: útil para dicts/listas
l          → list: mostrar las líneas de código alrededor
q          → quit: salir del debugger
```

### Inspeccionar un request desde la vista

```python
def create(self, request, *args, **kwargs):
    print("Headers:", dict(request.headers))
    print("Data:", request.data)
    print("User:", request.user)
    print("Auth:", request.auth)  # el token JWT decodificado
    ...
```

Los `print()` aparecen en `docker compose logs -f web`.

### Checklist de debugging

Cuando algo no funciona, revisar en este orden:

```
1. ¿Cuál es el status code de la respuesta?
   → curl -s -w "\nHTTP: %{http_code}\n" ...

2. ¿Cuál es el body de la respuesta?
   → curl -s ... | python3 -m json.tool

3. ¿Hay traceback en los logs?
   → docker compose logs --tail=30 web

4. ¿El token es válido? ¿Expiró?
   → Decodificar en https://jwt.io (solo con tokens de dev)

5. ¿La migración está aplicada?
   → docker compose exec web python manage.py showmigrations

6. ¿El dato existe en la DB?
   → docker compose exec db psql -U todouser -d tododb
   → SELECT * FROM <tabla>;

7. ¿Qué query está ejecutando Django?
   → docker compose exec web python manage.py shell
   → print(MiModelo.objects.filter(...).query)
```

---

## Tokens JWT — cómo funciona el flujo

```
┌─────────┐   POST /login (user+pass)    ┌──────────┐
│ Cliente │ ──────────────────────────► │  Server  │
│         │ ◄────────────────────────── │          │
│         │   {access: "...", refresh: "..."}       │
│         │                             │          │
│         │   GET /todos/ (Bearer access)│          │
│         │ ──────────────────────────► │          │
│         │ ◄────────────────────────── │          │
│         │   [{id:1, title:...}, ...]  │          │
│         │                             │          │
│         │   (access expira en 60 min) │          │
│         │                             │          │
│         │   POST /token/refresh/      │          │
│         │   (Bearer refresh)          │          │
│         │ ──────────────────────────► │          │
│         │ ◄────────────────────────── │          │
│         │   {access: "nuevo...",      │          │
└─────────┘    refresh: "nuevo..."}     └──────────┘
```

- El **access token** dura 60 minutos. Se manda en cada request como `Authorization: Bearer <token>`.
- El **refresh token** dura 7 días. Solo se usa para obtener un nuevo par de tokens.
- Al hacer logout, el refresh token se agrega a una **blacklist** en la BD y ya no puede usarse.
- El access token **no se puede invalidar** (es stateless). Por eso su vida corta es importante.
