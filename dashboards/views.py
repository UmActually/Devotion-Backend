from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from projects.models import Project
from .dashboard import Dashboard


@api_view(["GET"])
def get_project_dashboard(request: Request, project_id: str) -> Response:
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({"message": "El proyecto no existe."}, status=status.HTTP_404_NOT_FOUND)

    if "configuration" in request.data:
        try:
            config_number = int(request.data["configuration"])
        except ValueError:
            return Response(
                {"message": "La configuración de widgets debe ser un número entero."},
                status=status.HTTP_400_BAD_REQUEST)

        project.widget_config = config_number
        project.save()

    dashboard = Dashboard(project, request.user)
    return dashboard.get_response()
