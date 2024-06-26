from uuid import UUID

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from projects.models import Project
from projects.serializers import ProjectSerializer
from tasks.subtasks import handle_global_calendar_response
from .models import User
from .serializers import UserSerializer, UserMinimalSerializer, UserDeserializer


@api_view(["GET"])
def test(_request: Request) -> Response:
    """Endpoint de prueba."""
    return Response({"message": "mango para siempre tío"}, status=status.HTTP_200_OK)


class UsersView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return []
        return [IsAuthenticated()]

    def post(self, request: Request) -> Response:
        """
        Crea un usuario.

        Campos:
        - email
        - password
        - first_names
        - last_names
        """
        data = request.data
        serializer = UserDeserializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_user = serializer.save()

        return Response({
            "id": new_user.id,
            "token": str(AccessToken.for_user(new_user))
        }, status=status.HTTP_201_CREATED)

    def get(self, _request: Request) -> Response:
        """Obtiene todos los usuarios"""
        users = User.objects.filter(is_superuser=False)
        serializer = UserMinimalSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Obtiene la información del usuario autenticado."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request) -> Response:
        """Actualiza la información del usuario autenticado."""
        if "profile_picture" in request.data and request.user.profile_picture == request.data["profile_picture"]:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if "password" in request.data:
            return Response(
                {"message": "No se puede actualizar la contraseña por este medio."},
                status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDeserializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user_projects(request: Request) -> Response:
    """Obtiene los proyectos del usuario autenticado."""
    user = request.user
    
    projects = user.member_of.filter(parent__isnull=True)
    serializer = ProjectSerializer(projects, many=True)
    leaded_projects = user.leader_of.filter(parent__isnull=True).values_list("id", flat=True)

    for project in serializer.data:
        project["isLeader"] = UUID(project["id"]) in leaded_projects

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_search_select_pool(request: Request) -> Response:
    """Obtiene los usuarios disponibles para ser seleccionados en un campo de búsqueda."""
    project_id = request.query_params.get("project", "none")
    project = None

    if project_id != "none":
        try:
            project = Project.objects.get(id=project_id).parent
        except Project.DoesNotExist:
            return Response({"message": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    if not project:
        users = User.objects.filter(is_superuser=False)
        serializer = UserMinimalSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    members = project.members.all()
    serializer = UserMinimalSerializer(members, many=True, context={"project": project})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user_global_calendar(request: Request) -> Response:
    """Obtiene el calendario global del usuario autenticado."""
    response = {}
    handle_global_calendar_response(request, response)
    return Response(response, status=status.HTTP_200_OK)
