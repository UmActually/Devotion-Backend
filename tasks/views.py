from django.db.models.query import QuerySet
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from projects.models import Project
from .models import Task, TaskStatus
from .serializers import TaskSerializer, TaskViewSerializer, TaskDeserializer


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
    - asignee
    """
    data = request.data
    serializer = TaskDeserializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    parent_project_id = serializer.validated_data["parent_project"]
    if not user.is_superuser:
        parent_project = Project.objects.get(id=parent_project_id)
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

    def get(self, _request: Request, task_id: str) -> Response:
        """Obtiene la información de una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskViewSerializer(task)
        response = serializer.data

        response["breadcrumbs"] = get_task_breadcrumbs(task)
        response["tasks"] = TaskViewSerializer(task.tasks.all(), many=True).data

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
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, task_id: str) -> Response:
        """Elimina una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not user.is_superuser and user not in task.parent_project.leaders.all():
            return Response(
                {"message": "No eres líder de este proyecto."},
                status=status.HTTP_403_FORBIDDEN)

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_task_status(request: Request, task_id: str) -> Response:
    """Actualiza el estado de una tarea."""
    if "status" not in request.data:
        return Response({"message": "Campo 'status' faltante."}, status=status.HTTP_400_BAD_REQUEST)

    new_status = request.data["status"]

    if new_status not in TaskStatus.values:
        return Response({"message": "Valor de status inválido."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"message": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    is_leader = user.is_superuser or user in task.parent_project.leaders.all()
    if user != task.asignee and not is_leader:
        return Response(
            {"message": "No eres el asignado de esta tarea, o líder del proyecto."},
            status=status.HTTP_403_FORBIDDEN)

    old_status = task.status

    if not is_leader and (old_status == TaskStatus.DONE or new_status == TaskStatus.DONE):
        return Response(
            {"message": "Solo los líderes pueden marcar tareas como completadas, o desmarcarlas."},
            status=status.HTTP_403_FORBIDDEN)

    task.status = new_status
    task.save()

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
    serializer = TaskViewSerializer(all_tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
