from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AddTaskView, HealthView, NoteViewSet, SlowTaskView, TaskStatusView

router = DefaultRouter()
router.register("notes", NoteViewSet, basename="note")

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("tasks/add/", AddTaskView.as_view(), name="task-add"),
    path("tasks/slow/", SlowTaskView.as_view(), name="task-slow"),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
    path("", include(router.urls)),
]
