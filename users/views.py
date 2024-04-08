from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken

from projects.serializers import ProjectSerializer
from .serializers import UserSerializer, UserDeserializer


@api_view(["GET"])
def test(_request: Request) -> Response:
    """Endpoint de prueba."""
    return Response({"message": "mango foreva"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def create_user(request: Request) -> Response:
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


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Obtiene la información del usuario autenticado."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request: Request) -> Response:
        """Actualiza la información del usuario autenticado."""
        if "password" in request.data:
            return Response(
                {"message": "You cannot update your password here"},
                status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDeserializer(request.data, instance=request.user)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user_projects(request: Request) -> Response:
    """Obtiene los proyectos del usuario autenticado."""
    user = request.user

    # Query que obtiene los proyectos que no tienen parent y donde el usuario
    # autenticado está en los IDs de los miembros o líderes
    projects = (user.leader_of.filter(parent__isnull=True) |
                user.member_of.filter(parent__isnull=True))

    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
