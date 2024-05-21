from django.db.models.query import QuerySet
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from devotion.apis import delete_event, GoogleAPIException
from .models import Task, TaskStatus
from .subtasks import handle_subtasks_response
from .serializers import (
    TaskSerializer, TaskViewSerializer, SubtaskTableSerializer, TaskDeserializer)


def bad_request(message: str) -> Response:
    return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_task(request: Request) -> Response:
    """
    Crea una tarea.

    Campos:
    - name
    - description (opcional)
    - priority (opcional)
    - start_date (opcional)
    - due_date
    - parent_project
    - parent_task (opcional)
    - assignee
    """
    data = request.data
    serializer = TaskDeserializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    parent_project = serializer.context["parent_project"]

    if not user.is_superuser:
        if user not in parent_project.members.all():
            return Response(
                {"message": "No eres miembro de este proyecto."},
                status=status.HTTP_403_FORBIDDEN)

    new_task = serializer.save()
    serializer = TaskSerializer(new_task)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def get_task_breadcrumbs(task: Task) -> list[tuple[str, str, bool]]:
    breadcrumbs = [(task.id, task.name, True)]
    project = task.parent_project
    task = task.parent_task

    while task is not None:
        breadcrumbs.append((task.id, task.name, True))
        task = task.parent_task

    breadcrumbs.append((project.id, "Tareas", False))

    while project is not None:
        breadcrumbs.append((project.id, project.name, False))
        project = project.parent

    breadcrumbs.reverse()
    return breadcrumbs


class TaskView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return [IsAuthenticated()]

    def get(self, request: Request, task_id: str) -> Response:
        """Obtiene la información de una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        response_fields = request.query_params.get("get", "all")
        response = {}

        if response_fields in ("info", "all"):
            response = TaskViewSerializer(task).data

        if response_fields == "all":
            response["breadcrumbs"] = get_task_breadcrumbs(task)

        if response_fields in ("tasks", "all"):
            handle_subtasks_response(request, response, task)

        return Response(response, status=status.HTTP_200_OK)

    def put(self, request: Request, task_id: str) -> Response:
        """Actualiza la información de una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not user.is_superuser and user not in task.parent_project.leaders.all():
            return Response(
                {"message": "No eres líder de este proyecto."},
                status=status.HTTP_403_FORBIDDEN)

        data = request.data
        serializer = TaskDeserializer(task, data=data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = serializer.save()

        if "status" in data and data["status"] == TaskStatus.DONE:
            task_count = task.parent_project.tasks.count()
            task.parent_project.progress *= task_count
            task.parent_project.progress += 1
            task.parent_project.progress /= task_count
            task.parent_project.save()

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, task_id: str) -> Response:
        """Elimina una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        parent_project = task.parent_project
        if not user.is_superuser and user not in parent_project.leaders.all():
            return Response(
                {"message": "No eres líder de este proyecto."},
                status=status.HTTP_403_FORBIDDEN)

        task.delete()

        task_count = parent_project.tasks.count()
        if task_count == 0:
            parent_project.progress = 0
        else:
            parent_project.progress *= task_count + 1
            if task.status == TaskStatus.DONE:
                parent_project.progress -= 100
            parent_project.progress /= task_count
        parent_project.save()

        try:
            delete_event(task)
        except GoogleAPIException:
            return Response(
                {"message": "Error al eliminar el evento."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_task_status(request: Request, task_id: str) -> Response:
    """Actualiza el estado de una tarea."""

    if "status" not in request.data:
        return bad_request("Campo 'status' faltante.")
    try:
        new_status = int(request.data["status"])
    except ValueError:
        return bad_request("Valor de status inválido.")
    if new_status not in TaskStatus.values:
        return bad_request("Valor de status inválido.")

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    parent_project = task.parent_project
    is_leader = user.is_superuser or user in parent_project.leaders.all()
    if user != task.assignee and not is_leader:
        return Response(
            {"message": "No eres el asignado de esta tarea, o líder del proyecto."},
            status=status.HTTP_403_FORBIDDEN)

    old_status = task.status
    if old_status == new_status:
        return Response({"message": "Task is already in this status"}, status=status.HTTP_204_NO_CONTENT)

    if not is_leader and (old_status == TaskStatus.DONE or new_status == TaskStatus.DONE):
        return Response(
            {"message": "Solo los líderes pueden marcar tareas como completadas, o desmarcarlas."},
            status=status.HTTP_403_FORBIDDEN)

    task.status = new_status
    task.save()

    task_count = parent_project.tasks.count()
    if old_status == TaskStatus.DONE:
        parent_project.progress *= task_count
        parent_project.progress -= 100
        parent_project.progress /= task_count
    if new_status == TaskStatus.DONE:
        parent_project.progress *= task_count
        parent_project.progress += 100
        parent_project.progress /= task_count
    parent_project.save()

    serializer = TaskSerializer(task)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_subtree_tasks(_request: Request, task_id: str) -> Response:
    """Obtiene todas las subtareas de una tarea."""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    all_tasks: QuerySet = task.tasks.all()

    def recurse_task(_task: Task) -> None:
        nonlocal all_tasks
        for subtask in _task.tasks.all():
            recurse_task(subtask)
            all_tasks |= _task.tasks.all()

    recurse_task(task)
    serializer = SubtaskTableSerializer(all_tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
