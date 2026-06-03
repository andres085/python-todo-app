from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from apps.todos.models import Todo

SEED_USERS = [
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Seed1234!",
        "todos": [
            {
                "title": "Aprender Django REST Framework",
                "description": "Completar el tutorial oficial y entender ViewSets, serializers y routers.",
                "completed": True,
            },
            {
                "title": "Implementar autenticación JWT",
                "description": "Usar SimpleJWT con access token de 60 min y refresh de 7 días.",
                "completed": True,
            },
            {
                "title": "Escribir tests de integración",
                "description": "Cubrir todos los endpoints de la API con pytest y factory-boy.",
                "completed": False,
            },
            {
                "title": "Agregar paginación a los endpoints",
                "description": "Configurar PageNumberPagination en DRF para /api/todos/.",
                "completed": False,
            },
        ],
    },
    {
        "username": "bob",
        "email": "bob@example.com",
        "password": "Seed1234!",
        "todos": [
            {
                "title": "Leer sobre PostgreSQL indexing",
                "description": "Entender cuándo usar B-tree vs GIN vs GiST y cómo medirlo con EXPLAIN ANALYZE.",
                "completed": True,
            },
            {
                "title": "Optimizar queries N+1",
                "description": "Identificar y corregir con select_related y prefetch_related.",
                "completed": False,
            },
            {
                "title": "Configurar pre-commit hooks",
                "description": "ruff para linting + black para formato, que corran antes de cada commit.",
                "completed": False,
            },
        ],
    },
    {
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "Seed1234!",
        "todos": [
            {
                "title": "Revisar el PR de alice",
                "description": "Code review del branch feature/pagination antes del merge.",
                "completed": True,
            },
            {
                "title": "Configurar CI con GitHub Actions",
                "description": "Pipeline con tres jobs: tests, linting y reporte de cobertura.",
                "completed": False,
            },
            {
                "title": "Documentar el flujo de autenticación",
                "description": "Diagrama de secuencia: login → access token → refresh → logout.",
                "completed": False,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Carga datos de prueba (3 usuarios con todos). Solo corre cuando DEBUG=True."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "El comando seed solo puede correr con DEBUG=True. "
                "Revisá tu archivo .env antes de continuar."
            )

        self.stdout.write("Cargando seed data...\n")

        for user_data in SEED_USERS:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={"email": user_data["email"]},
            )

            if not created:
                self.stdout.write(f"  • {user.username} ya existe, salteando.")
                continue

            user.set_password(user_data["password"])
            user.save()

            todos_created = 0
            for todo_data in user_data["todos"]:
                _, todo_new = Todo.objects.get_or_create(
                    user=user,
                    title=todo_data["title"],
                    defaults={
                        "description": todo_data["description"],
                        "completed": todo_data["completed"],
                    },
                )
                if todo_new:
                    todos_created += 1

            self.stdout.write(
                f"  • {user.username} ({user.email}) — {todos_created} todos creados"
            )

        self.stdout.write(self.style.SUCCESS("\n✓ Seed completado."))
        self.stdout.write(
            "\nCredenciales de prueba:\n"
            "  username: alice / bob / charlie\n"
            "  password: Seed1234!\n"
        )
