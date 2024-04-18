from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from users.serializers import UserSerializer
from .models import Project
from .serializers import ProjectSerializer, ProjectDeserializer
from tasks.serializers import TaskViewSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_project(request: Request) -> Response:
    """
    Crea un proyecto.

    Campos:
    - name
    - description
    - parent (opcional)
    - leaders
    - members
    """
    data = request.data
    serializer = ProjectDeserializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # TODO: Validar, si es un subproyecto, que el usuario sea líder

    new_project = serializer.save()
    serializer = ProjectSerializer(new_project)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def get_project_breadcrumbs(project: Project) -> list[tuple[str, str, bool]]:
    breadcrumbs = [(project.id, project.name, False)]
    project = project.parent
    while project is not None:
        breadcrumbs.append((project.id, project.name, False))
        project = project.parent

    breadcrumbs.reverse()
    return breadcrumbs


class ProjectView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return [IsAuthenticated()]

    def get(self, _request: Request, project_id: str) -> Response:
        """Obtiene la información de un proyecto."""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectSerializer(project)
        response = serializer.data

        response["breadcrumbs"] = get_project_breadcrumbs(project)
        response["projects"] = ProjectSerializer(project.projects.all(), many=True).data
        response["tasks"] = TaskViewSerializer(
            project.tasks.all().filter(parent_task__isnull=True),
            many=True
        ).data

        return Response(response, status=status.HTTP_200_OK)

    def put(self, request: Request, project_id: str) -> Response:
        """Actualiza la información de un proyecto."""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user not in project.leaders.all():
            return Response(
                {"message": "You are not a leader of this project"},
                status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectDeserializer(request.data, instance=project)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project = serializer.save()
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, project_id: str) -> Response:
        """Elimina un proyecto."""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user not in project.leaders.all():
            return Response(
                {"message": "You are not a leader of this project"},
                status=status.HTTP_403_FORBIDDEN)

        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_members(request: Request, project_id: str) -> Response:
    """Obtiene todos los usuarios de un proyecto."""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    members = project.members.all()

    if user not in members:
        return Response(
            {"message": "You are not a member of this project"},
            status=status.HTTP_403_FORBIDDEN)

    serializer = UserSerializer(members, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_subtree_tasks(_request: Request, project_id: str) -> Response:
    """Obtiene todas las tareas de un proyecto y sus subproyectos."""
    try:
        Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    # TODO: Query bien hermoso para buscar en todo el
    #  subárbol de tareas
    return Response([], status=status.HTTP_200_OK)
