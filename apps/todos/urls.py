from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.todos import views

# DefaultRouter genera automáticamente las URLs del ViewSet:
#   GET    /api/todos/        → list
#   POST   /api/todos/        → create
#   GET    /api/todos/{id}/   → retrieve
#   PUT    /api/todos/{id}/   → update
#   PATCH  /api/todos/{id}/   → partial_update
#   DELETE /api/todos/{id}/   → destroy
router = DefaultRouter()
router.register(r'', views.TodoViewSet, basename='todo')

urlpatterns = [
    path('', include(router.urls)),
]
