from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Task, TaskStatus
from .serializers import TaskSerializer, TaskDeserializer


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

    # TODO: Validar que el usuario pertenezca al proyecto

    new_project = serializer.save()
    serializer = TaskSerializer(new_project)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request, task_id: str) -> Response:
        """Actualiza la información de una tarea."""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user not in task.parent_project.leaders.all():
            return Response(
                {"message": "You are not a leader of this project"},
                status=status.HTTP_403_FORBIDDEN)

        data = request.data
        serializer = TaskDeserializer(data=data, instance=task)
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
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user not in task.parent_project.leaders.all():
            return Response(
                {"message": "You are not a leader of this project"},
                status=status.HTTP_403_FORBIDDEN)

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_task_status(request: Request, task_id: str) -> Response:
    """Actualiza el estado de una tarea."""
    if "status" not in request.data:
        return Response({"message": "Missing status field"}, status=status.HTTP_400_BAD_REQUEST)

    if request.data["status"] not in TaskStatus.values:
        return Response({"message": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    is_leader = user in task.parent_project.leaders.all()
    if user != task.asignee or not is_leader:
        return Response(
            {"message": "You are not the asignee or a leader of this project"},
            status=status.HTTP_403_FORBIDDEN)

    old_status = task.status
    new_status = request.data["status"]

    if not is_leader and (old_status == TaskStatus.DONE or new_status == TaskStatus.DONE):
        return Response(
            {"message": "Only leaders can mark tasks as done, or undo this action"},
            status=status.HTTP_403_FORBIDDEN)

    task.status = new_status
    task.save()

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
