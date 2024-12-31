from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from devotion.apis import delete_calendar, GoogleAPIException
from users.serializers import UserRoleSerializer
from tasks.subtasks import handle_subtasks_response
from .models import Project
from .serializers import ProjectSerializer, SubprojectSerializer, ProjectDeserializer, ProjectUpdateDeserializer


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

        verbose_typing = request.query_params.get("typing", "false") == "true"
        response_fields = request.query_params.get("get", "all")
        response = {}

        if response_fields in ("info", "all"):
            project_context = {"project": project}
            leaders = set(project.leaders.all())
            members = set(project.members.all()) - leaders
            response = ProjectSerializer(project).data
            response.update({
                "breadcrumbs": get_project_breadcrumbs(project),
                "progress": project.progress,
                "leaders": UserRoleSerializer(leaders, many=True, context=project_context).data,
                "members": UserRoleSerializer(members, many=True, context=project_context).data,
                "projects": SubprojectSerializer(project.projects.all(), many=True).data
            })

        if response_fields in ("tasks", "all"):
            handle_subtasks_response(request, response, project)

        if verbose_typing:
            response = {
                "type": "project",
                "data": response
            }

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

        serializer = ProjectUpdateDeserializer(project, data=request.data, partial=True)
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

        if calendar_id:
            try:
                delete_calendar(calendar_id)
            except GoogleAPIException:
                return Response(
                    {"message": "Error al eliminar el calendario."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)
