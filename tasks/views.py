from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

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
    parent_project = serializer.context["parent_project"]

    if not user.is_superuser:
        if user not in parent_project.members.all():
            return Response(
                {"message": "You are not a member of this project"},
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
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

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
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not user.is_superuser and user not in task.parent_project.leaders.all():
            return Response(
                {"message": "You are not a leader of this project"},
                status=status.HTTP_403_FORBIDDEN)

        data = request.data
        serializer = TaskDeserializer(task, data=data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = serializer.save()

        if "status" in data and data["status"] == TaskStatus.DONE:
            task.parent_project.progress *= len(task.parent_project.tasks)
            task.parent_project.progress += 1
            task.parent_project.progress /= len(task.parent_project.tasks)
            task.parent_project.save()

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, task_id: str) -> Response:
        """Elimina una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not user.is_superuser and user not in task.parent_project.leaders.all():
            return Response(
                {"message": "You are not a leader of this project"},
                status=status.HTTP_403_FORBIDDEN)
        
        task.parent_project.progress *= len(task.parent_project.tasks)
        if task.status == TaskStatus.DONE:
            task.parent_project.progress -= 1
        task.parent_project.progress /= len(task.parent_project.tasks) - 1
        task.parent_project.save()

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_task_status(request: Request, task_id: str) -> Response:
    """Actualiza el estado de una tarea."""

    if "status" not in request.data:
        return Response({"message": "Missing status field"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        new_status = int(request.data["status"])
    except ValueError:
        return Response({"message": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

    if new_status not in TaskStatus.values:
        return Response({"message": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    parent_project = task.parent_project
    is_leader = user.is_superuser or user in parent_project.leaders.all()
    if user != task.asignee and not is_leader:
        return Response(
            {"message": "You are not the asignee or a leader of this project"},
            status=status.HTTP_403_FORBIDDEN)

    old_status = task.status
    if old_status == new_status:
        return Response({"message": "Task is already in this status"}, status=status.HTTP_204_NO_CONTENT)

    if not is_leader and (old_status == TaskStatus.DONE or new_status == TaskStatus.DONE):
        return Response(
            {"message": "Only leaders can mark tasks as done, or undo this action"},
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
        Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    # TODO: Query bien hermoso para buscar en todo el
    #  subárbol de tareas parte 2
    return Response([], status=status.HTTP_200_OK)
