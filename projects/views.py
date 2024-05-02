from django.db.models.query import QuerySet
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from devotion.apis import delete_calendar, GoogleAPIException
from tasks.serializers import SubtaskViewSerializer, calendar_view_type, kanban_view_type
from users.serializers import UserSerializer, UserMinimalSerializer
from .models import Project
from .serializers import ProjectSerializer, ProjectDeserializer


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

    parent_id = serializer.validated_data.get("parent")
    if parent_id is not None and not request.user.is_superuser:
        parent = Project.objects.get(id=parent_id)
        if request.user not in parent.leaders.all():
            return Response(
                {"message": "No eres líder del proyecto papá."},
                status=status.HTTP_403_FORBIDDEN)

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

    def get(self, request: Request, project_id: str) -> Response:
        """Obtiene la información de un proyecto."""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        view_type = request.query_params.get("view", "table")
        partial_response = request.query_params.get("partial", "false") == "true"

        if partial_response:
            response = {}
        else:
            response = ProjectSerializer(project).data
            response.update({
                "breadcrumbs": get_project_breadcrumbs(project),
                "progress": project.progress,
                "leaders": UserMinimalSerializer(project.leaders.all(), many=True).data,
                "members": UserMinimalSerializer(project.members.all(), many=True).data,
                "projects": ProjectSerializer(project.projects.all(), many=True).data
            })

        if view_type == "calendar":
            calendar_view_type(response, project)
        elif view_type == "kanban":
            kanban_view_type(response, project)
        else:
            response["tasks"] = SubtaskViewSerializer(
                project.tasks.filter(parent_task__isnull=True),
                many=True
            ).data

        return Response(response, status=status.HTTP_200_OK)

    def put(self, request: Request, project_id: str) -> Response:
        """Actualiza la información de un proyecto."""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not user.is_superuser and user not in project.leaders.all():
            return Response(
                {"message": "No eres líder de este proyecto."},
                status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectDeserializer(project, data=request.data, partial=True)
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
            return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not user.is_superuser and user not in project.leaders.all():
            return Response(
                {"message": "No eres líder de este proyecto."},
                status=status.HTTP_403_FORBIDDEN)

        calendar_id = project.calendar_id
        project.delete()

        try:
            delete_calendar(calendar_id)
        except GoogleAPIException:
            return Response(
                {"message": "Error al eliminar el calendario."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_project_members(request: Request, project_id: str) -> Response:
    """Obtiene todos los usuarios de un proyecto."""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    members = project.members.all()

    if not user.is_superuser and user not in members:
        return Response(
            {"message": "No eres miembro de este proyecto."},
            status=status.HTTP_403_FORBIDDEN)

    serializer = UserSerializer(members, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_subtree_tasks(_request: Request, project_id: str) -> Response:
    """Obtiene todas las tareas de un proyecto y sus subproyectos."""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    all_tasks: QuerySet = project.tasks.all()

    def recurse_project(_project: Project) -> None:
        nonlocal all_tasks
        for subproject in _project.projects.all():
            recurse_project(subproject)
            all_tasks |= _project.tasks.all()

    recurse_project(project)
    serializer = SubtaskViewSerializer(all_tasks, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
